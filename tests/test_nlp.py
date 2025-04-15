import pytest
from src.nlp.processor import NLProcessor # Adjust import path as needed

# Fixture to initialize the processor once per module if model loading is slow
# @pytest.fixture(scope="module")
# def nlp_processor():
#     print("\nSetting up NLProcessor for tests...")
#     # Use a specific small model for testing if possible
#     return NLProcessor(model_name="en_core_web_sm") # Make sure this model is downloaded

# If model loading is fast, use function scope fixture:
@pytest.fixture
def nlp_processor():
    # Simple initialization for basic tests if no real model needed
    return NLProcessor(model_name="dummy_model") # Avoid real model loading for basic unit tests

def test_nlprocessor_initialization(nlp_processor):
    """Tests if the NLProcessor initializes without errors."""
    assert nlp_processor is not None
    # If using a real model, you might assert its type or loaded status
    # assert nlp_processor.model is not None # This would fail with the dummy model

def test_parse_basic_requirement(nlp_processor):
    """Tests parsing a simple requirement string."""
    text = "Define a signal named Speed."
    result = nlp_processor.parse_requirement(text)

    assert isinstance(result, dict)
    assert result["text"] == text
    # Basic assertions for dummy model / fallback
    assert "entities" in result
    assert isinstance(result["entities"], list)
    assert result["intent"] == "example_intent" # Or "unknown" depending on implementation

# --- Add more tests for specific NLP capabilities ---
# These would likely require a real NLP model and more complex assertions

# @pytest.mark.skipif(condition=lambda: not nlp_processor_has_real_model(), reason="Requires a real spaCy model")
# def test_entity_extraction(nlp_processor_real_model): # Requires fixture with real model
#     text = "Create a ComSignal named 'VehicleSpeed' with length 8."
#     result = nlp_processor_real_model.parse_requirement(text)
#     entities = result.get("entities", [])
#     assert len(entities) >= 2 # Expecting at least 'VehicleSpeed' and '8'
#     # More specific checks on entity text and labels
#     entity_texts = [e[0] for e in entities]
#     assert 'VehicleSpeed' in entity_texts
#     assert '8' in entity_texts

# @pytest.mark.skipif(condition=lambda: not nlp_processor_has_real_model(), reason="Requires a real spaCy model")
# def test_intent_recognition(nlp_processor_real_model):
#      text = "The system shall define a port."
#      result = nlp_processor_real_model.parse_requirement(text)
#      # Assert the expected intent based on your intent logic
#      assert result.get("intent") == "define_entity" # Example intent

def test_parse_empty_string(nlp_processor):
    """Tests parsing an empty requirement string."""
    text = ""
    result = nlp_processor.parse_requirement(text)
    assert result["text"] == text
    assert len(result["entities"]) == 0

def test_parse_none_input(nlp_processor):
    """Tests handling of None input (should ideally raise error or handle gracefully)."""
    with pytest.raises(TypeError): # Or appropriate error type if handled differently
        nlp_processor.parse_requirement(None)

# Helper function to check if a real model is likely loaded (example)
# def nlp_processor_has_real_model():
#     try:
#         import spacy
#         spacy.load("en_core_web_sm") # Check if default test model is available
#         return True
#     except OSError:
#         return False