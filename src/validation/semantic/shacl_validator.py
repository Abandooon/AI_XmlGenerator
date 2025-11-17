# src/validation/semantic/shacl_validator.py (增强版 - 支持细粒度控制)
from typing import Dict, List, Optional
import rdflib
from pyshacl import validate
import xml.etree.ElementTree as ET
import json
from pathlib import Path


class SHACLValidator:
    """SHACL语义约束验证器 - 增强版（支持细粒度控制）"""

    def __init__(self, shapes_file: str,
                 raw_attributes_file: Optional[str] = None,
                 enriched_constraints_file: Optional[str] = None,
                 semantic_config: Optional[Dict] = None):
        """
        初始化SHACL验证器

        Args:
            shapes_file: SHACL形状文件路径 (autosar_shapes.ttl)
            raw_attributes_file: raw_attributes.jsonl文件路径 (可选，启用映射功能)
            enriched_constraints_file: enriched_constraints.json文件路径 (可选，增强映射)
            semantic_config: 语义验证配置 (新增)
        """
        print("🔧 初始化SHACL验证器...")

        self.shapes_file = shapes_file

        # 🔧 语义验证配置处理
        self.semantic_config = semantic_config or {}
        self.validation_scope = self.semantic_config.get('validation_scope', {})
        self.validation_strategy = self.semantic_config.get('validation_strategy', {})
        self.performance_config = self.semantic_config.get('performance', {})
        self.output_config = self.semantic_config.get('output', {})

        # 解析验证模式和范围
        self.validation_mode = self.validation_strategy.get('mode', 'hybrid')
        self.severity_filter = self.validation_strategy.get('severity_filter', {})
        self.semantic_types_enabled = self.validation_scope.get('semantic_types', {})

        print(f"📋 SHACL验证配置:")
        print(f"   验证模式: {self.validation_mode}")
        print(f"   结构验证: {'启用' if self.validation_scope.get('structural_validation', True) else '禁用'}")
        print(f"   语义验证: {'启用' if self.validation_scope.get('semantic_validation', True) else '禁用'}")

        # 显示启用的约束类型
        if self.semantic_types_enabled:
            enabled_types = [k for k, v in self.semantic_types_enabled.items() if v]
            disabled_types = [k for k, v in self.semantic_types_enabled.items() if not v]
            if enabled_types:
                print(f"   启用类型: {', '.join(enabled_types)}")
            if disabled_types:
                print(f"   禁用类型: {', '.join(disabled_types)}")

        # 加载SHACL形状
        self.shapes_graph = self._load_shapes(shapes_file)

        # 映射机制 - 向后兼容
        self.mapping_enabled = raw_attributes_file is not None
        self.xml_to_attr_mapping = {}
        self.attr_to_xml_mapping = {}
        self.class_context_mapping = {}

        # Wrapper标签映射表
        self.wrapper_mappings = {}
        self.text_content_mappings = {}

        if self.mapping_enabled:
            print("🔧 启用增强映射功能（包含Wrapper处理）")
            self._build_mapping_tables(raw_attributes_file)

            if enriched_constraints_file:
                self._load_constraint_mappings(enriched_constraints_file)
        else:
            print("📝 使用标准验证模式")

        print("✅ SHACL验证器初始化完成")

    def validate_semantics(self, xml_content: str) -> Dict:
        """执行SHACL语义验证 - 支持细粒度控制的版本"""
        print(f"\n🔍 开始SHACL语义验证 ({self.validation_mode} 模式)...")

        try:
            if len(self.shapes_graph) == 0:
                print("❌ SHACL shapes为空，无法执行验证")
                return self._create_error_result("SHACL shapes文件为空或加载失败")

            # 🔧 根据验证模式决定验证范围
            if self.validation_mode == "structural_only":
                print("🔧 仅进行结构性SHACL验证")
                return self._validate_structural_only(xml_content)
            elif self.validation_mode == "semantic_only":
                print("🔧 仅进行语义性SHACL验证")
                return self._validate_semantic_only(xml_content)
            else:  # hybrid mode
                print("🔧 混合SHACL验证模式")
                return self._validate_hybrid_mode(xml_content)

        except Exception as e:
            print(f"❌ SHACL验证过程出错: {e}")
            import traceback
            traceback.print_exc()
            return self._create_error_result(str(e))

    def _validate_structural_only(self, xml_content: str) -> Dict:
        """🔧 新增：仅验证结构性SHACL约束"""
        print("📝 执行结构性SHACL验证...")

        # XML转RDF
        rdf_graph = self._xml_to_rdf_with_config(xml_content)
        if len(rdf_graph) == 0:
            return self._create_error_result("XML转RDF失败")

        # 执行SHACL验证，重点关注结构约束
        validation_result = self._execute_shacl_validation(rdf_graph)

        # 过滤结果，只保留结构性违规
        filtered_violations = self._filter_structural_violations(validation_result['violations'])

        # 构建结果
        result = self._build_validation_result(
            validation_result,
            filtered_violations,
            mode="structural_only"
        )

        return result

    def _validate_semantic_only(self, xml_content: str) -> Dict:
        """🔧 新增：仅验证语义性SHACL约束"""
        print("📝 执行语义性SHACL验证...")

        # XML转RDF
        rdf_graph = self._xml_to_rdf_with_config(xml_content)
        if len(rdf_graph) == 0:
            return self._create_error_result("XML转RDF失败")

        # 执行SHACL验证
        validation_result = self._execute_shacl_validation(rdf_graph)

        # 过滤结果，只保留语义性违规，并按类型过滤
        filtered_violations = self._filter_semantic_violations(validation_result['violations'])

        # 构建结果
        result = self._build_validation_result(
            validation_result,
            filtered_violations,
            mode="semantic_only"
        )

        return result

    def _validate_hybrid_mode(self, xml_content: str) -> Dict:
        """🔧 新增：混合验证模式"""
        print("📝 执行混合SHACL验证...")

        # XML转RDF
        rdf_graph = self._xml_to_rdf_with_config(xml_content)
        if len(rdf_graph) == 0:
            return self._create_error_result("XML转RDF失败")

        # 执行SHACL验证
        validation_result = self._execute_shacl_validation(rdf_graph)

        # 应用配置的过滤器
        filtered_violations = self._filter_violations_by_config(validation_result['violations'])

        # 构建结果
        result = self._build_validation_result(
            validation_result,
            filtered_violations,
            mode="hybrid"
        )

        return result

    def _xml_to_rdf_with_config(self, xml_content: str) -> rdflib.Graph:
        """🔧 根据配置转换XML到RDF"""
        if self.mapping_enabled:
            return self._xml_to_rdf_enhanced_fixed(xml_content)
        else:
            return self._xml_to_rdf_standard_fixed(xml_content)

    def _execute_shacl_validation(self, rdf_graph: rdflib.Graph) -> Dict:
        """🔧 执行SHACL验证核心逻辑"""
        try:
            print(f"✅ RDF图生成成功，包含 {len(rdf_graph)} 个三元组")
            print("📝 执行SHACL约束验证...")

            # 执行pyshacl验证
            validation_result = validate(
                data_graph=rdf_graph,
                shacl_graph=self.shapes_graph,
                inference='rdfs',
                abort_on_first=False,
                debug=False
            )

            # 处理验证结果
            if isinstance(validation_result, tuple):
                if len(validation_result) >= 3:
                    conforms, results_graph, results_text = validation_result[:3]
                elif len(validation_result) == 2:
                    conforms, results_graph = validation_result
                    results_text = "No detailed results available"
                else:
                    conforms = validation_result[0] if validation_result else False
                    results_graph = rdflib.Graph()
                    results_text = "Unexpected validation result format"
            else:
                print(f"⚠️  非标准验证结果类型: {type(validation_result)}")
                conforms = False
                results_graph = None
                results_text = str(validation_result)

            print(f"✅ SHACL验证完成，整体符合性: {conforms}")

            # 提取违规信息
            violations = []
            if not conforms:
                if results_graph is not None and hasattr(results_graph, 'subjects'):
                    try:
                        if self.mapping_enabled:
                            violations = self._extract_violations_enhanced(results_graph)
                        else:
                            violations = self._extract_violations_standard(results_graph)
                    except Exception as extract_error:
                        print(f"⚠️  从RDF图提取违规信息失败: {extract_error}")
                        violations = self._extract_violations_from_text(results_text)
                else:
                    print("⚠️  results_graph无效，尝试从文本提取违规信息")
                    violations = self._extract_violations_from_text(results_text)

            return {
                'conforms': conforms,
                'violations': violations,
                'results_text': results_text,
                'rdf_triples': len(rdf_graph)
            }

        except Exception as e:
            print(f"❌ SHACL验证执行失败: {e}")
            return {
                'conforms': False,
                'violations': [{"message": f"SHACL验证执行失败: {str(e)}", "severity": "Error"}],
                'results_text': str(e),
                'rdf_triples': 0
            }

    def _filter_structural_violations(self, violations: List[Dict]) -> List[Dict]:
        """🔧 过滤结构性违规"""
        # 结构性约束通常涉及：基数、必需属性、数据类型等
        structural_indicators = [
            'cardinality', 'mincount', 'maxcount', 'required', 'datatype',
            'exists', 'presence', 'mandatory', 'MinCountConstraintComponent',
            'MaxCountConstraintComponent', 'DatatypeConstraintComponent'
        ]

        filtered = []
        for violation in violations:
            # 检查约束组件是否为结构性
            constraint_component = violation.get('constraint_component', '').lower()
            message = violation.get('message', '').lower()

            is_structural = any(indicator in constraint_component or indicator in message
                                for indicator in structural_indicators)

            if is_structural:
                violation['violation_category'] = 'structural'
                filtered.append(violation)

        print(f"📊 过滤结构性违规: {len(filtered)}/{len(violations)} 个")
        return filtered

    def _filter_semantic_violations(self, violations: List[Dict]) -> List[Dict]:
        """🔧 过滤语义性违规并按类型分类"""
        # 语义性约束通常涉及：值限制、格式、依赖关系等
        semantic_type_indicators = {
            'value_restriction': ['pattern', 'enum', 'in', 'hasvalue', 'value'],
            'format': ['pattern', 'regex', 'format', 'PatternConstraintComponent'],
            'dependency': ['qualified', 'if', 'then', 'conditional', 'QualifiedConstraintComponent'],
            'range': ['min', 'max', 'range', 'MinInclusiveConstraintComponent', 'MaxInclusiveConstraintComponent'],
            'existence': ['exists', 'not', 'NotConstraintComponent'],
            'mutual_exclusion': ['xone', 'or', 'ExclusiveOr'],
            'other': []
        }

        filtered = []
        for violation in violations:
            constraint_component = violation.get('constraint_component', '').lower()
            message = violation.get('message', '').lower()
            result_path = violation.get('result_path', '').lower()

            # 确定语义约束类型
            semantic_type = 'other'
            for type_name, indicators in semantic_type_indicators.items():
                if any(indicator in constraint_component or indicator in message or indicator in result_path
                       for indicator in indicators):
                    semantic_type = type_name
                    break

            # 检查该类型是否被启用
            if self.semantic_types_enabled.get(semantic_type, True):
                violation['violation_category'] = 'semantic'
                violation['semantic_type'] = semantic_type
                filtered.append(violation)

        print(f"📊 过滤语义性违规: {len(filtered)}/{len(violations)} 个")

        # 按类型统计
        type_counts = {}
        for violation in filtered:
            semantic_type = violation.get('semantic_type', 'other')
            type_counts[semantic_type] = type_counts.get(semantic_type, 0) + 1

        for type_name, count in type_counts.items():
            status = "启用" if self.semantic_types_enabled.get(type_name, True) else "禁用"
            print(f"   {type_name}: {count} 个 ({status})")

        return filtered

    def _filter_violations_by_config(self, violations: List[Dict]) -> List[Dict]:
        """🔧 根据配置过滤违规"""
        filtered = []

        # 应用严重性过滤
        semantic_severities = self.severity_filter.get('semantic', ['violation', 'warning', 'info'])
        structural_severities = self.severity_filter.get('structural', ['violation'])

        for violation in violations:
            severity = violation.get('severity', 'violation').lower()

            # 确定违规类别
            is_structural = self._is_structural_violation(violation)
            is_semantic = not is_structural

            # 应用过滤规则
            should_include = False

            if is_structural and self.validation_scope.get('structural_validation', True):
                should_include = severity in [s.lower() for s in structural_severities]
                violation['violation_category'] = 'structural'
            elif is_semantic and self.validation_scope.get('semantic_validation', True):
                # 进一步检查语义类型过滤
                semantic_type = self._determine_semantic_type(violation)
                type_enabled = self.semantic_types_enabled.get(semantic_type, True)
                severity_allowed = severity in [s.lower() for s in semantic_severities]

                should_include = type_enabled and severity_allowed
                violation['violation_category'] = 'semantic'
                violation['semantic_type'] = semantic_type

            if should_include:
                filtered.append(violation)

        print(f"📊 配置过滤后违规: {len(filtered)}/{len(violations)} 个")
        return filtered

    def _is_structural_violation(self, violation: Dict) -> bool:
        """🔧 判断是否为结构性违规"""
        structural_indicators = [
            'cardinality', 'mincount', 'maxcount', 'required', 'datatype',
            'exists', 'presence', 'mandatory', 'MinCountConstraintComponent',
            'MaxCountConstraintComponent', 'DatatypeConstraintComponent'
        ]

        constraint_component = violation.get('constraint_component', '').lower()
        message = violation.get('message', '').lower()

        return any(indicator in constraint_component or indicator in message
                   for indicator in structural_indicators)

    def _determine_semantic_type(self, violation: Dict) -> str:
        """🔧 确定语义违规类型"""
        semantic_type_indicators = {
            'value_restriction': ['pattern', 'enum', 'in', 'hasvalue', 'value'],
            'format': ['pattern', 'regex', 'format', 'PatternConstraintComponent'],
            'dependency': ['qualified', 'if', 'then', 'conditional', 'QualifiedConstraintComponent'],
            'range': ['min', 'max', 'range', 'MinInclusiveConstraintComponent', 'MaxInclusiveConstraintComponent'],
            'existence': ['exists', 'not', 'NotConstraintComponent'],
            'mutual_exclusion': ['xone', 'or', 'ExclusiveOr'],
            'cardinality': ['count', 'cardinality', 'occurs'],
            'behavioral': ['order', 'sequence', 'state', 'temporal']
        }

        constraint_component = violation.get('constraint_component', '').lower()
        message = violation.get('message', '').lower()
        result_path = violation.get('result_path', '').lower()

        for type_name, indicators in semantic_type_indicators.items():
            if any(indicator in constraint_component or indicator in message or indicator in result_path
                   for indicator in indicators):
                return type_name

        return 'other'

    def _build_validation_result(self, validation_result: Dict, filtered_violations: List[Dict], mode: str) -> Dict:
        """🔧 构建验证结果"""
        conforms = validation_result['conforms']

        # 按严重性分类统计
        violation_stats = self._categorize_violations(filtered_violations)

        # 🔧 构建详细的违规分解
        violation_breakdown = self._build_violation_breakdown(filtered_violations)

        # 判断验证结果
        structural_valid = violation_stats['violations'] == 0

        if violation_stats['warnings'] == 0:
            semantic_compliance = "FULL"
        elif violation_stats['warnings'] <= len(filtered_violations) * 0.2:
            semantic_compliance = "HIGH"
        elif violation_stats['warnings'] <= len(filtered_violations) * 0.5:
            semantic_compliance = "PARTIAL"
        else:
            semantic_compliance = "LOW"

        # 根据验证模式调整整体有效性
        if mode == "structural_only":
            overall_valid = structural_valid
        elif mode == "semantic_only":
            overall_valid = semantic_compliance in ["FULL", "HIGH"]
        else:  # hybrid
            overall_valid = structural_valid and (semantic_compliance in ["FULL", "HIGH"])

        print(f"📊 SHACL验证结果 ({mode} 模式):")
        print(f"   🔧 结构有效性: {'✅ 通过' if structural_valid else '❌ 失败'}")
        print(f"   💡 语义合规性: {semantic_compliance}")
        print(f"   📈 总体: {'✅ 通过' if overall_valid else '❌ 失败'}")

        result = {
            "valid": overall_valid,
            "structural_valid": structural_valid,
            "semantic_compliance": semantic_compliance,
            "violation_count": len(filtered_violations),
            "violation_stats": violation_stats,
            "violations": filtered_violations,
            "violation_breakdown": violation_breakdown,
            "results_text": validation_result['results_text'],
            "rdf_triples": validation_result['rdf_triples'],
            "shapes_applied": len(self.shapes_graph),
            "validation_mode": mode
        }

        # 增强模式下添加额外信息
        if self.mapping_enabled:
            result["mapping_stats"] = {
                "xml_to_attr_mappings": len(self.xml_to_attr_mapping),
                "attr_to_xml_mappings": len(self.attr_to_xml_mapping),
                "wrapper_mappings": len(self.wrapper_mappings),
                "text_content_mappings": len(self.text_content_mappings),
                "mapping_enabled": True
            }
        else:
            result["mapping_stats"] = {"mapping_enabled": False}

        # 🔧 新增：配置信息
        result["validation_config"] = {
            "structural_enabled": self.validation_scope.get('structural_validation', True),
            "semantic_enabled": self.validation_scope.get('semantic_validation', True),
            "semantic_types_config": self.semantic_types_enabled,
            "severity_filter": self.severity_filter,
            "mode": mode
        }

        return result

    def _build_violation_breakdown(self, violations: List[Dict]) -> Dict:
        """🔧 构建详细的违规类型分解"""
        breakdown = {
            "summary": {
                "total_violations": len(violations),
                "validation_mode": self.validation_mode
            },
            "structural": {},
            "semantic": {}
        }

        # 分析结构违规
        structural_violations = [v for v in violations if v.get('violation_category') == 'structural']
        structural_type_stats = {}
        for violation in structural_violations:
            constraint_type = violation.get('constraint_component', 'unknown')
            if constraint_type not in structural_type_stats:
                structural_type_stats[constraint_type] = {
                    "total": 0,
                    "violations": 0,
                    "enabled": True
                }
            structural_type_stats[constraint_type]["total"] += 1
            structural_type_stats[constraint_type]["violations"] += 1

        breakdown["structural"] = structural_type_stats

        # 分析语义违规
        semantic_violations = [v for v in violations if v.get('violation_category') == 'semantic']
        semantic_type_stats = {}
        for violation in semantic_violations:
            semantic_type = violation.get('semantic_type', 'other')
            severity = violation.get('severity', 'violation').lower()

            if semantic_type not in semantic_type_stats:
                semantic_type_stats[semantic_type] = {
                    "total": 0,
                    "violations": 0,
                    "warnings": 0,
                    "info": 0,
                    "enabled": self.semantic_types_enabled.get(semantic_type, True)
                }

            semantic_type_stats[semantic_type]["total"] += 1
            if severity in ['violation', 'error']:
                semantic_type_stats[semantic_type]["violations"] += 1
            elif severity == 'warning':
                semantic_type_stats[semantic_type]["warnings"] += 1
            elif severity == 'info':
                semantic_type_stats[semantic_type]["info"] += 1

        breakdown["semantic"] = semantic_type_stats

        # 🔧 配置信息
        breakdown["configuration"] = {
            "structural_enabled": self.validation_scope.get('structural_validation', True),
            "semantic_enabled": self.validation_scope.get('semantic_validation', True),
            "semantic_types_config": self.semantic_types_enabled,
            "severity_filter": self.severity_filter
        }

        return breakdown

    def _create_error_result(self, error_message: str) -> Dict:
        """创建错误结果"""
        return {
            "valid": False,
            "structural_valid": False,
            "semantic_compliance": "ERROR",
            "violation_count": 1,
            "violation_stats": {"violations": 1, "warnings": 0, "info": 0},
            "violations": [{"message": error_message, "severity": "Error"}],
            "violation_breakdown": {},
            "results_text": error_message,
            "rdf_triples": 0,
            "shapes_applied": 0,
            "validation_mode": self.validation_mode,
            "error": error_message
        }

    # ==================== 原有方法保持不变 ====================
    # 以下方法保持原有实现，只需要确保它们被正确调用

    def _load_shapes(self, shapes_file: str) -> rdflib.Graph:
        """加载SHACL形状文件"""
        try:
            shapes_graph = rdflib.Graph()

            if not Path(shapes_file).exists():
                print(f"⚠️  SHACL shapes文件不存在: {shapes_file}")
                return shapes_graph

            try:
                shapes_graph.parse(shapes_file, format="turtle")
            except Exception as parse_error:
                print(f"❌ TTL解析错误: {parse_error}")
                try:
                    with open(shapes_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    content = self._fix_ttl_content(content)
                    shapes_graph.parse(data=content, format="turtle")
                    print("✅ TTL文件经修复后成功解析")
                except Exception as retry_error:
                    print(f"❌ TTL修复后仍无法解析: {retry_error}")
                    return rdflib.Graph()

            SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
            node_shapes = len(list(shapes_graph.subjects(rdflib.RDF.type, SH.NodeShape)))
            property_shapes = len(list(shapes_graph.subjects(rdflib.RDF.type, SH.PropertyShape)))

            print(f"✅ SHACL shapes加载成功: {Path(shapes_file).name}")
            print(f"   📊 包含 {node_shapes} 个节点形状, {property_shapes} 个属性形状")
            print(f"   📊 总计 {len(shapes_graph)} 个RDF三元组")

            return shapes_graph

        except Exception as e:
            print(f"⚠️  SHACL shapes加载失败: {e}")
            return rdflib.Graph()

    def _fix_ttl_content(self, content: str) -> str:
        """修复TTL内容"""
        import re

        # 移除控制字符表示
        content = re.sub(r'\^[a-zA-Z@\[\\\]^_]', '', content)
        content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', content)
        content = re.sub(r'\\x[0-9a-fA-F]{2}', '', content)
        content = re.sub(r"b'([^']*)'", r'\1', content)

        # 替换特殊Unicode字符
        replacements = {
            '•': 'bullet', '"': '"', '"': '"', ''': "'", ''': "'",
            '–': '-', '—': '-', '…': '...',
        }

        for old_char, new_char in replacements.items():
            content = content.replace(old_char, new_char)

        lines = content.split('\n')
        fixed_lines = []

        for line in lines:
            if 'sh:pattern' in line:
                match = re.search(r'sh:pattern\s+"([^"]*)"', line)
                if match:
                    pattern = match.group(1)
                    simplified_pattern = pattern.replace('\\|', 'pipe')
                    simplified_pattern = simplified_pattern.replace('\\\\', '\\')
                    line = re.sub(r'sh:pattern\s+"[^"]*"', f'sh:pattern "{simplified_pattern}"', line)

            quote_count = line.count('"')
            if quote_count % 2 != 0:
                if any(keyword in line for keyword in ['sh:message', 'rdfs:label', 'rdfs:comment']):
                    if line.endswith(' ;'):
                        line = line[:-2] + '" ;'
                    elif line.endswith(' .'):
                        line = line[:-2] + '" .'
                    elif not line.endswith('"'):
                        line = line + '"'

            line = re.sub(r'[^\x20-\x7E\r\n]', '', line)
            fixed_lines.append(line)

        fixed_content = '\n'.join(fixed_lines)
        fixed_content = re.sub(r'\\{3,}', '\\\\', fixed_content)

        return fixed_content

    def _build_mapping_tables(self, raw_attributes_file: str):
        """从raw_attributes.jsonl构建映射表"""
        try:
            known_wrappers = {
                'RUNNABLES': 'RUNNABLE-ENTITY',
                'INTERNAL-BEHAVIORS': 'SWC-INTERNAL-BEHAVIOR',
                'EXTERNAL-BEHAVIORS': 'SWC-EXTERNAL-BEHAVIOR',
                'PORTS': 'P-PORT-PROTOTYPE',
                'PROVIDED-PORTS': 'P-PORT-PROTOTYPE',
                'REQUIRED-PORTS': 'R-PORT-PROTOTYPE',
                'SW-COMPONENTS': 'APPLICATION-SW-COMPONENT-TYPE',
                'DATA-ELEMENTS': 'VARIABLE-DATA-PROTOTYPE',
                'ELEMENTS': 'AUTOSAR-ELEMENT',
                'CONNECTORS': 'ASSEMBLY-SW-CONNECTOR',
                'MAPPINGS': 'DATA-MAPPING',
                'CONSTRAINTS': 'CONSTRAINT',
                'VARIANTS': 'VARIANT',
                'COMPOSITIONS': 'COMPOSITION-SW-COMPONENT-TYPE'
            }

            text_content_elements = {
                'SD': 'VALUE',
                'VALUE': 'VALUE',
                'SHORT-NAME': 'VALUE',
                'CATEGORY': 'VALUE',
                'UUID': 'VALUE',
                'DESC': 'VALUE',
                'INTRODUCTION': 'VALUE'
            }

            with open(raw_attributes_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        attr_record = json.loads(line)

                        class_id = attr_record["classId"]
                        attr_id = attr_record["attrId"]
                        xml_tag = attr_record["xml_tag"]
                        xml_wrapper_tag = attr_record.get("xml_wrapper_tag")

                        if xml_wrapper_tag:
                            self.wrapper_mappings[xml_wrapper_tag] = xml_tag
                            # print(f"🔗 发现Wrapper映射: {xml_wrapper_tag} -> {xml_tag}")

                        attr_uri = f"ATTR_{attr_id}"
                        context_key = f"{class_id}:{xml_tag}"
                        self.xml_to_attr_mapping[context_key] = attr_uri

                        if xml_tag not in self.xml_to_attr_mapping:
                            self.xml_to_attr_mapping[xml_tag] = attr_uri

                        self.attr_to_xml_mapping[attr_uri] = xml_tag

                        if class_id not in self.class_context_mapping:
                            self.class_context_mapping[class_id] = {}
                        self.class_context_mapping[class_id][xml_tag] = attr_uri

            for wrapper, item in known_wrappers.items():
                if wrapper not in self.wrapper_mappings:
                    self.wrapper_mappings[wrapper] = item

            self.text_content_mappings = text_content_elements

            print(f"✅ 构建映射表成功:")
            print(f"   📋 XML->Attr映射: {len(self.xml_to_attr_mapping)} 个")
            print(f"   📦 Wrapper映射: {len(self.wrapper_mappings)} 个")
            print(f"   📝 文本内容映射: {len(self.text_content_mappings)} 个")

        except Exception as e:
            print(f"❌ 构建映射表失败: {e}")
            self.mapping_enabled = False

    def _load_constraint_mappings(self, enriched_constraints_file: str):
        """从enriched_constraints.json加载约束映射信息"""
        try:
            with open(enriched_constraints_file, 'r', encoding='utf-8') as f:
                constraints = json.load(f)

            for constraint in constraints:
                xml_mapping = constraint.get("xml_mapping", {})
                for attr_key, mapping_info in xml_mapping.items():
                    xml_tag = mapping_info["xml_tag"]
                    context_path = mapping_info["context_path"]

                    self.xml_to_attr_mapping[context_path] = attr_key
                    self.xml_to_attr_mapping[xml_tag] = attr_key
                    self.attr_to_xml_mapping[attr_key] = xml_tag

            print(f"✅ 加载约束映射成功")

        except Exception as e:
            print(f"⚠️  加载约束映射失败: {e}")

    def _categorize_violations(self, violations: List[Dict]) -> Dict[str, int]:
        """按严重性对违规进行分类统计"""
        stats = {"violations": 0, "warnings": 0, "info": 0}

        for violation in violations:
            severity = violation.get("severity", "Violation").lower()
            if severity in ['violation', 'error']:
                stats["violations"] += 1
            elif severity == "warning":
                stats["warnings"] += 1
            elif severity == "info":
                stats["info"] += 1
            else:
                stats["violations"] += 1

        return stats

    def _extract_violations_from_text(self, results_text: str) -> List[Dict]:
        """从验证结果文本提取违规信息"""
        violations = []

        if not results_text:
            return [{
                "severity": "Violation",
                "message": "SHACL validation failed but no details available",
                "focus_node": "unknown",
                "result_path": "unknown"
            }]

        try:
            text_str = str(results_text)
            if "violation" in text_str.lower() or "constraint" in text_str.lower():
                lines = text_str.split('\n')
                for line in lines:
                    if line.strip() and any(
                            keyword in line.lower() for keyword in ['violation', 'constraint', 'failed', 'error']):
                        violations.append({
                            "severity": "Violation",
                            "message": line.strip()[:200],
                            "focus_node": "unknown",
                            "result_path": "unknown"
                        })

            if not violations:
                violations.append({
                    "severity": "Violation",
                    "message": f"SHACL validation failed: {text_str[:200]}...",
                    "focus_node": "unknown",
                    "result_path": "unknown"
                })

        except Exception as e:
            violations.append({
                "severity": "Error",
                "message": f"Failed to parse validation results: {str(e)}",
                "focus_node": "unknown",
                "result_path": "unknown"
            })

        return violations

    def _xml_to_rdf_enhanced_fixed(self, xml_content: str) -> rdflib.Graph:
        """增强的XML到RDF转换"""
        graph = rdflib.Graph()
        element_count = 0

        try:
            root = ET.fromstring(xml_content)
            print(f"📋 解析XML根元素: {root.tag}")

            AUTOSAR = rdflib.Namespace("http://autosar.org/")
            graph.bind("autosar", AUTOSAR)

            def clean_element_name(tag):
                if '}' in tag:
                    return tag.split('}')[1]
                return tag

            def is_wrapper_element(tag_name: str) -> bool:
                return tag_name in self.wrapper_mappings

            def get_expected_item_tag(wrapper_tag: str) -> str:
                return self.wrapper_mappings.get(wrapper_tag, wrapper_tag)

            def should_treat_as_text_content(element) -> bool:
                clean_tag = clean_element_name(element.tag)
                return (
                        element.text and element.text.strip() and
                        len(element) == 0 and
                        clean_tag in self.text_content_mappings
                )

            def xml_to_triples_enhanced_fixed(element, subject_uri=None, parent_class_id=None, depth=0):
                nonlocal element_count

                if depth > 20:
                    return

                element_count += 1
                clean_tag = clean_element_name(element.tag)

                if subject_uri is None:
                    subject_uri = f"http://autosar.org/instance/{clean_tag}_{element_count}"

                subject = rdflib.URIRef(subject_uri)

                if is_wrapper_element(clean_tag):
                    # print(f"🔗 处理Wrapper元素: {clean_tag}")

                    expected_item_tag = get_expected_item_tag(clean_tag)

                    for i, child in enumerate(element):
                        clean_child_tag = clean_element_name(child.tag)

                        if clean_child_tag == expected_item_tag:
                            child_uri = f"{subject_uri.rsplit('/', 1)[0]}/{expected_item_tag}_{i}"
                            child_subject = rdflib.URIRef(child_uri)

                            parent_subject = rdflib.URIRef(subject_uri.rsplit('/', 1)[0])
                            predicate = AUTOSAR[expected_item_tag]
                            graph.add((parent_subject, predicate, child_subject))

                            # print(f"   🔗 透明连接: {parent_subject} --{expected_item_tag}--> {child_subject}")

                            xml_to_triples_enhanced_fixed(child, child_uri, parent_class_id, depth)
                        else:
                            child_uri = f"{subject_uri}/{clean_child_tag}_{i}"
                            predicate = AUTOSAR[clean_child_tag]
                            child_subject = rdflib.URIRef(child_uri)
                            graph.add((subject, predicate, child_subject))
                            xml_to_triples_enhanced_fixed(child, child_uri, None, depth + 1)

                    return

                if should_treat_as_text_content(element):
                    # print(f"📝 处理文本内容元素: {clean_tag} = '{element.text.strip()}'")

                    element_type_uri = AUTOSAR[clean_tag]
                    graph.add((subject, rdflib.RDF.type, element_type_uri))

                    expected_attr = self.text_content_mappings[clean_tag]
                    predicate = AUTOSAR[expected_attr]
                    obj = rdflib.Literal(element.text.strip())
                    graph.add((subject, predicate, obj))

                    # print(f"   📝 文本映射: {clean_tag}.{expected_attr} = '{element.text.strip()}'")
                    return

                element_type_uri = AUTOSAR[clean_tag]
                graph.add((subject, rdflib.RDF.type, element_type_uri))

                for attr_name, attr_value in element.attrib.items():
                    clean_attr = clean_element_name(attr_name)
                    current_class_id = hash(clean_tag) % 10000
                    attr_uri_key = self._resolve_attr_mapping(clean_attr, current_class_id)

                    if attr_uri_key:
                        predicate = AUTOSAR[attr_uri_key]
                        obj = rdflib.Literal(attr_value)
                        graph.add((subject, predicate, obj))
                    else:
                        predicate = AUTOSAR[clean_attr]
                        obj = rdflib.Literal(attr_value)
                        graph.add((subject, predicate, obj))

                if element.text and element.text.strip() and len(element) > 0:
                    predicate = AUTOSAR["hasValue"]
                    obj = rdflib.Literal(element.text.strip())
                    graph.add((subject, predicate, obj))

                for i, child in enumerate(element):
                    clean_child_tag = clean_element_name(child.tag)
                    child_uri = f"{subject_uri}/{clean_child_tag}_{i}"

                    predicate = AUTOSAR[clean_child_tag]
                    child_subject = rdflib.URIRef(child_uri)
                    graph.add((subject, predicate, child_subject))

                    xml_to_triples_enhanced_fixed(child, child_uri, None, depth + 1)

            xml_to_triples_enhanced_fixed(root)
            print(f"📊 处理了 {element_count} 个XML元素")

        except ET.ParseError as e:
            print(f"❌ XML解析错误: {e}")
        except Exception as e:
            print(f"❌ XML转RDF错误: {e}")

        return graph

    def _xml_to_rdf_standard_fixed(self, xml_content: str) -> rdflib.Graph:
        """标准的XML到RDF转换"""
        graph = rdflib.Graph()
        element_count = 0

        try:
            root = ET.fromstring(xml_content)
            print(f"📋 解析XML根元素: {root.tag}")

            AUTOSAR = rdflib.Namespace("http://autosar.org/")
            graph.bind("autosar", AUTOSAR)

            def clean_element_name(tag):
                if '}' in tag:
                    return tag.split('}')[1]
                return tag

            def is_likely_wrapper(element) -> bool:
                clean_tag = clean_element_name(element.tag)
                wrapper_patterns = ['RUNNABLES', 'INTERNAL-BEHAVIORS', 'PORTS', 'ELEMENTS', 'CONNECTORS']
                return clean_tag in wrapper_patterns and len(element) > 0

            def should_treat_as_text_content(element) -> bool:
                return (
                        element.text and element.text.strip() and
                        len(element) == 0
                )

            def xml_to_triples_fixed(element, subject_uri=None, depth=0):
                nonlocal element_count

                if depth > 20:
                    return

                element_count += 1
                clean_tag = clean_element_name(element.tag)

                if subject_uri is None:
                    subject_uri = f"http://autosar.org/instance/{clean_tag}_{element_count}"

                subject = rdflib.URIRef(subject_uri)

                if is_likely_wrapper(element):
                    print(f"🔗 检测到可能的Wrapper: {clean_tag}")

                    element_type_uri = AUTOSAR[clean_tag]
                    graph.add((subject, rdflib.RDF.type, element_type_uri))

                    for i, child in enumerate(element):
                        clean_child_tag = clean_element_name(child.tag)
                        child_uri = f"{subject_uri}/{clean_child_tag}_{i}"
                        child_subject = rdflib.URIRef(child_uri)

                        predicate = AUTOSAR[clean_child_tag]
                        graph.add((subject, predicate, child_subject))

                        if '/' in subject_uri:
                            parent_uri = subject_uri.rsplit('/', 1)[0]
                            parent_subject = rdflib.URIRef(parent_uri)
                            direct_predicate = AUTOSAR[clean_child_tag]
                            graph.add((parent_subject, direct_predicate, child_subject))

                        xml_to_triples_fixed(child, child_uri, depth + 1)

                    return

                if should_treat_as_text_content(element):
                    print(f"📝 处理文本内容: {clean_tag} = '{element.text.strip()}'")

                    element_type_uri = AUTOSAR[clean_tag]
                    graph.add((subject, rdflib.RDF.type, element_type_uri))

                    predicate = AUTOSAR["VALUE"]
                    obj = rdflib.Literal(element.text.strip())
                    graph.add((subject, predicate, obj))
                    return

                element_type_uri = AUTOSAR[clean_tag]
                graph.add((subject, rdflib.RDF.type, element_type_uri))

                for attr_name, attr_value in element.attrib.items():
                    clean_attr = clean_element_name(attr_name)
                    predicate = AUTOSAR[clean_attr]
                    obj = rdflib.Literal(attr_value)
                    graph.add((subject, predicate, obj))

                if element.text and element.text.strip() and len(element) > 0:
                    predicate = AUTOSAR["hasValue"]
                    obj = rdflib.Literal(element.text.strip())
                    graph.add((subject, predicate, obj))

                for i, child in enumerate(element):
                    clean_child_tag = clean_element_name(child.tag)
                    child_uri = f"{subject_uri}/{clean_child_tag}_{i}"
                    predicate = AUTOSAR[clean_child_tag]
                    child_subject = rdflib.URIRef(child_uri)
                    graph.add((subject, predicate, child_subject))
                    xml_to_triples_fixed(child, child_uri, depth + 1)

            xml_to_triples_fixed(root)
            print(f"📊 处理了 {element_count} 个XML元素")

        except ET.ParseError as e:
            print(f"❌ XML解析错误: {e}")
        except Exception as e:
            print(f"❌ XML转RDF错误: {e}")

        return graph

    def _resolve_attr_mapping(self, xml_tag: str, class_id: int = None) -> Optional[str]:
        """解析XML标签到属性URI的映射"""
        if class_id:
            context_key = f"{class_id}:{xml_tag}"
            if context_key in self.xml_to_attr_mapping:
                return self.xml_to_attr_mapping[context_key]

            if class_id in self.class_context_mapping:
                class_mappings = self.class_context_mapping[class_id]
                if xml_tag in class_mappings:
                    return class_mappings[xml_tag]

        if xml_tag in self.xml_to_attr_mapping:
            return self.xml_to_attr_mapping[xml_tag]

        return None

    def _extract_violations_enhanced(self, results_graph: rdflib.Graph) -> List[Dict]:
        """增强的违规信息提取"""
        violations = []

        try:
            if not results_graph or not hasattr(results_graph, 'subjects'):
                raise ValueError("Invalid results_graph object")

            SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
            validation_results = list(results_graph.subjects(rdflib.RDF.type, SH.ValidationResult))

            if not validation_results:
                print("⚠️  在结果图中未找到ValidationResult")
                return []

            for violation in validation_results:
                violation_info = {
                    "severity": "Violation",
                    "message": None,
                    "focus_node": None,
                    "result_path": None,
                    "source_constraint": None,
                    "constraint_component": None,
                    "xml_element": None,
                    "xml_attribute": None
                }

                try:
                    for pred, obj in results_graph.predicate_objects(violation):
                        if pred == SH.resultSeverity:
                            severity_str = str(obj)
                            if '#' in severity_str:
                                violation_info["severity"] = severity_str.split('#')[-1]
                            else:
                                violation_info["severity"] = severity_str
                        elif pred == SH.resultMessage:
                            violation_info["message"] = str(obj)
                        elif pred == SH.focusNode:
                            focus_node_str = str(obj)
                            if '/' in focus_node_str:
                                violation_info["focus_node"] = focus_node_str.split('/')[-1]
                            else:
                                violation_info["focus_node"] = focus_node_str
                        elif pred == SH.resultPath:
                            result_path = str(obj)
                            if '#' in result_path:
                                violation_info["result_path"] = result_path.split('#')[-1]
                            elif '/' in result_path:
                                violation_info["result_path"] = result_path.split('/')[-1]
                            else:
                                violation_info["result_path"] = result_path

                            if result_path.startswith("http://autosar.org/ATTR_"):
                                attr_key = result_path.split("/")[-1]
                                xml_element = self.attr_to_xml_mapping.get(attr_key)
                                if xml_element:
                                    violation_info["xml_element"] = xml_element
                        elif pred == SH.sourceConstraintComponent:
                            component_str = str(obj)
                            if '#' in component_str:
                                violation_info["constraint_component"] = component_str.split('#')[-1]
                            else:
                                violation_info["constraint_component"] = component_str
                        elif pred == SH.sourceShape:
                            shape_str = str(obj)
                            if '#' in shape_str:
                                violation_info["source_constraint"] = shape_str.split('#')[-1]
                            else:
                                violation_info["source_constraint"] = shape_str

                except Exception as pred_error:
                    print(f"⚠️  处理违规谓词时出错: {pred_error}")
                    continue

                if not violation_info["message"]:
                    constraint_comp = violation_info.get('constraint_component', 'unknown')
                    xml_element = violation_info.get('xml_element', 'unknown element')
                    violation_info["message"] = f"约束违规 ({constraint_comp}) - XML元素: {xml_element}"

                violations.append(violation_info)

        except Exception as e:
            print(f"⚠️  提取违规信息时出错: {e}")
            violations.append({
                "severity": "Error",
                "message": f"提取违规详情失败: {str(e)}",
                "focus_node": "unknown",
                "result_path": "unknown"
            })

        return violations

    def _extract_violations_standard(self, results_graph: rdflib.Graph) -> List[Dict]:
        """标准违规信息提取"""
        violations = []

        try:
            if not results_graph or not hasattr(results_graph, 'subjects'):
                raise ValueError("Invalid results_graph object")

            SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
            validation_results = list(results_graph.subjects(rdflib.RDF.type, SH.ValidationResult))

            if not validation_results:
                print("⚠️  在结果图中未找到ValidationResult")
                return []

            for violation in validation_results:
                violation_info = {
                    "severity": "Violation",
                    "message": None,
                    "focus_node": None,
                    "result_path": None,
                    "source_constraint": None,
                    "constraint_component": None
                }

                try:
                    for pred, obj in results_graph.predicate_objects(violation):
                        if pred == SH.resultSeverity:
                            severity_str = str(obj)
                            if '#' in severity_str:
                                violation_info["severity"] = severity_str.split('#')[-1]
                            else:
                                violation_info["severity"] = severity_str
                        elif pred == SH.resultMessage:
                            violation_info["message"] = str(obj)
                        elif pred == SH.focusNode:
                            focus_node_str = str(obj)
                            if '/' in focus_node_str:
                                violation_info["focus_node"] = focus_node_str.split('/')[-1]
                            else:
                                violation_info["focus_node"] = focus_node_str
                        elif pred == SH.resultPath:
                            result_path = str(obj)
                            if '#' in result_path:
                                violation_info["result_path"] = result_path.split('#')[-1]
                            elif '/' in result_path:
                                violation_info["result_path"] = result_path.split('/')[-1]
                            else:
                                violation_info["result_path"] = result_path
                        elif pred == SH.sourceConstraintComponent:
                            component_str = str(obj)
                            if '#' in component_str:
                                violation_info["constraint_component"] = component_str.split('#')[-1]
                            else:
                                violation_info["constraint_component"] = component_str
                        elif pred == SH.sourceShape:
                            shape_str = str(obj)
                            if '#' in shape_str:
                                violation_info["source_constraint"] = shape_str.split('#')[-1]
                            else:
                                violation_info["source_constraint"] = shape_str

                except Exception as pred_error:
                    print(f"⚠️  处理违规谓词时出错: {pred_error}")
                    continue

                if not violation_info["message"]:
                    constraint_comp = violation_info.get('constraint_component', 'unknown')
                    violation_info["message"] = f"约束违规 ({constraint_comp})"

                violations.append(violation_info)

        except Exception as e:
            print(f"⚠️  提取违规信息时出错: {e}")
            violations.append({
                "severity": "Error",
                "message": f"提取违规详情失败: {str(e)}",
                "focus_node": "unknown",
                "result_path": "unknown"
            })

        return violations