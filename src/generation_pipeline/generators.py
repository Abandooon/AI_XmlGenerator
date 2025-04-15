import logging
from .base_generator import BaseGenerator
from src.llm_interaction.prompt_formatter import format_basic_prompt, format_kg_enhanced_prompt
from src.validation.xsd_validator import validate_xsd # Direct import for XSD-specific generator

logger = logging.getLogger(__name__)

MAX_REPAIR_ATTEMPTS = 2 # Configurable: How many times to try repairing

class NaiveGenerator(BaseGenerator):
    """Baseline 1: Generates XML using only the LLM with a basic prompt."""

    def generate(self, requirement_text: str, parsed_requirement: dict) -> tuple[str | None, list[str]]:
        logger.info("Running NaiveGenerator...")
        if not self.llm_client:
            logger.error("LLM client not configured for NaiveGenerator.")
            return None, ["LLM client not available."]

        prompt = format_basic_prompt(requirement_text)
        generated_xml = self.llm_client.generate_text(prompt)

        if not generated_xml:
            logger.error("LLM failed to generate any output.")
            return None, ["LLM generation failed."]

        # Basic check if it looks like XML
        if not (generated_xml.strip().startswith("<") and generated_xml.strip().endswith(">")):
             logger.warning("LLM output doesn't look like XML.")
             return None, ["LLM output is not valid XML structure."]

        logger.info("Naive generation complete.")
        # No validation performed in this baseline
        return generated_xml, []


class XsdConstrainedGenerator(BaseGenerator):
    """Baseline 2: LLM generation followed by XSD validation and optional repair."""

    def generate(self, requirement_text: str, parsed_requirement: dict) -> tuple[str | None, list[str]]:
        logger.info("Running XsdConstrainedGenerator...")
        if not self.llm_client:
            logger.error("LLM client not configured.")
            return None, ["LLM client not available."]
        if not self.xsd_schema:
             logger.error("XSD schema not provided for validation.")
             return None, ["XSD schema not available."]

        prompt = format_basic_prompt(requirement_text) # Start with basic prompt
        current_xml = self.llm_client.generate_text(prompt)
        final_errors = ["Initial LLM generation failed."] # Default error

        if not current_xml:
            logger.error("Initial LLM generation failed.")
            return None, final_errors

        for attempt in range(MAX_REPAIR_ATTEMPTS + 1):
            logger.info(f"Validation attempt {attempt + 1}/{MAX_REPAIR_ATTEMPTS + 1}")

            # Basic XML structure check before validation
            if not (current_xml.strip().startswith("<") and current_xml.strip().endswith(">")):
                final_errors = ["LLM output is not valid XML structure."]
                logger.warning(final_errors[0])
                if attempt >= MAX_REPAIR_ATTEMPTS: break # Stop if structure is bad and no more repairs
                 # Try to repair even if structure is bad? Maybe not useful.
                current_xml = self._repair_xml(requirement_text, current_xml, final_errors)
                if not current_xml: break # Repair failed
                continue # Retry validation with repaired XML


            is_valid, errors = validate_xsd(current_xml, self.xsd_schema)
            final_errors = errors # Store errors from this attempt

            if is_valid:
                logger.info("XSD validation successful.")
                return current_xml, [] # Success
            else:
                logger.warning(f"XSD validation failed with {len(errors)} errors.")
                if attempt < MAX_REPAIR_ATTEMPTS:
                    repaired_xml = self._repair_xml(requirement_text, current_xml, errors)
                    if repaired_xml:
                        current_xml = repaired_xml
                    else:
                        logger.error("Repair attempt failed. Stopping.")
                        break # Stop if repair fails
                else:
                    logger.error("Max repair attempts reached. Returning last invalid XML with errors.")
                    break # Stop after max attempts

        # If loop finishes without returning success
        return current_xml, final_errors # Return the last generated (possibly invalid) XML and its errors


class FullConstrainedGenerator(BaseGenerator):
    """Baseline 3: LLM + XSD Validation + Drools Validation + Repair."""

    def generate(self, requirement_text: str, parsed_requirement: dict) -> tuple[str | None, list[str]]:
        logger.info("Running FullConstrainedGenerator...")
        if not self.llm_client:
            logger.error("LLM client not configured.")
            return None, ["LLM client not available."]
        if not self.xsd_schema:
             logger.warning("XSD schema not provided. Skipping XSD checks.")
             # Allow proceeding without XSD if needed, but log warning
             # return None, ["XSD schema not available."]
        if not self.drools_validator:
             logger.warning("Drools validator not configured. Skipping Drools checks.")
             # Allow proceeding without Drools if needed, but log warning
             # return None, ["Drools validator not available."]


        prompt = format_basic_prompt(requirement_text) # Start with basic prompt
        current_xml = self.llm_client.generate_text(prompt)
        final_errors = ["Initial LLM generation failed."]

        if not current_xml:
            logger.error("Initial LLM generation failed.")
            return None, final_errors

        for attempt in range(MAX_REPAIR_ATTEMPTS + 1):
            logger.info(f"Validation attempt {attempt + 1}/{MAX_REPAIR_ATTEMPTS + 1}")

            # Basic XML structure check
            if not (current_xml.strip().startswith("<") and current_xml.strip().endswith(">")):
                final_errors = ["LLM output is not valid XML structure."]
                logger.warning(final_errors[0])
                if attempt >= MAX_REPAIR_ATTEMPTS: break
                current_xml = self._repair_xml(requirement_text, current_xml, final_errors)
                if not current_xml: break
                continue

            # Use the combined validation method from BaseGenerator
            is_valid, errors = self._validate_xml(current_xml)
            final_errors = errors

            if is_valid:
                logger.info("Full validation (XSD + Drools) successful.")
                return current_xml, [] # Success
            else:
                logger.warning(f"Full validation failed with {len(errors)} errors.")
                if attempt < MAX_REPAIR_ATTEMPTS:
                    repaired_xml = self._repair_xml(requirement_text, current_xml, errors)
                    if repaired_xml:
                        current_xml = repaired_xml
                    else:
                        logger.error("Repair attempt failed. Stopping.")
                        break
                else:
                    logger.error("Max repair attempts reached. Returning last invalid XML with errors.")
                    break

        return current_xml, final_errors


class KgEnhancedGenerator(BaseGenerator):
    """Proposed Method: Uses KG Queries to enhance the prompt, then full validation + repair."""

    def generate(self, requirement_text: str, parsed_requirement: dict) -> tuple[str | None, list[str]]:
        logger.info("Running KgEnhancedGenerator...")
        if not self.llm_client:
            logger.error("LLM client not configured.")
            return None, ["LLM client not available."]
        if not self.kg_querier:
            logger.error("KG Querier not configured.")
            # Decide: Fallback to FullConstrained or fail? Let's fail for now.
            return None, ["KG Querier not available."]
        # XSD/Drools checks are optional but recommended, handled by _validate_xml

        # --- 1. Query Knowledge Graph ---
        kg_context = self._query_kg_for_context(parsed_requirement)

        # --- 2. Format Prompt with KG Context ---
        prompt = format_kg_enhanced_prompt(requirement_text, kg_context)

        # --- 3. Generate Initial XML ---
        current_xml = self.llm_client.generate_text(prompt)
        final_errors = ["Initial LLM generation failed (KG enhanced)."]

        if not current_xml:
            logger.error("Initial LLM generation failed.")
            return None, final_errors

        # --- 4. Validate and Repair Loop (using BaseGenerator's methods) ---
        for attempt in range(MAX_REPAIR_ATTEMPTS + 1):
            logger.info(f"Validation attempt {attempt + 1}/{MAX_REPAIR_ATTEMPTS + 1}")

            # Basic XML structure check
            if not (current_xml.strip().startswith("<") and current_xml.strip().endswith(">")):
                final_errors = ["LLM output is not valid XML structure."]
                logger.warning(final_errors[0])
                if attempt >= MAX_REPAIR_ATTEMPTS: break
                current_xml = self._repair_xml(requirement_text, current_xml, final_errors)
                if not current_xml: break
                continue

            # Use the combined validation method
            is_valid, errors = self._validate_xml(current_xml)
            final_errors = errors

            if is_valid:
                logger.info("KG Enhanced generation and validation successful.")
                return current_xml, [] # Success
            else:
                logger.warning(f"KG Enhanced validation failed with {len(errors)} errors.")
                if attempt < MAX_REPAIR_ATTEMPTS:
                    repaired_xml = self._repair_xml(requirement_text, current_xml, errors)
                    if repaired_xml:
                        current_xml = repaired_xml
                    else:
                        logger.error("Repair attempt failed. Stopping.")
                        break
                else:
                    logger.error("Max repair attempts reached. Returning last invalid XML with errors.")
                    break

        return current_xml, final_errors

    def _query_kg_for_context(self, parsed_requirement: dict) -> str:
        """
        Queries the KG based on parsed requirements to get relevant context.
        This is a placeholder for potentially complex logic.
        """
        logger.info("Querying KG for context based on parsed requirement...")
        context_str = "No specific context found." # Default
        entities = parsed_requirement.get("entities", [])
        intent = parsed_requirement.get("intent", "unknown")

        # Example Logic: Find info about mentioned entities
        all_related_info = []
        for entity_text, entity_type in entities:
            # Need to map entity_text/type to KG URIs/concepts
            # concept_uri = map_entity_to_uri(entity_text, entity_type) # Placeholder function
            concept_uri = f"http://example.org/autosar/{entity_text}" # Dummy URI
            if concept_uri:
                 # Example query: find properties or related items
                 # query = f"DESCRIBE <{concept_uri}>" # Or more specific queries
                 # results = self.kg_querier.execute_query(query)
                 # Process results into a string format suitable for the prompt
                 # simulated_results = self.kg_querier.find_related_concepts(concept_uri)
                 simulated_results = [f"Related_to_{entity_text}_1", f"Attribute_{entity_text}_A"] # Simulate
                 if simulated_results:
                     all_related_info.append(f"Context for '{entity_text}': {', '.join(simulated_results)}")

        if all_related_info:
            context_str = "\n".join(all_related_info)

        logger.debug(f"Generated KG context: {context_str}")
        return context_str