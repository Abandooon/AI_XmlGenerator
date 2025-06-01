import re
from config import (
    CLASS_ANNOTATION_PATTERN, ENUM_ANNOTATION_PATTERN, SECTION_ANNOTATION_PATTERN
)


# get_enum_literals 函数保持不变 (如原文档提供)
def get_enum_literals(metadata, enum_name):
    def to_camel_case(s):
        parts = s.lower().split('-')
        return parts[0] + ''.join(word.capitalize() for word in parts[1:]) if len(parts) > 1 else s

    literals = set()
    if enum_name in metadata.get("simpleTypes", {}):
        simple_type_data = metadata["simpleTypes"][enum_name]
        if "enumerations" in simple_type_data and isinstance(simple_type_data["enumerations"], list):
            for literal in simple_type_data["enumerations"]:
                if isinstance(literal, str):
                    literals.add(literal)
                    camel_literal = to_camel_case(literal)
                    if camel_literal != literal:
                        literals.add(camel_literal)
    if enum_name in metadata.get("complexTypes", {}):
        complex_type_data = metadata["complexTypes"][enum_name]
        if "enumeration" in complex_type_data and isinstance(complex_type_data["enumeration"], list):
            for item in complex_type_data["enumeration"]:
                if isinstance(item, str):
                    literals.add(item)
                    camel_item = to_camel_case(item)
                    if camel_item != item:
                        literals.add(camel_item)
                elif isinstance(item, dict) and "value" in item:
                    value = item["value"]
                    literals.add(value)
                    camel_value = to_camel_case(value)
                    if camel_value != value:
                        literals.add(camel_value)
        if "attributes" in complex_type_data and isinstance(complex_type_data["attributes"], list):
            for attr in complex_type_data["attributes"]:
                attr_type = attr.get("type")
                if attr_type and attr_type in metadata.get("simpleTypes", {}):
                    simple_type_data = metadata["simpleTypes"][attr_type]
                    if "enumerations" in simple_type_data and isinstance(simple_type_data["enumerations"], list):
                        for enum_item in simple_type_data["enumerations"]:
                            if isinstance(enum_item, str):
                                literals.add(enum_item)
                                camel_enum_item = to_camel_case(enum_item)
                                if camel_enum_item != enum_item:
                                    literals.add(camel_enum_item)
                            elif isinstance(enum_item, dict) and "value" in enum_item:
                                value = enum_item["value"]
                                literals.add(value)
                                camel_value = to_camel_case(value)
                                if camel_value != value:
                                    literals.add(camel_value)
    if not literals:
        print(f"警告: 未能为枚举 '{enum_name}' 从元数据中找到任何字面量。")
    return sorted(list(literals))


def get_class_info(metadata, class_name):
    """
    从元数据中获取指定类的属性（包括所有父类的属性）、
    直接继承关系和直接子类信息。
    """
    accumulated_attributes = set()
    direct_parents_of_target_class = []
    childs_of_target_class = []

    processing_queue = [class_name]  # Start with the requested class
    visited_classes_for_attributes = set()

    while processing_queue:
        current_class_to_process = processing_queue.pop(0)  # FIFO for BFS-like traversal

        if current_class_to_process in visited_classes_for_attributes:
            continue
        visited_classes_for_attributes.add(current_class_to_process)

        # 1. Collect direct attributes for current_class_to_process
        # From "groups"
        if current_class_to_process in metadata.get("groups", {}):
            group_data = metadata["groups"][current_class_to_process]
            elements = group_data.get("elements", [])
            if isinstance(elements, list):
                for el in elements:
                    if isinstance(el, dict) and el.get("qualifiedName"):
                        accumulated_attributes.add(el["qualifiedName"])

        # From "complexTypes"
        if current_class_to_process in metadata.get("complexTypes", {}):
            complex_type_data = metadata["complexTypes"][current_class_to_process]
            # Attributes from "attributes" key
            complex_attributes_list = complex_type_data.get("attributes", [])
            if isinstance(complex_attributes_list, list):
                for attr in complex_attributes_list:
                    if isinstance(attr, dict) and attr.get("name"):
                        accumulated_attributes.add(attr["name"])
            # Attributes from "elements" key (if complexType also uses 'elements' for attribute-like things)
            complex_elements_list = complex_type_data.get("elements", [])
            if isinstance(complex_elements_list, list):
                for el in complex_elements_list:
                    if isinstance(el, dict) and el.get("name"):
                        accumulated_attributes.add(el["name"])

        # From "extract_inner_class"
        if current_class_to_process in metadata.get("extract_inner_class", {}):
            inner_class_data = metadata["extract_inner_class"][current_class_to_process]
            inner_attributes_list = inner_class_data.get("attributes", [])
            if isinstance(inner_attributes_list, list):
                for attr in inner_attributes_list:
                    if isinstance(attr, dict) and attr.get("name"):
                        accumulated_attributes.add(attr["name"])

        # 2. Process parents (Generalization) for current_class_to_process
        # Parents are typically defined within the "groups" structure for class hierarchies
        if current_class_to_process in metadata.get("groups", {}):
            group_data_for_parents = metadata["groups"][current_class_to_process]
            parents_of_current = group_data_for_parents.get("generalization", [])

            if isinstance(parents_of_current, list):
                # If this is the originally requested class, store its direct parents
                if current_class_to_process == class_name:
                    for p_name in parents_of_current:
                        if isinstance(p_name, str) and p_name.strip():
                            direct_parents_of_target_class.append(p_name.strip())

                # Add valid parents to the queue for further attribute collection
                for parent_name_str in parents_of_current:
                    if isinstance(parent_name_str, str) and parent_name_str.strip():
                        cleaned_parent_name = parent_name_str.strip()
                        # Only add to queue if not already visited (its attributes would be processed)
                        # and not already in queue (though visited check is primary)
                        if cleaned_parent_name not in visited_classes_for_attributes:
                            if cleaned_parent_name not in processing_queue:  # Minor optimization
                                processing_queue.append(cleaned_parent_name)

    # Collect Child Information (for the original class_name only)
    if class_name in metadata.get("groups", {}):
        group_data_for_children = metadata["groups"][class_name]
        child_names_list = group_data_for_children.get("childs", [])
        if isinstance(child_names_list, list):
            for c_name in child_names_list:
                if isinstance(c_name, str) and c_name.strip():
                    childs_of_target_class.append(c_name.strip())

    # Warning if no attributes were found in the entire hierarchy for the requested class
    if not accumulated_attributes:
        print(f"警告: 未能为类 '{class_name}' 或其任何父类从元数据中找到任何属性。")

    return {
        "attributes": sorted(list(accumulated_attributes)),
        "generalization": sorted(list(set(direct_parents_of_target_class))),  # Unique, sorted direct parents
        "childs": sorted(list(set(childs_of_target_class)))  # Unique, sorted direct children
    }


def inject_local_context(markdown_content, metadata):
    print("DEBUG: 开始局部上下文注入 (inject_local_context)...")
    processed_lines = []
    lines = markdown_content.splitlines()
    print(f"DEBUG: inject_local_context: 总共需要处理 {len(lines)} 行。")

    for i, line in enumerate(lines):
        current_line_number = i + 1
        processed_lines.append(line)

        class_match = re.search(CLASS_ANNOTATION_PATTERN, line)
        if class_match:
            # This block remains largely the same, but the 'attributes' list from get_class_info
            # will now be comprehensive (including inherited ones).
            print(f"DEBUG: inject_local_context: 第 {current_line_number} 行 - CLASS_ANNOTATION_PATTERN 成功匹配!")
            class_name = class_match.group(1).strip()
            print(f"DEBUG: inject_local_context: 在第 {current_line_number} 行找到 CLASS 标注: '{class_name}'")

            class_info = get_class_info(metadata, class_name)  # This now returns inherited attributes too
            attributes = class_info["attributes"]
            generalization = class_info["generalization"]  # Direct parents
            childs = class_info["childs"]  # Direct children

            context_parts = []
            if attributes:
                attr_str = ', '.join(attributes)
                context_parts.append(f"Attributes=[{attr_str}] (包含继承属性)")  # Clarified in comment
            else:
                # Updated message to reflect that inherited attributes were also checked
                context_parts.append("Attributes=[] (元数据中未找到该类及其父类的任何属性)")

            if generalization:
                gen_str = ', '.join(generalization)
                context_parts.append(f"Generalization=[{gen_str}] (直接父类)")  # Clarified

            if childs:
                child_str = ', '.join(childs)
                context_parts.append(f"Childs=[{child_str}] (直接子类)")  # Clarified

            context_comment_content = '; '.join(context_parts)
            context_comment = f"<!-- LLM_CONTEXT FOR CLASS {class_name}: {context_comment_content} -->"

            print(f"DEBUG: inject_local_context: 为 CLASS '{class_name}' 生成的上下文: {context_comment}")
            if not attributes and not generalization and not childs:
                print(
                    f"DEBUG: inject_local_context: 注意 - 为 CLASS '{class_name}' 未在元数据中找到任何属性（包括继承）、直接父类或直接子类信息。")

            processed_lines.append(context_comment)
            print(f"DEBUG: inject_local_context: 已追加 CLASS 上下文到第 {current_line_number} 行之后。")
            continue
        else:
            if line.strip().startswith("#@CLASS"):
                print(f"DEBUG: inject_local_context: 第 {current_line_number} 行 - CLASS_ANNOTATION_PATTERN 未能匹配。")
                if not line.startswith("#@CLASS:"):
                    print(
                        f"DEBUG: inject_local_context: 第 {current_line_number} 行 - 问题: 不是以 '#@CLASS:' 开头。实际开头 (前10字符): '{line[:10]}'")
                else:
                    remainder_after_prefix = line[len("#@CLASS:"):]
                    print(
                        f"DEBUG: inject_local_context: 第 {current_line_number} 行 - 前缀 '#@CLASS:' 存在。检查剩余部分: {repr(remainder_after_prefix)}")
                    if not re.match(r"\s*(\S+)", remainder_after_prefix):
                        print(
                            f"DEBUG: inject_local_context: 第 {current_line_number} 行 - 问题: 剩余部分 '{remainder_after_prefix}' (repr: {repr(remainder_after_prefix)}) 与 r'\\s*(\\S+)' 不匹配。")

        enum_match = re.search(ENUM_ANNOTATION_PATTERN, line)
        if enum_match:
            # Enum handling remains the same as it doesn't have inheritance of literals in this context
            print(f"DEBUG: inject_local_context: 第 {current_line_number} 行 - ENUM_ANNOTATION_PATTERN 成功匹配!")
            enum_name = enum_match.group(1).strip()
            print(f"DEBUG: inject_local_context: 在第 {current_line_number} 行找到 ENUM 标注: '{enum_name}'")
            literals = get_enum_literals(metadata, enum_name)

            context_parts_enum = []
            if literals:
                lit_str = ', '.join(literals)
                context_parts_enum.append(f"Literals=[{lit_str}]")
            else:
                context_parts_enum.append("Literals=[] (元数据中未找到字面量)")

            enum_context_comment_content = '; '.join(context_parts_enum)
            context_comment = f"<!-- LLM_CONTEXT FOR ENUM {enum_name}: {enum_context_comment_content} -->"

            print(f"DEBUG: inject_local_context: 为 ENUM '{enum_name}' 生成的上下文: {context_comment}")
            processed_lines.append(context_comment)
            print(f"DEBUG: inject_local_context: 已追加 ENUM 上下文到第 {current_line_number} 行之后。")

    enhanced_content = "\n".join(processed_lines)
    print(f"DEBUG: inject_local_context: 局部上下文注入完成。增强后内容的长度: {len(enhanced_content)}")
    return enhanced_content


def process_document_for_llm(markdown_content, metadata):
    print("DEBUG: 调用 process_document_for_llm...")
    enhanced_content = inject_local_context(markdown_content, metadata)
    return enhanced_content