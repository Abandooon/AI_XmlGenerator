import re
from .config import (
    CLASS_ANNOTATION_PATTERN, ENUM_ANNOTATION_PATTERN, SECTION_ANNOTATION_PATTERN
)


def get_class_attributes(metadata, class_name):
    """
    从 unified_metadata.json 中为给定的 class_name 提取属性。
    会检查 'groups', 'complexTypes', 和 'extract_inner_class'。
    """
    attributes = set()  # 使用集合来自动处理重复项

    # 1. 检查 'groups'
    if class_name in metadata.get("groups", {}):
        group_data = metadata["groups"][class_name]
        elements = group_data.get("elements", [])
        for el in elements:
            if el.get("name"):
                attributes.add(el["name"])

    # 2. 检查 'complexTypes'
    # complexTypes 中的 'attributes' 列表似乎更像是直接的属性定义
    if class_name in metadata.get("complexTypes", {}):
        complex_type_data = metadata["complexTypes"][class_name]
        # 'attributes' 列表
        complex_attributes = complex_type_data.get("attributes", [])
        for attr in complex_attributes:
            if attr.get("name"):
                attributes.add(attr["name"])
        # 'elements' 列表 (如果 complexTypes 也用 elements 存储子组件/属性)
        complex_elements = complex_type_data.get("elements", [])
        for el in complex_elements:
            if el.get("name"):
                attributes.add(el["name"])

    # 3. 检查 'extract_inner_class'
    if class_name in metadata.get("extract_inner_class", {}):
        inner_class_data = metadata["extract_inner_class"][class_name]
        inner_attributes = inner_class_data.get("attributes", [])
        for attr in inner_attributes:
            if attr.get("name"):
                attributes.add(attr["name"])

    # 4. (可选) 检查 'attributeGroups'
    # 如果类引用了 attributeGroups，并且我们想把这些组内的属性也视为类的直接属性
    # 这会增加复杂性，因为需要解析 attributeGroups 的引用并递归查找
    # 例如，如果 metadata["groups"][class_name]["attributeGroups"] = ["ARObject"]
    # 则需要去 metadata["attributeGroups"]["ARObject"] 中提取属性。
    # 为简化起见，当前版本不递归解析 attributeGroups，但可以作为扩展点。

    if not attributes:
        print(f"警告: 未能为类 '{class_name}' 从元数据中找到任何属性。")

    return sorted(list(attributes))


def get_enum_literals(metadata, enum_name):
        """
        从 unified_metadata.json 中为给定的 enum_name 提取字面量。
        会检查 'simpleTypes' 和 'complexTypes'。
        """
        def to_camel_case(s):
            parts = s.lower().split('-')
            return parts[0] + ''.join(word.capitalize() for word in parts[1:]) if len(parts) > 1 else s

        literals = set()  # 使用集合自动去重

        # 1. 检查 'simpleTypes' (这是最常见的枚举定义位置)
        if enum_name in metadata.get("simpleTypes", {}):
            simple_type_data = metadata["simpleTypes"][enum_name]
            # 'enumerations' 键通常直接包含字面量列表
            if "enumerations" in simple_type_data and isinstance(simple_type_data["enumerations"], list):
                for literal in simple_type_data["enumerations"]:
                    if isinstance(literal, str):  # 直接是字符串列表
                        literals.add(literal)
                        camel_literal = to_camel_case(literal)
                        if camel_literal != literal:
                            literals.add(camel_literal)

        # 2. 检查 'complexTypes' (有些 XSD 结构可能在 complexType 中定义枚举)
        if enum_name in metadata.get("complexTypes", {}):
            complex_type_data = metadata["complexTypes"][enum_name]
            # 检查是否存在 'enumeration' 键，这在 XSD 转 JSON 中常见
            if "enumeration" in complex_type_data and isinstance(complex_type_data["enumeration"], list):
                for item in complex_type_data["enumeration"]:
                    if isinstance(item, str):
                        literals.add(item)
                        camel_item = to_camel_case(item)
                        if camel_item != item:
                            literals.add(camel_item)
                    elif isinstance(item, dict) and "value" in item:  # 例如 <xs:enumeration value="LITERAL_A"/>
                        value = item["value"]
                        literals.add(value)
                        camel_value = to_camel_case(value)
                        if camel_value != value:
                            literals.add(camel_value)
            # 根据 'attributes' 中元素的 type 查找对应的 simpleTypes 中的枚举值
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

        # 3. (可选) 检查 'groups' 或 'extract_inner_class' 中的 'elements'/'attributes' 的 'type' 是否指向一个枚举
        # 并且该 'type' 的定义在别处。这需要更复杂的类型解析，当前版本不处理。
        # 例如，如果一个 element 的 "type" 是 "MyEnumType"，则需要再去查找 "MyEnumType" 的定义。

        if not literals:
            print(f"警告: 未能为枚举 '{enum_name}' 从元数据中找到任何字面量。")

        return sorted(list(literals))


def inject_context_into_document(markdown_content, metadata):
    """
    将上下文注入到 Markdown 文档中。
    对于 V4 版本，此函数会在文档开头创建一个包含文档中找到的所有类和枚举的大型上下文块。
    """

    all_classes = set(re.findall(CLASS_ANNOTATION_PATTERN, markdown_content))
    all_enums = set(re.findall(ENUM_ANNOTATION_PATTERN, markdown_content))

    context_lines = ["--- CONTEXT START ---"]

    first_section_match = re.search(SECTION_ANNOTATION_PATTERN, markdown_content)
    if first_section_match:
        context_lines.append(f"Document Section Context: {first_section_match.group(1).strip()}")

    if all_classes:
        context_lines.append("Referenced Classes:")
        for class_name in sorted(list(all_classes)):
            attributes = get_class_attributes(metadata, class_name)  # 使用重构后的函数
            if attributes:
                context_lines.append(f"  - {class_name}: Attributes [{', '.join(attributes)}]")
            else:
                # 即使没有属性，也列出类名，LLM 可能需要处理类级别的约束
                context_lines.append(f"  - {class_name}: Attributes [] (元数据中未找到属性或该类无直接定义的属性)")

    if all_enums:
        context_lines.append("Referenced Enums:")
        for enum_name in sorted(list(all_enums)):
            literals = get_enum_literals(metadata, enum_name)  # 使用重构后的函数
            if literals:
                context_lines.append(f"  - {enum_name}: Literals [{', '.join(literals)}]")
            else:
                context_lines.append(f"  - {enum_name}: Literals [] (元数据中未找到字面量)")

    context_lines.append("--- CONTEXT END ---")
    context_block = "\n".join(context_lines) + "\n\n"

    return context_block + markdown_content


def process_document_for_llm(markdown_content, metadata):
    """
    上下文注入阶段的主函数。
    """
    print("开始上下文注入...")
    enhanced_content = inject_context_into_document(markdown_content, metadata)
    print("上下文注入完成。")
    return enhanced_content