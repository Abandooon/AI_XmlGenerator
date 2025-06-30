# src/validation/semantic/shacl_validator.py
from typing import Dict, List
import rdflib
from pyshacl import validate
import xml.etree.ElementTree as ET
from pathlib import Path


class SHACLValidator:
    """SHACL语义约束验证器"""

    def __init__(self, shapes_file: str):
        """
        初始化SHACL验证器

        Args:
            shapes_file: SHACL形状文件路径 (autosar_shapes.ttl)
        """
        self.shapes_file = shapes_file
        self.shapes_graph = self._load_shapes(shapes_file)

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

            print(f"✅ SHACL shapes加载成功: {shapes_file}")
            print(f"   📊 包含 {node_shapes} 个节点形状, {property_shapes} 个属性形状")
            print(f"   📊 总计 {len(shapes_graph)} 个RDF三元组")

            return shapes_graph

        except Exception as e:
            print(f"⚠️  SHACL shapes加载失败: {e}")
            return rdflib.Graph()

    def validate_semantics(self, xml_content: str) -> Dict:
        """执行SHACL语义约束验证"""
        print("\n🔍 开始SHACL语义验证...")

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
            rdf_graph = self.xml_to_rdf(xml_content)

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
                abort_on_first=False
            )

            print(f"✅ SHACL验证完成，符合性: {conforms}")

            # 3. 分析验证结果
            violations = []
            if not conforms:
                print("📝 步骤3: 分析违规信息...")
                violations = self.extract_violations(results_graph)
                print(f"❌ 发现 {len(violations)} 个违规")

                # 显示违规详情
                for i, violation in enumerate(violations[:3], 1):  # 只显示前3个
                    print(
                        f"   {i}. {violation.get('severity', 'Error')}: {violation.get('message', 'Unknown violation')}")
                    if violation.get('focus_node'):
                        print(f"      📍 节点: {violation['focus_node']}")
                    if violation.get('result_path'):
                        print(f"      🔗 路径: {violation['result_path']}")

                if len(violations) > 3:
                    print(f"   ... 还有 {len(violations) - 3} 个违规")
            else:
                print("✅ 所有SHACL约束都满足")

            return {
                "valid": conforms,
                "violation_count": len(violations),
                "violations": violations,
                "results_text": results_text,
                "rdf_triples": len(rdf_graph),
                "shapes_applied": len(self.shapes_graph)
            }

        except Exception as e:
            print(f"❌ SHACL验证过程出错: {e}")
            return {
                "valid": False,
                "violation_count": 1,
                "violations": [{"message": f"SHACL验证错误: {str(e)}"}],
                "results_text": str(e)
            }

    # 在 xml_to_rdf 方法中优化URI生成
    def xml_to_rdf(self, xml_content: str) -> rdflib.Graph:
        """将AUTOSAR XML转换为RDF图 - 优化版"""
        graph = rdflib.Graph()
        element_count = 0

        try:
            root = ET.fromstring(xml_content)
            print(f"📋 解析XML根元素: {root.tag}")

            # 定义命名空间
            AUTOSAR = rdflib.Namespace("http://autosar.org/schema/")
            graph.bind("autosar", AUTOSAR)

            def clean_element_name(tag):
                """清理元素名称，移除命名空间前缀"""
                if '}' in tag:
                    return tag.split('}')[1]  # 移除 {namespace} 前缀
                return tag

            def xml_to_triples(element, subject_uri=None, depth=0):
                nonlocal element_count

                if depth > 20:  # 限制递归深度
                    return

                element_count += 1

                # 清理元素名称
                clean_tag = clean_element_name(element.tag)

                if subject_uri is None:
                    subject_uri = f"http://autosar.org/schema/{clean_tag}"

                subject = rdflib.URIRef(subject_uri)

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

                # 处理子元素
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

    def extract_violations(self, results_graph: rdflib.Graph) -> List[Dict]:
        """提取和格式化SHACL违规信息"""
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