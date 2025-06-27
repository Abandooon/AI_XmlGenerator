import re
from src.utils.logger import get_logger
logger = get_logger(__name__)

class XMLPostProcessor:
    def clean_generated_xml(self, raw: str) -> str:
        # very naive – 去除 ``` 补全换行等
        cleaned = re.sub(r"^[\s`]+|[\s`]+$", "", raw)
        return cleaned
