# src/validation/semantic/shacl_validator.py
from typing import Dict, List
import rdflib
from pyshacl import validate
import xml.etree.ElementTree as ET


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

    def validate_semantics(self, xml_content: str) -> Dict:
        """执行SHACL语义约束验证"""

        try:
            # 1. XML转RDF
            rdf_graph = self.xml_to_rdf(xml_content)

            # 2. SHACL验证
            conforms, results_graph, results_text = validate(
                data_graph=rdf_graph,
                shacl_graph=self.shapes_graph,
                inference='rdfs',
                abort_on_first=False
            )

            # 3. 提取违规信息
            violations = self.extract_violations(results_graph) if not conforms else []

            return {
                "valid": conforms,
                "violation_count": len(violations),
                "violations": violations,
                "results_text": results_text
            }

        except Exception as e:
            return {
                "valid": False,
                "violation_count": 1,
                "violations": [{"message": f"Validation error: {str(e)}"}],
                "results_text": str(e)
            }

    def xml_to_rdf(self, xml_content: str) -> rdflib.Graph:
        """将AUTOSAR XML转换为RDF图"""

        graph = rdflib.Graph()

        try:
            root = ET.fromstring(xml_content)

            # 定义命名空间
            AUTOSAR = rdflib.Namespace("http://autosar.org/schema#")
            graph.bind("autosar", AUTOSAR)

            # 递归转换XML元素为RDF三元组
            def xml_to_triples(element, subject_uri=None):
                if subject_uri is None:
                    subject_uri = AUTOSAR[element.tag]

                subject = rdflib.URIRef(subject_uri)

                # 处理属性
                for attr_name, attr_value in element.attrib.items():
                    predicate = AUTOSAR[attr_name]
                    obj = rdflib.Literal(attr_value)
                    graph.add((subject, predicate, obj))

                # 处理子元素
                for child in element:
                    child_uri = f"{subject_uri}/{child.tag}"
                    predicate = AUTOSAR[child.tag]
                    child_subject = rdflib.URIRef(child_uri)

                    graph.add((subject, predicate, child_subject))
                    xml_to_triples(child, child_uri)

            xml_to_triples(root)

        except ET.ParseError as e:
            print(f"XML parsing error: {e}")

        return graph

    def extract_violations(self, results_graph: rdflib.Graph) -> List[Dict]:
        """提取和格式化SHACL违规信息"""

        violations = []

        # SHACL结果命名空间
        SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")

        # 查询违规报告
        for violation in results_graph.subjects(rdflib.RDF.type, SH.ValidationResult):
            violation_info = {
                "severity": None,
                "message": None,
                "focus_node": None,
                "result_path": None,
                "source_constraint": None
            }

            # 提取违规详情
            for pred, obj in results_graph.predicate_objects(violation):
                if pred == SH.resultSeverity:
                    violation_info["severity"] = str(obj)
                elif pred == SH.resultMessage:
                    violation_info["message"] = str(obj)
                elif pred == SH.focusNode:
                    violation_info["focus_node"] = str(obj)
                elif pred == SH.resultPath:
                    violation_info["result_path"] = str(obj)
                elif pred == SH.sourceConstraintComponent:
                    violation_info["source_constraint"] = str(obj)

            violations.append(violation_info)

        return violations