# src/validation/orchestrator/validation_orchestrator.py
from typing import Dict, Optional
from ..structure.gbnf_validator import GBNFValidator
from ..semantic.shacl_validator import SHACLValidator
from ..constraints.smt_validator import SMTValidator


class ValidationOrchestrator:
    """验证流程编排器"""

    def __init__(self, validator_config: Dict):
        """
        初始化验证编排器

        Args:
            validator_config: 验证器配置
        """
        self.config = validator_config

        # 初始化各验证器
        self.structure_validator = GBNFValidator(
            validator_config["gbnf_grammar_file"]
        )
        self.semantic_validator = SHACLValidator(
            validator_config["shacl_shapes_file"]
        )
        self.constraint_validator = SMTValidator(
            validator_config["smt_template_file"]
        )

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
                "total_stages": 3,
                "passed_stages": 0,
                "failed_stage": None,
                "execution_time": 0
            }
        }

        import time
        start_time = time.time()

        try:
            # 第一段：结构验证
            if validation_level in ["full", "structure"]:
                structure_result = self.structure_validator.validate_structure(xml_content)
                validation_results["stages"]["structure"] = {
                    "executed": True,
                    "result": structure_result
                }

                if not structure_result["valid"]:
                    validation_results["summary"]["failed_stage"] = "structure"
                    return validation_results

                validation_results["summary"]["passed_stages"] += 1

            # 第二段：语义验证
            if validation_level in ["full", "semantic"]:
                semantic_result = self.semantic_validator.validate_semantics(xml_content)
                validation_results["stages"]["semantic"] = {
                    "executed": True,
                    "result": semantic_result
                }

                if not semantic_result["valid"]:
                    validation_results["summary"]["failed_stage"] = "semantic"
                    return validation_results

                validation_results["summary"]["passed_stages"] += 1

            # 第三段：约束验证
            if validation_level in ["full", "constraint"]:
                constraint_result = self.constraint_validator.validate_constraints(xml_content)
                validation_results["stages"]["constraint"] = {
                    "executed": True,
                    "result": constraint_result
                }

                if not constraint_result["valid"]:
                    validation_results["summary"]["failed_stage"] = "constraint"
                    return validation_results

                validation_results["summary"]["passed_stages"] += 1

            # 所有验证通过
            validation_results["overall_valid"] = True

        except Exception as e:
            validation_results["summary"]["error"] = str(e)

        finally:
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
        report_lines.append("")

        # 各阶段详情
        stage_names = {"structure": "Structure", "semantic": "Semantic", "constraint": "Constraint"}

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

                    if "constraint_count" in result:
                        satisfied = result.get("satisfied_count", 0)
                        total = result["constraint_count"]
                        report_lines.append(f"  Constraints: {satisfied}/{total} satisfied")

                report_lines.append("")

        return "\n".join(report_lines)