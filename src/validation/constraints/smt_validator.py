# src/validation/constraints/smt_validator.py
import subprocess
import tempfile
from typing import Dict, List
import xml.etree.ElementTree as ET
import re


class SMTValidator:
    """SMT约束验证器"""

    def __init__(self, smt_template_file: str):
        """
        初始化SMT验证器

        Args:
            smt_template_file: SMT约束模板文件路径 (constraints.smt2)
        """
        self.smt_template_file = smt_template_file
        self.smt_template = self._load_smt_template(smt_template_file)

    def validate_constraints(self, xml_content: str) -> Dict:
        """SMT约束验证"""

        try:
            # 1. 从XML提取约束数据
            constraint_data = self.extract_constraint_data(xml_content)

            # 2. 生成SMT实例
            smt_instances = self.generate_smt_instances(constraint_data)

            # 3. 调用Z3求解
            results = []
            for smt_instance in smt_instances:
                result = self.solve_smt_instance(smt_instance)
                results.append(result)

            # 4. 汇总结果
            all_sat = all(r["status"] == "sat" for r in results)
            unsat_constraints = [r for r in results if r["status"] == "unsat"]

            return {
                "valid": all_sat,
                "constraint_count": len(smt_instances),
                "satisfied_count": len(results) - len(unsat_constraints),
                "unsat_constraints": unsat_constraints,
                "detailed_results": results
            }

        except Exception as e:
            return {
                "valid": False,
                "constraint_count": 0,
                "satisfied_count": 0,
                "unsat_constraints": [],
                "detailed_results": [],
                "error": str(e)
            }

    def extract_constraint_data(self, xml_content: str) -> Dict:
        """从XML提取约束相关的数值和关系"""

        constraint_data = {
            "timing_events": [],
            "periods": [],
            "deadlines": [],
            "priorities": [],
            "relationships": []
        }

        try:
            root = ET.fromstring(xml_content)

            # 提取时序事件
            for timing_event in root.findall(".//TIMING-EVENT"):
                event_data = {
                    "id": timing_event.get("ID", "unknown"),
                    "period": None,
                    "deadline": None,
                    "priority": None
                }

                # 提取周期
                period_elem = timing_event.find(".//PERIOD")
                if period_elem is not None:
                    event_data["period"] = float(period_elem.text)
                    constraint_data["periods"].append(event_data["period"])

                # 提取截止时间
                deadline_elem = timing_event.find(".//DEADLINE")
                if deadline_elem is not None:
                    event_data["deadline"] = float(deadline_elem.text)
                    constraint_data["deadlines"].append(event_data["deadline"])

                # 提取优先级
                priority_elem = timing_event.find(".//PRIORITY")
                if priority_elem is not None:
                    event_data["priority"] = int(priority_elem.text)
                    constraint_data["priorities"].append(event_data["priority"])

                constraint_data["timing_events"].append(event_data)

        except ET.ParseError as e:
            print(f"XML parsing error in constraint extraction: {e}")

        return constraint_data

    def generate_smt_instances(self, constraint_data: Dict) -> List[str]:
        """基于模板生成具体的SMT实例"""

        smt_instances = []

        # 基本数值约束
        for event in constraint_data["timing_events"]:
            if event["period"] is not None:
                smt_instance = f"""
                (declare-const period_{event['id']} Real)
                (assert (= period_{event['id']} {event['period']}))
                (assert (and (>= period_{event['id']} 1.0) (<= period_{event['id']} 1000.0)))
                (check-sat)
                """
                smt_instances.append(smt_instance)

            # 截止时间约束
            if event["deadline"] is not None and event["period"] is not None:
                smt_instance = f"""
                (declare-const deadline_{event['id']} Real)
                (declare-const period_{event['id']} Real)
                (assert (= deadline_{event['id']} {event['deadline']}))
                (assert (= period_{event['id']} {event['period']}))
                (assert (< deadline_{event['id']} period_{event['id']}))
                (check-sat)
                """
                smt_instances.append(smt_instance)

        return smt_instances

    def solve_smt_instance(self, smt_instance: str) -> Dict:
        """调用Z3求解器验证约束可满足性"""

        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.smt2', delete=False) as f:
                f.write(smt_instance)
                temp_file = f.name

            # 调用Z3求解器
            result = subprocess.run(
                ['z3', temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )

            # 解析结果
            output = result.stdout.strip()

            if "sat" in output:
                status = "sat"
            elif "unsat" in output:
                status = "unsat"
            else:
                status = "unknown"

            return {
                "status": status,
                "output": output,
                "error": result.stderr if result.stderr else None
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "output": "",
                "error": "SMT solving timeout"
            }
        except Exception as e:
            return {
                "status": "error",
                "output": "",
                "error": str(e)
            }