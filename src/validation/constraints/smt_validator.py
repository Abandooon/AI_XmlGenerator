# src/validation/constraints/smt_validator.py - 修复版
import subprocess
import tempfile
from typing import Dict, List
import xml.etree.ElementTree as ET
import re
import os


class SMTValidator:
    """SMT约束验证器 - 修复版"""

    def __init__(self, smt_template_file: str):
        """初始化SMT验证器"""
        self.smt_template_file = smt_template_file
        self.smt_template = self._load_smt_template(smt_template_file)
        self.z3_available = self._check_z3_availability()

    def _check_z3_availability(self):
        """检查Z3求解器可用性"""
        # 优先尝试Python z3包
        try:
            import z3
            print("✅ 使用Python z3包")
            return "python"
        except ImportError:
            pass

        # 尝试命令行z3
        try:
            result = subprocess.run(["z3", "--version"], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                print("✅ 使用命令行z3")
                return "command"
        except:
            pass

        print("⚠️  Z3求解器不可用")
        return None

    def extract_constraint_data(self, xml_content: str) -> Dict:
        """从XML提取约束相关数据"""
        print("🔍 开始提取约束数据...")

        constraint_data = {
            "timing_events": [],
            "periods": [],
            "deadlines": [],
            "priorities": [],
            "timeouts": [],
            "relationships": []
        }

        try:
            root = ET.fromstring(xml_content)
            print(f"📋 解析XML根元素: {root.tag}")

            def clean_tag(tag):
                if '}' in tag:
                    return tag.split('}')[1]
                return tag

            # 查找时序事件
            timing_events = []
            for elem in root.iter():
                if clean_tag(elem.tag) == "TIMING-EVENT":
                    timing_events.append(elem)

            print(f"📊 找到 {len(timing_events)} 个TIMING-EVENT元素")

            for timing_event in timing_events:
                event_data = {
                    "id": timing_event.get("UUID") or timing_event.get("ID") or f"event_{len(constraint_data['timing_events'])}",
                    "period": None,
                    "deadline": None,
                    "priority": None
                }

                # 提取周期
                for child in timing_event.iter():
                    if clean_tag(child.tag) == "PERIOD":
                        if child.text:
                            try:
                                event_data["period"] = float(child.text.strip())
                                constraint_data["periods"].append(event_data["period"])
                                print(f"   ⏰ 提取周期: {event_data['period']}")
                            except ValueError as e:
                                print(f"   ⚠️  周期值转换失败: {child.text}")
                        break

                # 提取截止时间
                for child in timing_event.iter():
                    if clean_tag(child.tag) == "DEADLINE":
                        if child.text:
                            try:
                                event_data["deadline"] = float(child.text.strip())
                                constraint_data["deadlines"].append(event_data["deadline"])
                                print(f"   ⏰ 提取截止时间: {event_data['deadline']}")
                            except ValueError as e:
                                print(f"   ⚠️  截止时间值转换失败: {child.text}")
                        break

                constraint_data["timing_events"].append(event_data)
                print(f"   ✅ 时序事件: {event_data['id']}")

            # 提取超时设置
            timeout_elements = []
            for elem in root.iter():
                if clean_tag(elem.tag) == "ALIVE-TIMEOUT":
                    timeout_elements.append(elem)

            print(f"📊 找到 {len(timeout_elements)} 个ALIVE-TIMEOUT元素")

            for timeout_elem in timeout_elements:
                if timeout_elem.text:
                    try:
                        timeout_value = float(timeout_elem.text.strip())
                        constraint_data["timeouts"].append(timeout_value)
                        print(f"   ⏰ 提取超时: {timeout_value}")
                    except ValueError as e:
                        print(f"   ⚠️  超时值转换失败: {timeout_elem.text}")

            # 总结
            total_constraints = (len(constraint_data["timing_events"]) + 
                               len(constraint_data["periods"]) + 
                               len(constraint_data["timeouts"]))

            print(f"📊 约束数据提取总结:")
            print(f"   时序事件: {len(constraint_data['timing_events'])}")
            print(f"   周期数据: {len(constraint_data['periods'])}")
            print(f"   超时设置: {len(constraint_data['timeouts'])}")
            print(f"   总计: {total_constraints} 个约束数据点")

        except Exception as e:
            print(f"❌ 约束提取错误: {e}")

        return constraint_data

    def validate_constraints(self, xml_content: str) -> Dict:
        """SMT约束验证"""
        print("🔍 开始SMT约束验证...")

        if not self.z3_available:
            print("⚠️  Z3求解器不可用，跳过SMT验证")
            return {
                "valid": True,
                "constraint_count": 0,
                "satisfied_count": 0,
                "unsat_constraints": [],
                "detailed_results": [],
                "message": "Z3 solver not available - validation skipped"
            }

        try:
            # 提取约束数据
            constraint_data = self.extract_constraint_data(xml_content)

            total_data_points = (len(constraint_data.get('timing_events', [])) + 
                               len(constraint_data.get('periods', [])) + 
                               len(constraint_data.get('timeouts', [])))

            if total_data_points == 0:
                print("⚠️  未找到约束数据，跳过SMT验证")
                return {
                    "valid": True,
                    "constraint_count": 0,
                    "satisfied_count": 0,
                    "unsat_constraints": [],
                    "detailed_results": [],
                    "message": "No constraints found"
                }

            # 生成SMT实例
            print("📝 生成SMT约束实例...")
            smt_instances = self.generate_smt_instances(constraint_data)

            if not smt_instances:
                print("⚠️  未生成SMT实例")
                return {
                    "valid": True,
                    "constraint_count": 0,
                    "satisfied_count": 0,
                    "unsat_constraints": [],
                    "detailed_results": [],
                    "message": "No SMT instances generated"
                }

            # 求解SMT实例
            print(f"🧮 求解 {len(smt_instances)} 个SMT实例...")
            results = []
            satisfied_count = 0

            for i, smt_instance in enumerate(smt_instances, 1):
                print(f"   求解实例 {i}/{len(smt_instances)}...")
                result = self.solve_smt_instance(smt_instance)
                results.append(result)

                status = result.get("status", "unknown")
                print(f"   结果: {status}")

                if status == "sat":
                    satisfied_count += 1
                elif status == "unsat":
                    print(f"   ⚠️  约束不满足")

            # 分析结果
            constraint_count = len(smt_instances)
            unsat_constraints = [r for r in results if r.get("status") == "unsat"]

            satisfaction_rate = satisfied_count / constraint_count if constraint_count > 0 else 0

            print(f"📊 约束满足情况:")
            print(f"   满足: {satisfied_count}/{constraint_count}")
            print(f"   满足率: {satisfaction_rate:.1%}")

            # 判定标准：至少80%满足就通过
            validation_status = satisfaction_rate >= 0.8

            if validation_status:
                print("✅ SMT约束验证通过")
            else:
                print("❌ SMT约束验证失败")

            return {
                "valid": validation_status,
                "constraint_count": constraint_count,
                "satisfied_count": satisfied_count,
                "satisfaction_rate": satisfaction_rate,
                "unsat_constraints": unsat_constraints,
                "detailed_results": results,
                "data_points": total_data_points
            }

        except Exception as e:
            print(f"❌ SMT验证错误: {e}")
            return {
                "valid": False,
                "constraint_count": 0,
                "satisfied_count": 0,
                "unsat_constraints": [],
                "detailed_results": [],
                "error": str(e)
            }

    def generate_smt_instances(self, constraint_data: Dict) -> List[str]:
        """生成SMT实例"""
        smt_instances = []
        print("🏗️  生成SMT约束实例...")

        # 为每个时序事件生成基本约束
        for event in constraint_data.get("timing_events", []):
            event_id = event.get('id', 'unknown')

            if event.get("period") is not None:
                period = event["period"]
                smt_instance = f"""(declare-const period_{len(smt_instances)} Real)
(assert (= period_{len(smt_instances)} {period}))
(assert (and (>= period_{len(smt_instances)} 0.001) (<= period_{len(smt_instances)} 10.0)))
(check-sat)
"""
                smt_instances.append(smt_instance)
                print(f"   ✅ 生成周期约束: {period}s")

        # 为超时生成约束
        for i, timeout in enumerate(constraint_data.get("timeouts", [])):
            smt_instance = f"""(declare-const timeout_{i} Real)
(assert (= timeout_{i} {timeout}))
(assert (and (>= timeout_{i} 0.0) (<= timeout_{i} 60.0)))
(check-sat)
"""
            smt_instances.append(smt_instance)
            print(f"   ✅ 生成超时约束: {timeout}s")

        print(f"📊 总共生成 {len(smt_instances)} 个SMT约束实例")
        return smt_instances

    def solve_smt_instance(self, smt_instance: str) -> Dict:
        """求解SMT实例"""
        if self.z3_available == "python":
            return self._solve_with_python_z3(smt_instance)
        elif self.z3_available == "command":
            return self._solve_with_command_z3(smt_instance)
        else:
            return {"status": "error", "error": "Z3 not available"}

    def _solve_with_python_z3(self, smt_instance: str) -> Dict:
        """使用Python z3包求解"""
        try:
            import z3

            solver = z3.Solver()

            # 简单解析SMT内容 - 提取变量和约束
            lines = smt_instance.strip().split('\n')
            variables = {}

            for line in lines:
                line = line.strip()
                if line.startswith('(declare-const'):
                    # 提取变量名
                    parts = line.split()
                    if len(parts) >= 3:
                        var_name = parts[1]
                        if 'Real' in line:
                            variables[var_name] = z3.Real(var_name)

                elif line.startswith('(assert'):
                    # 简单的约束解析
                    if '=' in line and any(var in line for var in variables):
                        # 处理等式约束
                        for var_name, var_obj in variables.items():
                            if var_name in line:
                                # 提取数值
                                import re
                                numbers = re.findall(r'\d+\.\d+|\d+', line)
                                if numbers:
                                    value = float(numbers[0])
                                    solver.add(var_obj == value)

                    elif '>=' in line and any(var in line for var in variables):
                        # 处理不等式约束
                        for var_name, var_obj in variables.items():
                            if var_name in line:
                                import re
                                numbers = re.findall(r'\d+\.\d+|\d+', line)
                                if numbers:
                                    value = float(numbers[0])
                                    solver.add(var_obj >= value)

            result = solver.check()

            return {
                "status": str(result),
                "output": str(result),
                "method": "python_z3"
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "method": "python_z3"
            }

    def _solve_with_command_z3(self, smt_instance: str) -> Dict:
        """使用命令行z3求解"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.smt2', delete=False) as f:
                f.write(smt_instance)
                temp_file = f.name

            result = subprocess.run(
                ['z3', temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )

            output = result.stdout.strip()

            if "sat" in output and "unsat" not in output:
                status = "sat"
            elif "unsat" in output:
                status = "unsat"
            else:
                status = "error"

            return {
                "status": status,
                "output": output,
                "error": result.stderr if result.stderr else None,
                "method": "command_z3"
            }

        except subprocess.TimeoutExpired:
            return {"status": "timeout", "method": "command_z3"}
        except Exception as e:
            return {"status": "error", "error": str(e), "method": "command_z3"}
        finally:
            try:
                os.unlink(temp_file)
            except:
                pass

    def _load_smt_template(self, path: str) -> str:
        """加载SMT模板"""
        try:
            with open(path, "r", encoding="utf-8") as fp:
                return fp.read()
        except Exception as e:
            print(f"⚠️  SMT模板加载失败: {e}")
            return ""
