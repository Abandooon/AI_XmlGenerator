#!/usr/bin/env python3
"""
AUTOSAR ARXML 完整性检查脚本
检查生成文件的完整性：文件存在性、大小、结构完整性
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
import xml.etree.ElementTree as ET


class CompletenessChecker:
    def __init__(self, base_dir: str = "generated_arxml"):
        self.base_dir = Path(base_dir)
        self.categories = ["simple", "middle", "complex"]

    def check_file_structure(self, filepath: Path) -> Dict:
        """检查单个文件的完整性"""
        result = {
            "exists": False,
            "size_bytes": 0,
            "is_empty": True,
            "has_xml_declaration": False,
            "has_root_open": False,
            "has_root_close": False,
            "is_truncated": False,
            "line_count": 0,
            "error": None
        }

        if not filepath.exists():
            result["error"] = "File does not exist"
            return result

        result["exists"] = True
        result["size_bytes"] = filepath.stat().st_size

        if result["size_bytes"] == 0:
            result["error"] = "File is empty"
            return result

        result["is_empty"] = False

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                result["line_count"] = len(lines)

                # 检查前几行是否有XML声明和根标签
                first_10_lines = ''.join(lines[:10])
                result["has_xml_declaration"] = '<?xml' in first_10_lines
                result["has_root_open"] = '<AUTOSAR' in first_10_lines

                # 检查最后几行是否有闭合根标签
                last_10_lines = ''.join(lines[-10:])
                result["has_root_close"] = '</AUTOSAR>' in last_10_lines

                # 判断是否被截断
                if result["has_root_open"] and not result["has_root_close"]:
                    result["is_truncated"] = True
                    result["error"] = "File appears to be truncated (missing </AUTOSAR>)"

        except Exception as e:
            result["error"] = f"Error reading file: {str(e)}"

        return result

    def check_xml_wellformed(self, filepath: Path) -> Tuple[bool, str]:
        """检查XML是否格式良好（可选的深度检查）"""
        try:
            ET.parse(filepath)
            return True, "Well-formed XML"
        except ET.ParseError as e:
            return False, f"XML parse error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def analyze_category(self, category: str) -> Dict:
        """分析某个类别下的所有文件"""
        category_dir = self.base_dir / category

        if not category_dir.exists():
            return {
                "category": category,
                "directory_exists": False,
                "files": [],
                "summary": {}
            }

        files_data = []
        files = sorted(category_dir.glob("*.arxml"))

        for filepath in files:
            file_result = {
                "filename": filepath.name,
                "filepath": str(filepath),
                **self.check_file_structure(filepath)
            }

            # 如果文件看起来完整，进行深度XML检查
            if not file_result["is_truncated"] and file_result["has_root_close"]:
                is_wellformed, msg = self.check_xml_wellformed(filepath)
                file_result["is_wellformed"] = is_wellformed
                file_result["wellformed_msg"] = msg
            else:
                file_result["is_wellformed"] = False
                file_result["wellformed_msg"] = "Skipped due to structural issues"

            files_data.append(file_result)

        # 统计摘要
        summary = {
            "total_files": len(files_data),
            "existing_files": sum(1 for f in files_data if f["exists"]),
            "empty_files": sum(1 for f in files_data if f["is_empty"]),
            "truncated_files": sum(1 for f in files_data if f["is_truncated"]),
            "wellformed_files": sum(1 for f in files_data if f.get("is_wellformed", False)),
            "total_size_bytes": sum(f["size_bytes"] for f in files_data),
            "avg_size_bytes": sum(f["size_bytes"] for f in files_data) / len(files_data) if files_data else 0,
            "completeness_rate": 0.0
        }

        # 计算完整性比例（非截断 + 格式良好）
        if summary["total_files"] > 0:
            complete_files = sum(
                1 for f in files_data
                if not f["is_truncated"] and f.get("is_wellformed", False)
            )
            summary["completeness_rate"] = (complete_files / summary["total_files"]) * 100

        return {
            "category": category,
            "directory_exists": True,
            "files": files_data,
            "summary": summary
        }

    def run_full_check(self) -> Dict:
        """执行完整检查"""
        results = {
            "base_directory": str(self.base_dir),
            "categories": {}
        }

        for category in self.categories:
            print(f"Checking {category} category...")
            results["categories"][category] = self.analyze_category(category)

        # 全局统计
        global_summary = {
            "total_files_all": 0,
            "complete_files_all": 0,
            "truncated_files_all": 0,
            "empty_files_all": 0,
            "overall_completeness_rate": 0.0
        }

        for cat_data in results["categories"].values():
            if cat_data["directory_exists"]:
                summary = cat_data["summary"]
                global_summary["total_files_all"] += summary["total_files"]
                global_summary["complete_files_all"] += summary["wellformed_files"]
                global_summary["truncated_files_all"] += summary["truncated_files"]
                global_summary["empty_files_all"] += summary["empty_files"]

        if global_summary["total_files_all"] > 0:
            global_summary["overall_completeness_rate"] = (
                                                                  global_summary["complete_files_all"] / global_summary[
                                                              "total_files_all"]
                                                          ) * 100

        results["global_summary"] = global_summary

        return results

    def print_report(self, results: Dict):
        """打印易读的报告"""
        print("\n" + "=" * 80)
        print("AUTOSAR ARXML 完整性检查报告")
        print("=" * 80)

        for category, data in results["categories"].items():
            print(f"\n【{category.upper()} 组】")

            if not data["directory_exists"]:
                print("  ⚠️  目录不存在")
                continue

            summary = data["summary"]
            print(f"  文件总数: {summary['total_files']}")
            print(f"  完整文件: {summary['wellformed_files']} ({summary['completeness_rate']:.1f}%)")
            print(f"  截断文件: {summary['truncated_files']}")
            print(f"  空文件: {summary['empty_files']}")
            print(f"  总大小: {summary['total_size_bytes'] / 1024:.1f} KB")
            print(f"  平均大小: {summary['avg_size_bytes'] / 1024:.1f} KB")

            # 列出有问题的文件
            problem_files = [
                f for f in data["files"]
                if f["is_truncated"] or f["is_empty"] or not f.get("is_wellformed", False)
            ]

            if problem_files:
                print(f"\n  ⚠️  问题文件 ({len(problem_files)} 个):")
                for f in problem_files:
                    print(f"    - {f['filename']}: {f.get('error', f.get('wellformed_msg', 'Unknown issue'))}")

        print(f"\n{'=' * 80}")
        print("【全局统计】")
        gs = results["global_summary"]
        print(f"  总文件数: {gs['total_files_all']}")
        print(f"  完整文件数: {gs['complete_files_all']}")
        print(f"  截断文件数: {gs['truncated_files_all']}")
        print(f"  空文件数: {gs['empty_files_all']}")
        print(f"  整体完整率: {gs['overall_completeness_rate']:.1f}%")
        print("=" * 80 + "\n")


def main():
    # 使用相对路径或绝对路径
    checker = CompletenessChecker(base_dir="generated_arxml")

    print("开始执行完整性检查...")
    results = checker.run_full_check()

    # 打印报告
    checker.print_report(results)

    # 保存详细结果到JSON
    output_file = "completeness_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"✅ 详细报告已保存到: {output_file}")


if __name__ == "__main__":
    main()