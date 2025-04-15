import pytest
from lxml import etree # For creating dummy schema/xml
import os
import tempfile

# --- XSD Validation Tests ---
from src.validation.xsd_validator import load_xsd_schema, validate_xsd

# Dummy XSD content for testing
DUMMY_XSD_CONTENT = """<?xml version="1.0" encoding="UTF-8" ?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="ROOT">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="MANDATORY_ELEMENT" type="xs:string" minOccurs="1"/>
        <xs:element name="OPTIONAL_ELEMENT" type="xs:int" minOccurs="0"/>
      </xs:sequence>
      <xs:attribute name="id" type="xs:ID" use="required"/>
    </xs:complexType>
  </xs:element>
</xs:schema>
"""

@pytest.fixture(scope="module")
def dummy_xsd_schema():
    """Fixture to load the dummy XSD schema once."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".xsd") as tmp_xsd:
        tmp_xsd.write(DUMMY_XSD_CONTENT)
        xsd_path = tmp_xsd.name
    schema = load_xsd_schema(xsd_path)
    yield schema # Provide the loaded schema to tests
    # Teardown: remove the temp file
    os.remove(xsd_path)

def test_load_xsd_schema_success(dummy_xsd_schema):
    """Tests successful loading of a valid XSD."""
    assert dummy_xsd_schema is not None
    assert isinstance(dummy_xsd_schema, etree.XMLSchema)

def test_load_xsd_schema_not_found():
    """Tests loading a non-existent XSD file."""
    schema = load_xsd_schema("non_existent_schema.xsd")
    assert schema is None

def test_load_xsd_schema_invalid_syntax():
    """Tests loading an invalid XSD file."""
    invalid_xsd_content = "<schema><invalid></schema>"
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".xsd") as tmp_xsd:
        tmp_xsd.write(invalid_xsd_content)
        xsd_path = tmp_xsd.name
    schema = load_xsd_schema(xsd_path)
    os.remove(xsd_path)
    assert schema is None


def test_validate_xsd_valid_xml(dummy_xsd_schema):
    """Tests validating a correct XML against the schema."""
    valid_xml = '<ROOT id="r1"><MANDATORY_ELEMENT>Test</MANDATORY_ELEMENT></ROOT>'
    is_valid, errors = validate_xsd(valid_xml, dummy_xsd_schema)
    assert is_valid is True
    assert not errors

def test_validate_xsd_missing_element(dummy_xsd_schema):
    """Tests validating XML missing a mandatory element."""
    invalid_xml = '<ROOT id="r2"></ROOT>'
    is_valid, errors = validate_xsd(invalid_xml, dummy_xsd_schema)
    assert is_valid is False
    assert len(errors) > 0
    assert "MANDATORY_ELEMENT" in errors[0] # Check if error message is relevant

def test_validate_xsd_missing_attribute(dummy_xsd_schema):
    """Tests validating XML missing a required attribute."""
    invalid_xml = '<ROOT><MANDATORY_ELEMENT>Test</MANDATORY_ELEMENT></ROOT>'
    is_valid, errors = validate_xsd(invalid_xml, dummy_xsd_schema)
    assert is_valid is False
    assert len(errors) > 0
    assert "attribute 'id'" in errors[0]

def test_validate_xsd_incorrect_type(dummy_xsd_schema):
    """Tests validating XML with incorrect element type."""
    invalid_xml = '<ROOT id="r3"><MANDATORY_ELEMENT>Test</MANDATORY_ELEMENT><OPTIONAL_ELEMENT>abc</OPTIONAL_ELEMENT></ROOT>'
    is_valid, errors = validate_xsd(invalid_xml, dummy_xsd_schema)
    assert is_valid is False
    assert len(errors) > 0
    assert "OPTIONAL_ELEMENT" in errors[0] # Error should mention the element

def test_validate_xsd_syntax_error(dummy_xsd_schema):
    """Tests validating malformed XML."""
    invalid_xml = '<ROOT id="r4"><MANDATORY_ELEMENT>Test</MANDATORY_ELEMENT' # No closing ROOT
    is_valid, errors = validate_xsd(invalid_xml, dummy_xsd_schema)
    assert is_valid is False
    assert len(errors) == 1
    assert "Syntax Error" in errors[0]

def test_validate_xsd_none_schema():
    """Tests validation attempt when schema loading failed."""
    xml_content = '<ROOT id="r5"><MANDATORY_ELEMENT>Test</MANDATORY_ELEMENT></ROOT>'
    is_valid, errors = validate_xsd(xml_content, None)
    assert is_valid is False
    assert len(errors) == 1
    assert "schema was not loaded" in errors[0]


# --- Drools Validation Tests (Mocking Example) ---
# Testing Drools usually requires mocking the interaction (e.g., requests.post)
# as setting up a real KIE server for unit tests is complex.

from src.validation.drools_validator import DroolsValidator
from unittest.mock import patch, MagicMock # Import mock library

@pytest.fixture
def drools_validator_instance():
    """Fixture for a DroolsValidator instance with a dummy endpoint."""
    config = {"endpoint": "http://mock-kie-server:8080/kie-server/services/rest/server/containers/instances/test-container"}
    return DroolsValidator(config)

# Use patch to mock 'requests.post' within the test's scope
@patch('src.validation.drools_validator.requests.post')
def test_drools_validation_success(mock_post, drools_validator_instance):
    """Tests successful Drools validation (mocked response)."""
    # Configure the mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Simulate a KIE server success response with no violations found
    mock_response.json.return_value = {
        "type": "SUCCESS",
        "msg": "Container test-container successfully called.",
        "result": { "execution-results": { "results": [] } } # Empty results = no violations
    }
    mock_post.return_value = mock_response

    data_payload = {"com.example.Fact": {"field": "valid_data"}}
    is_valid, violations = drools_validator_instance.validate_data(data_payload)

    assert is_valid is True
    assert not violations
    mock_post.assert_called_once() # Check if requests.post was called

@patch('src.validation.drools_validator.requests.post')
def test_drools_validation_violations_found(mock_post, drools_validator_instance):
    """Tests Drools validation where violations are found (mocked response)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Simulate finding violation objects (structure depends on your rules/query)
    mock_response.json.return_value = {
        "type": "SUCCESS",
        "msg": "Container test-container successfully called.",
        "result": { "execution-results": {
            "results": [
                {"key": "violations", "value": ["Rule Violated: Name too short", "Rule Violated: Value out of range"]}
            ]
        }}
    }
    mock_post.return_value = mock_response

    data_payload = {"com.example.Fact": {"field": "invalid_data"}}
    is_valid, violations = drools_validator_instance.validate_data(data_payload)

    assert is_valid is False
    assert len(violations) == 2
    assert "Rule Violated: Name too short" in violations
    mock_post.assert_called_once()

@patch('src.validation.drools_validator.requests.post')
def test_drools_validation_connection_error(mock_post, drools_validator_instance):
    """Tests handling of connection errors when calling Drools."""
    # Configure the mock to raise a connection error
    from requests.exceptions import ConnectionError
    mock_post.side_effect = ConnectionError("Failed to connect to mock server")

    data_payload = {"com.example.Fact": {"field": "any_data"}}
    is_valid, violations = drools_validator_instance.validate_data(data_payload)

    assert is_valid is False
    assert len(violations) == 1
    assert "Drools communication error" in violations[0]
    mock_post.assert_called_once()

def test_drools_validation_no_endpoint():
    """Tests validator behavior when endpoint is not configured."""
    validator = DroolsValidator({}) # Empty config
    data_payload = {"com.example.Fact": {"field": "any_data"}}
    is_valid, violations = validator.validate_data(data_payload)

    assert is_valid is False
    assert len(violations) == 1
    assert "Drools endpoint not configured" in violations[0]