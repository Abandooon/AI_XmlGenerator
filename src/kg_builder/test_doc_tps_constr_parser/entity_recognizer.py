import pathlib

import spacy
from spacy.matcher import PhraseMatcher, Matcher
from spacy.tokens import Doc, Span
import json
from typing import Optional, Any, List, Tuple, Dict
from spacy.lang.en.stop_words import STOP_WORDS
from models import Entity, ConstraintRaw

# 可选：追加领域无关、高频误触词
CUSTOM_STOP_WORDS = {"can", "will", "should", "shall"}

class EntityRecognizer:
    def __init__(self, metadata_path: str):
        # 加载spaCy模型 - 使用英语小模型以提高性能
        self.nlp = spacy.load("en_core_web_sm")

        # 加载元数据
        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)

        # 构建术语表和匹配器
        self.terminology = self._build_terminology()
        with open(pathlib.Path("output/debug/autosar_metadata_entities.json"), "w", encoding="utf-8") as fp:
            json.dump(self.terminology, fp, ensure_ascii=False, indent=2)
        self.phrase_matcher = self._build_phrase_matcher()
        self.pattern_matcher = self._build_pattern_matcher()

        # 实体去重缓存
        self.entity_cache = {}



    def _build_terminology(self) -> Dict[str, List[Dict[str, Any]]]:
        terminology = {"CLASS": [], "ATTRIBUTE": [], "ENUM_VALUE": []}

        # ---------- 1. 处理类 ----------
        for class_name, class_data in self.metadata.get("groups", {}).items():
            # -- 类名词条 --
            terminology["CLASS"].append({
                "text": class_name,
                "metadata": {
                    "description": class_data.get("description", ""),
                    "package": ".".join(class_data.get("Package", [])) or None
                }
            })

            # ---------- 2. 处理属性 ----------
            for element in class_data.get("elements", []):
                # A. 裸属性名（qualifiedName）
                qname = element.get("qualifiedName", "").strip()
                # B. 类.属性（document_name）
                doc_name = element.get("document_name", "").strip() or f"{class_name}.{qname}"

                if not qname:  # 没有裸名就跳过
                    continue

                base_meta = {
                    "parent_class": class_name,
                    "type": element.get("type", ""),
                    "description": element.get("description", ""),
                    "qualified_name": qname,
                    "document_name": doc_name
                }

                # 裸属性名
                terminology["ATTRIBUTE"].append({
                    "text": qname,
                    "metadata": base_meta
                })
                # 类.属性
                terminology["ATTRIBUTE"].append({
                    "text": doc_name,
                    "metadata": base_meta
                })

        # ---------- 3. 处理枚举 ----------
        for typ_id, typ_data in self.metadata.get("simpleTypes", {}).items():
            for enum_val in typ_data.get("enumerations", []):
                terminology["ENUM_VALUE"].append({
                    "text": enum_val,
                    "metadata": {"parent_type": typ_id}
                })

        return terminology

    def _build_phrase_matcher(self) -> PhraseMatcher:
        """构建基于短语的匹配器"""
        matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")

        # 添加类名匹配模式
        class_patterns = [self.nlp(term["text"]) for term in self.terminology["CLASS"]]
        if class_patterns:
            matcher.add("CLASS", class_patterns)

        # 添加属性名匹配模式
        attr_patterns = [self.nlp(term["text"]) for term in self.terminology["ATTRIBUTE"]]
        if attr_patterns:
            matcher.add("ATTRIBUTE", attr_patterns)

        # 添加枚举值匹配模式
        enum_patterns = [self.nlp(term["text"]) for term in self.terminology["ENUM_VALUE"]]
        if enum_patterns:
            matcher.add("ENUM_VALUE", enum_patterns)

        return matcher

    def _build_pattern_matcher(self) -> Matcher:
        """构建基于规则的匹配器，处理特殊模式"""
        matcher = Matcher(self.nlp.vocab)

        # 添加属性路径匹配模式 (如 Class.attribute)
        attr_path_pattern = [
            {"TEXT": {"REGEX": r"[A-Z][A-Za-z0-9]+"}},  # Class
            {"TEXT": "."},  # dot
            {"TEXT": {"REGEX": r"[a-z][A-Za-z0-9]+"}}  # attr
        ]
        matcher.add("ATTRIBUTE_PATH", [attr_path_pattern])

        # 添加对于单独属性名的更严格匹配
        single_attr_pattern = [
            {"TEXT": {"REGEX": r"^[a-z][A-Za-z0-9]+$"}}
        ]
        matcher.add("SINGLE_ATTRIBUTE", [single_attr_pattern])

        return matcher

    def _get_entity_metadata(self, entity_text: str, entity_type: str) -> Dict[str, Any]:
        """获取实体的元数据"""
        for term in self.terminology[entity_type]:
            if term["text"].lower() == entity_text.lower():
                return term["metadata"]
        return {}


    # main函数调用，遍历约束列表，返回该条约束和对应在这里匹配到的实体
    def recognize_entities(self, constraint: ConstraintRaw) -> Tuple[ConstraintRaw, List[Entity]]:
        """识别约束文本中的实体"""
        # 重置实体缓存
        self.entity_cache = {}

        # 处理文本
        text = constraint.body
        doc = self.nlp(text)

        # 存储识别到的实体
        identified_entities = []

        # 使用短语匹配器查找实体
        matches = self.phrase_matcher(doc)
        for match_id, start, end in matches:
            match_type = self.nlp.vocab.strings[match_id]
            span = doc[start:end]
            entity_text = span.text

            # 检查可能的误识别
            if self._is_potential_false_positive(entity_text, text, span.start_char, span.end_char):
                continue

            # 获取实体元数据
            metadata = self._get_entity_metadata(entity_text, match_type)

            # 创建实体对象
            entity = self._create_entity(entity_text, match_type, span.start_char, span.end_char, metadata)
            if entity:
                identified_entities.append(entity)

        # 使用规则匹配器查找特殊模式
        pattern_matches = self.pattern_matcher(doc)
        for match_id, start, end in pattern_matches:
            match_type = self.nlp.vocab.strings[match_id]
            span = doc[start:end]
            entity_text = span.text

            # 检查可能的误识别
            if self._is_potential_false_positive(entity_text, text, span.start_char, span.end_char):
                continue

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

                    # 创建实体对象
                    entity = self._create_entity(entity_text, "ATTRIBUTE_PATH", span.start_char, span.end_char,
                                                 metadata, parent=class_name)
                    if entity:
                        identified_entities.append(entity)

            elif match_type == "SINGLE_ATTRIBUTE":
                # 对单独属性名做额外验证
                if self._validate_single_attribute(entity_text):
                    # 查找元数据
                    metadata = {}
                    parent_class = None

                    for term in self.terminology["ATTRIBUTE"]:
                        if term["text"] == entity_text:
                            metadata = term["metadata"]
                            parent_class = metadata.get("parent_class")
                            break

                    # 创建实体对象
                    entity = self._create_entity(entity_text, "ATTRIBUTE", span.start_char, span.end_char,
                                                 metadata, parent=parent_class)
                    if entity:
                        identified_entities.append(entity)

        # 执行实体验证和去重
        final_entities = self._validate_and_deduplicate_entities(identified_entities)

        return constraint, final_entities



    def _is_potential_false_positive(self,
                                     entity_text: str,
                                     full_text: str,
                                     start: int,
                                     end: int) -> bool:
        text_lc = entity_text.lower()

        # 1) 停用词过滤
        if text_lc in STOP_WORDS or text_lc in CUSTOM_STOP_WORDS:
            return True

        # 2) 长度太短
        if len(entity_text) <= 2:
            return True

        # 3) 前后都是字母 → 可能嵌在单词内部
        if start > 0 and end < len(full_text):
            if full_text[start - 1].isalpha() and full_text[end].isalpha():
                return True

        return False

    def _validate_single_attribute(self, attr_text: str) -> bool:
        """验证单独属性名是否有效"""
        # 检查属性名是否在术语表中
        for term in self.terminology["ATTRIBUTE"]:
            term_parts = term["text"].split(".")
            if len(term_parts) > 1 and term_parts[1] == attr_text:
                return True
            elif term["text"] == attr_text:
                return True

        return False

    def _create_entity(self, text: str, type_str: str, start: int, end: int,
                       metadata: Dict[str, Any], parent: Optional[str] = None) -> Optional[Entity]:
        """创建实体对象，并应用验证规则"""
        # 提取parent，如果未提供
        if not parent and type_str == "ATTRIBUTE":
            parent = metadata.get("parent_class")

        # 创建实体对象
        entity = Entity(
            text=text,
            type=type_str,
            start=start,
            end=end,
            parent=parent,
            metadata=metadata
        )

        # 缓存此实体以便后续去重
        entity_key = f"{start}_{end}_{text}"
        self.entity_cache[entity_key] = entity

        return entity

    def _validate_and_deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """验证和去重实体列表"""
        if not entities:
            return []

        # 按照起始位置排序
        entities.sort(key=lambda e: (e.start, -e.end))

        # 去重并处理重叠
        final_entities = []
        last_end = -1

        for entity in entities:
            # 跳过重叠实体
            if entity.start < last_end:
                # 但保留更长/更具体的实体
                for i, existing in enumerate(final_entities):
                    if existing.start <= entity.start and existing.end >= entity.end:
                        # 当前实体被现有实体完全包含，检查是否更具体
                        if entity.type in ["ATTRIBUTE_PATH"] and existing.type in ["CLASS", "ATTRIBUTE"]:
                            # 属性路径优先级高于单独类或属性
                            final_entities[i] = entity
                        break
                continue

            final_entities.append(entity)
            last_end = entity.end

        return final_entities