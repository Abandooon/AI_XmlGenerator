# src/validation/semantic/shacl_validator.py
from typing import Dict, List, Optional
import rdflib
from pyshacl import validate
import xml.etree.ElementTree as ET
import json
from pathlib import Path


class SHACLValidator:
    """SHACL语义约束验证器 - 修复版（修正变量引用错误）"""

    def __init__(self, shapes_file: str,
                 raw_attributes_file: Optional[str] = None,
                 enriched_constraints_file: Optional[str] = None):
        """
        初始化SHACL验证器

        Args:
            shapes_file: SHACL形状文件路径 (autosar_shapes.ttl)
            raw_attributes_file: raw_attributes.jsonl文件路径 (可选，启用映射功能)
            enriched_constraints_file: enriched_constraints.json文件路径 (可选，增强映射)
        """
        self.shapes_file = shapes_file
        self.shapes_graph = self._load_shapes(shapes_file)

        # 映射机制 - 向后兼容
        self.mapping_enabled = raw_attributes_file is not None
        self.xml_to_attr_mapping = {}
        self.attr_to_xml_mapping = {}
        self.class_context_mapping = {}

        if self.mapping_enabled:
            print("🔧 启用增强映射功能")
            self._build_mapping_tables(raw_attributes_file)

            if enriched_constraints_file:
                self._load_constraint_mappings(enriched_constraints_file)
        else:
            print("📝 使用标准验证模式")

    def _load_shapes(self, shapes_file: str) -> rdflib.Graph:
        """加载SHACL形状文件"""
        try:
            shapes_graph = rdflib.Graph()

            if not Path(shapes_file).exists():
                print(f"⚠️  SHACL shapes文件不存在: {shapes_file}")
                return shapes_graph

            shapes_graph.parse(shapes_file, format="turtle")

            # 统计shapes信息
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

    def _build_mapping_tables(self, raw_attributes_file: str):
        """从raw_attributes.jsonl构建映射表"""
        try:
            with open(raw_attributes_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        attr_record = json.loads(line)

                        class_id = attr_record["classId"]
                        attr_id = attr_record["attrId"]
                        xml_tag = attr_record["xml_tag"]

                        # 构建映射关系
                        attr_uri = f"ATTR_{attr_id}"

                        # 上下文相关映射：classId:xml_tag -> ATTR_ID
                        context_key = f"{class_id}:{xml_tag}"
                        self.xml_to_attr_mapping[context_key] = attr_uri

                        # 全局映射作为后备
                        if xml_tag not in self.xml_to_attr_mapping:
                            self.xml_to_attr_mapping[xml_tag] = attr_uri

                        # 反向映射：ATTR_ID -> xml_tag
                        self.attr_to_xml_mapping[attr_uri] = xml_tag

                        # 类上下文映射
                        if class_id not in self.class_context_mapping:
                            self.class_context_mapping[class_id] = {}
                        self.class_context_mapping[class_id][xml_tag] = attr_uri

            print(f"✅ 构建映射表成功: {len(self.xml_to_attr_mapping)} 个映射")

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

                    # 更新映射表
                    self.xml_to_attr_mapping[context_path] = attr_key
                    self.xml_to_attr_mapping[xml_tag] = attr_key
                    self.attr_to_xml_mapping[attr_key] = xml_tag

            print(f"✅ 加载约束映射成功")

        except Exception as e:
            print(f"⚠️  加载约束映射失败: {e}")

    def validate_semantics(self, xml_content: str) -> Dict:
        """执行SHACL语义验证 - 修改为分级报告结果"""
        print("\n🔍 开始SHACL分级验证...")

        try:
            if len(self.shapes_graph) == 0:
                print("❌ SHACL shapes为空，无法执行验证")
                return {
                    "valid": False,
                    "violation_count": 1,
                    "violations": [{"message": "SHACL shapes文件为空或加载失败"}],
                    "results_text": "No SHACL shapes available for validation"
                }

            # 1. XML转RDF
            print("📝 步骤1: 将XML转换为RDF图...")
            if self.mapping_enabled:
                rdf_graph = self._xml_to_rdf_enhanced(xml_content)
            else:
                rdf_graph = self._xml_to_rdf_standard(xml_content)

            if len(rdf_graph) == 0:
                print("❌ XML转RDF失败")
                return {
                    "valid": False,
                    "violation_count": 1,
                    "violations": [{"message": "XML转RDF失败，无法进行SHACL验证"}],
                    "results_text": "Failed to convert XML to RDF"
                }

            print(f"✅ RDF图生成成功，包含 {len(rdf_graph)} 个三元组")

            # 2. 执行SHACL验证
            print("📝 步骤2: 执行SHACL约束验证...")
            conforms, results_graph, results_text = validate(
                data_graph=rdf_graph,
                shacl_graph=self.shapes_graph,
                inference='rdfs',
                abort_on_first=False,
                debug=self.mapping_enabled
            )

            print(f"✅ SHACL验证完成，整体符合性: {conforms}")

            # 3. 分级分析验证结果
            violations = []
            if not conforms:
                print("📝 步骤3: 分级分析违规信息...")
                if self.mapping_enabled:
                    violations = self._extract_violations_enhanced(results_graph)
                else:
                    violations = self._extract_violations_standard(results_graph)

                # 🔧 按严重性分类统计
                violation_stats = self._categorize_violations(violations)

                print(f"📊 违规统计:")
                print(f"   ❌ 结构错误 (Violation): {violation_stats['violations']} 个")
                print(f"   ⚠️  语义警告 (Warning): {violation_stats['warnings']} 个")
                print(f"   ℹ️  格式建议 (Info): {violation_stats['info']} 个")

                # 显示关键违规
                critical_violations = [v for v in violations if v.get('severity') == 'Violation']
                if critical_violations:
                    print(f"\n❌ 关键结构错误（必须修复）:")
                    for i, violation in enumerate(critical_violations[:3], 1):
                        print(f"   {i}. {violation.get('message', 'Unknown violation')}")
                        if violation.get('focus_node'):
                            print(f"      📍 节点: {violation['focus_node']}")

            else:
                print("✅ 所有SHACL约束都满足")
                violation_stats = {'violations': 0, 'warnings': 0, 'info': 0}

            # 🔧 构建分级验证结果
            result = {
                "valid": conforms,
                "structural_valid": violation_stats['violations'] == 0,  # 结构是否有效
                "semantic_compliance": "FULL" if violation_stats['warnings'] == 0 else "PARTIAL",
                "violation_count": len(violations),
                "violation_stats": violation_stats,
                "violations": violations,
                "results_text": results_text,
                "rdf_triples": len(rdf_graph),
                "shapes_applied": len(self.shapes_graph)
            }

            # 增强模式下添加额外信息
            if self.mapping_enabled:
                result["mapping_stats"] = {
                    "xml_to_attr_mappings": len(self.xml_to_attr_mapping),
                    "attr_to_xml_mappings": len(self.attr_to_xml_mapping),
                    "mapping_enabled": True
                }
            else:
                result["mapping_stats"] = {"mapping_enabled": False}

            return result

        except Exception as e:
            print(f"❌ SHACL验证过程出错: {e}")
            import traceback
            traceback.print_exc()
            return {
                "valid": False,
                "structural_valid": False,
                "violation_count": 1,
                "violations": [{"message": f"SHACL验证错误: {str(e)}"}],
                "results_text": str(e)
            }

    def _categorize_violations(self, violations: List[Dict]) -> Dict[str, int]:
        """按严重性对违规进行分类统计"""
        stats = {"violations": 0, "warnings": 0, "info": 0}

        for violation in violations:
            severity = violation.get("severity", "Violation")
            if severity == "Violation":
                stats["violations"] += 1
            elif severity == "Warning":
                stats["warnings"] += 1
            elif severity == "Info":
                stats["info"] += 1

        return stats

    def _xml_to_rdf_enhanced(self, xml_content: str) -> rdflib.Graph:
        """增强的XML到RDF转换，使用实际XML元素名称"""
        graph = rdflib.Graph()
        element_count = 0

        try:
            root = ET.fromstring(xml_content)
            print(f"📋 解析XML根元素: {root.tag}")

            # 修改：统一使用 http://autosar.org/ 命名空间
            AUTOSAR = rdflib.Namespace("http://autosar.org/")
            graph.bind("autosar", AUTOSAR)

            def clean_element_name(tag):
                """清理元素名称，移除命名空间前缀"""
                if '}' in tag:
                    return tag.split('}')[1]
                return tag

            def xml_to_triples_enhanced(element, subject_uri=None, parent_class_id=None, depth=0):
                nonlocal element_count

                if depth > 20:  # 限制递归深度
                    return

                element_count += 1
                clean_tag = clean_element_name(element.tag)

                if subject_uri is None:
                    subject_uri = f"http://autosar.org/instance/{clean_tag}_{element_count}"

                subject = rdflib.URIRef(subject_uri)

                # 关键修改：使用实际的XML元素名称作为RDF类型
                element_type_uri = AUTOSAR[clean_tag]
                graph.add((subject, rdflib.RDF.type, element_type_uri))

                # 处理属性 - 使用映射表
                for attr_name, attr_value in element.attrib.items():
                    clean_attr = clean_element_name(attr_name)

                    # 查找属性映射
                    current_class_id = hash(clean_tag) % 10000  # 简化的类ID推断
                    attr_uri_key = self._resolve_attr_mapping(clean_attr, current_class_id)

                    if attr_uri_key:
                        predicate = AUTOSAR[attr_uri_key]
                        obj = rdflib.Literal(attr_value)
                        graph.add((subject, predicate, obj))
                    else:
                        # 后备：直接使用属性名
                        predicate = AUTOSAR[clean_attr]
                        obj = rdflib.Literal(attr_value)
                        graph.add((subject, predicate, obj))

                # 处理文本内容
                if element.text and element.text.strip():
                    predicate = AUTOSAR["hasValue"]
                    obj = rdflib.Literal(element.text.strip())
                    graph.add((subject, predicate, obj))

                # 处理子元素 - 使用实际XML标签名
                for i, child in enumerate(element):
                    clean_child_tag = clean_element_name(child.tag)
                    child_uri = f"{subject_uri}/{clean_child_tag}_{i}"

                    # 直接使用XML标签作为属性路径
                    predicate = AUTOSAR[clean_child_tag]
                    child_subject = rdflib.URIRef(child_uri)
                    graph.add((subject, predicate, child_subject))

                    # 递归处理子元素
                    xml_to_triples_enhanced(child, child_uri, None, depth + 1)

            xml_to_triples_enhanced(root)
            print(f"📊 处理了 {element_count} 个XML元素")

        except ET.ParseError as e:
            print(f"❌ XML解析错误: {e}")
        except Exception as e:
            print(f"❌ XML转RDF错误: {e}")

        return graph

    def _xml_to_rdf_standard(self, xml_content: str) -> rdflib.Graph:
        """标准的XML到RDF转换 - 修改为使用实际XML元素名称"""
        graph = rdflib.Graph()
        element_count = 0

        try:
            root = ET.fromstring(xml_content)
            print(f"📋 解析XML根元素: {root.tag}")

            # 修改：统一使用 http://autosar.org/ 命名空间
            AUTOSAR = rdflib.Namespace("http://autosar.org/")
            graph.bind("autosar", AUTOSAR)

            def clean_element_name(tag):
                """清理元素名称，移除命名空间前缀"""
                if '}' in tag:
                    return tag.split('}')[1]
                return tag

            def xml_to_triples(element, subject_uri=None, depth=0):
                nonlocal element_count

                if depth > 20:  # 限制递归深度
                    return

                element_count += 1

                # 清理元素名称
                clean_tag = clean_element_name(element.tag)

                if subject_uri is None:
                    subject_uri = f"http://autosar.org/instance/{clean_tag}_{element_count}"

                subject = rdflib.URIRef(subject_uri)

                # 关键修改：使用实际的XML元素名称作为RDF类型
                element_type_uri = AUTOSAR[clean_tag]
                graph.add((subject, rdflib.RDF.type, element_type_uri))

                # 处理属性
                for attr_name, attr_value in element.attrib.items():
                    clean_attr = clean_element_name(attr_name)
                    predicate = AUTOSAR[clean_attr]
                    obj = rdflib.Literal(attr_value)
                    graph.add((subject, predicate, obj))

                # 处理文本内容
                if element.text and element.text.strip():
                    predicate = AUTOSAR["hasValue"]
                    obj = rdflib.Literal(element.text.strip())
                    graph.add((subject, predicate, obj))

                # 处理子元素 - 使用实际XML标签名
                for i, child in enumerate(element):
                    clean_child_tag = clean_element_name(child.tag)
                    child_uri = f"{subject_uri}/{clean_child_tag}_{i}"
                    predicate = AUTOSAR[clean_child_tag]
                    child_subject = rdflib.URIRef(child_uri)
                    graph.add((subject, predicate, child_subject))
                    xml_to_triples(child, child_uri, depth + 1)

            xml_to_triples(root)
            print(f"📊 处理了 {element_count} 个XML元素")

        except ET.ParseError as e:
            print(f"❌ XML解析错误: {e}")
        except Exception as e:
            print(f"❌ XML转RDF错误: {e}")

        return graph

    def _resolve_attr_mapping(self, xml_tag: str, class_id: int = None) -> Optional[str]:
        """解析XML标签到属性URI的映射"""
        # 1. 优先使用上下文相关映射
        if class_id:
            context_key = f"{class_id}:{xml_tag}"
            if context_key in self.xml_to_attr_mapping:
                return self.xml_to_attr_mapping[context_key]

            # 检查类上下文映射
            if class_id in self.class_context_mapping:
                class_mappings = self.class_context_mapping[class_id]
                if xml_tag in class_mappings:
                    return class_mappings[xml_tag]

        # 2. 后备：使用全局映射
        if xml_tag in self.xml_to_attr_mapping:
            return self.xml_to_attr_mapping[xml_tag]

        # 3. 最后后备：返回None，使用原始标签
        return None

    def _extract_violations_enhanced(self, results_graph: rdflib.Graph) -> List[Dict]:
        """增强的违规信息提取，包含XML元素映射"""
        violations = []

        try:
            SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")

            for violation in results_graph.subjects(rdflib.RDF.type, SH.ValidationResult):
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

                for pred, obj in results_graph.predicate_objects(violation):
                    if pred == SH.resultSeverity:
                        violation_info["severity"] = str(obj).split('#')[-1]
                    elif pred == SH.resultMessage:
                        violation_info["message"] = str(obj)
                    elif pred == SH.focusNode:
                        violation_info["focus_node"] = str(obj).split('/')[-1]
                    elif pred == SH.resultPath:
                        result_path = str(obj)
                        violation_info["result_path"] = result_path.split('#')[-1]

                        # 尝试将ATTR_ID映射回XML元素
                        if result_path.startswith("http://autosar.org/ATTR_"):
                            attr_key = result_path.split("/")[-1]
                            xml_element = self.attr_to_xml_mapping.get(attr_key)
                            if xml_element:
                                violation_info["xml_element"] = xml_element
                    elif pred == SH.sourceConstraintComponent:
                        violation_info["constraint_component"] = str(obj).split('#')[-1]
                    elif pred == SH.sourceShape:
                        violation_info["source_constraint"] = str(obj).split('#')[-1]

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
        """标准违规信息提取 - 保持原有逻辑"""
        violations = []

        try:
            SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")

            for violation in results_graph.subjects(rdflib.RDF.type, SH.ValidationResult):
                violation_info = {
                    "severity": "Violation",
                    "message": None,
                    "focus_node": None,
                    "result_path": None,
                    "source_constraint": None,
                    "constraint_component": None
                }

                for pred, obj in results_graph.predicate_objects(violation):
                    if pred == SH.resultSeverity:
                        violation_info["severity"] = str(obj).split('#')[-1]
                    elif pred == SH.resultMessage:
                        violation_info["message"] = str(obj)
                    elif pred == SH.focusNode:
                        violation_info["focus_node"] = str(obj).split('/')[-1]
                    elif pred == SH.resultPath:
                        violation_info["result_path"] = str(obj).split('#')[-1]
                    elif pred == SH.sourceConstraintComponent:
                        violation_info["constraint_component"] = str(obj).split('#')[-1]
                    elif pred == SH.sourceShape:
                        violation_info["source_constraint"] = str(obj).split('#')[-1]

                if not violation_info["message"]:
                    violation_info["message"] = f"约束违规 ({violation_info.get('constraint_component', 'unknown')})"

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

