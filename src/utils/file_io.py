import logging
import yaml
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)

def load_yaml(file_path: str | Path) -> dict | None:
    """Loads a YAML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        logger.debug(f"Successfully loaded YAML from: {file_path}")
        return data
    except FileNotFoundError:
        logger.error(f"YAML file not found: {file_path}")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file {file_path}: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred loading YAML {file_path}: {e}", exc_info=True)
        return None

def save_yaml(data: dict, file_path: str | Path):
    """Saves data to a YAML file."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        logger.debug(f"Successfully saved YAML to: {file_path}")
    except Exception as e:
        logger.error(f"Error saving YAML to {file_path}: {e}", exc_info=True)


def load_text(file_path: str | Path) -> str | None:
    """Loads a text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.debug(f"Successfully loaded text from: {file_path}")
        return content
    except FileNotFoundError:
        logger.error(f"Text file not found: {file_path}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred loading text {file_path}: {e}", exc_info=True)
        return None

def save_text(content: str, file_path: str | Path):
    """Saves text content to a file."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.debug(f"Successfully saved text to: {file_path}")
    except Exception as e:
        logger.error(f"Error saving text to {file_path}: {e}", exc_info=True)

def save_xml(xml_content: str, file_path: str | Path):
    """Saves XML content to a file (essentially same as save_text)."""
    save_text(xml_content, file_path)
    logger.debug(f"Saved XML content to: {file_path}")

def load_json(file_path: str | Path) -> dict | list | None:
    """Loads a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.debug(f"Successfully loaded JSON from: {file_path}")
        return data
    except FileNotFoundError:
        logger.error(f"JSON file not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON file {file_path}: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred loading JSON {file_path}: {e}", exc_info=True)
        return None

def save_json(data: dict | list, file_path: str | Path, indent=4):
    """Saves data to a JSON file."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        logger.debug(f"Successfully saved JSON to: {file_path}")
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}", exc_info=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # Create dummy files for testing
    test_dir = "temp_test_io"
    os.makedirs(test_dir, exist_ok=True)
    yaml_file = os.path.join(test_dir, "test.yaml")
    txt_file = os.path.join(test_dir, "test.txt")
    json_file = os.path.join(test_dir, "test.json")

    # Test YAML
    my_dict = {"a": 1, "b": [1, 2, 3], "c": "hello"}
    save_yaml(my_dict, yaml_file)
    loaded_yaml = load_yaml(yaml_file)
    print(f"YAML Load Test: {'PASS' if loaded_yaml == my_dict else 'FAIL'}")

    # Test Text
    my_text = "This is line one.\nThis is line two."
    save_text(my_text, txt_file)
    loaded_text = load_text(txt_file)
    print(f"Text Load Test: {'PASS' if loaded_text == my_text else 'FAIL'}")

    # Test JSON
    my_json_data = [{"id": 1, "value": "apple"}, {"id": 2, "value": "banana"}]
    save_json(my_json_data, json_file)
    loaded_json = load_json(json_file)
    print(f"JSON Load Test: {'PASS' if loaded_json == my_json_data else 'FAIL'}")

    # Clean up
    import shutil
    shutil.rmtree(test_dir)
    print("Cleaned up test directory.")