import json
import re
import tiktoken
import google.generativeai as genai
import time
from typing import List, Dict, Any, Optional

from openai import OpenAI
from config import (
    LLM_API_BASE, LLM_API_KEY, LLM_MODEL_NAME,
    CONSTRAINT_SCHEMA, CLASS_ANNOTATION_PATTERN, ENUM_ANNOTATION_PATTERN,
    SECTION_ANNOTATION_PATTERN, SECTION_SPLIT_PATTERN, PARENT_SECTION_CONTEXT_TAG,
    CLASS_LEVEL_ATTR, ENUM_LEVEL_ATTR,
    MAX_CONTEXT_TOKENS, MAX_OUTPUT_TOKENS, TOKEN_BUFFER, SAFE_INPUT_CONTENT_MAX_TOKENS
)

try:
    tokenizer = tiktoken.encoding_for_model(f"{LLM_MODEL_NAME}")
except KeyError:
    print(f"Warning: Model {LLM_MODEL_NAME} not found for tiktoken. Using cl100k_base.")
    tokenizer = tiktoken.get_encoding("cl100k_base")


def count_tokens(text):
    if not text:
        return 0
    return len(tokenizer.encode(text))


class LlmExtractor:
    def __init__(self):
        if not LLM_API_KEY:
            raise ValueError("环境变量中未找到 LLM_API_KEY。")
        # openai
        # self.client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_API_BASE)
        # gemini
        genai.configure(api_key=LLM_API_KEY,transport="rest",client_options={"api_endpoint": "https://api.openai-proxy.org/google"})  # 配置 Gemini
        self.model = genai.GenerativeModel(LLM_MODEL_NAME)  # 初始化 Gemini 模型
        self.constraint_schema_str = json.dumps(CONSTRAINT_SCHEMA)
    def _build_extraction_prompt(self, text_block_for_llm):
        prompt = f"""
        # 角色
        你是一位 AUTOSAR 规范助手，负责把文档片段转换为结构化约束 JSON。
        
        # 输出格式
        严格按照以下要求输出：
        1.  仅返回一个 JSON 对象。
        2.  该 JSON 对象必须包含一个顶层键 `"extracted_constraints"`，其值为一个 JSON 数组。
        3.  数组中的每个元素都是一个代表单个约束的 JSON 对象，且必须 100% 符合通过 API 的 `response_schema` 参数强制执行的输出 Schema。
        4.  每个约束对象新增 **"is_active"** 布尔字段：若该约束显然不会参与后续 XML 生成 / 验证，则设为 **false**，否则为 true。
        5.  若无任何约束可提取，则返回 `{{"extracted_constraints":[]}}`。
        
        
        # 约束提取指令与优先级
        
        ## 1. 提取带显式 ID 的约束 (最高优先级)
           - 查找文本中的显式 ID 标记 (如 `[TPS_SWCT_xxxx]` 或 `[constr_xxxx]`)。
           - 对每个 ID：
             - `id`: 完整 ID 字符串。
             - `id_type`: 根据 ID 前缀设为 "TPS_SWCT" 或 "constr"。
             - `title`: 通常在 ID 与 `(cid:100)` 之间。
             - `expression`: 通常在 `(cid:100)` 与 `(cid:99)` 之间。
             - `references`: 通常在 `(cid:99)` 之后括号内或约束文本中。
        
        ## 2. 提取无显式 ID 的文本/推理约束 (次高优先级)
           - **扫描所有文本内容（优先处理主要叙述文本，其次是多模态上下文内的描述性文本）**，寻找表达规范性要求（定义、规则、推荐、限制等）的语句。
           - **`id_type` 判断**:
             - 若语句含 `shall`, `must`, `shall not`, `has to` 等强硬语气词，`id_type` = `"additional_binding"`。
             - 若语句含 `recommended`, `should`, `may` 等建议性语气词，`id_type` = `"additional_not_binding"`。
           - **`id` 生成**:
             - **优先**: 若要求与特定图表（如 "Figure X.Y", "Table X.Y"）的**标题或其直接描述**紧密关联，使用图/表编号作 ID (例: `Figure_X_Y`, `Table_X_Y`)。
             - **其次**: 若源自纯文本且无直接关联图表编号，生成描述性 ID (例: `Constr_主题描述_上下文`)。
           - **`title` 与 `expression`**:
             - `expression`: 捕获完整的规范性语句或其核心内容。
             - `title`: 根据 `expression` 简洁概括主题。
           - **处理多模态上下文 (`<-------- multimodal context ... -------->`)**:
             - 此类上下文通常描述图/表。
             - **原则**: **优先从主要叙述文本提取约束。**
             - **仅当**约束的**核心信息主要通过图/表传达**，或多模态上下文为正文约束提供了**关键且不可或缺的细节**时，才重点依赖此上下文。
             - **若基于多模态上下文提取** (因其满足上述条件)，可参考以下映射：
               | multimodal 元素 (图/表描述) | JSON 字段 (参考)             |
               |------------------------------|-----------------------------|
               | 图/表内关键项/属性列         | targets[i].targetAttributes   |
               | 图/表内某项的说明            | expression (补充) / value   |
               | 整体图/表标题                | title (补充); scope_path 末尾 |
             - **避免冗余**: 若主要叙述文本已清晰表达约束，则**不应**仅因存在多模态上下文而生成重复约束。
        
        ## 3. 提取 XML 示例约束
           - 识别 "Listing X.Y" 及其后的 XML 代码块。
           - `id`: 根据 Listing 编号生成 (例: `Listing_X_Y`)。
           - `id_type`: `"example"`。
           - `constraint_type`: `"xml_instantiation_example"`。
           * `xml_example_content`: 提取的 XML 代码。
        
        # 通用字段处理规则 (适用于所有约束类型)
        
        -   **`targets`**:
        - 主要依据 `#@CLASS: Name` / `#@ENUM: Name` 及 `<!-- LLM_CONTEXT ... -->` 注释。
        - **当 `targetEntityName` 是一个具体的类名或枚举名时** (`entityType` 为 `"class"` 或 `"enum"`):
        - 如果约束针对该实体下的特定属性/字面量，则 `targetAttributes` 列出这些属性/字面量名。
        - 如果约束针对整个实体本身，则 `targetAttributes` 为 `["_classLevel"]` (对于类) 或 `["_enumLevel"]` (对于枚举)。
        - **注意**: `["_abstractLevel"]` **不应**用于具体类或枚举的 `targetAttributes`。
        - **当约束针对广泛场景或抽象概念时** (`entityType` 设为 `"abstract"`):
        - `targetEntityName` 应为一个描述该抽象概念或场景的名称 (例如 "GeneralDatatypeRule", "PretendedNetworkingConcept")。*（如果链接器已修改为接受 `targetEntityName: "_abstractLevel"`，则此处也可允许）*
        - `targetAttributes` 应为 `["_abstractLevel"]`。
        -   **`scope_path`**:
            - 依据 `<!-- PARENT_SECTION_CONTEXT: ... -->` 和最近的 `#@SECTION: Title` 组装。
            - 若与特定图/表关联，其标题可作 `scope_path` 末尾。
        -   **`constraint_type`**: 根据约束语义选择 (如 `definition`, `cardinality`, `existence`, `relationship` 等)。仔细判断无 ID 约束的类型。
        -   **其他字段** (`value`, `references` 等): 根据上下文提取，缺失则为 `null` 或 `[]`。
        - **自动判定 "is_active"**：  
            - 若 title 或 expression 中出现 “Definition of…”, “shall be considered…”, “legacy”, “old-world”, “example”, “listing”, “deprecated”,  
            - **或** 句式 “shall be used to … afterwards shall be considered …” / “shall be considered compatible” 等表示**后续语义效果**的短语， 则设 is_active = false
        
        # Few-shot 示例 (保持不变或根据需要调整)
        # few-shot 1：最简单
        [BEGIN]
        #@CLASS: SwComponentPrototype
        <!-- LLM_CONTEXT FOR CLASS SwComponentPrototype: Attributes=[shortName] -->
        [TPS_SWCT_00001] Short name uniqueness (cid:100) shortName must be unique. (cid:99)
        [END]
        期望输出:
        {{
            "extracted_constraints":[
                {{
                    "id":"TPS_SWCT_00001",
                    "id_type":"TPS_SWCT",
                    "title":"Short name uniqueness",
                    "is_active":true,
                    "expression":"shortName must be unique.",
                    "references":[],
                    "targets":
                        [
                            {{
                                "targetEntityName":"SwComponentPrototype",
                                "entityType":"class",
                                "targetAttributes":["shortName"]
                            }}
                        ],
                    "constraint_type":"other",
                    "value":null,"scope_path":[],
                    "xml_example_content":null
                }}
            ]
        }}

        # few-shot 2：XML 示例
        [BEGIN]
        Listing 5.1 SwComponentPrototype example
        <SW-COMPONENT-PROTOTYPE>
          <SHORT-NAME>Main</SHORT-NAME>
        </SW-COMPONENT-PROTOTYPE>
        [END]
        …(JSON，其中 id="Listing_5_1", id_type="example", constraint_type="xml_instantiation_example")…
        
        # few-shot 3：multimodal 推荐性（not_binding）
        输入片段:
        Table 11.7: NvBlockNeeds dependencies
        <-------------- multimodal context
        | Attribute | NvBlockDescriptor side |
        | readonly  | Recommended to match for all connected PortPrototypes |
        -------------->
        期望输出:
        {{
            "extracted_constraints": [
                {{
                    "id": "Table_11_7",
                    "id_type": "additional_not_binding",
                    "title": "readonly consistency (recommended)",
                    "expression": "NvBlockDescriptor.readonly is recommended to match the value requested by all connected PortPrototypes.",
                    "references": [],
                    "targets": [
                        {{
                            "targetEntityName": "NvBlockNeeds",
                            "entityType": "class",
                            "targetAttributes": ["readonly"]
                        }},
                        {{
                            "targetEntityName": "NvBlockDescriptor",
                            "entityType": "class",
                            "targetAttributes": ["readonly"]
                        }}
                    ],
                    "constraint_type": "relationship",
                    "value": null,
                    "scope_path": ["Table 11.7 NvBlockNeeds dependencies"],
                    "xml_example_content": null
                }}
            ]
        }}
        # few-shot 4：定义性（is_active = false）
        [BEGIN]
        [TPS_SWCT_01642] Definition of an “old-world” dynamic-size array (cid:100) … shall be considered an “old-world” dynamic-size array. (cid:99)
        [END]
        期望输出:
        {{
          "extracted_constraints":[
            {{
              "id":"TPS_SWCT_01642",
              "is_active":false,
              ...
            }}
          ]
        }}

        # 待处理文档
        \"\"\"{text_block_for_llm}\"\"\"

        将所有提取的约束信息输出为单个 JSON 对象。该 JSON 对象应包含一个名为 "extracted_constraints" 的键，其值为一个 JSON 数组。数组中的每个元素都是一个代表单个约束的 JSON 对象，并且必须严格符合通过 API 的 `response_schema` 参数强制执行的输出 Schema。
        """
        #数组中的每个元素都是一个代表单个约束的JSON对象，并且必须严格符合以下CONSTRAINT_SCHEMA:
        #{self.constraint_schema_str}
        return prompt

    def extract_constraints_from_block(self, text_block_for_llm):
        """
        调用 Gemini / OpenAI 接口，把单个文档块转为约束列表。
        · 出错自动重试 3 次（1s / 3s / 放弃）
        · 保证 raw_response_content 判空，避免 NoneType 切片
        · 返回值始终为 list
        """
        # ---------- 1. 组装 Prompt ----------
        prompt = self._build_extraction_prompt(text_block_for_llm)
        current_tokens = count_tokens(text_block_for_llm)
        total_input_tokens = count_tokens(prompt)  # prompt 已包含原文
        print(f"\n--- 正在向 LLM 发送请求 (片段内容 tokens: {current_tokens}, 总输入 tokens: {total_input_tokens}) ---")

        # ---------- 2. 调用 LLM（带重试） ----------
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json",
            response_schema=CONSTRAINT_SCHEMA,
            temperature=0.0,
            max_output_tokens=MAX_OUTPUT_TOKENS
        )

        # try:
        #     completion = self.client.chat.completions.create(
        #         model=LLM_MODEL_NAME,
        #         messages=[
        #             {"role": "system",
        #              "content": "你是一位专业的 AUTOSAR 助手，设计用于将信息精确提取为 JSON 格式。请严格遵循输出 Schema。"},
        #             {"role": "user", "content": prompt}
        #         ],
        #         response_format={"type": "json_object"},
        #         temperature=0.0,
        #         max_completion_tokens=MAX_OUTPUT_TOKENS,
        #         stream=False
        #     )
        #     raw_response_content = completion.choices[0].message.content
            # print(f"DEBUG: LLM 原始响应:\n{raw_response_content[:1000]}...")

        raw_response_content = None
        for attempt in range(3):
            try:
                resp = self.model.generate_content(
                    contents=prompt,
                    generation_config=generation_config
                )
                raw_response_content = resp.text          # 成功拿到响应
                break
            except Exception as call_err:
                print(f"LLM 调用失败 (第 {attempt+1}/3 次): {call_err}")
                if attempt < 2:
                    time.sleep(2 ** attempt + 1)          # 1 秒 → 3 秒
                else:
                    print("LLM 连续失败，跳过该块。")
                    return []                             # 放弃该块

        # 若三次都失败 raw_response_content 仍为空
        if not raw_response_content:
            print("LLM 无返回内容，跳过该块。")
            return []

        # ---------- 3. 解析 JSON ----------
        try:
            extracted_data = json.loads(raw_response_content)
        except json.JSONDecodeError as je:
            print(f"LLM JSON 解析失败: {je}")
            print(f"LLM 原始响应(前500): {raw_response_content[:500]}")
            return []

        # ---------- 4. 校验字段 ----------
        if isinstance(extracted_data.get("extracted_constraints"), list):
            cnt = len(extracted_data["extracted_constraints"])
            print(f"--- LLM 成功解析并提取了 {cnt} 个约束 ---")
            return extracted_data["extracted_constraints"]
        else:
            print("--- LLM 响应格式不正确: 未找到 'extracted_constraints' 列表 ---")
            print(f"LLM 原始响应(前500): {raw_response_content[:500]}")
            return []


    def _split_text_by_paragraphs(self, text, max_tokens_for_sub_chunk, parent_section_context_str=""):
        """按段落分割文本，确保每个子块（加上父章节上下文）不超过token限制。"""
        output_sub_chunks = []
        current_sub_chunk_parts = []
        current_sub_chunk_tokens = count_tokens(parent_section_context_str)
        paragraphs = re.split(r'\n\s*\n', text.strip())

        for i, para in enumerate(paragraphs):
            if not para.strip():
                continue

            para_to_add = para
            if i < len(paragraphs) - 1:
                para_to_add += "\n\n"

            para_tokens = count_tokens(para_to_add)

            if count_tokens(parent_section_context_str + para_to_add) > max_tokens_for_sub_chunk:
                if current_sub_chunk_parts:
                    output_sub_chunks.append(parent_section_context_str + "".join(current_sub_chunk_parts))
                    current_sub_chunk_parts = []
                    current_sub_chunk_tokens = count_tokens(parent_section_context_str)

                print(
                    f"警告: 段落 (加父上下文后 {count_tokens(parent_section_context_str + para_to_add)} tokens) 单独超出了子块的最大 token 限制 ({max_tokens_for_sub_chunk} tokens)，将单独处理。段落预览: '{para_to_add[:100]}...'")
                output_sub_chunks.append(parent_section_context_str + para_to_add)  # 即使超限也发送
                continue

            if current_sub_chunk_tokens + para_tokens > max_tokens_for_sub_chunk and current_sub_chunk_parts:
                output_sub_chunks.append(parent_section_context_str + "".join(current_sub_chunk_parts))
                current_sub_chunk_parts = [para_to_add]
                current_sub_chunk_tokens = count_tokens(parent_section_context_str) + para_tokens
            else:
                current_sub_chunk_parts.append(para_to_add)
                current_sub_chunk_tokens += para_tokens

        if current_sub_chunk_parts:
            output_sub_chunks.append(parent_section_context_str + "".join(current_sub_chunk_parts))

        return [chunk for chunk in output_sub_chunks if chunk.strip()]

    def _split_document_into_chunks(self, enhanced_markdown_content, max_tokens_for_chunk_content):
        """
        (修改版：贪心策略)
        将增强后的Markdown文档分割成适合LLM处理的块，使每个块尽可能接近max_tokens_for_chunk_content。
        会尝试合并小的章节/段落，直到块接近满额。
        """
        print(f"信息: 开始使用贪心策略进行文档分块，目标 token 数: {max_tokens_for_chunk_content}")
        all_chunks = []
        current_chunk_parts = []
        current_chunk_tokens = 0

        section_hierarchy_titles = []
        current_block_initial_parent_context_str = ""  # 当前块构建时，其开头的父章节上下文

        # 1. 将文档初步分解为章节标记和它们之间的文本内容块
        # SECTION_SPLIT_PATTERN 应该是一个捕获组 (e.g., r"(^#@SECTION:.*?$)")
        # 这样 re.split 会保留分隔符
        doc_elements_raw = re.split(f'({SECTION_SPLIT_PATTERN})', enhanced_markdown_content, flags=re.MULTILINE)

        # 2. 将原始元素细化为 'section_marker' 或 'paragraph' 单元队列
        processing_queue = []
        for element_text_raw in doc_elements_raw:
            if not element_text_raw or not element_text_raw.strip():
                continue

            element_text = element_text_raw.strip()  # 处理时都用strip后的，但添加时可能要原始的或加换行

            if re.fullmatch(SECTION_SPLIT_PATTERN, element_text, flags=re.MULTILINE):
                processing_queue.append({'type': 'section_marker', 'text': element_text_raw})  # 保留原始格式用于拼接
            else:
                # 对于非章节标记的文本块，按段落拆分
                # 使用 re.split 保留段落间的空行感觉（通过捕获空行）会复杂，简单按\n\s*\n分割后，再补回去
                paragraphs_text = element_text_raw.strip().split('\n\n')  # 更简单的段落分割
                for i, para_text_raw in enumerate(paragraphs_text):
                    if para_text_raw.strip():
                        # 为了在块内拼接时能保留段落结构，我们假设段落间用\n\n
                        # 如果不是最后一个段落，或者这个文本块后没有紧跟section marker,则加\n\n
                        # 这个逻辑在后面拼接 current_chunk_parts 时通过 "\n\n".join() 实现更简单
                        processing_queue.append({'type': 'paragraph', 'text': para_text_raw.strip()})

        # 3. 迭代处理处理队列中的每个单元 (章节标记或段落)
        for i, unit in enumerate(processing_queue):
            unit_text_to_add = unit['text']  # 这是将被实际加入到块中的文本
            unit_tokens = count_tokens(unit_text_to_add)

            # 3.1 更新全局章节层级 (如果单元是章节标记)
            #     并确定此单元如果开启新块，其父章节上下文
            parent_context_for_this_unit_if_new_block_str = ""
            parent_context_for_this_unit_if_new_block_tokens = 0

            if unit['type'] == 'section_marker':
                current_section_title_match = re.search(SECTION_ANNOTATION_PATTERN, unit_text_to_add)
                current_section_title = current_section_title_match.group(
                    1).strip() if current_section_title_match else "Unknown Section"

                level = current_section_title.count('.')  # 简化层级判断

                # 更新层级 (如果新章节层级更低或同级但在不同分支，则截断旧层级)
                while section_hierarchy_titles and level <= section_hierarchy_titles[-1]['level']:
                    section_hierarchy_titles.pop()
                section_hierarchy_titles.append({'title': current_section_title, 'level': level})

            # 确定父章节上下文：基于当前（可能已更新的）section_hierarchy_titles
            # 父章节是当前层级列表的除最后一个元素外的所有部分
            if len(section_hierarchy_titles) > 1:
                parent_titles = [s['title'] for s in section_hierarchy_titles[:-1]]
                parent_context_for_this_unit_if_new_block_str = f"<!-- {PARENT_SECTION_CONTEXT_TAG}: {' > '.join(parent_titles)} -->"  # 注意：没有末尾的\n，拼接时加
                parent_context_for_this_unit_if_new_block_tokens = count_tokens(
                    parent_context_for_this_unit_if_new_block_str)

            # 3.2 决策：是否将当前单元添加到 current_chunk_parts
            can_add_to_current_chunk = False
            if not current_chunk_parts:  # 当前块为空，此单元将是第一个
                # 新块的总 token = 父上下文 token + 单元 token
                if parent_context_for_this_unit_if_new_block_tokens + unit_tokens <= max_tokens_for_chunk_content:
                    can_add_to_current_chunk = True
                    current_block_initial_parent_context_str = parent_context_for_this_unit_if_new_block_str  # 记录这个块的父上下文
                else:
                    # 单元本身（加父上下文）就超限了
                    print(f"警告: 单元 '{unit_text_to_add[:100]}...' (tokens: {unit_tokens}) "
                          f"加上其父章节上下文 (tokens: {parent_context_for_this_unit_if_new_block_tokens}) "
                          f"后为 {parent_context_for_this_unit_if_new_block_tokens + unit_tokens} tokens, "
                          f"超出了新块的限制 ({max_tokens_for_chunk_content} tokens)。"
                          "该单元将单独成块（可能依然超限）。")
                    # 完成之前可能存在的块 (虽然这里 current_chunk_parts 为空)
                    if current_chunk_parts:  # 理论上这里不会执行
                        all_chunks.append("\n\n".join(current_chunk_parts))
                        # 此超大单元（带父上下文）单独成块
                    forced_chunk_parts = []
                    if parent_context_for_this_unit_if_new_block_str:
                        forced_chunk_parts.append(parent_context_for_this_unit_if_new_block_str)
                    forced_chunk_parts.append(unit_text_to_add)
                    all_chunks.append("\n\n".join(forced_chunk_parts))
                    current_chunk_parts = []  # 重置
                    current_chunk_tokens = 0
                    current_block_initial_parent_context_str = ""
                    continue  # 处理下一个单元
            else:  # 当前块已有内容
                # 预估加入后的 token = 当前块已有 token + 单元 token
                if current_chunk_tokens + unit_tokens <= max_tokens_for_chunk_content:
                    can_add_to_current_chunk = True
                # else: 不能加入，当前块需要结束

            # 3.3 执行添加或结束当前块的逻辑
            if can_add_to_current_chunk:
                if not current_chunk_parts:  # 如果是块的第一个实际内容单元
                    # 确保父章节上下文（如果存在且之前没加过）被加入
                    if current_block_initial_parent_context_str and current_block_initial_parent_context_str not in current_chunk_parts:
                        current_chunk_parts.append(current_block_initial_parent_context_str)
                        current_chunk_tokens += count_tokens(current_block_initial_parent_context_str)

                current_chunk_parts.append(unit_text_to_add)
                current_chunk_tokens += unit_tokens
            else:
                # 不能加入此单元，意味着当前块结束
                if current_chunk_parts:
                    all_chunks.append("\n\n".join(current_chunk_parts))

                # 用此单元开始新块
                current_chunk_parts = []
                current_chunk_tokens = 0
                current_block_initial_parent_context_str = parent_context_for_this_unit_if_new_block_str  # 新块的父上下文

                if current_block_initial_parent_context_str:
                    current_chunk_parts.append(current_block_initial_parent_context_str)
                    current_chunk_tokens += count_tokens(current_block_initial_parent_context_str)

                # 再次检查，如果这个单元加上父上下文后，作为新块的第一个元素是否超限
                if current_chunk_tokens + unit_tokens > max_tokens_for_chunk_content:
                    print(f"警告: 单元 '{unit_text_to_add[:100]}...' (tokens: {unit_tokens}) "
                          f"作为新块的第一个元素 (带父上下文共 {current_chunk_tokens + unit_tokens} tokens) "
                          f"可能超限 ({max_tokens_for_chunk_content} tokens)。")

                current_chunk_parts.append(unit_text_to_add)
                current_chunk_tokens += unit_tokens

        # 循环结束后，处理剩余在 current_chunk_parts 中的内容
        if current_chunk_parts:
            all_chunks.append("\n\n".join(current_chunk_parts))

        print(f"信息: 贪心分块完成，共生成 {len(all_chunks)} 个块。")
        # for idx, chunk_text in enumerate(all_chunks):
        #     print(f"  块 {idx+1} token 数: {count_tokens(chunk_text)}, 预览: '{chunk_text[:150].replace('\n', ' ')}...'")
        return [chunk for chunk in all_chunks if chunk.strip()]

    def remove_duplicates(self, constraints):
        processed_ids = set()
        unique_constraints = []
        duplicates_count = 0
        for constraint in constraints:
            constraint_id = constraint.get('id')
            if constraint_id:
                if constraint_id not in processed_ids:
                    processed_ids.add(constraint_id)
                    unique_constraints.append(constraint)
                else:
                    print(f"信息: 发现重复约束ID '{constraint_id}'，将跳过后续出现。")
                    duplicates_count += 1
            else:
                unique_constraints.append(constraint)
                print(f"警告: 发现一个没有ID的约束: {str(constraint)[:100]}...")
        if duplicates_count > 0:
            print(f"信息: 基于ID移除了 {duplicates_count} 个重复约束。")
        return unique_constraints

    def extract_constraints_from_text(self, enhanced_markdown_content):
        main_document_content = enhanced_markdown_content
        main_doc_tokens = count_tokens(main_document_content)
        print(f"信息: 主文档 (含局部上下文) {main_doc_tokens} tokens.")
        print(f"信息: 每LLM调用目标内容Token数上限: {SAFE_INPUT_CONTENT_MAX_TOKENS} tokens.")

        chunks_to_process = []
        # 使用新的分块逻辑
        chunks_to_process = self._split_document_into_chunks(main_document_content,
                                                             SAFE_INPUT_CONTENT_MAX_TOKENS)

        if not chunks_to_process and main_document_content.strip():  # 如果分块后为空但原文不为空，则原文整体作为一个块
            print("信息: 分块后无结果，但原文不为空，将尝试整体处理。")
            if main_doc_tokens <= SAFE_INPUT_CONTENT_MAX_TOKENS:
                chunks_to_process.append(main_document_content)
            else:
                print(f"警告: 原文过大 ({main_doc_tokens} tokens) 且无法按策略分块，可能导致处理失败或截断。")
                # 仍然尝试发送，或者在这里可以有一个备用分割策略（如之前的按章节）
                # chunks_to_process.append(main_document_content) # 风险较大
                # 或者使用旧的_split_text_by_paragraphs作为最后手段
                chunks_to_process = self._split_text_by_paragraphs(main_document_content, SAFE_INPUT_CONTENT_MAX_TOKENS,
                                                                   "")

        print(f"信息: 文档被分割为 {len(chunks_to_process)} 个块进行处理。")

        all_extracted_constraints = []
        for i, chunk_text in enumerate(chunks_to_process):
            print(f"\n--- 正在处理块 {i + 1}/{len(chunks_to_process)} (块token: {count_tokens(chunk_text)}) ---")
            if not chunk_text.strip():
                print("信息: 跳过空块。")
                continue

            extracted_list_from_chunk = self.extract_constraints_from_block(chunk_text)
            if extracted_list_from_chunk:
                all_extracted_constraints.extend(extracted_list_from_chunk)

        print(f"\n信息: 所有块处理完毕。总共提取了 {len(all_extracted_constraints)} 个约束（去重前）。")

        final_constraints = self.remove_duplicates(all_extracted_constraints)
        print(f"信息: 去重后剩余 {len(final_constraints)} 个约束。")

        return final_constraints

    def get_text_chunks(self, enhanced_markdown: str) -> List[str]:
        """
        返回分块后的文本列表，每个元素对应一个待 LLM 处理的块
        """
        return self._split_document_into_chunks(enhanced_markdown)

    def extract_constraints_from_text(
            self,
            enhanced_markdown: str,
            rerun_chunks: Optional[List[int]] = None  # 新增参数
    ) -> List[Dict]:
        # 1) 调用私有分块，拿到 chunks 列表
        chunks = self._split_document_into_chunks(enhanced_markdown)

        raw_results: List[Dict] = []
        # 2) 初次遍历所有块
        for chunk in chunks:
            items = self.extract_constraints_from_block(chunk)
            raw_results.extend(items)

        # 3) 如果指定了重跑块，按索引（从1开始）再次提取并追加
        if rerun_chunks:
            for idx in rerun_chunks:
                # 忽略越界检查留给调用方
                chunk_text = chunks[idx - 1]
                rerun_items = self.extract_constraints_from_block(chunk_text)
                raw_results.extend(rerun_items)

        return raw_results

_extractor = LlmExtractor()

def get_text_chunks(enhanced_markdown: str) -> List[str]:
    """
    返回分块后的文本列表，可供 main.py 拆分并重跑指定块。
    """
    default_max_tokens = SAFE_INPUT_CONTENT_MAX_TOKENS  # 或者替换成你 LlmExtractor 初始化时实际使用的值
    return _extractor._split_document_into_chunks(enhanced_markdown, default_max_tokens)

def extract_constraints_from_block(chunk_text: str) -> List[Dict]:
    """
    对单个块文本调用 LLM 提取约束，返回约束 Dict 列表。
    """
    return _extractor.extract_constraints_from_block(chunk_text)

def remove_duplicates(raw_results: List[Dict]) -> List[Dict]:
    """
    对原始约束列表去重，保留首次出现的条目。
    """
    return _extractor.remove_duplicates(raw_results)
