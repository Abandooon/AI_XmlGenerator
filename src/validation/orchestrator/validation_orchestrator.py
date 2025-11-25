# src/validation/orchestrator/validation_orchestrator.py
from typing import Dict, Optional
import time


class ValidationOrchestrator:
    """验证流程编排器"""

    def __init__(self, validator_config: Dict):
        """
        初始化验证编排器

        Args:
            validator_config: 验证器配置
        """
        self.config = validator_config
        self.structure_validator = None
        self.semantic_validator = None
        self.constraint_validator = None

        # 延迟初始化验证器，避免导入错误
        self._init_validators()

    def _init_validators(self):
        """初始化各验证器"""
        try:
            # 初始化结构验证器
            if self.config.get("validators", {}).get("structure", {}).get("enabled", True):
                from ..structure.xsd_validator import XSDValidator
                self.structure_validator = XSDValidator(
                    self.config.get("xsd_schema_file")
                )
                print("✅ Structure validator initialized")
        except Exception as e:
            print(f"⚠️  Structure validator initialization failed: {e}")

        try:
            # 初始化语义验证器
            if self.config.get("validators", {}).get("semantic", {}).get("enabled", True):
                from ..semantic.shacl_validator import SHACLValidator
                self.semantic_validator = SHACLValidator(
                    self.config.get("shacl_shapes_file")
                )
                print("✅ Semantic validator initialized")
        except Exception as e:
            print(f"⚠️  Semantic validator initialization failed: {e}")

        try:
            # 初始化约束验证器
            if self.config.get("validators", {}).get("constraint", {}).get("enabled", True):
                from ..constraints.smt_validator import SMTValidator

                # 获取SMT模板和映射文件路径
                smt_template = self.config.get("smt_template_file")
                smt_mapping = self.config.get("smt_mapping_file")  # ← 新增

                self.constraint_validator = SMTValidator(
                    smt_template,
                    mapping_file=smt_mapping  # ← 关键修改：传递mapping文件
                )
                print("✅ Constraint validator initialized")

                # 可选：显示mapping加载状态
                if smt_mapping:
                    print(f"   📄 SMT Mapping: {smt_mapping}")
        except Exception as e:
            print(f"⚠️  Constraint validator initialization failed: {e}")

    def execute_full_validation(self, xml_content: str, validation_level: str = "full") -> Dict:
        """执行三段式完整验证"""

        validation_results = {
            "overall_valid": False,
            "validation_level": validation_level,
            "stages": {
                "structure": {"executed": False, "result": None},
                "semantic": {"executed": False, "result": None},
                "constraint": {"executed": False, "result": None}
            },
            "summary": {
                "total_stages": 0,
                "passed_stages": 0,
                "failed_stage": None,
                "execution_time": 0,
                "warnings": []
            }
        }

        start_time = time.time()

        try:
            # 第一段：结构验证
            if validation_level in ["full", "structure"] and self.structure_validator:
                print("Executing structure validation...")
                validation_results["summary"]["total_stages"] += 1

                try:
                    structure_result = self.structure_validator.validate_structure(xml_content)
                    validation_results["stages"]["structure"] = {
                        "executed": True,
                        "result": structure_result
                    }

                    if structure_result["valid"]:
                        validation_results["summary"]["passed_stages"] += 1
                        print("✅ Structure validation passed")
                    else:
                        validation_results["summary"]["failed_stage"] = "structure"
                        print(f"❌ Structure validation failed: {structure_result.get('error_info', 'Unknown error')}")
                        return self._finalize_results(validation_results, start_time)

                except Exception as e:
                    validation_results["stages"]["structure"] = {
                        "executed": True,
                        "result": {"valid": False, "error_info": f"Structure validation error: {str(e)}"}
                    }
                    validation_results["summary"]["failed_stage"] = "structure"
                    print(f"❌ Structure validation error: {e}")
                    return self._finalize_results(validation_results, start_time)

            elif validation_level in ["full", "structure"]:
                validation_results["summary"]["warnings"].append("Structure validator not available")

            # 第二段：语义验证
            if validation_level in ["full", "semantic"] and self.semantic_validator:
                print("Executing semantic validation...")
                validation_results["summary"]["total_stages"] += 1

                try:
                    semantic_result = self.semantic_validator.validate_semantics(xml_content)
                    validation_results["stages"]["semantic"] = {
                        "executed": True,
                        "result": semantic_result
                    }

                    if semantic_result["valid"]:
                        validation_results["summary"]["passed_stages"] += 1
                        print("✅ Semantic validation passed")
                    else:
                        validation_results["summary"]["failed_stage"] = "semantic"
                        violations = semantic_result.get("violation_count", 0)
                        print(f"❌ Semantic validation failed: {violations} violations found")
                        return self._finalize_results(validation_results, start_time)

                except Exception as e:
                    validation_results["stages"]["semantic"] = {
                        "executed": True,
                        "result": {"valid": False, "violation_count": 1, "violations": [{"message": str(e)}]}
                    }
                    validation_results["summary"]["failed_stage"] = "semantic"
                    print(f"❌ Semantic validation error: {e}")
                    return self._finalize_results(validation_results, start_time)

            elif validation_level in ["full", "semantic"]:
                validation_results["summary"]["warnings"].append("Semantic validator not available")

            # 第三段：约束验证
            if validation_level in ["full", "constraint"] and self.constraint_validator:
                print("Executing constraint validation...")
                validation_results["summary"]["total_stages"] += 1

                try:
                    constraint_result = self.constraint_validator.validate_constraints(xml_content)
                    validation_results["stages"]["constraint"] = {
                        "executed": True,
                        "result": constraint_result
                    }

                    if constraint_result["valid"]:
                        validation_results["summary"]["passed_stages"] += 1
                        print("✅ Constraint validation passed")
                    else:
                        validation_results["summary"]["failed_stage"] = "constraint"
                        satisfied = constraint_result.get("satisfied_count", 0)
                        total = constraint_result.get("constraint_count", 0)
                        print(f"❌ Constraint validation failed: {satisfied}/{total} constraints satisfied")
                        return self._finalize_results(validation_results, start_time)

                except Exception as e:
                    validation_results["stages"]["constraint"] = {
                        "executed": True,
                        "result": {"valid": False, "constraint_count": 0, "satisfied_count": 0, "error": str(e)}
                    }
                    validation_results["summary"]["failed_stage"] = "constraint"
                    print(f"❌ Constraint validation error: {e}")
                    return self._finalize_results(validation_results, start_time)

            elif validation_level in ["full", "constraint"]:
                validation_results["summary"]["warnings"].append("Constraint validator not available")

            # 所有验证通过
            if validation_results["summary"]["passed_stages"] == validation_results["summary"]["total_stages"]:
                validation_results["overall_valid"] = True
                print("🎉 All validations passed!")

        except Exception as e:
            validation_results["summary"]["error"] = str(e)
            print(f"❌ Validation orchestrator error: {e}")

        return self._finalize_results(validation_results, start_time)

    def _finalize_results(self, validation_results: Dict, start_time: float) -> Dict:
        """完成验证结果"""
        validation_results["summary"]["execution_time"] = time.time() - start_time
        return validation_results

    def generate_validation_report(self, validation_results: Dict) -> str:
        """生成人类可读的验证报告"""

        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("AUTOSAR XML Validation Report")
        report_lines.append("=" * 60)

        # 总体结果
        overall_status = "✅ PASSED" if validation_results["overall_valid"] else "❌ FAILED"
        report_lines.append(f"Overall Status: {overall_status}")
        report_lines.append(f"Validation Level: {validation_results['validation_level']}")
        report_lines.append(f"Execution Time: {validation_results['summary']['execution_time']:.3f}s")

        # 执行摘要
        passed = validation_results['summary']['passed_stages']
        total = validation_results['summary']['total_stages']
        report_lines.append(f"Stages Passed: {passed}/{total}")

        if validation_results['summary'].get('failed_stage'):
            report_lines.append(f"Failed at: {validation_results['summary']['failed_stage']} stage")

        # 警告信息
        warnings = validation_results['summary'].get('warnings', [])
        if warnings:
            report_lines.append(f"Warnings: {len(warnings)}")
            for warning in warnings:
                report_lines.append(f"  - {warning}")

        report_lines.append("")

        # 各阶段详情
        stage_names = {"structure": "Structure (XSD)", "semantic": "Semantic (SHACL)", "constraint": "Constraint (SMT)"}

        for stage_key, stage_info in validation_results["stages"].items():
            if stage_info["executed"]:
                stage_name = stage_names.get(stage_key, stage_key.title())
                result = stage_info["result"]

                if result and result.get("valid", False):
                    status = "✅ PASSED"
                else:
                    status = "❌ FAILED"

                report_lines.append(f"{stage_name} Validation: {status}")

                # 添加详细信息
                if result:
                    if "error_info" in result and result["error_info"]:
                        report_lines.append(f"  Error: {result['error_info']}")

                    if "violation_count" in result and result["violation_count"] > 0:
                        report_lines.append(f"  Violations: {result['violation_count']}")

                        # 显示前几个违规详情
                        violations = result.get("violations", [])
                        for i, violation in enumerate(violations[:3]):  # 只显示前3个
                            msg = violation.get("message", "No message")
                            report_lines.append(f"    {i + 1}. {msg}")

                        if len(violations) > 3:
                            report_lines.append(f"    ... and {len(violations) - 3} more violations")

                    if "constraint_count" in result:
                        satisfied = result.get("satisfied_count", 0)
                        total_constraints = result["constraint_count"]
                        report_lines.append(f"  Constraints: {satisfied}/{total_constraints} satisfied")

                        diagnosis = result.get("diagnosis", {})
                        if diagnosis and isinstance(diagnosis, dict):
                            diag_text = diagnosis.get("diagnosis", "")
                            if diag_text:
                                report_lines.append(f"\n  📋 诊断报告:")
                                for line in diag_text.split('\n'):
                                    report_lines.append(f"    {line}")

                            conflicts = diagnosis.get("conflicting_facts", [])
                            if conflicts:
                                report_lines.append(f"\n  ⚠️  冲突详情 ({len(conflicts)} 个):")
                                for conflict in conflicts[:3]:
                                    idx = conflict.get("index", -1)
                                    cid = conflict.get("constraint_id", "UNKNOWN_CONSTRAINT")
                                    fact = conflict.get("fact", "")[:120]
                                    report_lines.append(f"    #{idx + 1} [{cid}]: {fact}...")
                                if len(conflicts) > 3:
                                    report_lines.append(f"    ... 还有 {len(conflicts) - 3} 个冲突")

                        # 显示未满足的约束
                        unsat_constraints = result.get("unsat_constraints", [])
                        if unsat_constraints:
                            report_lines.append(f"  Unsatisfied constraints:")
                            for i, unsat in enumerate(unsat_constraints[:3]):  # 只显示前3个
                                status = unsat.get("status", "unknown")
                                report_lines.append(f"    {i + 1}. Status: {status}")

                            if len(unsat_constraints) > 3:
                                report_lines.append(f"    ... and {len(unsat_constraints) - 3} more")



                    if "error" in result and result["error"]:
                        report_lines.append(f"  Error: {result['error']}")

                report_lines.append("")

        # 添加建议
        if not validation_results["overall_valid"]:
            report_lines.append("Recommendations:")
            failed_stage = validation_results['summary'].get('failed_stage')
            if failed_stage == "structure":
                report_lines.append("  - Check XML syntax and schema compliance")
                report_lines.append("  - Verify element names and attributes")
            elif failed_stage == "semantic":
                report_lines.append("  - Review SHACL constraint violations")
                report_lines.append("  - Check data type constraints and cardinalities")
            elif failed_stage == "constraint":
                report_lines.append("  - Review timing and numerical constraints")
                report_lines.append("  - Check that deadlines are less than periods")
            report_lines.append("")

        return "\n".join(report_lines)