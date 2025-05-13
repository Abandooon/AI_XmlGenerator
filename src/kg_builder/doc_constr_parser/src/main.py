import argparse
import os
import pandas as pd

from .config import (
    UNIFIED_METADATA_FILENAME, OUTPUT_LINKED_CONSTRAINTS_FILENAME,
    OUTPUT_REVIEW_QUEUE_FILENAME
)
from .utils import load_markdown, load_json, save_json, save_dataframe_to_csv, save_jsonl
from .context_injector import process_document_for_llm
from .llm_extractor import extract_constraints_from_text
from .linker_validator import validate_and_link_constraints


def main():
    parser = argparse.ArgumentParser(description="AUTOSAR 约束提取流程 (V4)")
    parser.add_argument("input_dir", help="包含输入 MD 文件和 unified_metadata.json 的目录")
    parser.add_argument("test_chapter3.md", help="输入 Markdown 文件的名称")
    parser.add_argument("output_dir", help="保存输出文件的目录")
    args = parser.parse_args()

    # 构建完整路径
    md_filepath = os.path.join(args.input_dir, args.md_filename)
    metadata_filepath = os.path.join(args.input_dir, UNIFIED_METADATA_FILENAME)

    output_linked_filepath = os.path.join(args.output_dir, OUTPUT_LINKED_CONSTRAINTS_FILENAME)
    output_review_filepath = os.path.join(args.output_dir, OUTPUT_REVIEW_QUEUE_FILENAME)
    output_raw_llm_filepath = os.path.join(args.output_dir, "constraints_raw_v4.jsonl")  # 保存原始LLM输出

    # --- 1. 加载数据 ---
    print("--- 阶段 1: 加载数据 ---")
    markdown_content = load_markdown(md_filepath)
    unified_metadata = load_json(metadata_filepath)

    if not markdown_content or not unified_metadata:
        print("未能加载初始数据。正在退出。")
        return

    # --- 2. 上下文注入 ---
    print("\n--- 阶段 2: 上下文注入 ---")
    enhanced_markdown = process_document_for_llm(markdown_content, unified_metadata)
    # 用于调试，您可能希望保存增强后的 markdown
    # with open(os.path.join(args.output_dir, "enhanced_document.md"), "w", encoding="utf-8") as f:
    #     f.write(enhanced_markdown)

    # --- 3. LLM 提取 ---
    print("\n--- 阶段 3: LLM 提取 ---")
    raw_extracted_data = extract_constraints_from_text(enhanced_markdown)  # 返回字典列表
    if not raw_extracted_data:
        print("LLM 未提取到数据。正在退出。")
        # 可选：保存空文件或作为错误处理
        save_json([], output_linked_filepath)  # 保存为JSON数组
        save_dataframe_to_csv(pd.DataFrame(), output_review_filepath)
        save_jsonl([], output_raw_llm_filepath)  # 保存为空的JSONL
        return

    # 保存原始 LLM 输出以供调试 (JSONL格式)
    save_jsonl(raw_extracted_data, output_raw_llm_filepath)

    # --- 4. 链接与验证 ---
    print("\n--- 阶段 4: 链接与验证 ---")
    linked_constraints, review_queue_items = validate_and_link_constraints(raw_extracted_data, unified_metadata)

    # --- 5. 保存输出 ---
    print("\n--- 阶段 5: 保存输出 ---")
    save_json(linked_constraints, output_linked_filepath)  # 保存为JSON数组

    if review_queue_items:
        review_df = pd.DataFrame(review_queue_items)
        save_dataframe_to_csv(review_df, output_review_filepath)
    else:
        print("审查队列为空。")
        # 如果需要，可以创建一个空的 CSV 文件
        save_dataframe_to_csv(pd.DataFrame(), output_review_filepath)

    print("\n流程成功完成！")


if __name__ == "__main__":
    main()