import logging
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

logger = logging.getLogger(__name__)

def perform_analysis(results_df: pd.DataFrame, output_dir: Path):
    """
    Performs analysis on the experiment results DataFrame and saves plots.

    Args:
        results_df: DataFrame containing the results from run_experiment.py.
        output_dir: Path object for the directory to save plots.
    """
    if results_df.empty:
        logger.warning("Results DataFrame is empty. Skipping analysis.")
        return

    logger.info(f"Performing analysis on {len(results_df)} results. Saving plots to {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Ensure numeric types where expected
        results_df['generation_time_s'] = pd.to_numeric(results_df['generation_time_s'], errors='coerce')
        results_df['validation_passed'] = results_df['validation_passed'].astype(bool)
        results_df['xsd_errors_count'] = pd.to_numeric(results_df['xsd_errors_count'], errors='coerce').fillna(0)
        results_df['drools_errors_count'] = pd.to_numeric(results_df['drools_errors_count'], errors='coerce').fillna(0)
        results_df['structural_similarity'] = pd.to_numeric(results_df['structural_similarity'], errors='coerce')


        # --- Plot 1: Generation Time per Method ---
        plt.figure(figsize=(10, 6))
        sns.boxplot(x='method', y='generation_time_s', data=results_df)
        plt.title('Generation Time Distribution per Method')
        plt.ylabel('Generation Time (seconds)')
        plt.xlabel('Method')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_dir / "generation_time_per_method.png")
        plt.close()
        logger.debug("Saved generation time plot.")

        # --- Plot 2: Validation Success Rate per Method ---
        success_rate = results_df.groupby('method')['validation_passed'].mean().reset_index()
        plt.figure(figsize=(10, 6))
        sns.barplot(x='method', y='validation_passed', data=success_rate)
        plt.title('Validation Success Rate per Method')
        plt.ylabel('Success Rate (Fraction)')
        plt.xlabel('Method')
        plt.ylim(0, 1)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_dir / "validation_success_rate_per_method.png")
        plt.close()
        logger.debug("Saved validation success rate plot.")

        # --- Plot 3: Error Counts per Method ---
        error_counts = results_df.groupby('method')[['xsd_errors_count', 'drools_errors_count', 'other_errors_count']].sum().reset_index()
        error_counts_melted = error_counts.melt(id_vars='method', var_name='error_type', value_name='count')
        plt.figure(figsize=(12, 7))
        sns.barplot(x='method', y='count', hue='error_type', data=error_counts_melted)
        plt.title('Total Validation Error Counts per Method')
        plt.ylabel('Total Error Count')
        plt.xlabel('Method')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_dir / "error_counts_per_method.png")
        plt.close()
        logger.debug("Saved error counts plot.")

        # --- Plot 4: Structural Similarity (if available) ---
        if 'structural_similarity' in results_df.columns and results_df['structural_similarity'].notna().any():
            plt.figure(figsize=(10, 6))
            sns.boxplot(x='method', y='structural_similarity', data=results_df)
            plt.title('Structural Similarity to Ground Truth per Method')
            plt.ylabel('Similarity Score (e.g., Text Ratio)')
            plt.xlabel('Method')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(output_dir / "structural_similarity_per_method.png")
            plt.close()
            logger.debug("Saved structural similarity plot.")
        else:
             logger.info("Skipping structural similarity plot (no data or column missing).")


        logger.info("Analysis plots generated successfully.")

    except Exception as e:
        logger.error(f"An error occurred during analysis plot generation: {e}", exc_info=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Example usage: Load a CSV and run analysis
    # This assumes a 'metrics_summary.csv' exists in 'results/reports/'
    results_file = Path("results/reports/metrics_summary.csv")
    analysis_out_dir = Path("results/reports/analysis_plots")

    if results_file.exists():
        print(f"Loading results from: {results_file}")
        try:
            df = pd.read_csv(results_file)
            print(f"Loaded {len(df)} records.")
            perform_analysis(df, analysis_out_dir)
        except Exception as e:
            print(f"Error loading or analyzing results: {e}")
    else:
        print(f"Results file not found: {results_file}")
        print("Cannot run standalone analysis example.")
        # You could create a dummy DataFrame here for testing if needed:
        # dummy_data = {
        #     'method': ['baseline1', 'baseline1', 'proposed', 'proposed'],
        #     'generation_time_s': [1.2, 1.5, 5.5, 6.1],
        #     'validation_passed': [False, True, True, True],
        #     'xsd_errors_count': [1, 0, 0, 0],
        #     'drools_errors_count': [0, 0, 0, 0],
        #     'other_errors_count': [0, 0, 0, 0],
        #     'structural_similarity': [0.5, 0.6, 0.9, 0.95]
        # }
        # df = pd.DataFrame(dummy_data)
        # perform_analysis(df, analysis_out_dir)