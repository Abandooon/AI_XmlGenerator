# src/validation/semantic_check/drools_wrapper.py
import subprocess


class DroolsValidator:
    def __init__(self, drools_path: str):
        self.drools_jar = drools_path  # drools-core-7.0.0.Final.jar

    def validate(self, xml_str: str) -> bool:
        result = subprocess.run(
            ["java", "-cp", self.drools_jar, "DroolsValidator", xml_str],
            capture_output=True
        )
        return result.returncode == 0