import os
import json
import re
from openai import OpenAI  # Works for DeepSeek if base_url and api_key are set

# Import configurations from config.py
try:
    import config
except ImportError:
    print("错误：无法导入 config.py。请确保它在正确的路径下。")
    exit(1)


# --- Helper Functions ---

def load_autosar_classes_from_metadata(metadata_file_path: str) -> list[str]:
    """
    从 unified_metadata.json 加载 AUTOSAR 类名。
    遍历 "groups" 字典中的每个组对象。如果组对象的 "Package" 列表
    以 ["AUTOSAR Templates", "SWComponentTemplate"] 开头，
    则将其 "name" 属性（即组名/类名本身）添加到类名列表。
    """
    autosar_classes = set()
    try:
        with open(metadata_file_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        if "groups" not in metadata or not isinstance(metadata["groups"], dict):
            print(f"警告：'{metadata_file_path}' 中未找到 'groups' 字典或格式不正确。")
            return []

        # metadata["groups"] is a dictionary where keys are group names
        # and values are group objects.
        for group_key, group_object in metadata["groups"].items():  # Iterate through the dictionary
            if isinstance(group_object, dict) and \
                    "name" in group_object and \
                    "Package" in group_object and \
                    isinstance(group_object["Package"], list):

                package_path = group_object["Package"]
                # 检查 Package 是否以 ["AUTOSAR Templates", "SWComponentTemplate"] 开头
                if len(package_path) >= 2 and \
                        package_path[0] == "AUTOSAR Templates" and \
                        package_path[1] == "SWComponentTemplate":
                    # The "name" of the group_object is the class name
                    autosar_classes.add(group_object["name"])
            # else:
            #     # Optional: print a warning if a group object doesn't meet criteria
            #     print(f"信息：跳过元数据中的组 '{group_key}'，因为它缺少 'name' 或 'Package' 字段，或者 'Package' 不是列表。")

        sorted_classes = sorted(list(autosar_classes))
        print(f"从元数据中加载了 {len(sorted_classes)} 个 AUTOSAR 类名。")
        if sorted_classes:  # 打印少量类名以供抽查
            print(f"抽查类名 (最多5个): {sorted_classes[:5]}")
        return sorted_classes

    except FileNotFoundError:
        print(f"错误：元数据文件 '{metadata_file_path}' 未找到。")
        return []
    except json.JSONDecodeError:
        print(f"错误：解析元数据文件 '{metadata_file_path}' 失败。")
        return []
    except Exception as e:
        print(f"加载 AUTOSAR 类名时发生未知错误: {e}")
        return []


import json # 需要确保 json 已导入，因为它在函数中被使用

def build_llm_prompt(raw_section_content: str, autosar_classes: list[str]) -> str:
    """
    构建发送给 LLM 的详细 Prompt。
    """
    class_list_str = "[]"
    if autosar_classes:
        class_list_str = json.dumps(autosar_classes)

    prompt_template = f"""您是一位专业的AUTOSAR技术文档预处理专家。您的任务是处理以下从PDF转换而来的Markdown文本章节。请严格按照以下步骤和要求操作：

**任务1：文本规范化 (Text Normalization)**
1.  **断词重连接：** 将因为换行和连字符（"-"）而被断开的单词重新连接。例如，"communica-\\ntion" 应变为 "communication"。
2.  **段内换行符合并：** 将段落内部用于强制换行的单个换行符替换为一个空格，以确保段落文本流畅。但请保留用于分隔不同段落的双换行符。对于列表项（如以 '•', '*', '- ' 开头的行）的内部换行，请尽量保持其原有格式或使其更自然。

**任务2：冗余信息移除 (Noise Removal)**
请从文本中移除以下类型的常见PDF转换冗余信息，但请注意保留图表标题本身：
1.  **保留图片标题行：** 请保留以 "Figure X.Y:" 或类似模式开头的行，这些是重要的图表标题。
2.  **保留表格标题行：** 请保留以 "Table X.Y:" 或类似模式开头的行，这些是重要的表格标题。
3.  **与图表相关的注释性文字：** 如果这些注释明显独立于主要段落内容，但构成了对图表的有意义解释，也应予以保留。
4.  **PDF页眉和页脚：** 移除包含页码（如 "35 of 905"）、文档ID（如 "Document ID 062:"）、以及保密声明（如 "--- AUTOSAR CONFIDENTIAL ---"）的行。
5.  **表格定义和图表产生的混乱文本：** 移除那些明显不是连贯段落、从表格或图表转换而来的混乱数据。这包括：
    *   包含许多大写单词且间隔较大，看起来像表格标题的行 (例如，"Class Package Note Attribute..." )。
    *   由多个无空格连接的大写单词组成的行 (例如，"ParameterInterfaceAtpBlueprintable...")。
    *   目标是保留清晰的段落、项目符号列表以及格式如 `[ID] Title (cid:100) Details (cid:99) (References)` 的约束定义。
6.  **保留特定标记：** 请勿移除文本内容中有效的 `(cid:xx)` 标记。
7.  **保留脚注：** 如文本末尾出现的 "2On a related note,..." 这样的脚注，如果是内容的一部分，应予以保留。

**任务3：AUTOSAR 类识别与标注 (AUTOSAR Class Identification and Annotation)**
在完成上述文本规范化和冗余信息移除之后：
1.  **扫描文本：** 仔细扫描处理后的文本内容，识别所有提及的 AUTOSAR 类名。
2.  **参考类名列表：** 以下是一个已知的 AUTOSAR 类名列表，请主要参考此列表进行识别。同时，也请注意文本中其他符合帕斯卡命名法（PascalCase）或大驼峰命名法（CamelCase）且可能是 AUTOSAR 类名的词汇。
    *   已知类名列表：{class_list_str}
3.  **收集与排序：** 收集所有找到的、唯一的 AUTOSAR 类名，并按字母顺序排序。
4.  **输出格式要求：**
    *   首先，将所有识别出的唯一 AUTOSAR 类名，每一个各占一行，并以 `#@CLASS: ` 作为前缀进行输出。例如：
        #@CLASS: ClassNameA
        #@CLASS: ClassNameB
    *   如果在当前章节未找到任何 AUTOSAR 类名，则不要添加任何 `#@CLASS:` 行。
    *   在 `#@CLASS:` 标注行（如果存在）之后，紧接着输出经过任务1和任务2完全清理和重排后的章节文本内容。

**请严格按照上述任务顺序和输出格式要求处理以下提供的Markdown文本章节：**
{raw_section_content}
请仅提供处理后的结果，包含必要的 #@CLASS: 标注（如果有）和清理后的文本。
"""
    return prompt_template


def call_llm_api(client: OpenAI, model_name: str, full_prompt_for_llm: str) -> str | None:
    """
    调用 LLM API 并返回结果。
    """
    try:
        print(f"\n--- 调用 LLM API (模型: {model_name}) ---")
        # print(f"发送给 LLM 的完整内容 (前1000字符):\n{full_prompt_for_llm[:1000]}...\n") # 调试时可以取消注释

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": full_prompt_for_llm,
                }
            ],
            model=model_name,
            temperature=0.0,  # 为了结果的确定性
            # max_tokens 可以根据需要调整，但通常一个章节的内容 LLM 应该能处理
        )
        response_content = chat_completion.choices[0].message.content
        print("--- LLM API 调用成功 ---")
        return response_content
    except Exception as e:
        print(f"LLM API 调用失败: {e}")
        return None


# --- Main Script Logic ---

def main():
    print("--- 开始Markdown文档LLM预处理脚本 ---")
    # 1. 加载配置
    llm_api_key = config.LLM_API_KEY
    llm_api_base = config.LLM_API_BASE
    llm_model_name = config.LLM_MODEL_NAME

    input_dir = config.INPUT_DIR
    md_filename = ".md"
    output_dir = config.OUTPUT_DIR
    unified_metadata_filename = config.UNIFIED_METADATA_FILENAME

    if not all([llm_api_key, llm_api_base, llm_model_name]):
        print("错误：LLM_API_KEY, LLM_API_BASE, 或 LLM_MODEL_NAME 未在 .env 或配置中完全设置。脚本将退出。")
        return

    os.makedirs(output_dir, exist_ok=True)

    # 2. 从 unified_metadata.json 加载 AUTOSAR 类名
    metadata_filepath = os.path.join(input_dir, unified_metadata_filename)
    known_autosar_classes = load_autosar_classes_from_metadata(metadata_filepath)
    if not known_autosar_classes:
        print("警告：未能从元数据加载任何 AUTOSAR 类名。LLM 将仅依赖其通用知识和启发式规则进行类识别。")
        # 如果不希望在没有类列表的情况下继续，可以在此处取消注释 return
        # return

    # 3. 初始化 LLM 客户端
    try:
        client = OpenAI(
            api_key=llm_api_key,
            base_url=llm_api_base
        )
    except Exception as e:
        print(f"初始化 LLM 客户端失败: {e}")
        return

    # 4. 读取输入 Markdown 文档
    input_md_filepath = os.path.join(input_dir, md_filename)
    try:
        with open(input_md_filepath, 'r', encoding='utf-8') as f:
            original_markdown_content = f.read()
        print(f"成功读取输入Markdown文件: {input_md_filepath}")
    except FileNotFoundError:
        print(f"错误：输入Markdown文件 '{input_md_filepath}' 未找到。")
        return
    except Exception as e:
        print(f"读取输入Markdown文件时发生错误: {e}")
        return

    # 5. 使用正则表达式分割文档成章节
    parts = re.split(config.SECTION_SPLIT_PATTERN, original_markdown_content, flags=re.MULTILINE | re.DOTALL)

    processed_document_parts = []

    # parts[0] 是第一个 #@SECTION: 之前的内容
    if parts and parts[0].strip():
        print("文档在第一个 #@SECTION: 之前有内容，将直接添加到输出。")
        processed_document_parts.append(parts[0])

    idx = 0
    if not parts[0].strip() and len(parts) > 1:  # 如果第一个部分为空，则第一个有效部分从索引1开始
        idx = 1

    while idx < len(parts):
        section_header = parts[idx]  # 这是 #@SECTION: ... 行
        raw_section_content = parts[idx + 1] if (idx + 1) < len(parts) else ""
        idx += 2  # 跳到下一个 #@SECTION: 行

        print(f"\n--- 正在处理章节 --- \n{section_header.strip()}")

        # 添加内容为空的检查
        processed_document_parts.append(section_header)

        if not raw_section_content.strip():
            print(f"章节 '{section_header.strip()}' 内容为空，跳过LLM处理。")
            continue  # 跳过空内容的处理，直接进入下一个循环

        # 6a. 构建 LLM Prompt
        full_prompt_for_section = build_llm_prompt(raw_section_content.strip(), known_autosar_classes)

        # 6b. 调用 LLM API
        llm_processed_content = call_llm_api(client, llm_model_name, full_prompt_for_section)

        if llm_processed_content:
            processed_document_parts.append(llm_processed_content.strip())
        else:
            print(f"警告：章节 '{section_header.strip()}' 未能从LLM获取处理结果，将使用原始未处理内容。")
            processed_document_parts.append(raw_section_content.strip())  # 保留原始内容以防LLM失败

    # 7. 组合处理后的章节并写入输出文件
    final_processed_markdown = "\n".join(processed_document_parts)
    if not final_processed_markdown.strip() and original_markdown_content.strip():
        print("警告：最终处理的文档内容为空，但原始文档有内容。可能所有章节处理都失败了或文档结构不符合预期。")

    output_filename_base, output_filename_ext = os.path.splitext(md_filename)
    # 确保输出文件名不包含非法字符，如果md_filename可能来自用户输入
    safe_output_filename_base = re.sub(r'[^\w\-_.]', '_', output_filename_base)
    output_md_filename = f"{safe_output_filename_base}_preprocessed_by_llm{output_filename_ext}"
    output_md_filepath = os.path.join(output_dir, output_md_filename)

    try:
        with open(output_md_filepath, 'w', encoding='utf-8') as f:
            f.write(final_processed_markdown)
        print(f"\n--- 预处理完成！结果已保存到: {output_md_filepath} ---")
    except Exception as e:
        print(f"写入输出文件时发生错误: {e}")

if __name__ == "__main__":
    main()