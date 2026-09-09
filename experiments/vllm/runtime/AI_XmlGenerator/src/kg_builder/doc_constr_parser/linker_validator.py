from config import CLASS_LEVEL_ATTR, ENUM_LEVEL_ATTR, UNIFIED_METADATA_FILENAME
from context_injector import get_class_info, get_enum_literals


def generate_target_refs_for_item(item):
    """根据 item['targets'] 列表生成 targetRef 列表。"""
    target_refs = []
    if not item.get("targets"):
        return []

    for target_entry in item["targets"]:
        entity_name = target_entry.get("targetEntityName")
        entity_type = target_entry.get("entityType")
        attributes_or_literals = target_entry.get("targetAttributes", [])

        if not entity_name or not attributes_or_literals:
            continue

        # 对于 abstract 类型且 entityName 为 _abstractLevel 的特殊处理
        if entity_type == "abstract" and entity_name == "_abstractLevel":
            if "_abstractLevel" in attributes_or_literals:  # 通常 attributes 应该是 ["_abstractLevel"]
                target_refs.append(f"{entity_name}._abstractLevel")  # 或者 entity_name 本身就代表了目标
            # 可以根据需要决定这里的 targetRef 格式，例如仅 entity_name
            # 或者如果 attributes_or_literals 总是 ["_abstractLevel"]，可以直接添加
            # target_refs.append(entity_name) # 作为一个选项
            continue  # 处理完毕，进行下一次循环

        default_attr = CLASS_LEVEL_ATTR if entity_type == "class" else ENUM_LEVEL_ATTR

        for attr_or_lit in attributes_or_literals:
            if attr_or_lit == CLASS_LEVEL_ATTR or attr_or_lit == ENUM_LEVEL_ATTR:
                # 确保 entity_name 不是 _abstractLevel，因为上面已经处理了
                if entity_name != "_abstractLevel":
                    target_refs.append(f"{entity_name}.{default_attr}")
            else:
                # 确保 entity_name 不是 _abstractLevel
                if entity_name != "_abstractLevel":
                    target_refs.append(f"{entity_name}.{attr_or_lit}")

    return sorted(list(set(target_refs)))


def validate_and_link_constraints(raw_extracted_data, metadata):
    linked_constraints = []
    review_queue_items = []

    # 定义有效的 id_type 列表
    VALID_ID_TYPES = ["TPS_SWCT", "constr", "example", "additional_binding", "additional_not_binding"]
    # 定义有效的 entityType 列表
    VALID_ENTITY_TYPES = ["class", "enum", "abstract"]

    for item in raw_extracted_data:
        # 非生产性则无需链接
        if item.get("is_active") is False:
            continue
        issues = []
        # 注意：字段名改为 targetRefs (复数), 确保在 item 中创建这个键
        item['targetRefs'] = generate_target_refs_for_item(item)

        if not item.get('id') or not item.get('id_type'):
            issues.append("缺失 id 或 id_type。")
        # 问题1 修改：使用 VALID_ID_TYPES 列表进行校验
        elif item.get('id_type') not in VALID_ID_TYPES:
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

                # 问题2 修改：使用 VALID_ENTITY_TYPES 列表进行校验
                if not entity_type or entity_type not in VALID_ENTITY_TYPES:
                    issues.append(
                        f"目标实体 '{entity_name}' 缺少有效 'entityType' (应为 {VALID_ENTITY_TYPES}): {target_entry}")
                    continue

                if not attributes_or_literals:
                    issues.append(f"目标实体 '{entity_name}' 的 'targetAttributes' 列表为空。")
                    continue

                # 问题2 修改：如果 entityType 是 "abstract"，则跳过后续针对 class/enum 的元数据查找和属性校验逻辑
                # 但我们仍然需要校验 targetEntityName 是否为 "_abstractLevel" (如果这是设计意图)
                # 以及 targetAttributes 是否为 ["_abstractLevel"]
                if entity_type == "abstract":
                    if entity_name != "_abstractLevel":
                        # 如果 entityType 是 abstract，但 entityName 不是 "_abstractLevel"，
                        # 这可能表示一个用户定义的概念名称，此时不应在元数据中查找它，
                        # 除非您的元数据中也存储了这些抽象概念的名称。
                        # 目前假设这种情况是允许的，并且不进行元数据查找。
                        # issues.append(f"抽象目标实体 '{entity_name}' 的名称不是预期的 '_abstractLevel'。")
                        pass  # 允许描述性的抽象实体名称

                    # 校验 abstract 类型的 targetAttributes 是否符合预期（通常是 ["_abstractLevel"]）
                    if not (len(attributes_or_literals) == 1 and attributes_or_literals[0] == "_abstractLevel"):
                        issues.append(
                            f"抽象目标实体 '{entity_name}' 的 targetAttributes 应为 ['_abstractLevel']，但得到: {attributes_or_literals}")
                    # 对于 abstract 类型，我们通常不在这里做进一步的属性存在性校验
                    continue  # 跳过对 class 和 enum 的具体校验逻辑

                if entity_type == "class":
                    class_exists_in_groups = entity_name in metadata.get("groups", {})
                    class_exists_in_complex = entity_name in metadata.get("complexTypes", {})
                    class_exists_in_inner = entity_name in metadata.get("extract_inner_class", {})

                    if not (class_exists_in_groups or class_exists_in_complex or class_exists_in_inner):
                        issues.append(f"目标类 '{entity_name}' 在元数据中未找到。")
                    else:
                        class_info_from_meta = get_class_info(metadata, entity_name)
                        class_attrs_from_meta = class_info_from_meta["attributes"]

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
                        enum_literals_from_meta = get_enum_literals(metadata, entity_name)
                        for literal in attributes_or_literals:
                            if literal != ENUM_LEVEL_ATTR and literal not in enum_literals_from_meta:
                                issues.append(
                                    f"字面量 '{literal}' 在元数据枚举 '{entity_name}' 的已知字面量列表中未找到。 (LLM 违规)")

        if 'confidence' not in item or item['confidence'] is None:
            item['confidence'] = 0.9

        if issues:
            item['review_issues'] = issues
            review_queue_items.append(item)
        else:
            linked_constraints.append(item)

    print(f"验证完成。已链接约束: {len(linked_constraints)}, 待审查约束: {len(review_queue_items)}")
    return linked_constraints, review_queue_items