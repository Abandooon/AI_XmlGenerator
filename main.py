import argparse
import logging
import os
import sys

# Ensure the src directory is in the Python path
# This allows importing modules from src like 'from src.utils...'
# Adjust the number of '..' based on where main.py is relative to src/
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
exp_path = os.path.join(project_root, 'experiments')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
if exp_path not in sys.path:
     sys.path.insert(0, exp_path)


# Setup logging first using the utility function
from src.utils.logging_config import setup_logging
setup_logging() # Assumes config/logging.yaml exists relative to where script is run

# Now import the main experiment runner function
try:
    from run_experiment import main as run_main_experiment
except ImportError as e:
     logging.critical(f"Failed to import run_experiment: {e}", exc_info=True)
     logging.critical("Ensure main.py is run from the project root directory or src/ and experiments/ are in PYTHONPATH.")
     sys.exit(1)


logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the application.
    Parses command-line arguments and calls the experiment runner.
    """
    parser = argparse.ArgumentParser(
        description="AUTOSAR XML Generator Project - Main Runner"
    )
    parser.add_argument(
        "-c", "--config",
        default="config/config.yaml",
        help="Path to the main configuration file (default: config/config.yaml)"
    )
    # Add other potential command-line arguments if needed
    # For example, override specific methods to run, select specific requirements, etc.
    # parser.add_argument(
    #     "--methods",
    #     nargs='+', # Allows multiple methods like --methods baseline1 proposed
    #     help="Override methods to run from config file."
    # )

    args = parser.parse_args()

    logger.info("Application started.")
    logger.info(f"Using configuration file: {args.config}")

    if not os.path.exists(args.config):
        logger.critical(f"Configuration file not found at specified path: {args.config}")
        sys.exit(1) # Exit if config is missing

    try:
        # Call the main function from run_experiment.py
        run_main_experiment(config_path=args.config)
        logger.info("Experiment run completed successfully.")
    except Exception as e:
        logger.critical(f"An unhandled error occurred during the experiment run: {e}", exc_info=True)
        sys.exit(1) # Exit with error status

if __name__ == "__main__":
    main()