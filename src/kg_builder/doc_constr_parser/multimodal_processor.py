import os
import re
import json
import base64
from typing import Dict, List, Tuple, Optional
import requests
from pathlib import Path
from config import (
    LLM_API_KEY, LLM_API_BASE, LLM_MODEL_NAME,
    MAX_OUTPUT_TOKENS,
    INPUT_DIR, MD_FILENAME, OUTPUT_DIR
)


class AutosarImageFactExtractor:
    def __init__(self):
        """
        初始化AUTOSAR图片事实提取器
        """
        self.api_key = LLM_API_KEY
        self.model_name = LLM_MODEL_NAME
        self.api_base = LLM_API_BASE
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def encode_image(self, image_path: str) -> str:
        """将图片编码为base64格式"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def extract_identifier_from_filename(self, filename: str) -> Optional[str]:
        """
        从文件名中提取标识符 (固定格式: t/fx.x)

        Args:
            filename: 图片文件名

        Returns:
            标识符，如 "f2.7", "t5.74" 等
        """
        # 移除文件扩展名
        name_without_ext = os.path.splitext(filename)[0]

        # 严格匹配格式: [ft]数字.数字
        pattern = r'^[ft]\d+\.\d+$'
        if re.match(pattern, name_without_ext, re.IGNORECASE):
            return name_without_ext.lower()

        return None

    def call_llm_api(self, image_path: str, identifier: str) -> str:
        """
        调用openai多模态LLM API提取AUTOSAR图片信息

        Args:
            image_path: 图片路径
            identifier: 图片标识符

        Returns:
            提取的结构化信息
        """
        try:
            # 编码图片
            base64_image = self.encode_image(image_path)

            # 根据标识符确定图片类型
            is_table = identifier.startswith('t')

            if is_table:
                # 表格特定的提示词
                autosar_prompt = """请提取这张AUTOSAR SWC规范文档中的表格，并转为md格式的表格。"""
            else:
                # 图形特定的提示词
                autosar_prompt = """请分析这张AUTOSAR SWC规范文档中的图形，并提取结构化信息。

**图形分析要点：**
1. **组件架构**：识别软件组件(SW Component)的类型、名称和层次关系
2. **端口与接口**：分析端口(Port)的类型(R-Port/P-Port)、数据接口和连接关系
3. **数据流**：理解组件间的数据传输路径和通信模式
4. **AUTOSAR概念**：识别图中的关键AUTOSAR元素，如原型(Prototype)、接口等
5. **用例场景**：理解图形所展示的具体应用场景或设计模式

**输出要求：**
- 重点描述架构关系和设计意图，而非细节标签
- 突出关键的AUTOSAR软件组件概念
- 用简洁的中文描述图形的主要目的和核心信息
- 适合作为技术文档上下文，帮助理解相关设计"""

            # 构建请求payload
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": autosar_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_completion_tokens": MAX_OUTPUT_TOKENS,
                "temperature": 0.1
            }

            # 发送请求
            api_url = f"{self.api_base}/chat/completions"
            response = requests.post(api_url, headers=self.headers, json=payload, timeout=60)

            # 添加详细的错误信息
            if response.status_code != 200:
                print(f"错误状态码: {response.status_code}")
                print(f"错误响应内容: {response.text}")
                try:
                    error_json = response.json()
                    print(f"错误详情: {json.dumps(error_json, indent=2, ensure_ascii=False)}")
                except:
                    pass

            response.raise_for_status()

            # 解析响应
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()

            return content


        except requests.exceptions.HTTPError as e:

            print(f"HTTP错误 ({image_path}): {str(e)}")

            print(f"响应内容: {e.response.text if hasattr(e, 'response') else 'N/A'}")

            return f"AUTOSAR图片分析失败: {str(e)}"

        except Exception as e:

            print(f"调用openai API失败 ({image_path}): {str(e)}")

            return f"AUTOSAR图片分析失败: {str(e)}"

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
                injection_text = f"<-------------- figure/table context {fact_info} ---------------------->"

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