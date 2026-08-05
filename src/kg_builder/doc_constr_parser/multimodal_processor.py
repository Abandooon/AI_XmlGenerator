import base64
import json
import os
import re
from typing import Dict, List, Optional

import requests

from config import (
    LLM_API_KEY, LLM_API_BASE, LLM_MODEL_NAME,
    MAX_OUTPUT_TOKENS,
    INPUT_DIR, MD_FILENAME, OUTPUT_DIR, UNIFIED_METADATA_FILENAME
)


# ────────────────────────────────────────────────────────────────
# 辅助函数：从 unified_metadata.json 提取 SWC 相关类名
# ────────────────────────────────────────────────────────────────
def load_autosar_classes_from_metadata(metadata_file_path: str) -> List[str]:
    """
    Parse `unified_metadata.json` and return all AUTOSAR class names that
    are under package path ["AUTOSAR Templates", "SWComponentTemplate"].
    """
    autosar_classes: set[str] = set()
    try:
        with open(metadata_file_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        if not isinstance(metadata.get("groups"), dict):
            print(f"Warning: 'groups' not found or invalid in {metadata_file_path}")
            return []

        for group in metadata["groups"].values():
            if (
                isinstance(group, dict)
                and isinstance(group.get("Package"), list)
                and len(group["Package"]) >= 2
                and group["Package"][:2] == ["AUTOSAR Templates", "SWComponentTemplate"]
            ):
                autosar_classes.add(group.get("name", ""))
        classes_sorted = sorted(c for c in autosar_classes if c)
        print(f"Loaded {len(classes_sorted)} AUTOSAR UML classes from metadata.")
        if classes_sorted:
            print(f"Sample classes: {classes_sorted[:5]}")
        return classes_sorted

    except FileNotFoundError:
        print(f"Error: metadata file '{metadata_file_path}' not found.")
    except json.JSONDecodeError:
        print(f"Error: failed to parse JSON from '{metadata_file_path}'.")
    except Exception as e:
        print(f"Unexpected error while loading class names: {e}")
    return []

class AutosarImageFactExtractor:
    def __init__(self) -> None:
        """Initialise extractor."""
        self.api_key: str = LLM_API_KEY
        self.model_name: str = LLM_MODEL_NAME
        self.api_base: str = LLM_API_BASE
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        metadata_filepath = os.path.join(INPUT_DIR, UNIFIED_METADATA_FILENAME)
        self.autosar_terms: List[str] = load_autosar_classes_from_metadata(
            metadata_filepath
        )

    # ───────────── 基础工具 ─────────────
    @staticmethod
    def encode_image(image_path: str) -> str:
        with open(image_path, "rb") as img:
            return base64.b64encode(img.read()).decode("utf-8")

    @staticmethod
    def extract_identifier_from_filename(filename: str) -> Optional[str]:
        """Extract figure/table id like f2.7 or t5.4 from filename."""
        stem = os.path.splitext(filename)[0]
        return stem.lower() if re.fullmatch(r"[ft]\d+\.\d+", stem, re.I) else None

    # ───────────── OpenAI 调用 ─────────────
    def call_llm_api(self, image_path: str, identifier: str) -> str:
        """
        Call multimodal LLM to analyse AUTOSAR figure / table.
        Always returns English content.
        """
        try:
            base64_img = self.encode_image(image_path)
            is_table = identifier.startswith("t")

            # -------- prompt 构造 --------
            autosar_glossary = (
                ", ".join(self.autosar_terms[:80]) + " ..."
                if self.autosar_terms
                else "N/A"
            )

            if is_table:
                autosar_prompt = (
                    "You are an AUTOSAR domain expert.\n\n"
                    "Task: Extract the table contained in this AUTOSAR SWC specification "
                    "figure and convert it into GitHub-flavoured Markdown. "
                    "Keep header rows, all rows, and cell content verbatim. "
                    "Do NOT add commentary or explanations.\n\n"
                    f"Reference UML class glossary (partial): {autosar_glossary}"
                )
            else:
                autosar_prompt = (
                    "You are an AUTOSAR domain expert.\n\n"
                    "Analyse the following AUTOSAR SWC architecture diagram and summarise its "
                    "structure in **concise English**.\n\n"
                    "Focus points:\n"
                    "1. Component hierarchy – identify SW-components and their relationships.\n"
                    "2. Ports & interfaces – list RPort/PPort, data interfaces and connections.\n"
                    "3. Data flow – describe communication patterns between components.\n"
                    "4. Key AUTOSAR concepts – prototypes, interfaces, modes, etc.\n"
                    "5. Scenario – briefly state the use-case or design intent expressed by the diagram.\n\n"
                    "Output format (strict):\n"
                    "- A short paragraph (≤150 words) describing the diagram purpose.\n"
                    "- A bullet list capturing the five focus points above.\n"
                    "Avoid translating labels; use the original technical terms when possible.\n\n"
                    f"Reference UML class glossary (partial): {autosar_glossary}"
                )

            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": autosar_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"},
                            },
                        ],
                    }
                ],
                "max_completion_tokens": MAX_OUTPUT_TOKENS,
                "temperature": 0.1,
            }

            api_url = f"{self.api_base}/chat/completions"
            resp = requests.post(api_url, headers=self.headers, json=payload, timeout=60)

            if resp.status_code != 200:
                print(f"HTTP {resp.status_code}: {resp.text}")
            resp.raise_for_status()

            return resp.json()["choices"][0]["message"]["content"].strip()

        except Exception as e:
            print(f"❌ LLM call failed for {image_path}: {e}")
            return f"Image analysis failed: {e}"

    def process_images(self, figures_dir: str) -> Dict[str, str]:
        """
        处理figures目录下的所有图片

        Args:
            figures_dir: 图片目录路径

        Returns:
            字典，键为标识符，值为提取的结构化信息
        """
        image_facts = {}

        if not os.path.exists(figures_dir):
            print(f"错误: 目录 {figures_dir} 不存在")
            return image_facts

        # 支持的图片格式
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg'}

        # 获取所有图片文件并排序
        image_files = []
        for filename in os.listdir(figures_dir):
            file_path = os.path.join(figures_dir, filename)

            if not os.path.isfile(file_path):
                continue

            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext not in image_extensions:
                continue

            # 检查文件名格式
            identifier = self.extract_identifier_from_filename(filename)
            if identifier:
                image_files.append((filename, identifier))

        # 按标识符排序
        image_files.sort(key=lambda x: x[1])

        print(f"发现 {len(image_files)} 个符合命名规范的图片文件")

        for filename, identifier in image_files:
            file_path = os.path.join(figures_dir, filename)

            print(f"处理AUTOSAR图片: {filename} (标识符: {identifier})")

            # 调用LLM提取信息
            structured_info = self.call_llm_api(file_path, identifier)
            image_facts[identifier] = structured_info

            print(f"完成: {identifier}")

        return image_facts

    def find_insertion_points(self, content: str) -> Dict[str, int]:
        """
        在Markdown内容中找到图表标题的插入点 (固定格式: Figure/Table x.x: title)

        Args:
            content: Markdown文档内容

        Returns:
            字典，键为标识符，值为插入位置的行号
        """
        lines = content.split('\n')
        insertion_points = {}

        for i, line in enumerate(lines):
            # 严格匹配格式: Figure/Table x.x: title
            figure_match = re.search(r'Figure\s+(\d+)\.(\d+):', line)
            table_match = re.search(r'Table\s+(\d+)\.(\d+):', line)

            if figure_match:
                major, minor = figure_match.groups()
                identifier = f"f{major}.{minor}"
                insertion_points[identifier] = i
            elif table_match:
                major, minor = table_match.groups()
                identifier = f"t{major}.{minor}"
                insertion_points[identifier] = i

        return insertion_points

    def inject_image_facts(self, markdown_file: str, image_facts: Dict[str, str], output_file: str = None) -> bool:
        """
        将图片事实注入到Markdown文档中。
        只为 image_facts 中存在的图片（即目录中实际处理过的图片）查找插入点并注入。

        Args:
            markdown_file: 输入的Markdown文件路径
            image_facts: 图片事实字典 (键为标识符，值为提取的结构化信息)
            output_file: 输出文件路径，如果为None则覆盖原文件

        Returns:
            是否成功
        """
        try:
            # 读取Markdown文件
            with open(markdown_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 找到Markdown中所有的图表引用位置，备用
            all_insertion_points = self.find_insertion_points(content)
            print(f"在Markdown文档中发现 {len(all_insertion_points)} 个图表引用位置。")

            # 转换为行列表
            lines = content.split('\n')

            # 为了按行号倒序插入，我们需要先收集所有需要注入的点及其行号
            injection_tasks = []
            for identifier, fact_info in image_facts.items():
                if identifier in all_insertion_points:
                    line_num = all_insertion_points[identifier]
                    injection_tasks.append({'identifier': identifier, 'line_num': line_num, 'fact_info': fact_info})
                else:
                    # 警告：图片处理了，但在Markdown中没有找到对应的引用位置
                    print(
                        f"警告: 处理了图片 {identifier}，但在Markdown文档中未找到其对应的引用位置 (如 'Figure/Table X.Y: ...')。")

            if not injection_tasks:
                print("没有在Markdown文档中找到任何已处理图片的对应插入位置。")
                # 根据需求，这里可以选择是否依然生成输出文件（可能是原样复制，或不生成）
                # 为了保持与原逻辑相似，我们依然尝试写入，即使没有注入任何内容
                # 如果希望在这种情况下不生成增强文件，可以在这里返回或采取其他操作

            # 按行号倒序排序，避免插入时行号偏移
            sorted_injection_tasks = sorted(injection_tasks, key=lambda x: x['line_num'], reverse=True)

            # 注入信息
            injected_count = 0
            for task in sorted_injection_tasks:
                identifier = task['identifier']
                line_num = task['line_num']
                fact_info = task['fact_info']

                # 构建注入文本
                injection_text = f"<-------------- multimodal context {fact_info} ---------------------->"

                # 在指定行上方插入
                lines.insert(line_num, injection_text)
                lines.insert(line_num, "")  # 添加空行保持格式

                injected_count += 1
                print(f"已注入: {identifier} (来自已处理的图片) -> 行 {line_num + 1}")

            # 生成输出文件路径
            if output_file is None:
                base_name = os.path.splitext(markdown_file)[0]
                output_file = f"{base_name}_enhanced.md"

            # 确保输出目录存在
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 写入文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))

            print(f"完成注入，共为 {injected_count} 个在目录中找到并处理的图片注入了信息。")

            # 更新处理结果摘要
            # missing_images 现在应该反映的是 Markdown 中引用了但 figures 目录中没有对应图片的情况
            # unused_images 现在应该反映的是 figures 目录中处理了但 Markdown 中没有引用的情况

            # Markdown中引用但未在figures目录中找到或处理的图表
            markdown_referenced_ids = set(all_insertion_points.keys())
            processed_image_ids = set(image_facts.keys())

            missing_from_figures = list(markdown_referenced_ids - processed_image_ids)
            # Figures目录中处理了但未在Markdown中找到引用的图表
            unused_in_markdown = list(processed_image_ids - markdown_referenced_ids)

            summary = {
                "source_file": markdown_file,
                "output_file": output_file,
                "processed_images_from_directory": len(image_facts),  # 实际从目录处理的图片数
                "injected_into_markdown_count": injected_count,  # 成功注入到MD的数量
                "markdown_references_not_found_in_figures": missing_from_figures,  # MD中引用但figures目录无对应
                "processed_images_not_referenced_in_markdown": unused_in_markdown  # figures目录处理了但MD无对应引用
            }

            summary_file = os.path.join(os.path.dirname(output_file), "enhancement_summary.json")
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)

            return True

        except FileNotFoundError:
            print(f"注入过程出错: Markdown文件 {markdown_file} 未找到。请检查路径和文件名。")
            return False
        except Exception as e:
            print(f"注入过程出错: {str(e)}")
            return False

    def run(self, figures_dir: str = None, markdown_file: str = None, output_file: str = None):
        """
        运行完整的AUTOSAR图片处理流程

        Args:
            figures_dir: 图片目录
            markdown_file: Markdown文件路径
            output_file: 输出文件路径
        """
        # 使用配置文件中的默认路径
        if figures_dir is None:
            figures_dir = os.path.join(INPUT_DIR, "figures")

        if markdown_file is None:
            markdown_file = os.path.join(INPUT_DIR, MD_FILENAME)

        if output_file is None:
            output_file = os.path.join(OUTPUT_DIR, f"{os.path.splitext(MD_FILENAME)[0]}_enhanced.md")

        print("开始处理AUTOSAR SWC规范文档...")
        print(f"图片目录: {figures_dir}")
        print(f"源文档: {markdown_file}")
        print(f"输出文档: {output_file}")

        # 检查API配置
        if not self.api_key:
            print("错误: 未配置LLM_API_KEY")
            return

        # 第一步：处理图片
        print("\n1. 处理AUTOSAR图片并提取结构化信息...")
        image_facts = self.process_images(figures_dir)

        if not image_facts:
            print("未找到任何符合命名规范的图片文件")
            return

        print(f"成功处理 {len(image_facts)} 张AUTOSAR图片")

        # 第二步：注入到Markdown文档
        print("\n2. 注入信息到AUTOSAR规范文档...")
        success = self.inject_image_facts(markdown_file, image_facts, output_file)

        if success:
            print(f"\n✅ AUTOSAR文档增强完成！")
            print(f"输出文件: {output_file}")
            print(f"处理摘要: {os.path.join(os.path.dirname(output_file), 'enhancement_summary.json')}")
        else:
            print("\n❌ 处理失败")


def main():
    """主函数"""
    print("AUTOSAR SWC规范文档图片增强工具")
    print("=" * 50)

    # 初始化提取器
    extractor = AutosarImageFactExtractor()

    # 运行处理流程
    extractor.run()


if __name__ == "__main__":
    main()