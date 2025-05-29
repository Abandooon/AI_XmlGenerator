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
    从元数据中获取指定类的属性、继承关系和子类信息。
    """
    attributes = set()
    generalization = []
    childs = []

    # 从 "groups" 中提取属性、继承和子类信息
    if class_name in metadata.get("groups", {}):
        group_data = metadata["groups"][class_name]

        # 提取属性
        elements = group_data.get("elements", [])
        for el in elements:
            if el.get("qualifiedName"):
                attributes.add(el["qualifiedName"])

        # 提取继承信息 (generalization)
        if "generalization" in group_data and isinstance(group_data["generalization"], list):
            # 确保列表中的元素是字符串且非空，然后去重并排序
            generalization = sorted(
                list(set(g for g in group_data["generalization"] if isinstance(g, str) and g.strip())))

        # 提取子类信息 (childs)
        if "childs" in group_data and isinstance(group_data["childs"], list):
            # 确保列表中的元素是字符串且非空，然后去重并排序
            childs = sorted(list(set(c for c in group_data["childs"] if isinstance(c, str) and c.strip())))

    # 从 "complexTypes" 中提取属性
    if class_name in metadata.get("complexTypes", {}):
        complex_type_data = metadata["complexTypes"][class_name]
        complex_attributes = complex_type_data.get("attributes", [])
        for attr in complex_attributes:
            if attr.get("name"):
                attributes.add(attr["name"])
        complex_elements = complex_type_data.get("elements", [])
        for el in complex_elements:
            if el.get("name"):
                attributes.add(el["name"])

    # 从 "extract_inner_class" 中提取属性
    if class_name in metadata.get("extract_inner_class", {}):
        inner_class_data = metadata["extract_inner_class"][class_name]
        inner_attributes = inner_class_data.get("attributes", [])
        for attr in inner_attributes:
            if attr.get("name"):
                attributes.add(attr["name"])

    sorted_attributes = sorted(list(attributes))

    # 仅当主要属性列表为空时发出警告，继承和子类是附加信息
    if not sorted_attributes:
        print(f"警告: 未能为类 '{class_name}' 从元数据中找到任何属性。")

    return {
        "attributes": sorted_attributes,
        "generalization": generalization,
        "childs": childs
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
            print(f"DEBUG: inject_local_context: 第 {current_line_number} 行 - CLASS_ANNOTATION_PATTERN 成功匹配!")
            class_name = class_match.group(1).strip()
            print(f"DEBUG: inject_local_context: 在第 {current_line_number} 行找到 CLASS 标注: '{class_name}'")

            class_info = get_class_info(metadata, class_name)
            attributes = class_info["attributes"]
            generalization = class_info["generalization"]
            childs = class_info["childs"]

            context_parts = []
            if attributes:
                attr_str = ', '.join(attributes)
                context_parts.append(f"Attributes=[{attr_str}]")
            else:
                # 即使属性为空，也明确指出
                context_parts.append("Attributes=[] (元数据中未找到属性或该类无直接定义的属性)")

            if generalization:
                gen_str = ', '.join(generalization)
                context_parts.append(f"Generalization=[{gen_str}]")

            if childs:
                child_str = ', '.join(childs)
                context_parts.append(f"Childs=[{child_str}]")

            context_comment_content = '; '.join(context_parts)
            context_comment = f"<!-- LLM_CONTEXT FOR CLASS {class_name}: {context_comment_content} -->"

            print(f"DEBUG: inject_local_context: 为 CLASS '{class_name}' 生成的上下文: {context_comment}")
            if not attributes and not generalization and not childs:
                # 这个额外的打印是为了在所有信息都缺失时（除了属性列表为空的默认信息外）引起注意
                print(
                    f"DEBUG: inject_local_context: 注意 - 为 CLASS '{class_name}' 未在元数据中找到任何属性、继承或子类信息 (除了属性列表为空的默认标记)。")

            processed_lines.append(context_comment)
            print(f"DEBUG: inject_local_context: 已追加 CLASS 上下文到第 {current_line_number} 行之后。")
            continue  # 处理下一行
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
            print(f"DEBUG: inject_local_context: 第 {current_line_number} 行 - ENUM_ANNOTATION_PATTERN 成功匹配!")
            enum_name = enum_match.group(1).strip()
            print(f"DEBUG: inject_local_context: 在第 {current_line_number} 行找到 ENUM 标注: '{enum_name}'")
            literals = get_enum_literals(metadata, enum_name)  # get_enum_literals 保持不变

            context_parts_enum = []
            if literals:
                lit_str = ', '.join(literals)
                context_parts_enum.append(f"Literals=[{lit_str}]")
            else:
                context_parts_enum.append("Literals=[] (元数据中未找到字面量)")

            enum_context_comment_content = '; '.join(context_parts_enum)  # 虽然目前只有Literals，但保持结构一致性
            context_comment = f"<!-- LLM_CONTEXT FOR ENUM {enum_name}: {enum_context_comment_content} -->"

            print(f"DEBUG: inject_local_context: 为 ENUM '{enum_name}' 生成的上下文: {context_comment}")
            processed_lines.append(context_comment)
            print(f"DEBUG: inject_local_context: 已追加 ENUM 上下文到第 {current_line_number} 行之后。")
        # else: # 可选：为 ENUM 添加类似的未匹配诊断
        # if line.strip().startswith("#@ENUM"):
        #     print(f"DEBUG: inject_local_context: 第 {current_line_number} 行 - ENUM_ANNOTATION_PATTERN 未能匹配。")

    enhanced_content = "\n".join(processed_lines)
    print(f"DEBUG: inject_local_context: 局部上下文注入完成。增强后内容的长度: {len(enhanced_content)}")
    return enhanced_content


def process_document_for_llm(markdown_content, metadata):
    print("DEBUG: 调用 process_document_for_llm...")
    enhanced_content = inject_local_context(markdown_content, metadata)
    return enhanced_content