import logging
import argparse
import os
import time
from pathlib import Path
import pandas as pd

# Setup logging first
from src.utils.logging_config import setup_logging
setup_logging() # Load config from default path 'config/logging.yaml'

from src.utils.file_io import load_yaml, load_text, save_xml, save_json, save_yaml
from src.nlp.processor import NLProcessor
from src.kg_query.querier import KGQuerier
from src.llm_interaction.llm_client import LLMClient
from src.validation.xsd_validator import load_xsd_schema
from src.validation.drools_validator import DroolsValidator
from src.generation_pipeline.generators import (
    NaiveGenerator, XsdConstrainedGenerator, FullConstrainedGenerator, KgEnhancedGenerator
)
from .dataset_loader import load_requirements
from .metrics_calculator import calculate_metrics

logger = logging.getLogger(__name__)

def get_generator_instance(method_name: str, config: dict, llm_client, kg_querier, xsd_schema, drools_validator):
    """Factory function to get generator instance based on method name."""
    common_args = {
        "config": config,
        "llm_client": llm_client,
        "kg_querier": kg_querier,
        "xsd_schema": xsd_schema,
        "drools_validator": drools_validator
    }
    if method_name == "baseline1": # Naive
        return NaiveGenerator(**common_args)
    elif method_name == "baseline2": # XSD Constrained
        return XsdConstrainedGenerator(**common_args)
    elif method_name == "baseline3": # Full Constrained (XSD + Drools)
        return FullConstrainedGenerator(**common_args)
    elif method_name == "proposed": # KG Enhanced
        return KgEnhancedGenerator(**common_args)
    else:
        logger.error(f"Unknown generator method name: {method_name}")
        raise ValueError(f"Unknown generator method name: {method_name}")

def main(config_path: str):
    """Main function to run the generation experiments."""
    logger.info(f"Starting experiment run with config: {config_path}")
    start_time = time.time()

    # --- 1. Load Configuration ---
    config = load_yaml(config_path)
    if not config:
        logger.critical("Failed to load main configuration. Exiting.")
        return
    paths = config.get("paths", {})
    exp_config = config.get("experiments", {})
    methods_to_run = exp_config.get("methods_to_run", [])

    # --- 2. Initialize Components ---
    logger.info("Initializing components...")
    # NLP Processor
    nlp_processor = NLProcessor() # Add model config if needed from main config

    # LLM Client
    llm_client = LLMClient(config.get("llm", {}), config.get("llm_api_keys", {}))
    if not llm_client.client:
         logger.warning("LLM Client failed to initialize. Some generators might not work.")
         # Decide if this is critical - maybe only run methods that don't need LLM?

    # KG Querier (optional, only needed for 'proposed' method)
    kg_querier = None
    if "proposed" in methods_to_run:
        kg_config = config.get("kg")
        if kg_config and kg_config.get("endpoint"):
            kg_querier = KGQuerier(kg_config)
            if not kg_querier.kg_client: # Check if client setup worked
                 logger.warning("KG Querier client failed to initialize. 'proposed' method might fail.")
        else:
            logger.warning("KG config missing or endpoint not set. 'proposed' method cannot run.")
            methods_to_run.remove("proposed") # Remove if KG is needed but not available

    # XSD Schema (optional, needed for methods >= baseline2)
    xsd_schema = None
    xsd_path = paths.get("schemas")
    if xsd_path and any(m in methods_to_run for m in ["baseline2", "baseline3", "proposed"]):
        xsd_schema = load_xsd_schema(xsd_path)
        if not xsd_schema:
            logger.warning(f"Failed to load XSD schema from {xsd_path}. Generators requiring XSD might fail or skip validation.")

    # Drools Validator (optional, needed for methods >= baseline3)
    drools_validator = None
    drools_config = config.get("validation", {}).get("drools")
    if drools_config and any(m in methods_to_run for m in ["baseline3", "proposed"]):
         # Check if endpoint is configured, as our example implementation needs it
         if drools_config.get("endpoint"):
             drools_validator = DroolsValidator(drools_config)
             logger.info("Drools Validator initialized.")
             # Add a check here to see if the endpoint is reachable? (Optional)
         else:
              logger.warning("Drools endpoint not configured. Generators requiring Drools validation will skip it.")


    # --- 3. Load Dataset ---
    logger.info("Loading requirement dataset...")
    requirements_path = paths.get("requirements")
    ground_truth_path = paths.get("ground_truth") # Optional
    requirements_data = load_requirements(requirements_path, ground_truth_path) # List of dicts
    if not requirements_data:
        logger.critical("No requirements loaded. Exiting.")
        return
    logger.info(f"Loaded {len(requirements_data)} requirements.")

    # --- 4. Run Generation for each Method and Requirement ---
    all_results = []
    output_base_dir = Path(paths.get("generated_xml", "results/generated_xml"))

    for method in methods_to_run:
        logger.info(f"--- Running Method: {method} ---")
        method_output_dir = output_base_dir / method
        os.makedirs(method_output_dir, exist_ok=True)

        try:
            generator = get_generator_instance(method, config, llm_client, kg_querier, xsd_schema, drools_validator)
        except ValueError:
            continue # Skip if generator couldn't be created

        for req_data in requirements_data:
            req_id = req_data["id"]
            req_text = req_data["text"]
            logger.info(f"Processing requirement ID: {req_id} using method: {method}")

            # Parse requirement with NLP
            parsed_req = nlp_processor.parse_requirement(req_text)

            # Generate XML
            gen_start_time = time.time()
            generated_xml, errors = generator.generate(req_text, parsed_req)
            gen_duration = time.time() - gen_start_time

            output_filename = method_output_dir / f"{req_id}_generated.arxml" # Or .xml
            if generated_xml:
                save_xml(generated_xml, output_filename)
                logger.info(f"Saved generated XML to: {output_filename}")
            else:
                logger.error(f"Generation failed for {req_id} with method {method}.")
                # Save errors maybe?
                error_file = method_output_dir / f"{req_id}_errors.json"
                save_json({"errors": errors}, error_file)


            # --- 5. Calculate Metrics ---
            # Metrics calculation might need the ground truth
            ground_truth_xml = req_data.get("ground_truth_content")
            metrics = calculate_metrics(generated_xml, ground_truth_xml, errors, xsd_schema, drools_validator)

            result_record = {
                "requirement_id": req_id,
                "method": method,
                "generation_time_s": round(gen_duration, 3),
                "output_path": str(output_filename) if generated_xml else None,
                "validation_errors": errors,
                **metrics # Add calculated metrics here
            }
            all_results.append(result_record)

    # --- 6. Save Results Summary ---
    results_df = pd.DataFrame(all_results)
    reports_dir = Path(paths.get("reports", "results/reports"))
    os.makedirs(reports_dir, exist_ok=True)
    summary_file = reports_dir / exp_config.get("output_metrics_file", "metrics_summary.csv")
    try:
        results_df.to_csv(summary_file, index=False)
        logger.info(f"Saved results summary to: {summary_file}")
    except Exception as e:
        logger.error(f"Failed to save results summary CSV: {e}")

    # Optionally save raw results list as JSON
    raw_results_file = reports_dir / "raw_results.json"
    save_json(all_results, raw_results_file)

    # --- 7. Optional Analysis ---
    # Call analysis script if it exists and is configured
    if os.path.exists("experiments/analysis.py"):
         logger.info("Running analysis script...")
         try:
             # Example: Run as subprocess or import and call a function
             # import subprocess
             # subprocess.run(["python", "experiments/analysis.py", str(summary_file)], check=True)
             from .analysis import perform_analysis
             analysis_output_dir = reports_dir / "analysis_plots"
             os.makedirs(analysis_output_dir, exist_ok=True)
             perform_analysis(results_df, analysis_output_dir)
             logger.info(f"Analysis plots saved to: {analysis_output_dir}")
         except Exception as e:
             logger.error(f"Failed to run analysis script: {e}", exc_info=True)


    end_time = time.time()
    total_duration = end_time - start_time
    logger.info(f"Experiment run finished in {total_duration:.2f} seconds.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AUTOSAR XML Generation Experiment")
    parser.add_argument(
        "-c", "--config",
        default="config/config.yaml",
        help="Path to the main configuration file (default: config/config.yaml)"
    )
    args = parser.parse_args()

    if not os.path.exists(args.config):
        logger.critical(f"Configuration file not found at: {args.config}")
    else:
        main(args.config)