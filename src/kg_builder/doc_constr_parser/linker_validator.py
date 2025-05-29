import pandas as pd
from config import CLASS_LEVEL_ATTR, ENUM_LEVEL_ATTR, UNIFIED_METADATA_FILENAME  # 假设元数据文件名在这里
from context_injector import get_class_info, get_enum_literals  # 重用以进行验证


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
        elif item.get('id_type') not in ["TPS_SWCT", "constr"]:  # 假设 "example" 类型如果添加了也应在此处包含
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
                    # class_exists_in_inner = entity_name in metadata.get("extract_inner_class", {}) # 如果也考虑这里作为类的定义源

                    if not (class_exists_in_groups or class_exists_in_complex):  # or class_exists_in_inner
                        issues.append(f"目标类 '{entity_name}' 在元数据中未找到。")
                    else:
                        # 验证属性
                        class_info_from_meta = get_class_info(metadata, entity_name)
                        class_attrs_from_meta = class_info_from_meta["attributes"]
                        # class_generalization = class_info_from_meta["generalization"] # 可选获取，当前未用于校验
                        # class_childs = class_info_from_meta["childs"]               # 可选获取，当前未用于校验

                        for attr in attributes_or_literals:
                            if attr != CLASS_LEVEL_ATTR and attr not in class_attrs_from_meta:
                                issues.append(
                                    f"属性 '{attr}' 在元数据类 '{entity_name}' 的已知属性列表中未找到。 (LLM 违规)")

                elif entity_type == "enum":
                    enum_exists_in_simple = entity_name in metadata.get("simpleTypes", {})
                    enum_exists_in_complex = entity_name in metadata.get("complexTypes", {})

                    if not (enum_exists_in_simple or enum_exists_in_complex):
                        issues.append(f"目标枚举 '{entity_name}' 在元数据中未找到。")
                    else:
                        # 验证字面量
                        enum_literals_from_meta = get_enum_literals(metadata, entity_name)
                        for literal in attributes_or_literals:
                            if literal != ENUM_LEVEL_ATTR and literal not in enum_literals_from_meta:
                                issues.append(
                                    f"字面量 '{literal}' 在元数据枚举 '{entity_name}' 的已知字面量列表中未找到。 (LLM 违规)")
                # else: # 如果未来有其他 entityType
                #     issues.append(f"未知的 entityType: {entity_type} for entity {entity_name}")

        # parent_id 验证逻辑已移除 (根据您之前的代码状态，如果需要可以加回来)
        # if item.get("scope", {}).get("parent_id"):
        #     parent_id = item["scope"]["parent_id"]
        #     # 这里需要一个方法来检查 parent_id 是否在 raw_extracted_data 或已知的ID库中
        #     # if not check_if_parent_id_exists(parent_id, raw_extracted_data, linked_constraints):
        #     #     issues.append(f"层级父ID '{parent_id}' 未找到。")

        if 'confidence' not in item or item['confidence'] is None:  # 检查 None
            item['confidence'] = 0.9  # 为缺失或None的confidence设置默认值

        if issues:
            item['review_issues'] = issues
            review_queue_items.append(item)
            # 可以在这里打印有问题的条目以供调试
            # print(f"DEBUG: Item ID '{item.get('id', 'N/A')}' 加入审查队列，原因: {issues}")
        else:
            linked_constraints.append(item)

    print(f"验证完成。已链接约束: {len(linked_constraints)}, 待审查约束: {len(review_queue_items)}")
    return linked_constraints, review_queue_items