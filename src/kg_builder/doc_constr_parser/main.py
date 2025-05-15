import argparse
import os
import pandas as pd

# 更新config导入，确保新的常量和Schema被使用
from config import (
    UNIFIED_METADATA_FILENAME,
    OUTPUT_LINKED_CONSTRAINTS_FILENAME, # 使用新的文件名
    OUTPUT_REVIEW_QUEUE_FILENAME,       # 使用新的文件名
    OUTPUT_RAW_LLM_FILENAME,            # 使用新的文件名
    INPUT_DIR, OUTPUT_DIR, MD_FILENAME
)
from utils import load_markdown, load_json, save_json, save_dataframe_to_csv, save_jsonl
from context_injector import process_document_for_llm
from llm_extractor import extract_constraints_from_text # 使用更新后的提取器
from linker_validator import validate_and_link_constraints # 使用更新后的验证器


def main():
    # 构建完整路径
    md_filepath = os.path.join(INPUT_DIR, MD_FILENAME)
    metadata_filepath = os.path.join(INPUT_DIR, UNIFIED_METADATA_FILENAME)

    output_linked_filepath = os.path.join(OUTPUT_DIR, OUTPUT_LINKED_CONSTRAINTS_FILENAME)
    output_review_filepath = os.path.join(OUTPUT_DIR, OUTPUT_REVIEW_QUEUE_FILENAME)
    output_raw_llm_filepath = os.path.join(OUTPUT_DIR, OUTPUT_RAW_LLM_FILENAME) # 使用config中的常量

    # --- 1. 加载数据 ---
    print("--- 阶段 1: 加载数据 ---")
    markdown_content = load_markdown(md_filepath)
    unified_metadata = load_json(metadata_filepath)

    if not markdown_content or not unified_metadata:
        print("未能加载初始数据。正在退出。")
        return

    # --- 2. 上下文注入 ---
    print("\n--- 阶段 2: 上下文注入 (局部上下文) ---")
    # enhanced_markdown 已经包含了 <!-- LLM_CONTEXT FOR CLASS/ENUM ... -->
    enhanced_markdown = process_document_for_llm(markdown_content, unified_metadata)

    enhanced_output_path = os.path.join(OUTPUT_DIR, "enhanced_" + MD_FILENAME)
    with open(enhanced_output_path, 'w', encoding='utf-8') as f:
        f.write(enhanced_markdown)
    print(f"增强文档已保存至: {enhanced_output_path}")


    # --- 3. LLM 提取 ---
    print("\n--- 阶段 3: LLM 提取 (支持多目标和新分块策略) ---")
    # extract_constraints_from_text 内部会处理分块和父章节上下文注入
    raw_extracted_data = extract_constraints_from_text(enhanced_markdown)
    if not raw_extracted_data:
        print("LLM 未提取到数据。正在退出。")
        save_json([], output_linked_filepath)
        save_dataframe_to_csv(pd.DataFrame(), output_review_filepath)
        save_jsonl([], output_raw_llm_filepath)
        return

    save_jsonl(raw_extracted_data, output_raw_llm_filepath)
    print(f"原始LLM输出已保存至: {output_raw_llm_filepath}")

    # --- 4. 链接与验证 ---
    print("\n--- 阶段 4: 链接与验证 (支持多目标) ---")
    linked_constraints, review_queue_items = validate_and_link_constraints(raw_extracted_data, unified_metadata)

    # --- 5. 保存输出 ---
    print("\n--- 阶段 5: 保存输出 ---")
    save_json(linked_constraints, output_linked_filepath)

    if review_queue_items: # 检查列表是否为空，而不是DataFrame是否为空
        review_df = pd.DataFrame(review_queue_items)
        save_dataframe_to_csv(review_df, output_review_filepath)
    else:
        print("审查队列为空。")
        save_dataframe_to_csv(pd.DataFrame(), output_review_filepath) # 创建空的CSV

    print("\n流程成功完成！")


if __name__ == "__main__":
    main()