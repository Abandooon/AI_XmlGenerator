import pytest
from unittest.mock import MagicMock, patch
import os
import tempfile

# Import generators and base class
from src.generation_pipeline.base_generator import BaseGenerator
from src.generation_pipeline.generators import (
    NaiveGenerator, XsdConstrainedGenerator, FullConstrainedGenerator, KgEnhancedGenerator
)
# Import necessary components to mock or provide
from src.llm_interaction.llm_client import LLMClient
from src.kg_query.querier import KGQuerier
from src.validation.xsd_validator import load_xsd_schema
from src.validation.drools_validator import DroolsValidator

# --- Test Fixtures ---

@pytest.fixture
def mock_llm_client():
    """Provides a mocked LLMClient."""
    client = MagicMock(spec=LLMClient)
    # Configure default behavior: return simple XML-like string
    client.generate_text.return_value = "<MOCK_XML>Generated Content</MOCK_XML>"
    return client

@pytest.fixture
def mock_kg_querier():
    """Provides a mocked KGQuerier."""
    querier = MagicMock(spec=KGQuerier)
    # Configure default behavior: return simple context
    querier.execute_query.return_value = [{"var": {"value": "mock_result"}}]
    # Mock the higher-level context generation method used in KgEnhancedGenerator
    querier.find_related_concepts = MagicMock(return_value=["Related_Concept_1"]) # Example mock
    # Add mock for the method actually called by the generator's _query_kg_for_context
    # This depends on the implementation detail of _query_kg_for_context
    # Let's assume it uses execute_query or similar:
    def mock_kg_context_query(parsed_req):
         # Simulate context generation based on parsed_req if needed
         if parsed_req and parsed_req.get("entities"):
             return f"Context based on entities: {parsed_req['entities']}"
         return "Default mock KG context."
    # We need to mock the method called inside KgEnhancedGenerator._query_kg_for_context
    # Let's refine KgEnhancedGenerator._query_kg_for_context to call a method on self.kg_querier
    # e.g., self.kg_querier.get_context_for_requirement(parsed_requirement)
    # Then we mock that specific method here:
    querier.get_context_for_requirement = MagicMock(side_effect=mock_kg_context_query)
    return querier


# Use the dummy XSD from test_validation
DUMMY_XSD_CONTENT_GEN = """<?xml version="1.0" encoding="UTF-8" ?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="MOCK_XML">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="REQUIRED" type="xs:string" minOccurs="1"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
"""

@pytest.fixture(scope="module")
def dummy_xsd_schema_gen():
    """Fixture to load the dummy XSD schema for generator tests."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".xsd") as tmp_xsd:
        tmp_xsd.write(DUMMY_XSD_CONTENT_GEN)
        xsd_path = tmp_xsd.name
    schema = load_xsd_schema(xsd_path)
    yield schema
    os.remove(xsd_path)


@pytest.fixture
def mock_drools_validator():
    """Provides a mocked DroolsValidator."""
    validator = MagicMock(spec=DroolsValidator)
    # Default behavior: validation passes
    validator.validate_data.return_value = (True, [])
    return validator

@pytest.fixture
def base_config():
    """Provides a basic configuration dictionary."""
    return {
        "paths": {},
        "llm": {},
        "kg": {},
        "validation": {"drools": {}},
        "experiments": {}
    }

# --- Test Generator Instantiation ---

def test_naive_generator_init(base_config, mock_llm_client):
    gen = NaiveGenerator(base_config, llm_client=mock_llm_client)
    assert isinstance(gen, NaiveGenerator)
    assert gen.llm_client == mock_llm_client

def test_xsd_constrained_generator_init(base_config, mock_llm_client, dummy_xsd_schema_gen):
    gen = XsdConstrainedGenerator(base_config, llm_client=mock_llm_client, xsd_schema=dummy_xsd_schema_gen)
    assert isinstance(gen, XsdConstrainedGenerator)
    assert gen.xsd_schema == dummy_xsd_schema_gen

def test_full_constrained_generator_init(base_config, mock_llm_client, dummy_xsd_schema_gen, mock_drools_validator):
    gen = FullConstrainedGenerator(base_config, llm_client=mock_llm_client, xsd_schema=dummy_xsd_schema_gen, drools_validator=mock_drools_validator)
    assert isinstance(gen, FullConstrainedGenerator)
    assert gen.drools_validator == mock_drools_validator

def test_kg_enhanced_generator_init(base_config, mock_llm_client, mock_kg_querier):
     # KG Enhanced might also need schema/drools, add them if needed by its flow
    gen = KgEnhancedGenerator(base_config, llm_client=mock_llm_client, kg_querier=mock_kg_querier)
    assert isinstance(gen, KgEnhancedGenerator)
    assert gen.kg_querier == mock_kg_querier


# --- Test Generation Logic ---

REQ_TEXT = "Generate a mock XML."
PARSED_REQ = {"text": REQ_TEXT, "entities": [("mock", "TYPE")], "intent": "generate"}

def test_naive_generator_generate(base_config, mock_llm_client):
    """Tests basic generation without validation."""
    generator = NaiveGenerator(base_config, llm_client=mock_llm_client)
    xml, errors = generator.generate(REQ_TEXT, PARSED_REQ)

    mock_llm_client.generate_text.assert_called_once()
    assert xml == "<MOCK_XML>Generated Content</MOCK_XML>"
    assert not errors

def test_naive_generator_llm_fails(base_config, mock_llm_client):
    """Tests NaiveGenerator when LLM returns None."""
    mock_llm_client.generate_text.return_value = None
    generator = NaiveGenerator(base_config, llm_client=mock_llm_client)
    xml, errors = generator.generate(REQ_TEXT, PARSED_REQ)

    assert xml is None
    assert len(errors) == 1
    assert "LLM generation failed" in errors[0]

def test_xsd_constrained_generator_valid(base_config, mock_llm_client, dummy_xsd_schema_gen):
    """Tests XSD generator when initial LLM output is valid."""
    # Adjust mock LLM to return XML valid according to DUMMY_XSD_CONTENT_GEN
    mock_llm_client.generate_text.return_value = "<MOCK_XML><REQUIRED>Value</REQUIRED></MOCK_XML>"
    generator = XsdConstrainedGenerator(base_config, llm_client=mock_llm_client, xsd_schema=dummy_xsd_schema_gen)
    xml, errors = generator.generate(REQ_TEXT, PARSED_REQ)

    mock_llm_client.generate_text.assert_called_once() # Only initial call
    assert xml == "<MOCK_XML><REQUIRED>Value</REQUIRED></MOCK_XML>"
    assert not errors

@patch('src.generation_pipeline.base_generator.validate_xsd') # Patch validate_xsd used internally
def test_xsd_constrained_generator_repair_success(mock_validate_xsd, base_config, mock_llm_client, dummy_xsd_schema_gen):
    """Tests XSD generator repair cycle successfully."""
    # 1. Initial LLM call returns invalid XML
    initial_invalid_xml = "<MOCK_XML></MOCK_XML>" # Missing REQUIRED element
    # 2. Repair LLM call returns valid XML
    repaired_valid_xml = "<MOCK_XML><REQUIRED>Repaired Value</REQUIRED></MOCK_XML>"

    # Configure mock LLM responses
    mock_llm_client.generate_text.side_effect = [initial_invalid_xml, repaired_valid_xml]

    # Configure mock validate_xsd responses
    # First call (on initial_invalid_xml) -> False, with errors
    # Second call (on repaired_valid_xml) -> True, no errors
    mock_validate_xsd.side_effect = [
        (False, ["XSD Error: Element 'REQUIRED' is missing."]),
        (True, [])
    ]

    generator = XsdConstrainedGenerator(base_config, llm_client=mock_llm_client, xsd_schema=dummy_xsd_schema_gen)
    xml, errors = generator.generate(REQ_TEXT, PARSED_REQ)

    assert mock_llm_client.generate_text.call_count == 2 # Initial + Repair
    assert mock_validate_xsd.call_count == 2
    assert xml == repaired_valid_xml
    assert not errors

@patch('src.generation_pipeline.base_generator.validate_xsd')
def test_xsd_constrained_generator_repair_fails(mock_validate_xsd, base_config, mock_llm_client, dummy_xsd_schema_gen):
    """Tests XSD generator when repair attempts fail."""
    initial_invalid_xml = "<MOCK_XML></MOCK_XML>"
    # LLM keeps returning invalid XML during repair attempts
    repair_invalid_xml_1 = "<MOCK_XML><WRONG>Data</WRONG></MOCK_XML>"
    repair_invalid_xml_2 = "<MOCK_XML></MOCK_XML>" # Still invalid

    mock_llm_client.generate_text.side_effect = [
        initial_invalid_xml, repair_invalid_xml_1, repair_invalid_xml_2
    ]
    # validate_xsd keeps returning False
    mock_validate_xsd.return_value = (False, ["XSD Error: Element 'REQUIRED' is missing."])

    # Assuming MAX_REPAIR_ATTEMPTS = 2 (default in generators.py)
    generator = XsdConstrainedGenerator(base_config, llm_client=mock_llm_client, xsd_schema=dummy_xsd_schema_gen)
    xml, errors = generator.generate(REQ_TEXT, PARSED_REQ)

    # Initial call + 2 repair calls = 3 LLM calls
    assert mock_llm_client.generate_text.call_count == 3
    # Initial validation + 2 repair validations = 3 validation calls
    assert mock_validate_xsd.call_count == 3
    # Should return the last invalid XML generated
    assert xml == repair_invalid_xml_2
    assert len(errors) > 0
    assert "XSD Error" in errors[0]


# --- Tests for FullConstrainedGenerator ---
# Similar pattern, but need to mock/patch _validate_xml or its components (xsd and drools)

@patch.object(BaseGenerator, '_validate_xml') # Patch the combined validation method
def test_full_constrained_generator_valid(mock_base_validate, base_config, mock_llm_client, dummy_xsd_schema_gen, mock_drools_validator):
    """Tests FullConstrained generator when initial validation passes."""
    valid_xml = "<MOCK_XML><REQUIRED>Value</REQUIRED></MOCK_XML>"
    mock_llm_client.generate_text.return_value = valid_xml
    # Configure the mocked _validate_xml to return success
    mock_base_validate.return_value = (True, [])

    generator = FullConstrainedGenerator(base_config, llm_client=mock_llm_client, xsd_schema=dummy_xsd_schema_gen, drools_validator=mock_drools_validator)
    xml, errors = generator.generate(REQ_TEXT, PARSED_REQ)

    mock_llm_client.generate_text.assert_called_once()
    mock_base_validate.assert_called_once_with(valid_xml)
    assert xml == valid_xml
    assert not errors

@patch.object(BaseGenerator, '_validate_xml')
def test_full_constrained_generator_repair_success(mock_base_validate, base_config, mock_llm_client, dummy_xsd_schema_gen, mock_drools_validator):
    """Tests FullConstrained generator repair cycle."""
    initial_invalid_xml = "<MOCK_XML></MOCK_XML>" # Fails XSD
    repaired_valid_xml = "<MOCK_XML><REQUIRED>Repaired Value</REQUIRED></MOCK_XML>" # Passes both

    mock_llm_client.generate_text.side_effect = [initial_invalid_xml, repaired_valid_xml]
    # _validate_xml fails first, then succeeds
    mock_base_validate.side_effect = [
        (False, ["XSD Error: Element 'REQUIRED' is missing."]), # Fails on initial
        (True, []) # Succeeds on repaired
    ]

    generator = FullConstrainedGenerator(base_config, llm_client=mock_llm_client, xsd_schema=dummy_xsd_schema_gen, drools_validator=mock_drools_validator)
    xml, errors = generator.generate(REQ_TEXT, PARSED_REQ)

    assert mock_llm_client.generate_text.call_count == 2
    assert mock_base_validate.call_count == 2
    assert xml == repaired_valid_xml
    assert not errors


# --- Tests for KgEnhancedGenerator ---

# Need to mock the _query_kg_for_context method or the kg_querier call within it
@patch.object(KgEnhancedGenerator, '_query_kg_for_context')
@patch.object(BaseGenerator, '_validate_xml')
def test_kg_enhanced_generator_valid(mock_base_validate, mock_query_kg, base_config, mock_llm_client, mock_kg_querier):
    """Tests KG Enhanced generator happy path."""
    valid_xml = "<MOCK_XML><REQUIRED>Value from KG</REQUIRED></MOCK_XML>"
    kg_context_str = "Context: MOCK_XML requires a REQUIRED element."

    # Mock KG query result
    mock_query_kg.return_value = kg_context_str
    # Mock LLM response (should be based on KG prompt)
    mock_llm_client.generate_text.return_value = valid_xml
    # Mock validation success
    mock_base_validate.return_value = (True, [])

    # Instantiate with necessary mocks (schema/drools might be needed depending on flow)
    generator = KgEnhancedGenerator(base_config, llm_client=mock_llm_client, kg_querier=mock_kg_querier)
    xml, errors = generator.generate(REQ_TEXT, PARSED_REQ)

    mock_query_kg.assert_called_once_with(PARSED_REQ)
    # Check that LLM was called with a prompt containing KG context
    llm_call_args = mock_llm_client.generate_text.call_args
    assert llm_call_args is not None
    prompt_arg = llm_call_args[0][0] # Get the first positional argument (the prompt)
    assert REQ_TEXT in prompt_arg
    assert kg_context_str in prompt_arg

    mock_base_validate.assert_called_once_with(valid_xml)
    assert xml == valid_xml
    assert not errors

# Add more tests for KG Enhanced repair cycles, similar to FullConstrained tests