import logging
import logging.config
import yaml
import os

DEFAULT_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout',
        },
    },
    'loggers': {
        '': { # root logger
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

def setup_logging(config_path: str = 'config/logging.yaml', default_level=logging.INFO, env_key='LOG_CFG'):
    """
    Setup logging configuration from a YAML file or use defaults.

    Args:
        config_path: Path to the logging configuration YAML file.
        default_level: Default logging level if config file is not found.
        env_key: Environment variable to check for config path override.
    """
    path = os.getenv(env_key, config_path)
    if os.path.exists(path):
        try:
            with open(path, 'rt', encoding='utf-8') as f:
                config_data = yaml.safe_load(f.read())

            # Ensure log file directory exists if specified in handlers
            for handler_name, handler_config in config_data.get('handlers', {}).items():
                if 'filename' in handler_config:
                    log_dir = os.path.dirname(handler_config['filename'])
                    if log_dir: # Ensure it's not just a filename in the current dir
                        os.makedirs(log_dir, exist_ok=True)

            logging.config.dictConfig(config_data)
            logging.getLogger(__name__).info(f"Logging configured successfully from {path}.")
        except Exception as e:
            logging.basicConfig(level=default_level)
            logging.getLogger(__name__).error(f"Error loading logging config from {path}: {e}. Using basicConfig.", exc_info=True)
    else:
        logging.basicConfig(level=default_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # Or use the DEFAULT_LOGGING_CONFIG defined above:
        # logging.config.dictConfig(DEFAULT_LOGGING_CONFIG)
        logging.getLogger(__name__).info(f"Logging config file not found at {path}. Using basicConfig with level {logging.getLevelName(default_level)}.")

if __name__ == '__main__':
    # Example usage: Call this early in your main script
    print("Setting up logging (default)...")
    setup_logging(config_path='non_existent_config.yaml') # Test fallback
    logging.info("This is an info message (default setup).")
    logging.warning("This is a warning message (default setup).")
    logging.debug("This is a debug message (should not appear with default INFO level).")

    # Create a dummy config file for testing
    dummy_config_content = """
version: 1
formatters:
  simple:
    format: '%(levelname)s:%(name)s: %(message)s'
handlers:
  console_simple:
    class: logging.StreamHandler
    formatter: simple
    level: DEBUG
    stream: ext://sys.stdout
loggers:
  '': # root
    handlers: [console_simple]
    level: DEBUG
"""
    dummy_config_path = "temp_logging_config.yaml"
    with open(dummy_config_path, 'w') as f:
        f.write(dummy_config_content)

    print(f"\nSetting up logging from dummy config file: {dummy_config_path}...")
    setup_logging(config_path=dummy_config_path)
    logging.info("This is an info message (dummy config setup).")
    logging.warning("This is a warning message (dummy config setup).")
    logging.debug("This is a debug message (dummy config setup - should appear).")

    # Clean up dummy file
    os.remove(dummy_config_path)
    print(f"\nCleaned up {dummy_config_path}.")