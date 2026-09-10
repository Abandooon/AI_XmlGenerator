import os

import pandas as pd

# 更新config导入，确保新的常量和Schema被使用
from config import (
    UNIFIED_METADATA_FILENAME,
    OUTPUT_LINKED_CONSTRAINTS_FILENAME,
    OUTPUT_REVIEW_QUEUE_FILENAME,
    OUTPUT_RAW_LLM_FILENAME,
    INPUT_DIR,
    OUTPUT_DIR,
    MD_FILENAME,
    RE_EXTRACT_CHUNKS
)
from context_injector import process_document_for_llm
from linker_validator import validate_and_link_constraints
from llm_extractor import (
    get_text_chunks,
    extract_constraints_from_block,
    remove_duplicates
)
from utils import (
    load_markdown,
    load_json,
    save_json,
    save_dataframe_to_csv,
    save_jsonl,
    load_jsonl
)


def main():
    # --- 1. 数据加载 ---
    markdown_filepath = os.path.join(INPUT_DIR, MD_FILENAME)
    metadata_filepath = os.path.join(INPUT_DIR, UNIFIED_METADATA_FILENAME)
    markdown_content = load_markdown(markdown_filepath)
    unified_metadata = load_json(metadata_filepath)
    if not markdown_content or not unified_metadata:
        print("未能加载初始数据。正在退出。")
        return

    # --- 2. 上下文注入 ---
    print("\n--- 阶段 2: 上下文注入 (局部上下文) ---")
    enhanced_markdown = process_document_for_llm(markdown_content, unified_metadata)
    enhanced_output_path = os.path.join(OUTPUT_DIR, "enhanced_" + MD_FILENAME)
    with open(enhanced_output_path, 'w', encoding='utf-8') as f:
        f.write(enhanced_markdown)
    print(f"增强文档已保存至: {enhanced_output_path}")

    # --- 3. 增量重跑指定块 ---
    print("\n--- 阶段 3: 增量重跑指定块 ---")
    raw_path = os.path.join(OUTPUT_DIR, OUTPUT_RAW_LLM_FILENAME)
    # 3.1 加载上一轮 raw 文件
    if os.path.exists(raw_path):
        old_raw = load_jsonl(raw_path)
    else:
        old_raw = []

    # 3.2 获取所有块文本
    chunks = get_text_chunks(enhanced_markdown)

    # 3.3 准备重跑块列表（空列表时重跑所有）
    rerun_chunks = RE_EXTRACT_CHUNKS if RE_EXTRACT_CHUNKS else list(range(1, len(chunks) + 1))

    # 3.4 对指定块重跑提取
    rerun_items = []
    for idx in rerun_chunks:
        if 1 <= idx <= len(chunks):
            print(f"第 {idx} 块提取...")
            rerun_items.extend(
                extract_constraints_from_block(chunks[idx - 1])
            )
        else:
            print(f"警告: 块索引 {idx} 越界 (有效范围: 1-{len(chunks)})")

    # 3.5 合并旧数据与重跑结果并去重
    merged = old_raw + rerun_items
    merged = remove_duplicates(merged)

    # 3.6 保存增量后的原始LLM输出
    save_jsonl(merged, raw_path)
    print(f"增量 raw 输出已保存至: {raw_path}")
    raw_extracted_data = merged

    # --- 4. 链接与校验 ---
    print("\n--- 阶段 4: 链接与校验 ---")
    linked_constraints, review_queue_items = validate_and_link_constraints(
        raw_extracted_data,
        unified_metadata
    )

    # --- 5. 保存最终输出 ---
    print("\n--- 阶段 5: 保存输出 ---")
    save_json(
        linked_constraints,
        os.path.join(OUTPUT_DIR, OUTPUT_LINKED_CONSTRAINTS_FILENAME)
    )
    if review_queue_items:
        df = pd.DataFrame(review_queue_items)
        save_dataframe_to_csv(
            df,
            os.path.join(OUTPUT_DIR, OUTPUT_REVIEW_QUEUE_FILENAME)
        )
    else:
        print("审查队列为空。")
        save_dataframe_to_csv(
            pd.DataFrame(),
            os.path.join(OUTPUT_DIR, OUTPUT_REVIEW_QUEUE_FILENAME)
        )

    print("\n流程成功完成！")


if __name__ == "__main__":
    main()
