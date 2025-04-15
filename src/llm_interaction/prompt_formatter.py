import logging

logger = logging.getLogger(__name__)

def format_basic_prompt(requirement_text: str) -> str:
    """
    Creates a basic prompt for the LLM to generate AUTOSAR XML.

    Args:
        requirement_text: The natural language requirement.

    Returns:
        The formatted prompt string.
    """
    prompt = f"""
Generate an AUTOSAR XML snippet corresponding to the following requirement.
Ensure the XML is well-formed.

Requirement:
"{requirement_text}"

AUTOSAR XML:
"""
    logger.debug("Formatted basic prompt.")
    return prompt

def format_kg_enhanced_prompt(requirement_text: str, kg_context: str) -> str:
    """
    Creates a prompt incorporating knowledge graph context.

    Args:
        requirement_text: The natural language requirement.
        kg_context: Relevant information retrieved from the knowledge graph.

    Returns:
        The formatted prompt string.
    """
    prompt = f"""
Generate an AUTOSAR XML snippet corresponding to the following requirement.
Use the provided Knowledge Graph Context to ensure correctness and consistency.
Ensure the XML is well-formed.

Requirement:
"{requirement_text}"

Knowledge Graph Context:
{kg_context}

AUTOSAR XML:
"""
    logger.debug("Formatted KG-enhanced prompt.")
    return prompt

def format_repair_prompt(original_requirement: str, incorrect_xml: str, error_messages: list[str]) -> str:
    """
    Creates a prompt asking the LLM to repair incorrect XML based on errors.

    Args:
        original_requirement: The initial requirement.
        incorrect_xml: The XML that failed validation.
        error_messages: A list of error messages from validation (XSD, Drools).

    Returns:
        The formatted repair prompt string.
    """
    errors = "\n".join(f"- {e}" for e in error_messages)
    prompt = f"""
The following AUTOSAR XML was generated for the requirement below, but it failed validation.
Please correct the XML based on the provided error messages.

Original Requirement:
"{original_requirement}"

Incorrect XML:
```xml
{incorrect_xml}"""