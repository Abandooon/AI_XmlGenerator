import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseGenerator(ABC):
    """Abstract base class for different XML generation strategies."""

    def __init__(self, config: dict, llm_client=None, kg_querier=None, xsd_schema=None, drools_validator=None):
        """
        Initializes the base generator.

        Args:
            config: General project configuration.
            llm_client: Instance of LLMClient.
            kg_querier: Instance of KGQuerier.
            xsd_schema: Loaded XSD schema object (e.g., from lxml).
            drools_validator: Instance of DroolsValidator.
        """
        self.config = config
        self.llm_client = llm_client
        self.kg_querier = kg_querier
        self.xsd_schema = xsd_schema
        self.drools_validator = drools_validator
        logger.info(f"Initializing {self.__class__.__name__}")

    @abstractmethod
    def generate(self, requirement_text: str, parsed_requirement: dict) -> tuple[str | None, list[str]]:
        """
        Generates the AUTOSAR XML based on the input requirement.

        Args:
            requirement_text: The original natural language requirement.
            parsed_requirement: The result from the NLProcessor.

        Returns:
            A tuple containing:
            - The generated XML string (or None if generation failed).
            - A list of validation errors encountered (if any).
        """
        pass

    def _validate_xml(self, xml_content: str) -> tuple[bool, list[str]]:
        """Helper method to perform configured validations."""
        all_errors = []
        xsd_valid = True
        drools_valid = True

        # 1. XSD Validation (if schema is provided)
        if self.xsd_schema:
            from src.validation.xsd_validator import validate_xsd # Local import
            xsd_valid, xsd_errors = validate_xsd(xml_content, self.xsd_schema)
            if not xsd_valid:
                all_errors.extend(xsd_errors)

        # Only proceed to Drools if XSD is valid (or no XSD check) and Drools is enabled
        if xsd_valid and self.drools_validator:
            # Convert XML to the format Drools expects (e.g., facts dict)
            # This conversion logic might be complex and specific
            drools_input_data = self._prepare_data_for_drools(xml_content)
            if drools_input_data is not None:
                 drools_valid, drools_errors = self.drools_validator.validate_data(drools_input_data)
                 if not drools_valid:
                     all_errors.extend(drools_errors)
            else:
                 logger.warning("Could not prepare data for Drools validation from XML.")
                 # Decide if this failure itself constitutes an error
                 # all_errors.append("Failed to prepare data for Drools validation.")

        is_fully_valid = xsd_valid and drools_valid
        return is_fully_valid, all_errors

    def _prepare_data_for_drools(self, xml_content: str) -> dict | str | None:
        """
        Placeholder: Converts generated XML into the format expected by DroolsValidator.
        This needs actual implementation based on how rules consume data.
        It might involve parsing the XML and creating a dictionary of facts.
        """
        logger.debug("Preparing data for Drools validation (Placeholder).")
        # Example: Parse XML and create a dict - highly dependent on XML structure and rules
        # try:
        #     from lxml import etree
        #     root = etree.fromstring(xml_content.encode('utf-8'))
        #     # Extract relevant info based on expected fact types
        #     facts = {"com.example.autosar.SomeFact": {"attribute": root.findtext("SOME_ELEMENT")}}
        #     return facts
        # except Exception as e:
        #     logger.error(f"Error parsing XML for Drools preparation: {e}")
        #     return None

        # Or, if rules work on raw XML string:
        # return xml_content

        # Return None if conversion is not possible or not implemented yet
        return {"simulated_fact": {"content": xml_content[:50]}} # Basic simulation

    def _repair_xml(self, requirement_text: str, incorrect_xml: str, errors: list[str]) -> str | None:
        """Attempts to repair the XML using the LLM based on validation errors."""
        if not self.llm_client:
            logger.warning("LLM client not available for repair attempt.")
            return None
        if not errors:
            logger.warning("No errors provided for repair attempt.")
            return incorrect_xml # Or None?

        logger.info(f"Attempting LLM-based repair for {len(errors)} errors.")
        from src.llm_interaction.prompt_formatter import format_repair_prompt # Local import
        repair_prompt = format_repair_prompt(requirement_text, incorrect_xml, errors)
        repaired_xml = self.llm_client.generate_text(repair_prompt)

        if repaired_xml:
            logger.info("Received repaired XML suggestion from LLM.")
            # Basic check: is it still XML-like?
            if not (repaired_xml.strip().startswith("<") and repaired_xml.strip().endswith(">")):
                 logger.warning("LLM repair output doesn't look like XML.")
                 return None # Or return the original incorrect one?
            return repaired_xml
        else:
            logger.error("LLM failed to generate a repair suggestion.")
            return None