import logging
from lxml import etree # lxml is commonly used for XSD validation

logger = logging.getLogger(__name__)

def load_xsd_schema(xsd_path: str) -> etree.XMLSchema | None:
    """Loads the XSD schema from a file."""
    try:
        xmlschema_doc = etree.parse(xsd_path)
        xmlschema = etree.XMLSchema(xmlschema_doc)
        logger.info(f"Successfully loaded XSD schema from: {xsd_path}")
        return xmlschema
    except etree.XMLSchemaParseError as e:
        logger.error(f"Failed to parse XSD schema file '{xsd_path}': {e}", exc_info=True)
        return None
    except FileNotFoundError:
        logger.error(f"XSD schema file not found at: {xsd_path}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading XSD '{xsd_path}': {e}", exc_info=True)
        return None

def validate_xsd(xml_content: str | bytes, xmlschema: etree.XMLSchema) -> tuple[bool, list[str]]:
    """
    Validates XML content against a loaded XSD schema.

    Args:
        xml_content: The XML content as a string or bytes.
        xmlschema: The loaded lxml.etree.XMLSchema object.

    Returns:
        A tuple: (is_valid: bool, error_messages: list[str])
    """
    if not xmlschema:
        logger.error("XSD schema object is None. Cannot validate.")
        return False, ["XSD schema was not loaded successfully."]

    if isinstance(xml_content, str):
        xml_content = xml_content.encode('utf-8') # lxml often prefers bytes

    try:
        xml_doc = etree.fromstring(xml_content)
        is_valid = xmlschema.validate(xml_doc)
        if is_valid:
            logger.debug("XSD validation successful.")
            return True, []
        else:
            errors = [f"XSD Error: {err.message} (Line: {err.line}, Col: {err.column})" for err in xmlschema.error_log]
            logger.warning(f"XSD validation failed: {errors}")
            return False, errors
    except etree.XMLSyntaxError as e:
        logger.warning(f"XML Syntax Error during parsing for XSD validation: {e}", exc_info=True)
        return False, [f"XML Syntax Error: {e}"]
    except Exception as e:
        logger.error(f"An unexpected error occurred during XSD validation: {e}", exc_info=True)
        return False, [f"Unexpected validation error: {e}"]

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # --- Example Usage ---
    # Replace with actual paths from config
    xsd_file = "../../data/schemas/AUTOSAR_XYZ.xsd" # Needs a real XSD
    # Create dummy XSD and XML for testing if real ones aren't available
    # Dummy XSD content (example)
    dummy_xsd_content = """<?xml version="1.0" encoding="UTF-8" ?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="ROOT">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="ELEMENT" type="xs:string" minOccurs="1"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
"""
    # Dummy XML content (valid and invalid)
    valid_xml = "<ROOT><ELEMENT>Hello</ELEMENT></ROOT>"
    invalid_xml_missing = "<ROOT></ROOT>"
    invalid_xml_syntax = "<ROOT><ELEMENT>Hello</ELEMENT" # Missing closing tag

    # Write dummy XSD to a temporary file for loading
    import tempfile
    import os
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".xsd") as tmp_xsd:
            tmp_xsd.write(dummy_xsd_content)
            xsd_file_path = tmp_xsd.name

        schema = load_xsd_schema(xsd_file_path)

        if schema:
            print("\n--- Testing Valid XML ---")
            is_valid, errors = validate_xsd(valid_xml, schema)
            print(f"Validation Result: {'Valid' if is_valid else 'Invalid'}")
            if errors: print("Errors:", errors)

            print("\n--- Testing Invalid XML (Missing Element) ---")
            is_valid, errors = validate_xsd(invalid_xml_missing, schema)
            print(f"Validation Result: {'Valid' if is_valid else 'Invalid'}")
            if errors: print("Errors:", errors)

            print("\n--- Testing Invalid XML (Syntax Error) ---")
            is_valid, errors = validate_xsd(invalid_xml_syntax, schema)
            print(f"Validation Result: {'Valid' if is_valid else 'Invalid'}")
            if errors: print("Errors:", errors)
        else:
            print("Could not load the dummy XSD schema.")

    finally:
        if 'xsd_file_path' in locals() and os.path.exists(xsd_file_path):
            os.remove(xsd_file_path) # Clean up temp file