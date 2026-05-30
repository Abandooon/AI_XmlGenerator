# src/validation/structure/xsd_validator.py
from typing import Dict, Optional, List
import os
import warnings
import tempfile
from pathlib import Path

warnings.filterwarnings("ignore", category=UserWarning, module="xmlschema")


class XSDValidator:
    """基于 XML Schema 的结构验证器（支持错误分级）"""

    def __init__(self, xsd_file: Optional[str] = None):
        self.xsd_file = xsd_file
        self.schema = None

        if not xsd_file or not os.path.exists(xsd_file):
            print(f"⚠️  XSD文件不存在: {xsd_file}")
            self.xsd_file = self._create_simplified_autosar_xsd()

        self._load_schema()

    def _create_simplified_autosar_xsd(self) -> str:
        return None

    def _load_schema(self):
        try:
            import xmlschema
            import sys

            original_recursion_limit = sys.getrecursionlimit()
            try:
                sys.setrecursionlimit(1000)

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    self.schema = xmlschema.XMLSchema(
                        self.xsd_file,
                        validation='skip',
                        locations=None
                    )

                print(f"✅ XSD Schema加载成功: {self.xsd_file}")

            finally:
                sys.setrecursionlimit(original_recursion_limit)

        except ImportError:
            print("⚠️  xmlschema包未安装")
            self.schema = None
        except Exception as e:
            print(f"⚠️  XSD Schema加载失败: {e}")
            self.schema = None

    def validate_structure(self, xml_content: str) -> Dict:
        print(f"🔍 开始XSD验证，Schema: {Path(self.xsd_file).name if self.xsd_file else 'None'}")

        if not self.schema:
            return self._basic_xml_validation(xml_content)

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(xml_content)
                temp_xml_path = temp_file.name

            try:
                print("📝 执行XSD Schema验证（分级报告）...")

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    errors = list(self.schema.iter_errors(temp_xml_path))

                report = {
                    "ERROR": [],
                    "WARN": [],
                    "INFO": []
                }

                for err in errors:
                    msg = str(err)
                    msg_lower = msg.lower()

                    # ===== WARN（你想忽略的）=====
                    if (
                        # 顺序
                        "sequence" in msg_lower or
                        "unexpected child" in msg_lower or

                        # 数量
                        "occurs" in msg_lower or
                        "minoccurs" in msg_lower or
                        "maxoccurs" in msg_lower or
                        "too many elements" in msg_lower or
                        "too few elements" in msg_lower or
                        "missing required element" in msg_lower or

                        # 枚举
                        "enumeration" in msg_lower or
                        "not an element of" in msg_lower or
                        "value must be one of" in msg_lower or

                        # 正则
                        "pattern" in msg_lower or
                        "doesn't match any pattern" in msg_lower
                    ):
                        report["WARN"].append(msg)

                    else:
                        report["ERROR"].append(msg)

                # ===== 控制台输出 =====
                self._print_report(report)

                return {
                    "valid": len(report["ERROR"]) == 0,
                    "report": report,
                    "schema_file": self.xsd_file,
                    "validation_type": "XSD(graded)"
                }

            finally:
                try:
                    os.unlink(temp_xml_path)
                except:
                    pass

        except Exception as e:
            error_msg = str(e)
            print(f"❌ XSD验证过程出错: {error_msg}")

            return {
                "valid": False,
                "report": {"ERROR": [error_msg], "WARN": [], "INFO": []},
                "validation_type": "XSD"
            }

    def _print_report(self, report: Dict[str, List[str]]):
        """分级输出"""

        print("\n📊 验证结果报告")

        # ERROR
        if report["ERROR"]:
            print(f"\n❌ ERROR ({len(report['ERROR'])})")
            for i, e in enumerate(report["ERROR"][:10], 1):
                print(f"[E{i}]")
                print(e)
                print("-" * 80)

        # WARN
        if report["WARN"]:
            print(f"\n⚠️ WARN ({len(report['WARN'])})")
            for i, e in enumerate(report["WARN"][:10], 1):
                print(f"[W{i}]")
                print(e)
                print("-" * 80)

        # INFO（预留）
        if report["INFO"]:
            print(f"\nℹ️ INFO ({len(report['INFO'])})")
            for i, e in enumerate(report["INFO"][:10], 1):
                print(f"[I{i}]")
                print(e)
                print("-" * 80)

        if not report["ERROR"]:
            print("\n✅ 结构验证通过（无ERROR）")

    def _basic_xml_validation(self, xml_content: str) -> Dict:
        try:
            import xml.etree.ElementTree as ET

            root = ET.fromstring(xml_content)

            return {
                "valid": True,
                "report": {"ERROR": [], "WARN": [], "INFO": []},
                "validation_type": "Basic XML",
                "root_element": root.tag
            }

        except ET.ParseError as e:
            return {
                "valid": False,
                "report": {"ERROR": [str(e)], "WARN": [], "INFO": []},
                "validation_type": "Basic XML"
            }