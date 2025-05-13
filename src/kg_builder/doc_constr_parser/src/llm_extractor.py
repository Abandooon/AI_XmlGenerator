import json
import re
from openai import OpenAI  # DeepSeek 使用 OpenAI 的库
from .config import (
    DEEPSEEK_API_KEY, DEEPSEEK_API_BASE, LLM_MODEL_NAME,
    CONSTRAINT_SCHEMA, CONSTRAINT_PATTERN,
    CLASS_ANNOTATION_PATTERN, ENUM_ANNOTATION_PATTERN,
    SECTION_ANNOTATION_PATTERN, HIERARCHICAL_ANNOTATION_PATTERN,
    CLASS_LEVEL_ATTR, ENUM_LEVEL_ATTR
)


class DeepSeekExtractor:
    def __init__(self):
        if not DEEPSEEK_API_KEY:
            raise ValueError("环境变量中未找到 DEEPSEEK_API_KEY。")
        self.client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_API_BASE)
        self.schema_json_str = json.dumps(CONSTRAINT_SCHEMA)  # 将 Schema 转为 JSON 字符串以便插入 Prompt

    def _build_prompt(self, constraint_text_block, document_context_block):
        # constraint_text_block 是从 #@CLASS ... 到约束本身的原始文本
        # document_context_block 是 "---CONTEXT START--- ... ---CONTEXT END---" 块

        prompt = f"""
你是一位专业的 AUTOSAR 助手。你的任务是从提供的 AUTOSAR 规范文档片段中提取结构化信息。
文档已经使用上下文块和注解进行了预处理。

{document_context_block}

现在，请分析以下特定的约束块。请密切关注约束之前紧邻的 #@CLASS, #@ENUM, 和 #@Hierarchical 等注解。

待分析的约束块:
\"\"\"
{constraint_text_block}
\"\"\"

提取指令:
1.  识别约束 ID (例如，TPS_SWCT_XXXX 或 constr_YYYY) 及其类型 ("TPS_SWCT" 或 "constr")，分别填入 `id` 和 `id_type` 字段。
2.  提取约束的标题，填入 `title` 字段。
3.  提取约束的详细表述 (位于 (cid:100) 和 (cid:99) 之间的文本)，填入 `expression` 字段。
4.  提取末尾括号中列出的任何引用 ID (例如 (RS_SWCT_00190, ...))，作为一个列表填入 `references` 字段。
5.  确定 `targetClass` 或 `targetEnum`:
    *   查看“待分析的约束块”中，紧邻约束 ID 行之前的 `#@CLASS: ClassName` 或 `#@ENUM: EnumName` 注解。这是主要的目标实体。如果找到 `#@CLASS`，则其值为 `targetClass`；如果找到 `#@ENUM`，则其值为 `targetEnum`。
6.  确定 `targetAttribute` (用于类或枚举):
    *   如果确定了 `targetClass`: 检查约束文本是否提及此类的特定属性。此属性必须在 `---CONTEXT START---` 块中对应 `ClassName` 的 `Attributes` 列表中。如果是，则使用该属性名。如果约束描述的是类本身的一般属性，或者上下文中未提及特定属性，则将 `targetAttribute` 设置为 "{CLASS_LEVEL_ATTR}"。
    *   如果确定了 `targetEnum`: 检查约束文本是否提及此枚举的特定字面量。此字面量必须在 `---CONTEXT START---` 块中对应 `EnumName` 的 `Literals` 列表中。如果是，则使用该字面量名称。如果约束描述的是枚举本身的一般属性，或者上下文中未提及特定字面量，则将 `targetAttribute` 设置为 "{ENUM_LEVEL_ATTR}"。
    *   **关键**: 不要自行创造属性或字面量名称。它们必须来自提供的上下文列表，或者是 "{CLASS_LEVEL_ATTR}" 或 "{ENUM_LEVEL_ATTR}"。
7.  确定 `parent_id`: 如果 "#@Hierarchical" 行紧邻约束 ID 行之前，则 `parent_id` 应该是*前一个*已处理的非层级约束的 ID。(如果适用，你会被告知前一个 ID，或者如果这是序列的一部分则进行推断)。目前，如果存在 #@Hierarchical，请注意它。调用代码将处理 parent_id 的链接。
8.  从“待分析的约束块”中最近的 #@SECTION 注解中提取章节信息，填入 `scope_section`。
9.  确定 `constraint_type` (例如："definition", "cardinality", "behavioral" 等)。
10. 如果适用，提取 `value`。

将提取的信息输出为严格符合以下 Schema 的单个 JSON 对象:
{self.schema_json_str}

确保 JSON 中的所有字符串值都已正确转义。
如果某个字段不适用或信息缺失，如果 Schema 允许，则对其值使用 `null`，如果不是必需的，则省略它。
专注于由 `[ID_TYPE_ID_NUMBER] Title (cid:100) ...` 模式标识的单个约束。
"""
        return prompt

    def extract_single_constraint_info(self, constraint_text_block, document_context_block):
        prompt = self._build_prompt(constraint_text_block, document_context_block)

        print("\n--- 正在向 LLM 发送请求 ---")
        print(f"用于 LLM 的约束块片段:\n{constraint_text_block[:500]}...")  # 打印片段以供调试

        try:
            completion = self.client.chat.completions.create(
                model=LLM_MODEL_NAME,
                messages=[
                    {"role": "system", "content": "你是一位专业的 AUTOSAR 助手，设计用于将信息精确提取为 JSON 格式。"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},  # 请求 JSON 输出 (如果 API 支持)
                temperature=0.0,  # 获取确定性输出
                stream=False  # 为简单起见，一次性获取 JSON 对象。控制台流式输出是不同的。
            )

            raw_response_content = completion.choices[0].message.content
            print("--- LLM 原始响应 ---")
            print(raw_response_content)  # 实时打印完整响应

            # 尝试解析 JSON
            # 响应应该是一个有效的 JSON 对象字符串。
            extracted_json = json.loads(raw_response_content)
            print("--- LLM 解析后的 JSON ---")
            print(json.dumps(extracted_json, indent=2))
            return extracted_json

        except Exception as e:
            print(f"LLM API 调用或 JSON 解析期间出错: {e}")
            print(f"有问题的约束块片段: {constraint_text_block[:200]}")
            if 'raw_response_content' in locals():  # 检查变量是否存在
                print(f"解析失败的 LLM 原始输出: {raw_response_content}")
            return None


def extract_constraints_from_text(enhanced_markdown_content):
    llm_extractor = DeepSeekExtractor()
    all_extracted_data = []

    # 分割增强内容以获取上下文块和主文档
    context_end_marker = "--- CONTEXT END ---"
    parts = enhanced_markdown_content.split(context_end_marker, 1)
    if len(parts) != 2:
        print("错误: 未找到 --- CONTEXT END --- 标记。")
        return []

    document_context_block = parts[0] + context_end_marker
    main_document_content = parts[1]

    previous_non_hierarchical_id = None  # 用于链接 parent_id

    # 遍历所有约束匹配项
    # 我们需要为 LLM 提供约束文本及其*周围*的文本，以获取 #@CLASS 等上下文。
    for match in re.finditer(CONSTRAINT_PATTERN, main_document_content):
        constraint_id_full_match_group = match.group(1)  # [TPS_SWCT_ID] or [constr_ID]
        # constraint_id_full = constraint_id_full_match_group.strip('[]') # 移除方括号得到纯ID

        # "constraint_text_block" 应该包含紧邻其前的注解。
        # 从 match.start() 向后查找这些注解。
        # 一个实用的窗口可能是几百个字符或几行。

        # 定义约束之前的文本窗口以捕获局部注解
        window_start = max(0, match.start() - 500)  # 向后查找 500 个字符
        # 确保窗口结束于当前匹配项的末尾，以包含整个约束文本
        text_before_and_including_match = main_document_content[window_start: match.end()]

        print(f"\n正在处理约束 (ID 匹配组): {constraint_id_full_match_group}")

        extracted_data = llm_extractor.extract_single_constraint_info(
            text_before_and_including_match,  # 这是 "待分析的约束块"
            document_context_block  # 这是 "---CONTEXT START---" 块
        )

        if extracted_data:
            # 对 LLM 输出进行后处理，例如确保 parent_id 逻辑
            # LLM 被要求“注意是否存在 #@Hierarchical”。
            # 我们可以使用自己的正则表达式检查 `text_before_and_including_match`
            # 来确定层级关系。

            # 根据提供给 LLM 的输入块重新检查层级关系
            # 检查 #@Hierarchical 是否紧邻当前约束的ID之前
            # 注意： constraint_id_full_match_group 包含方括号，需要转义
            hierarchical_marker_pattern = HIERARCHICAL_ANNOTATION_PATTERN + r"\s*" + re.escape(
                constraint_id_full_match_group)
            hierarchical_marker_found_in_llm_input = bool(
                re.search(hierarchical_marker_pattern, text_before_and_including_match, re.MULTILINE))

            if hierarchical_marker_found_in_llm_input and previous_non_hierarchical_id:
                extracted_data['parent_id'] = previous_non_hierarchical_id
            # else: # 确保如果不是层级关系或没有父级，则 parent_id 为 null (LLM应该已经处理)
            # extracted_data.setdefault('parent_id', None) # 确保字段存在

            # 更新 previous_non_hierarchical_id
            current_id = extracted_data.get('id')
            if current_id and not hierarchical_marker_found_in_llm_input:
                previous_non_hierarchical_id = current_id

            all_extracted_data.append(extracted_data)
        else:
            print(f"未能为约束块提取数据，该约束块始于: {match.group(0)[:100]}...")

    return all_extracted_data