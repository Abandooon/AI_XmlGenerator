#!/usr/bin/env python3
"""
AUTOSAR ARXML 跨文件引用完整性检查脚本
检查所有REF引用的目标是否存在
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
from lxml import etree


class CrossReferenceChecker:
    def __init__(self, base_dir: str = "generated_arxml"):
        self.base_dir = Path(base_dir)
        self.categories = ["simple", "middle", "complex"]

        # AUTOSAR命名空间（根据版本可能需要调整）
        self.ns = {
            'ar': 'http://autosar.org/schema/r4.0'
        }

        # 常见的引用标签后缀
        self.ref_suffixes = [
            'REF', 'IREF', 'TREF', '-REF', '-IREF', '-TREF',
            'DEFINITION-REF', 'TYPE-TREF', 'BASE-TYPE-REF'
        ]

    def parse_arxml(self, filepath: Path) -> Tuple[etree._Element, bool]:
        """解析ARXML文件，返回根节点"""
        try:
            parser = etree.XMLParser(remove_blank_text=True, huge_tree=True)
            tree = etree.parse(str(filepath), parser)
            return tree.getroot(), True
        except Exception as e:
            print(f"  ⚠️  解析失败 {filepath.name}: {str(e)}")
            return None, False

    def extract_definitions(self, root: etree._Element, filepath: Path) -> Dict[str, Dict]:
        """提取所有定义的实体（带SHORT-NAME的元素）"""
        definitions = {}

        # 查找所有带SHORT-NAME的元素
        for elem in root.iter():
            # 跳过非元素节点
            if not isinstance(elem.tag, str):
                continue

            short_name_elem = elem.find('.//ar:SHORT-NAME', self.ns)
            if short_name_elem is None:
                # 尝试不带命名空间
                short_name_elem = elem.find('.//SHORT-NAME')

            if short_name_elem is not None and short_name_elem.text:
                short_name = short_name_elem.text.strip()

                # 尝试构建完整路径
                path_parts = []
                current = elem
                while current is not None:
                    # 确保 current 是元素节点
                    if isinstance(current.tag, str):
                        sn = current.find('.//ar:SHORT-NAME', self.ns)
                        if sn is None:
                            sn = current.find('.//SHORT-NAME')
                        if sn is not None and sn.text:
                            path_parts.insert(0, sn.text.strip())
                    current = current.getparent()

                full_path = '/' + '/'.join(path_parts) if path_parts else f"/{short_name}"

                definitions[full_path] = {
                    'short_name': short_name,
                    'element_tag': self._clean_tag(elem.tag),
                    'source_file': filepath.name,
                    'xpath': self._get_xpath(elem)
                }

        return definitions

    def extract_references(self, root: etree._Element, filepath: Path) -> List[Dict]:
        """提取所有引用"""
        references = []

        for elem in root.iter():
            # 跳过非元素节点（注释、文本等）
            if not isinstance(elem.tag, str):
                continue

            tag = self._clean_tag(elem.tag)

            # 检查是否是引用标签
            if any(suffix in tag.upper() for suffix in self.ref_suffixes):
                ref_value = elem.text.strip() if elem.text else None

                if ref_value:
                    # 尝试找到包含此引用的SHORT-NAME上下文
                    context_name = self._find_context_name(elem)

                    # 获取更详细的上下文路径
                    context_path = self._get_context_path(elem)

                    # 获取行号（如果可能）
                    line_number = elem.sourceline if hasattr(elem, 'sourceline') else "N/A"

                    references.append({
                        'ref_tag': tag,
                        'ref_value': ref_value,
                        'source_file': filepath.name,
                        'context': context_name,
                        'context_path': context_path,
                        'line_number': line_number,
                        'xpath': self._get_xpath(elem)
                    })

        return references

    def _clean_tag(self, tag) -> str:
        """移除命名空间前缀"""
        # 确保 tag 是字符串
        if not isinstance(tag, str):
            return str(tag) if tag is not None else "Unknown"

        if '}' in tag:
            return tag.split('}')[1]
        return tag

    def _get_xpath(self, elem: etree._Element) -> str:
        """获取元素的简化XPath"""
        try:
            tree = elem.getroottree()
            return tree.getpath(elem)
        except:
            return "N/A"

    def _find_context_name(self, elem: etree._Element) -> str:
        """向上查找最近的SHORT-NAME作为上下文"""
        current = elem.getparent()
        while current is not None:
            # 确保是元素节点
            if not isinstance(current.tag, str):
                current = current.getparent()
                continue

            sn = current.find('.//ar:SHORT-NAME', self.ns)
            if sn is None:
                sn = current.find('.//SHORT-NAME')
            if sn is not None and sn.text:
                return sn.text.strip()
            current = current.getparent()
        return "Unknown"

    def _get_context_path(self, elem: etree._Element) -> str:
        """获取元素的上下文路径（包含所有父元素的SHORT-NAME）"""
        path_parts = []
        current = elem.getparent()

        while current is not None and len(path_parts) < 5:  # 最多5层
            if isinstance(current.tag, str):
                tag = self._clean_tag(current.tag)
                sn = current.find('.//ar:SHORT-NAME', self.ns)
                if sn is None:
                    sn = current.find('.//SHORT-NAME')
                if sn is not None and sn.text:
                    path_parts.insert(0, f"{tag}[{sn.text.strip()}]")
                else:
                    path_parts.insert(0, tag)
            current = current.getparent()

        return ' / '.join(path_parts) if path_parts else "Unknown"

    def build_global_symbol_table(self, category: str) -> Dict[str, Dict]:
        """构建某个类别的全局符号表"""
        category_dir = self.base_dir / category
        symbol_table = {}

        if not category_dir.exists():
            return symbol_table

        files = sorted(category_dir.glob("*.arxml"))

        for filepath in files:
            print(f"  📖 解析定义: {filepath.name}")
            root, success = self.parse_arxml(filepath)
            if success and root is not None:
                definitions = self.extract_definitions(root, filepath)
                symbol_table.update(definitions)

        return symbol_table

    def check_references(self, category: str) -> Dict:
        """检查某个类别的所有引用"""
        print(f"\n检查 {category} 类别...")

        # 1. 构建符号表
        print(f"  构建全局符号表...")
        symbol_table = self.build_global_symbol_table(category)
        print(f"  ✅ 符号表包含 {len(symbol_table)} 个定义")

        # 2. 提取所有引用
        category_dir = self.base_dir / category
        all_references = []

        if category_dir.exists():
            files = sorted(category_dir.glob("*.arxml"))

            for filepath in files:
                print(f"  🔍 提取引用: {filepath.name}")
                root, success = self.parse_arxml(filepath)
                if success and root is not None:
                    refs = self.extract_references(root, filepath)
                    all_references.extend(refs)

        print(f"  ✅ 发现 {len(all_references)} 个引用")

        # 3. 验证引用
        resolved_refs = []
        unresolved_refs = []

        for ref in all_references:
            ref_value = ref['ref_value']

            # 尝试多种匹配策略
            is_resolved = False
            matched_definition = None
            match_strategy = None

            # 策略1：完全路径匹配
            if ref_value in symbol_table:
                is_resolved = True
                matched_definition = symbol_table[ref_value]
                match_strategy = "完全路径匹配"

            # 策略2：SHORT-NAME匹配（部分路径）
            if not is_resolved:
                for path, definition in symbol_table.items():
                    if path.endswith(f"/{ref_value.split('/')[-1]}"):
                        is_resolved = True
                        matched_definition = definition
                        match_strategy = "部分路径匹配"
                        break

            # 策略3：只匹配最后一个SHORT-NAME（宽松匹配）
            if not is_resolved:
                ref_short_name = ref_value.split('/')[-1]
                for path, definition in symbol_table.items():
                    if definition['short_name'] == ref_short_name:
                        is_resolved = True
                        matched_definition = definition
                        match_strategy = "SHORT-NAME匹配"
                        break

            if is_resolved:
                ref['match_strategy'] = match_strategy
                ref['matched_definition'] = matched_definition
                resolved_refs.append(ref)
            else:
                unresolved_refs.append(ref)

        # 4. 按文件分组未解析引用
        unresolved_by_file = defaultdict(list)
        for ref in unresolved_refs:
            unresolved_by_file[ref['source_file']].append(ref)

        # 5. 生成报告
        result = {
            'category': category,
            'symbol_table_size': len(symbol_table),
            'symbol_table': symbol_table,  # 完整符号表
            'total_references': len(all_references),
            'resolved_references': len(resolved_refs),
            'unresolved_references': len(unresolved_refs),
            'resolution_rate': (len(resolved_refs) / len(all_references) * 100) if all_references else 0.0,
            'unresolved_details': unresolved_refs,
            'unresolved_by_file': dict(unresolved_by_file),
            'reference_by_file': self._group_by_file(all_references),
            'unresolved_count_by_file': {k: len(v) for k, v in unresolved_by_file.items()}
        }

        return result

    def _group_by_file(self, references: List[Dict]) -> Dict[str, int]:
        """按文件分组统计引用数量"""
        by_file = defaultdict(int)
        for ref in references:
            by_file[ref['source_file']] += 1
        return dict(by_file)

    def run_full_check(self) -> Dict:
        """执行完整检查"""
        results = {
            'base_directory': str(self.base_dir),
            'categories': {}
        }

        for category in self.categories:
            results['categories'][category] = self.check_references(category)

        # 全局统计
        global_summary = {
            'total_references_all': 0,
            'resolved_references_all': 0,
            'unresolved_references_all': 0,
            'overall_resolution_rate': 0.0
        }

        for cat_data in results['categories'].values():
            global_summary['total_references_all'] += cat_data['total_references']
            global_summary['resolved_references_all'] += cat_data['resolved_references']
            global_summary['unresolved_references_all'] += cat_data['unresolved_references']

        if global_summary['total_references_all'] > 0:
            global_summary['overall_resolution_rate'] = (
                    global_summary['resolved_references_all'] /
                    global_summary['total_references_all'] * 100
            )

        results['global_summary'] = global_summary

        return results

    def print_report(self, results: Dict):
        """打印易读的报告"""
        print("\n" + "=" * 80)
        print("AUTOSAR ARXML 跨文件引用完整性报告")
        print("=" * 80)

        for category, data in results['categories'].items():
            print(f"\n【{category.upper()} 组】")
            print(f"  符号表大小: {data['symbol_table_size']} 个定义")
            print(f"  引用总数: {data['total_references']}")
            print(f"  解析成功: {data['resolved_references']} ({data['resolution_rate']:.1f}%)")
            print(f"  解析失败: {data['unresolved_references']}")

            if data['unresolved_references'] > 0:
                print(f"\n  ⚠️  未解析引用示例 (前10个):")
                for ref in data['unresolved_details'][:10]:
                    print(f"    [{ref['source_file']}] 行{ref['line_number']}")
                    print(f"      引用类型: {ref['ref_tag']}")
                    print(f"      引用目标: {ref['ref_value']}")
                    print(f"      所在上下文: {ref['context']}")
                    print(f"      上下文路径: {ref['context_path']}")
                    print()

                print(f"  未解析引用按文件分布:")
                for filename, count in sorted(
                        data['unresolved_count_by_file'].items(),
                        key=lambda x: x[1],
                        reverse=True
                ):
                    print(f"    - {filename}: {count} 个")

        print(f"\n{'=' * 80}")
        print("【全局统计】")
        gs = results['global_summary']
        print(f"  引用总数: {gs['total_references_all']}")
        print(f"  解析成功: {gs['resolved_references_all']}")
        print(f"  解析失败: {gs['unresolved_references_all']}")
        print(f"  整体解析率: {gs['overall_resolution_rate']:.1f}%")
        print("=" * 80 + "\n")

    def generate_detailed_markdown_report(self, results: Dict, output_file: str):
        """生成详细的Markdown报告"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# AUTOSAR ARXML 跨文件引用完整性详细报告\n\n")
            f.write(f"**生成时间**: {Path(output_file).stat().st_mtime}\n\n")

            # 全局统计
            gs = results['global_summary']
            f.write("## 全局统计\n\n")
            f.write(f"- **引用总数**: {gs['total_references_all']}\n")
            f.write(f"- **解析成功**: {gs['resolved_references_all']} ({gs['overall_resolution_rate']:.1f}%)\n")
            f.write(f"- **解析失败**: {gs['unresolved_references_all']}\n\n")

            f.write("---\n\n")

            # 按类别详细报告
            for category, data in results['categories'].items():
                f.write(f"## {category.upper()} 组\n\n")
                f.write(f"### 统计摘要\n\n")
                f.write(f"- 符号表大小: {data['symbol_table_size']} 个定义\n")
                f.write(f"- 引用总数: {data['total_references']}\n")
                f.write(f"- 解析成功: {data['resolved_references']} ({data['resolution_rate']:.1f}%)\n")
                f.write(f"- 解析失败: {data['unresolved_references']}\n\n")

                # 未解析引用详情
                if data['unresolved_references'] > 0:
                    f.write(f"### ⚠️ 未解析引用详情 ({data['unresolved_references']} 个)\n\n")

                    # 按文件分组
                    for filename, refs in sorted(data['unresolved_by_file'].items()):
                        f.write(f"#### 📄 {filename} ({len(refs)} 个未解析引用)\n\n")

                        for i, ref in enumerate(refs, 1):
                            f.write(f"**#{i}** 行号: {ref['line_number']}\n\n")
                            f.write(f"- **引用类型**: `{ref['ref_tag']}`\n")
                            f.write(f"- **引用目标**: `{ref['ref_value']}`\n")
                            f.write(f"- **所在上下文**: `{ref['context']}`\n")
                            f.write(f"- **上下文路径**: `{ref['context_path']}`\n")
                            f.write(f"- **XPath**: `{ref['xpath']}`\n\n")
                            f.write("---\n\n")

                # 符号表（可用定义列表）
                f.write(f"### 📚 符号表 (可用定义, 共 {data['symbol_table_size']} 个)\n\n")
                f.write("<details>\n<summary>点击展开符号表</summary>\n\n")

                for path, definition in sorted(data['symbol_table'].items())[:100]:  # 最多显示100个
                    f.write(f"- `{path}` ({definition['element_tag']}) - 来自 `{definition['source_file']}`\n")

                if data['symbol_table_size'] > 100:
                    f.write(f"\n... 还有 {data['symbol_table_size'] - 100} 个定义（详见JSON报告）\n")

                f.write("\n</details>\n\n")
                f.write("---\n\n")


def main():
    checker = CrossReferenceChecker(base_dir="generated_arxml")

    print("开始执行跨文件引用完整性检查...")
    print("注意：这可能需要几分钟时间...")

    results = checker.run_full_check()

    # 打印控制台报告
    checker.print_report(results)

    # 保存详细JSON结果
    json_output = "cross_reference_report.json"
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON报告已保存到: {json_output}")

    # 生成Markdown详细报告
    md_output = "cross_reference_detailed_report.md"
    checker.generate_detailed_markdown_report(results, md_output)
    print(f"✅ Markdown详细报告已保存到: {md_output}")
    print(f"\n💡 建议使用Markdown编辑器或浏览器打开 {md_output} 查看详细错误信息")


if __name__ == "__main__":
    main()