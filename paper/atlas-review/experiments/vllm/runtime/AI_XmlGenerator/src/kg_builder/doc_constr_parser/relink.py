import os

import pandas as pd

from config import (
    INPUT_DIR,
    OUTPUT_DIR,
    UNIFIED_METADATA_FILENAME,
    OUTPUT_RAW_LLM_FILENAME,
    OUTPUT_LINKED_CONSTRAINTS_FILENAME,
    OUTPUT_REVIEW_QUEUE_FILENAME
)
from linker_validator import validate_and_link_constraints
from utils import (
    load_json,
    load_jsonl,
    save_json,
    save_dataframe_to_csv
)


def main():
    # 1. 加载元数据
    metadata_path = os.path.join(INPUT_DIR, UNIFIED_METADATA_FILENAME)
    unified_metadata = load_json(metadata_path)
    if not unified_metadata:
        print("未能加载元数据，退出。")
        return

    # 2. 读取原始约束和已链接约束
    raw_path = os.path.join(OUTPUT_DIR, OUTPUT_RAW_LLM_FILENAME)
    raw_constraints = load_jsonl(raw_path)
    linked_path = os.path.join(OUTPUT_DIR, OUTPUT_LINKED_CONSTRAINTS_FILENAME)
    existing_linked = load_json(linked_path)

    # 建立已链接字典，方便更新
    linked_map = {c['id']: c for c in existing_linked}

    # 3. 读取待审查队列，获取待重跑链接的ID
    review_path = os.path.join(OUTPUT_DIR, OUTPUT_REVIEW_QUEUE_FILENAME)
    df_review = pd.read_csv(review_path)
    relink_ids = df_review['id'].tolist()
    if not relink_ids:
        print("无待审查约束，无需重跑链接。")
        return

    # 4. 筛选需要重跑链接的原始约束
    raw_for_relink = [c for c in raw_constraints if c['id'] in relink_ids]
    if not raw_for_relink:
        print("未在 raw 文件中找到对应的待重跑约束。")
        return

    # 5. 执行链接校验
    new_linked, new_review = validate_and_link_constraints(
        raw_for_relink,
        unified_metadata
    )

    # 6. 合并新链接结果
    for item in new_linked:
        linked_map[item['id']] = item
    updated_linked = list(linked_map.values())
    save_json(updated_linked, linked_path)
    print(f"已更新链接文件: {linked_path}")

    # 7. 更新审查队列：移除已重跑项，追加新产生的 review
    df_remaining = df_review[~df_review['id'].isin(relink_ids)]
    df_new = pd.DataFrame(new_review)
    df_updated = pd.concat([df_remaining, df_new], ignore_index=True)
    save_dataframe_to_csv(df_updated, review_path)
    print(f"已更新审查队列: {review_path}")

    print("增量链接脚本执行完成。")


if __name__ == '__main__':
    main()
