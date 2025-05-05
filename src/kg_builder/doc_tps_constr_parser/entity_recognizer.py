import spacy
from spacy.matcher import PhraseMatcher, Matcher
from spacy.tokens import Doc, Span
import json
from typing import Optional, Any

from models import Entity, ConstraintRaw


class EntityRecognizer:
    def __init__(self, metadata_path: str):
        # 加载spaCy模型 - 使用英语小模型以提高性能
        self.nlp = spacy.load("en_core_web_sm")

        # 加载元数据
        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)

        # 构建术语表和匹配器
        self.terminology = self._build_terminology()
        self.phrase_matcher = self._build_phrase_matcher()
        self.pattern_matcher = self._build_pattern_matcher()

    def _build_terminology(self) -> dict[str, list[dict[str, Any]]]:
        """从元数据构建术语表，包括类名、属性名和枚举值"""
        terminology = {
            "CLASS": [],
            "ATTRIBUTE": [],
            "ENUM_VALUE": []
        }

        # 处理groups (类)
        for class_name, class_data in self.metadata.get("groups", {}).items():
            terminology["CLASS"].append({
                "text": class_name,
                "metadata": {
                    "description": class_data.get("description", ""),
                    "package": ".".join(class_data.get("Package", [])) if class_data.get("Package") else None
                }
            })

            # 处理类的属性
            for element in class_data.get("elements", []):
                attr_name = element.get("name", "")
                if attr_name:
                    terminology["ATTRIBUTE"].append({
                        "text": attr_name,
                        "metadata": {
                            "parent_class": class_name,
                            "type": element.get("type", ""),
                            "description": element.get("description", ""),
                            "qualified_name": element.get("qualifiedName", "")
                        }
                    })

                    # 添加类.属性形式
                    terminology["ATTRIBUTE"].append({
                        "text": f"{class_name}.{attr_name}",
                        "metadata": {
                            "parent_class": class_name,
                            "type": element.get("type", ""),
                            "description": element.get("description", ""),
                            "qualified_name": element.get("qualifiedName", "")
                        }
                    })

        # 处理simpleTypes (获取枚举值)
        for type_id, type_data in self.metadata.get("simpleTypes", {}).items():
            enumerations = type_data.get("enumerations", [])
            for enum_value in enumerations:
                terminology["ENUM_VALUE"].append({
                    "text": enum_value,
                    "metadata": {
                        "parent_type": type_id,
                        "description": ""
                    }
                })

        return terminology

    def _build_phrase_matcher(self) -> PhraseMatcher:
        """构建基于短语的匹配器"""
        matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")

        # 添加类名匹配模式
        class_patterns = [self.nlp(term["text"]) for term in self.terminology["CLASS"]]
        if class_patterns:
            matcher.add("CLASS", None, *class_patterns)

        # 添加属性名匹配模式
        attr_patterns = [self.nlp(term["text"]) for term in self.terminology["ATTRIBUTE"]]
        if attr_patterns:
            matcher.add("ATTRIBUTE", None, *attr_patterns)

        # 添加枚举值匹配模式
        enum_patterns = [self.nlp(term["text"]) for term in self.terminology["ENUM_VALUE"]]
        if enum_patterns:
            matcher.add("ENUM_VALUE", None, *enum_patterns)

        return matcher

    def _build_pattern_matcher(self) -> Matcher:
        """构建基于规则的匹配器，处理特殊模式"""
        matcher = Matcher(self.nlp.vocab)

        # 添加属性路径匹配模式 (如 Class.attribute)
        attr_path_pattern = [
            {"TEXT": {"REGEX": r"[A-Z][a-zA-Z0-9]+"}, "OP": "+"},  # 类名部分
            {"TEXT": "."},  # 点
            {"TEXT": {"REGEX": r"[a-z][a-zA-Z0-9]+"}, "OP": "+"}  # 属性名部分
        ]
        matcher.add("ATTRIBUTE_PATH", [attr_path_pattern])

        return matcher

    def _get_entity_metadata(self, entity_text: str, entity_type: str) -> dict[str, Any]:
        """获取实体的元数据"""
        for term in self.terminology[entity_type]:
            if term["text"].lower() == entity_text.lower():
                return term["metadata"]
        return {}

    def recognize_entities(self, constraint: ConstraintRaw) -> tuple[ConstraintRaw, list[Entity]]:
        """识别约束文本中的实体"""
        entities = []

        # 合并标题和正文以进行实体识别
        combined_text = f"{constraint.title} {constraint.body}"
        if constraint.explanation:
            combined_text += f" {constraint.explanation}"

        # 处理文本
        doc = self.nlp(combined_text)

        # 使用短语匹配器查找实体
        matches = self.phrase_matcher(doc)
        for match_id, start, end in matches:
            match_type = self.nlp.vocab.strings[match_id]
            span = doc[start:end]
            entity_text = span.text

            # 获取实体元数据
            metadata = self._get_entity_metadata(entity_text, match_type)

            entity = Entity(
                text=entity_text,
                type=match_type,
                start=span.start_char,
                end=span.end_char,
                parent=metadata.get("parent_class") or metadata.get("parent_type"),
                metadata=metadata
            )

            entities.append(entity)

        # 使用规则匹配器查找特殊模式
        pattern_matches = self.pattern_matcher(doc)
        for match_id, start, end in pattern_matches:
            match_type = self.nlp.vocab.strings[match_id]
            span = doc[start:end]
            entity_text = span.text

            # 对于属性路径，分解为类名和属性名
            if match_type == "ATTRIBUTE_PATH":
                parts = entity_text.split(".")
                if len(parts) == 2:
                    class_name, attr_name = parts

                    # 查找该类的属性元数据
                    metadata = {}
                    for term in self.terminology["ATTRIBUTE"]:
                        if term["text"] == entity_text:
                            metadata = term["metadata"]
                            break

                    entity = Entity(
                        text=entity_text,
                        type="ATTRIBUTE_PATH",
                        start=span.start_char,
                        end=span.end_char,
                        parent=class_name,
                        metadata=metadata
                    )

                    entities.append(entity)

        return constraint, entities