import pandas as pd
from config import CLASS_LEVEL_ATTR, ENUM_LEVEL_ATTR, UNIFIED_METADATA_FILENAME  # 假设元数据文件名在这里
from context_injector import get_class_attributes, get_enum_literals  # 重用以进行验证


def generate_target_refs_for_item(item):
    """根据 item['targets'] 列表生成 targetRef 列表。"""
    target_refs = []
    if not item.get("targets"):
        return []

    for target_entry in item["targets"]:
        entity_name = target_entry.get("targetEntityName")
        entity_type = target_entry.get("entityType")  # "class" or "enum"
        attributes_or_literals = target_entry.get("targetAttributes", [])

        if not entity_name or not attributes_or_literals:
            continue

        default_attr = CLASS_LEVEL_ATTR if entity_type == "class" else ENUM_LEVEL_ATTR

        for attr_or_lit in attributes_or_literals:
            if attr_or_lit == CLASS_LEVEL_ATTR or attr_or_lit == ENUM_LEVEL_ATTR:
                target_refs.append(f"{entity_name}.{default_attr}")
            else:
                target_refs.append(f"{entity_name}.{attr_or_lit}")

    return sorted(list(set(target_refs)))  # 去重并排序


def validate_and_link_constraints(raw_extracted_data, metadata):
    linked_constraints = []
    review_queue_items = []

    for item in raw_extracted_data:
        issues = []
        item['targetRefs'] = generate_target_refs_for_item(item)  # 注意：字段名改为 targetRefs (复数)

        if not item.get('id') or not item.get('id_type'):
            issues.append("缺失 id 或 id_type。")
        elif item.get('id_type') not in ["TPS_SWCT", "constr"]:
            issues.append(f"无效的 id_type: {item.get('id_type')}。")

        targets_data = item.get("targets", [])
        if not targets_data:
            issues.append("约束缺少 'targets' 字段或 'targets' 列表为空。")
        else:
            for target_entry in targets_data:
                entity_name = target_entry.get("targetEntityName")
                entity_type = target_entry.get("entityType")
                attributes_or_literals = target_entry.get("targetAttributes", [])

                if not entity_name:
                    issues.append(f"目标条目缺少 'targetEntityName': {target_entry}")
                    continue
                if not entity_type or entity_type not in ["class", "enum"]:
                    issues.append(f"目标实体 '{entity_name}' 缺少有效 'entityType': {target_entry}")
                    continue
                if not attributes_or_literals:
                    issues.append(f"目标实体 '{entity_name}' 的 'targetAttributes' 列表为空。")
                    continue

                if entity_type == "class":
                    class_exists_in_groups = entity_name in metadata.get("groups", {})
                    class_exists_in_complex = entity_name in metadata.get("complexTypes", {})
                    # class_exists_in_inner = entity_name in metadata.get("extract_inner_class", {})

                    if not (class_exists_in_groups or class_exists_in_complex):  # or class_exists_in_inner
                        issues.append(f"目标类 '{entity_name}' 在元数据中未找到。")
                    else:
                        # 验证属性
                        class_attrs_from_meta = get_class_attributes(metadata, entity_name)
                        for attr in attributes_or_literals:
                            if attr != CLASS_LEVEL_ATTR and attr not in class_attrs_from_meta:
                                issues.append(
                                    f"属性 '{attr}' 在元数据上下文中未找到对应的类 '{entity_name}'。 (LLM 违规)")

                elif entity_type == "enum":
                    enum_exists_in_simple = entity_name in metadata.get("simpleTypes", {})
                    enum_exists_in_complex = entity_name in metadata.get("complexTypes", {})  # 有些枚举可能定义在complexType下

                    if not (enum_exists_in_simple or enum_exists_in_complex):
                        issues.append(f"目标枚举 '{entity_name}' 在元数据中未找到。")
                    else:
                        # 验证字面量
                        enum_literals_from_meta = get_enum_literals(metadata, entity_name)
                        for literal in attributes_or_literals:
                            if literal != ENUM_LEVEL_ATTR and literal not in enum_literals_from_meta:
                                issues.append(
                                    f"字面量 '{literal}' 在元数据上下文中未找到对应的枚举 '{entity_name}'。 (LLM 违规)")

        # parent_id validation removed as per previous code state

        if 'confidence' not in item:  # LLM 可能不会输出confidence，可以后续评估或默认
            item['confidence'] = 0.9  # 默认值

        if issues:
            item['review_issues'] = issues
            review_queue_items.append(item)
        else:
            linked_constraints.append(item)

    print(f"验证完成。已链接: {len(linked_constraints)}, 审查队列: {len(review_queue_items)}")
    return linked_constraints, review_queue_items