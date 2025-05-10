import os
import re
import json
import asyncio
import aiohttp
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass, asdict, field
import hashlib

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# 约束数据类
@dataclass
class ConstraintRaw:
    """原始约束数据结构"""
    id: str
    type: str
    title: str = ""
    body: str = ""
    targetClass: str = ""
    targetAttribute: str = ""
    value: Optional[Any] = None
    scope: Dict[str, str] = field(default_factory=dict)
    confidence: float = 0.0
    reference_ids: List[str] = field(default_factory=list)


# 章节上下文跟踪器
class ChapterTracker:
    """跟踪文档章节和焦点信息"""

    def __init__(self):
        self.current_chapter = ""
        self.chapter_focus = {}  # 章节 -> 焦点类
        self.focus_attributes = {}  # 章节 -> 焦点属性列表
        self.chunks_focus = {}  # 块索引 -> (焦点类, 属性列表)

    def update_chapter(self, chapter_id):
        """更新当前章节"""
        self.current_chapter = chapter_id
        if chapter_id not in self.chapter_focus:
            self.chapter_focus[chapter_id] = None
            self.focus_attributes[chapter_id] = []

            # 继承父章节的焦点类（如果有）
            parent_chapter = self._get_parent_chapter(chapter_id)
            if parent_chapter and parent_chapter in self.chapter_focus:
                self.chapter_focus[chapter_id] = self.chapter_focus[parent_chapter]

    def _get_parent_chapter(self, chapter_id):
        """获取父章节ID"""
        if '.' in chapter_id:
            return chapter_id.rsplit('.', 1)[0]
        return None

    def update_focus_class(self, class_name):
        """更新当前章节的焦点类"""
        if self.current_chapter and self._is_valid_class_name(class_name):
            self.chapter_focus[self.current_chapter] = class_name
            logger.debug(f"更新焦点类: {class_name} (章节 {self.current_chapter})")

    def _is_valid_class_name(self, name):
        """验证类名是否有效"""
        if not name or not isinstance(name, str):
            return False

        # 类名应该是驼峰命名且不包含标点符号
        if not name[0].isupper():
            return False

        # 排除明显不是类名的情况
        invalid_endings = ['.', ',', ':', ';', ')', '(']
        if any(name.endswith(c) for c in invalid_endings):
            return False

        # 类名不应该是常见的英语单词
        common_words = ['This', 'These', 'That', 'Those', 'The', 'And', 'Or', 'For']
        if name in common_words:
            return False

        return True

    def add_focus_attribute(self, attribute_name):
        """添加焦点属性"""
        if self.current_chapter and attribute_name and self._is_valid_attribute_name(attribute_name):
            if attribute_name not in self.focus_attributes.get(self.current_chapter, []):
                self.focus_attributes.setdefault(self.current_chapter, []).append(attribute_name)
                logger.debug(f"添加焦点属性: {attribute_name} (章节 {self.current_chapter})")

    def _is_valid_attribute_name(self, name):
        """验证属性名是否有效"""
        if not name or not isinstance(name, str):
            return False

        # 属性名一般以小写字母开头
        if not name[0].islower():
            return False

        # 排除明显不是属性名的情况
        invalid_chars = ['.', ',', ':', ';', ')', '(', ' ']
        if any(c in name for c in invalid_chars):
            return False

        return True

    def save_chunk_focus(self, chunk_index):
        """保存当前块的焦点信息"""
        self.chunks_focus[chunk_index] = (
            self.chapter_focus.get(self.current_chapter),
            self.focus_attributes.get(self.current_chapter, []).copy()
        )

    def get_focus_for_chunk(self, chunk_index):
        """获取特定块的焦点信息"""
        return self.chunks_focus.get(chunk_index, (None, []))

    def get_current_focus(self):
        """获取当前焦点类和属性"""
        if not self.current_chapter:
            return None, []
        return (
            self.chapter_focus.get(self.current_chapter),
            self.focus_attributes.get(self.current_chapter, [])
        )


# LLM约束提取器
class LLMConstraintExtractor:
    """使用LLM从AUTOSAR文档中提取约束"""

    def __init__(self, api_key, model, debug=True):
        """初始化LLM约束提取器"""
        self.api_key = api_key
        self.model = model
        self.chapter_tracker = ChapterTracker()
        self.debug = debug

        # 创建调试目录
        if self.debug:
            os.makedirs("debug", exist_ok=True)

        # 正则表达式模式
        self.chapter_pattern = re.compile(r'#@chapter-([0-9.]+)')

        # 直接约束提取模式 - 优化为用户指定的精确格式
        self.constraint_pattern = re.compile(
            r'\[((?:constr|TPS_SWCT)_[^\]]+)\]\s*([^\(]+)\s*\(cid:100\)\s*(.*?)\s*\(cid:99\)(?:\s*\(([^)]*)\))?',
            re.DOTALL
        )

        # 类名识别模式
        self.class_pattern = re.compile(r'\b([A-Z][a-zA-Z0-9]+(?:[A-Z][a-zA-Z0-9]+)*)\b(?:\s*\([^)]*\))?')
        self.class_def_pattern = re.compile(r'\b([A-Z][a-zA-Z0-9]+(?:[A-Z][a-zA-Z0-9]+)*)\s*\([^\)]*\)')

        # 属性识别模式
        self.attribute_pattern = re.compile(r'\b([a-z][a-zA-Z0-9]+)\s*\|\s*([A-Z][a-zA-Z0-9]+)')

    def preprocess_text(self, text):
        """预处理文本，修复格式问题"""
        # 处理行尾连字符
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

        # 处理无连字符但明显被分割的单词
        text = re.sub(r'(\w{3,})\s*\n\s*(\w{2,})',
                      lambda m: m.group(1) + m.group(2)
                      if m.group(1)[-1].islower() and m.group(2)[0].islower()
                      else m.group(0), text)

        # 标准化约束格式中的cid标记
        text = re.sub(r'\(cid:100\)', ' (cid:100) ', text)
        text = re.sub(r'\(cid:99\)', ' (cid:99) ', text)

        # 清理干扰内容
        patterns = [
            (r"\b\d+\s+of\s+\d+\b", ""),  # 页码
            (r"Document ID \d+:.*?(?=\n|$)", ""),  # 文档ID
            (r"note \d+:.*?(?=\n|$)", ""),  # note
            (r"— AUTOSAR CONFIDENTIAL —", ""),  # 保密标记
            (r"Software Component Template\s*\nAUTOSAR Release \d+\.\d+\.\d+", ""),  # 文档头
            (r"\n{3,}", "\n\n")  # 规范化空行
        ]

        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text, flags=re.I)

        return text.strip()

    def _estimate_tokens(self, text):
        """估计文本的token数量"""
        return int(len(text.split()) * 1.3)

    def split_into_chunks(self, text, max_tokens=2000, overlap=400):
        """将文本分割成多个块，保持章节和约束的完整性"""
        lines = text.splitlines()
        chunks = []
        current_chunk = []
        current_token_count = 0

        i = 0
        while i < len(lines):
            line = lines[i]
            line_tokens = self._estimate_tokens(line) + 1  # +1 for newline

            # 检查是否是约束开始
            is_constraint_start = bool(re.match(r'^\s*\[(constr|TPS_SWCT)_', line))

            # 如果是新章节且当前块非空，则开始新块
            if self.chapter_pattern.match(line) and current_chunk:
                chunks.append('\n'.join(current_chunk))

                # 保留部分内容作为重叠
                if len(current_chunk) > 5:  # 至少保留5行
                    overlap_lines = current_chunk[-overlap // 20:]  # 大约overlap tokens
                    current_chunk = overlap_lines + [line]
                    current_token_count = sum(self._estimate_tokens(l) + 1 for l in current_chunk)
                else:
                    current_chunk = [line]
                    current_token_count = line_tokens

                i += 1
                continue

            # 如果当前行是约束开始且当前块即将超过阈值，则开始新块
            if is_constraint_start and current_token_count > max_tokens * 0.7 and current_chunk:
                chunks.append('\n'.join(current_chunk))

                # 保留部分内容作为重叠
                if len(current_chunk) > 5:
                    overlap_lines = current_chunk[-overlap // 20:]
                    current_chunk = overlap_lines
                    current_token_count = sum(self._estimate_tokens(l) + 1 for l in current_chunk)
                else:
                    current_chunk = []
                    current_token_count = 0

                # 不递增i，这样约束标记行将被添加到新块
                continue

            # 检查是否需要找到约束结束标记
            if is_constraint_start:
                # 记录当前行
                current_chunk.append(line)
                current_token_count += line_tokens
                i += 1

                # 找到约束结束 (cid:99) 和可能的引用
                constraint_complete = False
                while i < len(lines) and not constraint_complete:
                    constraint_line = lines[i]

                    # 添加行
                    current_chunk.append(constraint_line)
                    current_token_count += self._estimate_tokens(constraint_line) + 1

                    # 检查是否包含结束标记
                    if "(cid:99)" in constraint_line:
                        # 再添加一行以捕获可能的引用
                        if i + 1 < len(lines) and "(" in lines[i + 1] and ")" in lines[i + 1] and not lines[
                            i + 1].strip().startswith("["):
                            i += 1
                            current_chunk.append(lines[i])
                            current_token_count += self._estimate_tokens(lines[i]) + 1

                        constraint_complete = True

                    i += 1

                continue

            # 如果添加当前行会超过最大token数，则开始新块
            if current_token_count + line_tokens > max_tokens and current_chunk:
                chunks.append('\n'.join(current_chunk))

                # 保留部分内容作为重叠
                if len(current_chunk) > 5:
                    overlap_lines = current_chunk[-overlap // 20:]
                    current_chunk = overlap_lines
                    current_token_count = sum(self._estimate_tokens(l) + 1 for l in current_chunk)
                else:
                    current_chunk = []
                    current_token_count = 0

                # 不递增i，当前行将被添加到新块
                continue

            # 正常添加行
            current_chunk.append(line)
            current_token_count += line_tokens
            i += 1

        # 添加最后一个块
        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks

    def update_context_from_chunk(self, chunk, chunk_index):
        """从块中更新章节和焦点信息"""
        lines = chunk.splitlines()

        # 处理每一行更新章节和焦点
        for line in lines:
            # 检查章节标记
            chapter_match = self.chapter_pattern.search(line)
            if chapter_match:
                chapter_id = chapter_match.group(1)
                self.chapter_tracker.update_chapter(chapter_id)

            # 识别类定义 - 多种模式

            # 1. 表格风格: "ClassName (abstract)"
            class_def_match = self.class_def_pattern.search(line)
            if class_def_match:
                class_name = class_def_match.group(1)
                self.chapter_tracker.update_focus_class(class_name)
                continue

            # 2. 表格式的类定义中的类名
            if line.strip() and line.strip()[0].isupper():
                words = line.split()
                if words and len(words[0]) > 2 and self.chapter_tracker._is_valid_class_name(words[0]):
                    self.chapter_tracker.update_focus_class(words[0])

            # 3. 从"Class X"或"The X class"模式中识别
            class_patterns = [
                r'\bclass\s+([A-Z][a-zA-Z0-9]+)',
                r'The\s+([A-Z][a-zA-Z0-9]+)\s+class',
                r'A\s+([A-Z][a-zA-Z0-9]+)\s+is'
            ]
            for pattern in class_patterns:
                match = re.search(pattern, line, re.I)
                if match:
                    class_name = match.group(1)
                    self.chapter_tracker.update_focus_class(class_name)

            # 属性识别

            # 1. 明确的属性引用
            attr_patterns = [
                r'\battribute\s+([a-z][a-zA-Z0-9]+)',
                r'\bproperty\s+([a-z][a-zA-Z0-9]+)',
                r'\bthe\s+([a-z][a-zA-Z0-9]+)\s+attribute'
            ]

            for pattern in attr_patterns:
                for match in re.finditer(pattern, line, re.I):
                    attr_name = match.group(1)
                    self.chapter_tracker.add_focus_attribute(attr_name)

            # 2. 表格中的属性
            attr_table_match = self.attribute_pattern.search(line)
            if attr_table_match:
                attr_name = attr_table_match.group(1)
                self.chapter_tracker.add_focus_attribute(attr_name)

            # 3. 可能的属性行 - 首列是小写开头的单词
            if line.strip() and line.strip()[0].islower():
                words = line.split()
                if words and len(words[0]) > 2:
                    potential_attr = words[0].strip()
                    if self.chapter_tracker._is_valid_attribute_name(potential_attr):
                        self.chapter_tracker.add_focus_attribute(potential_attr)

        # 保存块的焦点信息
        self.chapter_tracker.save_chunk_focus(chunk_index)

        # 返回当前焦点信息
        return self.chapter_tracker.get_current_focus()

    def extract_constraints_with_regex(self, chunk, focus_class=None, focus_attrs=None):
        """使用正则表达式提取约束"""
        constraints = []

        # 使用更精确的模式匹配约束
        for match in self.constraint_pattern.finditer(chunk):
            constraint_id = match.group(1)
            title = match.group(2).strip() if match.group(2) else ""
            body = match.group(3).strip() if match.group(3) else ""
            refs_str = match.group(4) or ""

            # 提取引用ID
            reference_ids = []
            if refs_str:
                reference_ids = [
                    ref.strip()
                    for ref in re.split(r',\s*', refs_str)
                    if ref.strip()
                ]

            # 从约束正文中尝试提取目标类和属性
            target_class = focus_class
            target_attr = focus_attrs[0] if focus_attrs else ""

            # 在约束中查找类名提及
            class_mentions = list(self.class_pattern.finditer(body))
            if class_mentions and not target_class:
                # 使用约束中提到的第一个类名
                target_class = class_mentions[0].group(1)

            # 在约束中查找属性名提及
            attr_matches = re.finditer(r'\b([a-z][a-zA-Z0-9]+)\s+(?:attribute|property|field)', body, re.I)
            attr_mentions = [m.group(1) for m in attr_matches]

            if attr_mentions and not target_attr:
                target_attr = attr_mentions[0]

            # 确定约束类型
            constraint_type = "GENERIC"

            if "must have" in body.lower() or "shall have" in body.lower() or "is required" in body.lower():
                constraint_type = "mustHave"
            elif "maximum" in body.lower() or "at most" in body.lower() or "no more than" in body.lower():
                constraint_type = "maxCardinality"
            elif "minimum" in body.lower() or "at least" in body.lower() or "no less than" in body.lower():
                constraint_type = "minCardinality"
            elif "equal to" in body.lower() or "same as" in body.lower() or "equivalent" in body.lower():
                constraint_type = "equivalence"
            elif "if" in body.lower() and "then" in body.lower():
                constraint_type = "conditionalExistence"

            # 构建约束对象
            constraint = {
                "id": constraint_id,
                "type": constraint_type,
                "title": title,
                "body": body,
                "targetClass": target_class or "",
                "targetAttribute": target_attr,
                "reference_ids": reference_ids,
                "confidence": 0.9  # 正则表达式匹配格式的约束具有较高置信度
            }

            constraints.append(constraint)

        return constraints

    async def extract_constraints_from_text(self, chunk, focus_info, chunk_index):
        """使用多种方法从文本中提取约束"""
        focus_class, focus_attrs = focus_info

        # 保存调试信息
        if self.debug:
            chunk_hash = hashlib.md5(chunk.encode()).hexdigest()[:8]
            with open(f"debug/chunk_{chunk_index}_{chunk_hash}.txt", "w", encoding="utf-8") as f:
                f.write(f"焦点类: {focus_class}\n")
                f.write(f"焦点属性: {', '.join(focus_attrs) if focus_attrs else '无'}\n")
                f.write("\n--- 块内容 ---\n")
                f.write(chunk)

        # 首先尝试正则表达式直接匹配
        regex_constraints = self.extract_constraints_with_regex(chunk, focus_class, focus_attrs)
        if regex_constraints:
            logger.info(f"通过正则表达式从块 {chunk_index + 1} 中提取了 {len(regex_constraints)} 个约束")
            return regex_constraints

        # 如果正则表达式没有找到约束，尝试使用LLM
        logger.info(f"尝试使用LLM从块 {chunk_index + 1} 中提取约束")

        # 构建明确的提示
        system_prompt = """
        你是AUTOSAR规范分析专家。你的任务是识别并提取文档中的约束和规范。

        约束和规范的格式严格如下：
        [constr_**] title (cid:100) detail (cid:99) (reference id)
        或
        [TPS_SWCT_**] title (cid:100) detail (cid:99) (reference id)

        其中：
        - [constr_**]或[TPS_SWCT_**]是约束ID
        - title是约束标题
        - (cid:100)标记详细内容开始
        - detail是约束的详细内容
        - (cid:99)标记详细内容结束
        - (reference id)是可选的引用其他约束的ID列表

        请提取每个约束的以下信息：
        1. id：约束ID，不含方括号
        2. type：约束类型，如mustHave、maxCardinality等
        3. title：约束标题
        4. body：约束详细内容
        5. targetClass：约束的目标类
        6. targetAttribute：约束的目标属性
        7. reference_ids：引用的其他约束ID列表

        例如，从以下文本：
        [constr_123] 属性限制 (cid:100) PortPrototype必须包含clientServerAnnotation属性 (cid:99) (RS_456)

        应提取：
        {
          "id": "constr_123",
          "type": "mustHave",
          "title": "属性限制",
          "body": "PortPrototype必须包含clientServerAnnotation属性",
          "targetClass": "PortPrototype",
          "targetAttribute": "clientServerAnnotation",
          "reference_ids": ["RS_456"]
        }
        """

        user_prompt = f"""
        当前焦点信息：
        - 焦点类: {focus_class if focus_class else "未识别"}
        - 焦点属性: {', '.join(focus_attrs) if focus_attrs else "未识别"}

        请从以下文本中提取所有符合格式的约束和规范，格式为[constr_**] title (cid:100) detail (cid:99)(reference id)或[TPS_SWCT_**] title (cid:100) detail (cid:99)(reference id)：

        {chunk}

        如果未找到完全符合格式的约束，可以提取部分符合格式的约束。如果约束中未明确提及目标类或属性，请使用提供的焦点信息。

        以JSON数组格式返回结果：
        ```json
        [
          {
        "id": "约束ID",
            "type": "约束类型",
            "title": "约束标题",
            "body": "约束详细内容",
            "targetClass": "目标类",
            "targetAttribute": "目标属性",
            "reference_ids": ["引用ID1", "引用ID2"]
          }
        ]
        ```
        """

        try:
            # 调用DeepSeek API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        "https://api.deepseek.com/chat/completions",
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {self.api_key}"
                        },
                        json={
                            "model": self.model,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            "temperature": 0
                        }
                ) as response:
                    response_text = await response.text()

                    # 保存完整原始响应用于调试
                    if self.debug:
                        with open(f"debug/raw_response_{chunk_index}_{chunk_hash}.txt", "w", encoding="utf-8") as f:
                            f.write(response_text)

                    # 解析响应
                    try:
                        result = json.loads(response_text)

                        # 保存格式化的API响应
                        if self.debug:
                            with open(f"debug/response_{chunk_index}_{chunk_hash}.json", "w", encoding="utf-8") as f:
                                json.dump(result, f, indent=2)

                        # 提取约束
                        if "choices" in result and len(result["choices"]) > 0:
                            content = result["choices"][0]["message"]["content"]

                            # 保存格式化内容
                            if self.debug:
                                with open(f"debug/content_{chunk_index}_{chunk_hash}.txt", "w", encoding="utf-8") as f:
                                    f.write(content)

                            # 查找JSON部分
                            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content, re.DOTALL)
                            if json_match:
                                json_str = json_match.group(1).strip()
                            else:
                                # 尝试直接解析整个内容
                                json_str = content

                            # 清理JSON字符串
                            json_str = json_str.replace('\n', ' ').replace('\r', '')
                            json_str = re.sub(r'[\t ]+', ' ', json_str)

                            try:
                                constraints = json.loads(json_str)
                                if isinstance(constraints, list):
                                    # 应用焦点信息到每个约束
                                    for constraint in constraints:
                                        if not constraint.get("targetClass") and focus_class:
                                            constraint["targetClass"] = focus_class
                                            constraint["confidence"] = 0.8
                                        else:
                                            constraint["confidence"] = 0.9

                                        if not constraint.get("targetAttribute") and focus_attrs:
                                            constraint["targetAttribute"] = focus_attrs[0] if focus_attrs else ""

                                    logger.info(f"通过LLM从块 {chunk_index + 1} 中提取了 {len(constraints)} 个约束")
                                    return constraints
                                else:
                                    logger.warning(f"LLM未返回列表格式: {json_str[:100]}...")
                            except json.JSONDecodeError as e:
                                logger.error(f"JSON解析错误: {e}, 内容: {json_str[:100]}...")
                    except json.JSONDecodeError as e:
                        logger.error(f"API响应解析错误: {e}, 内容: {response_text[:100]}...")

            # 如果以上方法都失败，尝试最后的回退解析方式
            logger.warning(f"尝试手动解析块 {chunk_index + 1} 的内容")
            manual_constraints = self._manual_constraint_parsing(chunk, focus_class, focus_attrs)
            if manual_constraints:
                logger.info(f"通过手动解析从块 {chunk_index + 1} 中提取了 {len(manual_constraints)} 个约束")
                return manual_constraints

            # 所有方法都失败
            logger.warning(f"无法从块 {chunk_index + 1} 中提取约束")
            return []

        except Exception as e:
            logger.error(f"处理块 {chunk_index + 1} 出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def _manual_constraint_parsing(self, chunk, focus_class, focus_attrs):
        """最后的回退：手动解析约束"""
        constraints = []

        # 查找所有可能的约束ID
        id_matches = re.finditer(r'\[((?:constr|TPS_SWCT)_[^\]]+)\]', chunk)

        for id_match in id_matches:
            constraint_id = id_match.group(1)
            start_pos = id_match.end()

            # 查找约束标题（到第一个cid:100之前的文本）
            title_match = re.search(r'(.*?)\(cid:100\)', chunk[start_pos:], re.DOTALL)
            if not title_match:
                continue

            title = title_match.group(1).strip()
            body_start = start_pos + title_match.end()

            # 查找约束主体（从cid:100到cid:99之间的文本）
            body_match = re.search(r'\(cid:100\)(.*?)\(cid:99\)', chunk[start_pos:], re.DOTALL)
            if not body_match:
                continue

            body = body_match.group(1).strip()
            body_end = start_pos + body_match.end()

            # 查找可能的引用（在cid:99后面的括号内）
            refs = []
            ref_match = re.search(r'\(cid:99\)\s*\((.*?)\)', chunk[start_pos:], re.DOTALL)
            if ref_match:
                refs_text = ref_match.group(1).strip()
                refs = [ref.strip() for ref in refs_text.split(',') if ref.strip()]

            # 构建约束
            constraint = {
                "id": constraint_id,
                "type": "GENERIC",
                "title": title,
                "body": body,
                "targetClass": focus_class or "",
                "targetAttribute": focus_attrs[0] if focus_attrs else "",
                "reference_ids": refs,
                "confidence": 0.7  # 手动解析的置信度较低
            }

            constraints.append(constraint)

        return constraints

    async def process_file(self, file_path, output_dir):
        """处理单个文件"""
        try:
            file_name = Path(file_path).stem
            logger.info(f"开始处理文件: {file_path}")

            # 读取文件
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()

            # 预处理文本
            text = self.preprocess_text(text)

            # 保存预处理后的文本（用于调试）
            if self.debug:
                with open(f"debug/{file_name}_preprocessed.txt", "w", encoding="utf-8") as f:
                    f.write(text)

            # 分块
            chunks = self.split_into_chunks(text)
            logger.info(f"文件 {file_path} 被分割为 {len(chunks)} 个块")

            # 第一次遍历更新上下文
            for i, chunk in enumerate(chunks):
                self.update_context_from_chunk(chunk, i)

            # 第二次遍历提取约束
            all_constraints = []

            # 准备并行处理任务
            tasks = []
            for i, chunk in enumerate(chunks):
                focus_info = self.chapter_tracker.get_focus_for_chunk(i)
                tasks.append(self.extract_constraints_from_text(chunk, focus_info, i))

            # 并行获取结果
            chunk_results = await asyncio.gather(*tasks)

            # 处理结果
            for i, constraints in enumerate(chunk_results):
                logger.info(f"从块 {i + 1} 中提取了 {len(constraints)} 个约束")

                for constraint in constraints:
                    # 创建ConstraintRaw对象
                    constraint_obj = ConstraintRaw(
                        id=constraint.get("id", "UNKNOWN"),
                        type=constraint.get("type", "GENERIC"),
                        title=constraint.get("title", ""),
                        body=constraint.get("body", ""),
                        targetClass=constraint.get("targetClass", ""),
                        targetAttribute=constraint.get("targetAttribute", ""),
                        value=constraint.get("value"),
                        scope=constraint.get("scope", {}),
                        confidence=constraint.get("confidence", 0.0),
                        reference_ids=constraint.get("reference_ids", [])
                    )

                    all_constraints.append(constraint_obj)

            # 合并重复约束
            unique_constraints = self._merge_duplicate_constraints(all_constraints)

            # 输出结果
            output_file = Path(output_dir) / f"{file_name}_constraints.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(c) for c in unique_constraints], f, ensure_ascii=False, indent=2)

            logger.info(f"文件 {file_path} 处理完成，提取 {len(unique_constraints)} 个约束")
            return unique_constraints

        except Exception as e:
            logger.error(f"处理文件 {file_path} 时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def _merge_duplicate_constraints(self, constraints):
        """合并重复的约束"""
        constraint_map = {}

        for constraint in constraints:
            if constraint.id in constraint_map:
                # 选择置信度更高的约束
                if constraint.confidence > constraint_map[constraint.id].confidence:
                    constraint_map[constraint.id] = constraint

                # 合并引用ID
                existing_refs = set(constraint_map[constraint.id].reference_ids)
                for ref in constraint.reference_ids:
                    if ref not in existing_refs:
                        constraint_map[constraint.id].reference_ids.append(ref)
            else:
                constraint_map[constraint.id] = constraint

        return list(constraint_map.values())

    async def process_directory(self, input_dir, output_dir):
        """处理目录中的所有文件"""
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 获取所有markdown文件
        files = list(Path(input_dir).glob("**/*.md"))
        logger.info(f"发现 {len(files)} 个markdown文件")

        all_constraints = []

        # 处理每个文件
        for file_path in files:
            constraints = await self.process_file(file_path, output_dir)
            all_constraints.extend(constraints)

        # 输出所有约束到单个JSONL文件
        output_jsonl = Path(output_dir) / "constraints_raw.jsonl"
        with open(output_jsonl, 'w', encoding='utf-8') as f:
            for constraint in all_constraints:
                f.write(json.dumps(asdict(constraint), ensure_ascii=False) + "\n")

        logger.info(f"总共提取 {len(all_constraints)} 个约束，已保存到 {output_jsonl}")

        # 输出统计信息
        self._output_statistics(all_constraints, output_dir)

        return all_constraints

    def _output_statistics(self, constraints, output_dir):
        """输出约束统计信息"""
        # 按类型统计
        type_stats = {}
        for c in constraints:
            c_type = c.type
            type_stats[c_type] = type_stats.get(c_type, 0) + 1

        # 按目标类统计
        class_stats = {}
        for c in constraints:
            c_class = c.targetClass or "UNKNOWN"
            class_stats[c_class] = class_stats.get(c_class, 0) + 1

        # 置信度分布
        confidence_buckets = {
            "high (0.8-1.0)": 0,
            "medium (0.5-0.8)": 0,
            "low (0.0-0.5)": 0
        }

        for c in constraints:
            conf = c.confidence
            if conf >= 0.8:
                confidence_buckets["high (0.8-1.0)"] += 1
            elif conf >= 0.5:
                confidence_buckets["medium (0.5-0.8)"] += 1
            else:
                confidence_buckets["low (0.0-0.5)"] += 1

        # 输出统计数据
        stats = {
            "total_constraints": len(constraints),
            "type_distribution": type_stats,
            "class_distribution": {k: v for k, v in
                                   sorted(class_stats.items(), key=lambda item: item[1], reverse=True)[:20]},
            "confidence_distribution": confidence_buckets
        }

        stats_file = Path(output_dir) / "extraction_stats.json"
        with open(stats_file, 'w', encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        logger.info(f"统计信息已保存到 {stats_file}")


# 主函数
async def main(input_path, output_path):
    """主函数"""
    api_key = "sk-efc873f59a9643e59864347dd502505f"
    if not api_key:
        logger.error("未设置OPENAI_API_KEY环境变量")
        return

    extractor = LLMConstraintExtractor(api_key=api_key, model="deepseek-chat")
    await extractor.process_directory(input_path, output_path)


if __name__ == "__main__":

    input_dir = "input"
    output_dir = "output"

    asyncio.run(main(input_dir, output_dir))