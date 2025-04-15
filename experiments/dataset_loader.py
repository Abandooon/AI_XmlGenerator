import logging
import os
from pathlib import Path
from src.utils.file_io import load_text, load_json # Assuming requirements might be text or json

logger = logging.getLogger(__name__)

def load_requirements(requirements_dir: str, ground_truth_dir: str = None) -> list[dict]:
    """
    Loads requirement files from a directory.
    Assumes each file in requirements_dir is one requirement.
    Optionally loads corresponding ground truth XML files.

    Args:
        requirements_dir: Path to the directory containing requirement files (.txt, .json).
        ground_truth_dir: Optional path to the directory containing corresponding
                          ground truth .arxml files. Naming convention is assumed:
                          req_ID.txt corresponds to req_ID_gold.arxml.

    Returns:
        A list of dictionaries, each containing:
        - 'id': The base filename (without extension).
        - 'text': The content of the requirement file.
        - 'ground_truth_path': Path to the ground truth file (if found).
        - 'ground_truth_content': Content of the ground truth file (if found).
    """
    requirements_data = []
    if not os.path.isdir(requirements_dir):
        logger.error(f"Requirements directory not found or not a directory: {requirements_dir}")
        return requirements_data

    logger.info(f"Loading requirements from: {requirements_dir}")
    if ground_truth_dir:
        logger.info(f"Attempting to load corresponding ground truth from: {ground_truth_dir}")
        if not os.path.isdir(ground_truth_dir):
            logger.warning(f"Ground truth directory not found: {ground_truth_dir}. Ground truth will not be loaded.")
            ground_truth_dir = None # Disable ground truth loading

    for filename in os.listdir(requirements_dir):
        file_path = Path(requirements_dir) / filename
        if file_path.is_file():
            req_id = file_path.stem # Filename without extension
            req_text = None
            logger.debug(f"Processing requirement file: {filename}")

            # Load based on extension
            if filename.endswith(".txt"):
                req_text = load_text(file_path)
            elif filename.endswith(".json"):
                json_data = load_json(file_path)
                # Assuming JSON contains a 'requirement' field, adjust as needed
                if isinstance(json_data, dict) and "requirement" in json_data:
                    req_text = json_data["requirement"]
                else:
                    logger.warning(f"Could not find 'requirement' key in JSON file: {filename}. Skipping.")
                    continue # Skip this file
            else:
                logger.warning(f"Unsupported requirement file type: {filename}. Skipping.")
                continue # Skip unsupported files

            if req_text is None:
                logger.warning(f"Failed to load content from requirement file: {filename}. Skipping.")
                continue

            req_entry = {
                "id": req_id,
                "text": req_text,
                "ground_truth_path": None,
                "ground_truth_content": None
            }

            # Try to find corresponding ground truth
            if ground_truth_dir:
                # Example naming convention: req_001.txt -> req_001_gold.arxml
                gt_filename = f"{req_id}_gold.arxml" # Adjust suffix/extension as needed
                gt_path = Path(ground_truth_dir) / gt_filename
                if gt_path.is_file():
                    gt_content = load_text(gt_path)
                    if gt_content:
                        req_entry["ground_truth_path"] = str(gt_path)
                        req_entry["ground_truth_content"] = gt_content
                        logger.debug(f"Found and loaded ground truth for {req_id}: {gt_filename}")
                    else:
                        logger.warning(f"Found ground truth file {gt_filename} for {req_id}, but failed to load content.")
                else:
                    logger.debug(f"No corresponding ground truth file found for {req_id} (expected: {gt_filename})")

            requirements_data.append(req_entry)

    logger.info(f"Finished loading {len(requirements_data)} requirements.")
    return requirements_data

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # Create dummy data for testing
    test_req_dir = "temp_test_reqs"
    test_gt_dir = "temp_test_gt"
    os.makedirs(test_req_dir, exist_ok=True)
    os.makedirs(test_gt_dir, exist_ok=True)

    # Create dummy files
    with open(os.path.join(test_req_dir, "req_001.txt"), "w") as f:
        f.write("Requirement for signal A.")
    with open(os.path.join(test_req_dir, "req_002.json"), "w") as f:
        f.write('{"requirement": "Requirement for component B."}')
    with open(os.path.join(test_req_dir, "req_003.txt"), "w") as f:
        f.write("Requirement for function C.")
    with open(os.path.join(test_req_dir, "unsupported.pdf"), "w") as f:
        f.write("PDF Content") # To test skipping

    with open(os.path.join(test_gt_dir, "req_001_gold.arxml"), "w") as f:
        f.write("<SIGNAL name='A'></SIGNAL>")
    # No ground truth for req_002
    with open(os.path.join(test_gt_dir, "req_003_gold.arxml"), "w") as f:
        f.write("<FUNCTION name='C'></FUNCTION>")


    print("--- Loading requirements with ground truth ---")
    loaded_data = load_requirements(test_req_dir, test_gt_dir)
    print(f"Loaded {len(loaded_data)} entries.")
    for entry in loaded_data:
        print(f"ID: {entry['id']}, Has GT: {entry['ground_truth_content'] is not None}")
        # print(entry) # Uncomment to see full dict

    print("\n--- Loading requirements without ground truth ---")
    loaded_data_no_gt = load_requirements(test_req_dir)
    print(f"Loaded {len(loaded_data_no_gt)} entries.")
    for entry in loaded_data_no_gt:
         print(f"ID: {entry['id']}, Has GT: {entry['ground_truth_content'] is not None}")


    # Clean up
    import shutil
    shutil.rmtree(test_req_dir)
    shutil.rmtree(test_gt_dir)
    print("\nCleaned up test directories.")