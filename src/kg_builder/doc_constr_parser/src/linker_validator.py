import pandas as pd
from .config import CLASS_LEVEL_ATTR, ENUM_LEVEL_ATTR
from .context_injector import get_class_attributes, get_enum_literals  # 重用以进行验证


def generate_target_ref(item):
    """根据 targetClass/Enum 和 targetAttribute 生成 targetRef。"""
    target_class = item.get("targetClass")
    target_enum = item.get("targetEnum")
    # targetAttribute 字段现在存储属性名、字面量名，或者 _classLevel/_enumLevel
    target_attribute_val = item.get("targetAttribute")

    if target_class:
        if not target_attribute_val or target_attribute_val == CLASS_LEVEL_ATTR:
            return f"{target_class}.{CLASS_LEVEL_ATTR}"
        return f"{target_class}.{target_attribute_val}"
    elif target_enum:
        if not target_attribute_val or target_attribute_val == ENUM_LEVEL_ATTR:
            return f"{target_enum}.{ENUM_LEVEL_ATTR}"
        return f"{target_enum}.{target_attribute_val}"  # 字面量名称存储在 targetAttribute 中
    return None


def validate_and_link_constraints(raw_extracted_data, metadata):
    linked_constraints = []
    review_queue_items = []
    all_ids_extracted = {item.get('id') for item in raw_extracted_data if item.get('id')}

    for item in raw_extracted_data:
        issues = []
        item['targetRef'] = generate_target_ref(item)  # 首先生成 targetRef

        # 验证 ID 和 ID 类型 (基本检查，LLM 应该已处理)
        if not item.get('id') or not item.get('id_type'):
            issues.append("缺失 id 或 id_type。")
        elif item.get('id_type') not in ["TPS_SWCT", "constr"]:
            issues.append(f"无效的 id_type: {item.get('id_type')}。")

        # 验证 targetClass/targetEnum 的存在性
        target_class = item.get("targetClass")
        target_enum = item.get("targetEnum")
        target_attribute = item.get("targetAttribute")  # 包含属性、字面量、_classLevel 或 _enumLevel

        if target_class:
            # 检查类是否存在于元数据的 'groups' 或 'complexTypes' 中
            class_exists_in_groups = target_class in metadata.get("groups", {})
            class_exists_in_complex = target_class in metadata.get("complexTypes", {})
            # 您可能还需要检查 'extract_inner_class'
            # class_exists_in_inner = target_class in metadata.get("extract_inner_class", {})

            if not (class_exists_in_groups or class_exists_in_complex):  # or class_exists_in_inner
                issues.append(f"目标类 '{target_class}' 在元数据中未找到。")
            elif target_attribute and target_attribute != CLASS_LEVEL_ATTR:
                class_attrs = get_class_attributes(metadata, target_class)  # 从元数据获取该类的属性
                if target_attribute not in class_attrs:
                    issues.append(
                        f"属性 '{target_attribute}' 在元数据上下文中未找到对应的类 '{target_class}'。 (LLM 违规)")

        elif target_enum:
            # 检查枚举是否存在于元数据的 'simpleTypes' 或 'complexTypes' 中
            enum_exists_in_simple = target_enum in metadata.get("simpleTypes", {})
            enum_exists_in_complex = target_enum in metadata.get("complexTypes", {})

            if not (enum_exists_in_simple or enum_exists_in_complex):
                issues.append(f"目标枚举 '{target_enum}' 在元数据中未找到。")
            elif target_attribute and target_attribute != ENUM_LEVEL_ATTR:
                enum_literals = get_enum_literals(metadata, target_enum)  # 从元数据获取该枚举的字面量
                if target_attribute not in enum_literals:
                    issues.append(
                        f"字面量 '{target_attribute}' 在元数据上下文中未找到对应的枚举 '{target_enum}'。 (LLM 违规)")

        elif not item.get('targetRef'):  # 如果没有目标类/枚举，targetRef 将为 None
            issues.append("约束缺少 targetClass 或 targetEnum。")

        # 验证 parent_id 的存在性 (如果适用)
        # parent_id 现在是顶层字段
        parent_id = item.get("parent_id")
        if parent_id and parent_id not in all_ids_extracted:
            issues.append(f"父 ID '{parent_id}' 在已提取的约束中未找到。")

        # 置信度 (假设 LLM 提供，或设置默认值)
        if 'confidence' not in item:  # LLM 可能不直接输出 confidence
            item['confidence'] = 0.9  # 如果 LLM 未提供，则设置默认置信度

        if issues:
            item['review_issues'] = issues
            review_queue_items.append(item)
        else:
            linked_constraints.append(item)

    print(f"验证完成。已链接: {len(linked_constraints)}, 审查队列: {len(review_queue_items)}")
    return linked_constraints, review_queue_items