"""smt_validator.py (v5.0) - 形式化验证版
--------------------------------------------
修改：完全重写验证逻辑，以遵循用户定义的“阶段 2”工作流程。
- 移除所有对 enriched_constraints.json 和 raw_attributes.jsonl 的依赖。
- 移除所有基于配置的过滤逻辑。
- 核心功能：
    1. 加载 constraints.smt2 作为 SMT 逻辑模板。
    2. 解析 data.arxml 建立模型。
    3. 从 XML 模型生成 SMT 数据事实 (assert ...)。
    4. 将 (1) 和 (3) 合并并使用 Z3 求解。
"""
import subprocess
import tempfile
import json
import re
from typing import Dict, List, Any, Optional, Set
import xml.etree.ElementTree as ET
import os
from pathlib import Path
import z3  # 确保 z3-solver 已经安装 (pip install z3-solver)


class SMTValidator:
    """
    SMT约束验证器 - 遵循“阶段 2”形式化验证工作流程
    """

    def __init__(self, smt_template_file: str, **kwargs):
        """
        初始化SMT验证器。

        Args:
            smt_template_file: SMT模板文件路径 (constraints.smt2)
            **kwargs: 忽略所有其他旧参数 (如 config, raw_attributes 等)
        """
        print("🔧 初始化SMT形式化验证器 (V5.0)...")

        try:
            self.smt_template_file = str(smt_template_file) if smt_template_file else ""
            # ### 修改 ###: smt_template 是核心，必须加载
            self.smt_template = self._load_smt_template(self.smt_template_file)
            if not self.smt_template:
                raise FileNotFoundError(f"SMT 模板文件未找到或为空: {smt_template_file}")

            self.z3_available = self._check_z3_availability()
            if not self.z3_available:
                raise EnvironmentError("Z3 求解器 (python包或命令行) 未找到。")

            # ### 新增 ###: 用于存储生成的事实和实体映射
            self.smt_facts = []
            self.entity_map = {}  # 映射: (element_path) -> smt_name
            self.entity_counter = 0

            print("✅ SMT形式化验证器初始化完成")

        except Exception as e:
            print(f"❌ SMT验证器初始化失败: {e}")
            self._init_safe_defaults()

    def _init_safe_defaults(self):
        """初始化安全默认值以防出错"""
        self.smt_template = ""
        self.z3_available = None
        self.smt_facts = []
        self.entity_map = {}
        self.entity_counter = 0

    # ### 重写 ###: 核心验证工作流程
    def validate_constraints(self, xml_content: str) -> Dict:
        """
        执行完整的“阶段 2”SMT验证。
        """
        print("\n🔍 开始 SMT 形式化验证 (阶段 2)...")

        if not self.z3_available:
            return self._create_error_result("Z3 solver not available", "SKIPPED")

        if not self.smt_template:
            return self._create_error_result("SMT logic template (constraints.smt2) is missing", "FAILED")

        if not xml_content or not xml_content.strip():
            return self._create_error_result("XML content (data.arxml) is empty", "FAILED")

        try:
            # 步骤 1: 解析XML
            print("📝 步骤 2.1: 解析 ARXML...")
            root = ET.fromstring(xml_content)

            # 步骤 2: 生成 SMT 事实
            print("📝 步骤 2.2: 从 ARXML 生成 SMT 事实...")
            self.smt_facts = []
            self.entity_map = {}
            self.entity_counter = 0

            # (我们使用一个简化的父子映射来构建路径)
            parent_map = {c: p for p in root.iter() for c in p}

            self._generate_smt_facts(root, parent_map)
            print(f"   📊 生成了 {len(self.smt_facts)} 条 SMT 事实")

            # 步骤 3: 组合 SMT 脚本
            print("📝 步骤 2.3: 组合 SMT 逻辑和数据...")
            smt_logic = self.smt_template
            smt_data = "\n".join(self.smt_facts)

            # (check-sat 和 get-model 应该在模板的末尾，但我们在这里确保它们存在)
            full_script = f"{smt_logic}\n\n;; --- 自动生成的 ARXML 事实 ---\n{smt_data}\n"
            if "(check-sat)" not in full_script:
                full_script += "\n(check-sat)\n"

            # 步骤 4: 求解
            print("📝 步骤 2.4: 调用 Z3 求解器...")
            solve_result = self.solve_smt_instance(full_script)

            # 步骤 5: 分析和报告
            print("📝 步骤 2.5: 分析 Z3 结果...")
            return self._analyze_solve_result(solve_result)

        except ET.ParseError as e:
            print(f"❌ XML 解析错误: {e}")
            return self._create_error_result(f"XML ParseError: {e}", "FAILED")
        except Exception as e:
            print(f"❌ SMT 验证过程中发生意外错误: {e}")
            import traceback
            traceback.print_exc()
            return self._create_error_result(str(e), "ERROR")

    # ### 新增 ###: 辅助函数，用于获取元素的唯一路径
    def _get_element_path(self, element, parent_map):
        """通过父映射生成一个基于SHORT-NAME的唯一路径"""
        try:
            path_parts = []
            current = element
            while current in parent_map:
                name_elem = current.find('SHORT-NAME')
                if name_elem is not None and name_elem.text:
                    path_parts.append(name_elem.text)
                else:
                    # Fallback if no SHORT-NAME
                    path_parts.append(f"{self._clean_xml_tag(current.tag)}_{hash(current)}")
                current = parent_map[current]
            # Add root name
            name_elem = current.find('SHORT-NAME')
            if name_elem is not None and name_elem.text:
                path_parts.append(name_elem.text)

            return "/" + "/".join(reversed(path_parts))
        except Exception:
            # Fallback for root or errors
            name_elem = element.find('SHORT-NAME')
            if name_elem is not None:
                return name_elem.text
            return f"elem_{hash(element)}"

    # ### 新增 ###: 辅助函数，清理和创建SMT名称
    def _get_smt_name(self, element, prefix, parent_map):
        """获取或创建唯一的SMT标识符"""
        path = self._get_element_path(element, parent_map)
        if path in self.entity_map:
            return self.entity_map[path]

        short_name_elem = element.find('SHORT-NAME')
        if short_name_elem is not None and short_name_elem.text:
            # 清理 SMT 不支持的字符
            safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', short_name_elem.text)
            smt_name = f"{prefix}_{safe_name}"
        else:
            # 如果没有SHORT-NAME，使用计数器
            self.entity_counter += 1
            smt_name = f"{prefix}_id_{self.entity_counter}"

        self.entity_map[path] = smt_name
        return smt_name

    # ### 新增 ###: 核心事实生成器
    def _generate_smt_facts(self, root, parent_map):
        """
        遍历XML树并根据 constraints.smt2 [Source 53-246] 中的定义生成事实。
        """

        # 遍寻所有元素
        for element in root.iter():
            tag = self._clean_xml_tag(element.tag)

            try:
                # --- 1. 实例化主要实体 (Datatypes) ---
                # (declare-datatypes ((SwComponentType 0)) ((SCT (typeId Int)))) [Source 82]
                if tag == 'ECU-ABSTRACTION-SW-COMPONENT-TYPE':  # [Source 1]
                    smt_name = self._get_smt_name(element, 'SWC', parent_map)
                    self.entity_counter += 1
                    # 我们假设 SCT 匹配 SwComponentType
                    self.smt_facts.append(f"(assert (= {smt_name} (SCT {self.entity_counter})))")

                # (declare-datatypes ((RunnableEntity 0)) ((RE (reId Int) (symbol String)))) [Source 81]
                elif tag == 'RUNNABLE-ENTITY':  # [Source 7]
                    smt_name = self._get_smt_name(element, 'Runnable', parent_map)
                    symbol_elem = element.find('SYMBOL')
                    symbol = symbol_elem.text if symbol_elem is not None else ""  # [Source 17, 39, 52]
                    self.entity_counter += 1
                    self.smt_facts.append(f"(assert (= {smt_name} (RE {self.entity_counter} \"{symbol}\")))")

                # (declare-datatypes ((PortPrototype 0)) ((PP (portId Int) (isConnected Bool)))) [Source 82]
                elif tag == 'P-PORT-PROTOTYPE' or tag == 'R-PORT-PROTOTYPE':  # [Source 1, 3]
                    prefix = 'PPort' if tag == 'P-PORT-PROTOTYPE' else 'RPort'
                    smt_name = self._get_smt_name(element, prefix, parent_map)
                    self.entity_counter += 1
                    # 默认 isConnected 为 false，连接器会断言它为 true
                    self.smt_facts.append(f"(assert (= {smt_name} (PP {self.entity_counter} false)))")

                # (我们没有在 ARXML [Source 1-52] 中看到 ExclusiveArea，但 SMT [Source 53-246] 定义了它)
                # (declare-datatypes ((ExclusiveArea 0)) ((EA (eaId Int)))) [Source 81]
                elif tag == 'EXCLUSIVE-AREA':
                    smt_name = self._get_smt_name(element, 'EA', parent_map)
                    self.entity_counter += 1
                    self.smt_facts.append(f"(assert (= {smt_name} (EA {self.entity_counter})))")

                # --- 2. 实例化关系 (declare-fun) ---

                # (declare-fun get-owner-swc (RunnableEntity) AtomicSwComponentType) [Source 82]
                if tag == 'RUNNABLE-ENTITY':  # [Source 7]
                    runnable_smt_name = self._get_smt_name(element, 'Runnable', parent_map)

                    # 查找父级 SWC
                    current = element
                    owner_swc = None
                    while current in parent_map:
                        current = parent_map[current]
                        if self._clean_xml_tag(current.tag).endswith('SW-COMPONENT-TYPE'):  # [Source 1]
                            owner_swc = current
                            break

                    if owner_swc is not None:
                        swc_smt_name = self._get_smt_name(owner_swc, 'SWC', parent_map)
                        self.smt_facts.append(f"(assert (= (get-owner-swc {runnable_smt_name}) {swc_smt_name}))")

                # (declare-fun exclusiveAreas (RunnableEntity) (Set ExclusiveArea)) [Source 81]
                # (此 ARXML [Source 1-52] 中没有 exclusiveAreas，但逻辑如此)
                if tag == 'RUNNABLE-ENTITY':  # [Source 7]
                    runnable_smt_name = self._get_smt_name(element, 'Runnable', parent_map)
                    ea_refs = element.findall('.//RUNS-INSIDE-EXCLUSIVE-AREA-REF')
                    if not ea_refs:
                        self.smt_facts.append(
                            f"(assert (= (exclusiveAreas {runnable_smt_name}) (as set.empty (Set ExclusiveArea))))")
                    else:
                        # (此处需要更复杂的逻辑来解析 REF 并映射到 SMT 名称)
                        pass  # 示例中未包含，跳过

            except Exception as e:
                print(f"⚠️  在为 {tag} 生成事实时出错: {e}")
                pass  # 继续处理下一个元素

    # ### 新增 ###: 辅助函数，清理XML标签
    def _clean_xml_tag(self, tag: str) -> str:
        """清理XML标签名 {http://...}TAG -> TAG"""
        if '}' in tag:
            return tag.split('}')[1]
        return tag

    # ### 新增 ###: 分析 Z3 结果
    def _analyze_solve_result(self, solve_result: Dict) -> Dict:
        """将 Z3 求解结果转换为最终报告字典"""

        status = solve_result.get("status", "error")

        if status == "sat":
            print("   ✅ 结果: sat (通过)")
            return {
                "valid": True,
                "status_code": "SAT",
                "message": "ARXML data conforms to all SMT semantic constraints."
            }
        elif status == "unsat":
            print("   ❌ 结果: unsat (失败)")
            return {
                "valid": False,
                "status_code": "UNSAT",
                "message": "ARXML data VIOLATES SMT semantic constraints.",
                # (此处可以添加 get-unsat-core 来获取失败的断言)
            }
        elif status == "timeout":
            print("   ⚠️  结果: timeout (超时)")
            return {
                "valid": False,
                "status_code": "TIMEOUT",
                "message": "SMT solver timed out. Constraints could not be verified."
            }
        else:
            print(f"   🛑 结果: error ({solve_result.get('error', 'unknown')})")
            return {
                "valid": False,
                "status_code": "ERROR",
                "message": f"SMT solver failed to execute: {solve_result.get('error', 'unknown')}"
            }

    # ### MODIFIED ###: 保持此方法以处理 Z3 求解
    def solve_smt_instance(self, smt_instance: str) -> Dict:
        """求解SMT实例 (保持不变)"""
        if self.z3_available == "python":
            # 使用 `_solve_with_python_z3` (使用 parse_smt2_string 的版本)
            return self._solve_with_python_z3_parser(smt_instance)
        elif self.z3_available == "command":
            return self._solve_with_command_z3(smt_instance)
        else:
            return {"status": "error", "error": "Z3 not available"}

    # ### MODIFIED ###: 重命名并保留 *正确* 的 Z3 求解器
    # (这个版本使用 z3.parse_smt2_string，可以处理
    #  `declare-fun`, `forall` 等, [Source 53-246])
    def _solve_with_python_z3_parser(self, smt_instance: str) -> dict:
        """
        使用 Python Z3 包的 SMT-LIB 2 解析器进行求解。
        (这是原脚本中的第一个 _solve_with_python_z3 实现)
        """
        try:
            s = z3.Solver()
            # 直接用 z3 的 SMT-LIB2 解析器
            fmls = z3.parse_smt2_string(smt_instance)

            if isinstance(fmls, z3.AstVector):
                s.add(fmls)
            else:
                # (旧版 z3 可能返回列表)
                s.add(*fmls)

            res = s.check()
            model = s.model() if res == z3.sat else None

            return {
                "status": str(res),
                "method": "python_z3_parser",
                "model": str(model) if model is not None else None,
                "solver_assertions": len(s.assertions())
            }
        except Exception as e:
            print(f"   🛑 SMT Z3 解析器错误: {e}")
            return {"status": "error", "error": str(e), "method": "python_z3_parser"}

    # ### 保持不变 ###
    def _solve_with_command_z3(self, smt_instance: str) -> Dict:
        """使用命令行z3求解 (保持不变)"""
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.smt2', delete=False) as f:
                f.write(smt_instance)
                temp_file = f.name

            result = subprocess.run(
                ['z3', temp_file],
                capture_output=True,
                text=True,
                timeout=30  # 30秒超时
            )

            output = result.stdout.strip()

            if "sat" in output and "unsat" not in output:
                status = "sat"
            elif "unsat" in output:
                status = "unsat"
            else:
                status = "unknown"

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
            if temp_file:
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass

    # ### 保持不变 ###
    def _check_z3_availability(self):
        """检查Z3求解器可用性 (保持不变)"""
        try:
            import z3
            z3.Solver()  # 测试是否能实例化
            print("✅ 使用Python z3包 (z3-solver)")
            return "python"
        except ImportError:
            pass
        except Exception as e:
            print(f"⚠️  Python z3包导入了但无法使用: {e}")
            pass

        try:
            result = subprocess.run(["z3", "--version"],
                                    capture_output=True, timeout=5)
            if result.returncode == 0:
                print("✅ 使用命令行z3")
                return "command"
        except Exception:
            pass

        print("⚠️  Z3求解器不可用")
        return None

    # ### 保持不变 ###
    def _load_smt_template(self, path: str) -> str:
        """加载SMT模板 (保持不变)"""
        try:
            if Path(path).exists():
                with open(path, "r", encoding="utf-8") as fp:
                    return fp.read()
            else:
                print(f"⚠️  SMT模板文件不存在: {path}")
                return ""
        except Exception as e:
            print(f"⚠️  SMT模板加载失败: {e}")
            return ""

    # ### 辅助函数 (新) ###
    def _create_error_result(self, error_message: str, status_code: str = "ERROR") -> Dict:
        """创建统一的错误结果"""
        return {
            "valid": False,
            "status_code": status_code,
            "message": error_message,
        }

    # ==================================================================
    # ### 移除 ###: 所有旧的、不再使用的方法
    # ==================================================================
    # _filter_constraints_by_config (REMOVED)
    # _validate_structural_only (REMOVED)
    # _validate_semantic_only (REMOVED)
    # _analyze_validation_results (REMOVED - replaced by _analyze_solve_result)
    # _build_detailed_constraint_breakdown (REMOVED)
    # _build_complete_xml_model (RETAINED - 但现在仅用于解析)
    # _detect_wrapper_relationships (REMOVED)
    # _validate_with_concrete_smt_instances (REMOVED)
    # _validate_structural_constraint_concrete (REMOVED)
    # _count_actual_occurrences (REMOVED)
    # _generate_concrete_structural_smt (REMOVED)
    # _safe_int_conversion (REMOVED)
    # _create_safe_smt_identifier (REMOVED)
    # _validate_semantic_constraint_concrete (REMOVED)
    # _validate_existence_constraint_concrete (REMOVED)
    # _validate_value_restriction_concrete (REMOVED)
    # _validate_cardinality_constraint_concrete (REMOVED)
    # _check_element_exists_concrete (REMOVED)
    # _get_element_values_concrete (REMOVED)
    # _generate_concrete_existence_smt (REMOVED)
    # _load_enriched_constraints (REMOVED)
    # _build_mapping_tables (REMOVED)
    # _solve_with_python_z3 (REMOVED - 两个版本被合并/重命名)
    # _validate_constraints_as_recommendations (REMOVED)
    # _perform_basic_validation (REMOVED)

    # ### 保留 ###: XML解析器 (v4.0中的版本)
    def _build_complete_xml_model(self, xml_content: str) -> Optional[Dict]:
        """(保留) 构建完整的XML模型，包含实体映射"""
        try:
            root = ET.fromstring(xml_content)
            parent_map = {c: p for p in root.iter() for c in p}

            xml_model = {
                "root": root,
                "entities": {},  # tag -> List[XMLEntity]
                "parent_child_map": parent_map
                # (移除 V4 中其他未使用的字段)
            }

            entity_id = 0
            for elem in root.iter():
                clean_tag = self._clean_xml_tag(elem.tag)

                parent_elem = xml_model["parent_child_map"].get(elem)
                parent_tag = self._clean_xml_tag(parent_elem.tag) if parent_elem is not None else None

                xml_entity = {
                    "id": f"entity_{entity_id}",
                    "tag": clean_tag,
                    "element": elem,
                    "text": elem.text.strip() if elem.text and elem.text.strip() else None,
                    "attributes": dict(elem.attrib),
                    "parent_tag": parent_tag,
                    "children_tags": [self._clean_xml_tag(child.tag) for child in elem]
                }

                if clean_tag not in xml_model["entities"]:
                    xml_model["entities"][clean_tag] = []
                xml_model["entities"][clean_tag].append(xml_entity)
                entity_id += 1

            print(f"   📊 (保留的解析器) XML模型构建完成: {entity_id} 个元素")
            return xml_model

        except ET.ParseError as e:
            print(f"❌ (保留的解析器) XML解析错误: {e}")
            return None
        except Exception as e:
            print(f"❌ (保留的解析器) XML模型构建错误: {e}")
            import traceback
            traceback.print_exc()
            return None