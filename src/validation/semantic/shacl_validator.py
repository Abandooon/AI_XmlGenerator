# src/validation/semantic/shacl_validator.py (修正版 - 解决Wrapper和文本内容问题)
from typing import Dict, List, Optional
import rdflib
from pyshacl import validate
import xml.etree.ElementTree as ET
import json
from pathlib import Path


class SHACLValidator:
    """SHACL语义约束验证器 - 修正版（修复Wrapper标签和文本内容问题）"""

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

        # 🔧 新增：Wrapper标签映射表
        self.wrapper_mappings = {}  # wrapper_tag -> actual_item_tag
        self.text_content_mappings = {}  # element_tag -> expected_attr_name for text content

        if self.mapping_enabled:
            print("🔧 启用增强映射功能（包含Wrapper处理）")
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

            # 🔧 修复：更安全的TTL文件解析
            try:
                shapes_graph.parse(shapes_file, format="turtle")
            except Exception as parse_error:
                print(f"❌ TTL解析错误: {parse_error}")
                # 尝试基础错误修复
                try:
                    with open(shapes_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 基础修复：移除可能的问题字符
                    content = self._fix_ttl_content(content)

                    # 尝试重新解析
                    shapes_graph.parse(data=content, format="turtle")
                    print("✅ TTL文件经修复后成功解析")
                except Exception as retry_error:
                    print(f"❌ TTL修复后仍无法解析: {retry_error}")
                    return rdflib.Graph()

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

    def _fix_ttl_content(self, content: str) -> str:
        """彻底修复TTL内容 - 解决所有已知问题"""
        import re

        # 🔧 第一步：移除所有控制字符表示（这是主要问题）
        # 移除 ^a, ^b, ^c 等控制字符表示
        content = re.sub(r'\^[a-zA-Z@\[\\\]^_]', '', content)

        # 移除实际的控制字符（二进制）
        content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', content)

        # 移除十六进制转义序列
        content = re.sub(r'\\x[0-9a-fA-F]{2}', '', content)

        # 🔧 第二步：处理bytes字面量表示
        # 移除 b' 前缀（如果出现在错误的地方）
        content = re.sub(r"b'([^']*)'", r'\1', content)

        # 🔧 第三步：替换特殊Unicode字符
        replacements = {
            '•': 'bullet',
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'",
            '–': '-',
            '—': '-',
            '…': '...',
        }

        for old_char, new_char in replacements.items():
            content = content.replace(old_char, new_char)

        # 🔧 第四步：修复正则表达式转义问题
        lines = content.split('\n')
        fixed_lines = []

        for line in lines:
            # 检查是否是sh:pattern行
            if 'sh:pattern' in line:
                # 提取模式部分
                match = re.search(r'sh:pattern\s+"([^"]*)"', line)
                if match:
                    pattern = match.group(1)
                    # 简化正则表达式，移除可能有问题的转义
                    # 特别处理管道符等特殊字符
                    simplified_pattern = pattern.replace('\\|', 'pipe')
                    simplified_pattern = simplified_pattern.replace('\\\\', '\\')
                    # 重构这一行
                    line = re.sub(r'sh:pattern\s+"[^"]*"', f'sh:pattern "{simplified_pattern}"', line)

            # 检查未闭合的引号
            quote_count = line.count('"')
            if quote_count % 2 != 0:
                # 如果是消息、标签或注释行，尝试修复
                if any(keyword in line for keyword in ['sh:message', 'rdfs:label', 'rdfs:comment']):
                    if line.endswith(' ;'):
                        line = line[:-2] + '" ;'
                    elif line.endswith(' .'):
                        line = line[:-2] + '" .'
                    elif not line.endswith('"'):
                        line = line + '"'

            # 移除任何剩余的问题字符
            line = re.sub(r'[^\x20-\x7E\r\n]', '', line)

            fixed_lines.append(line)

        # 🔧 第五步：重新组合并最终清理
        fixed_content = '\n'.join(fixed_lines)

        # 确保没有连续的反斜杠问题
        fixed_content = re.sub(r'\\{3,}', '\\\\', fixed_content)

        return fixed_content

    def _build_mapping_tables(self, raw_attributes_file: str):
        """从raw_attributes.jsonl构建映射表 - 🔧 增强版本包含Wrapper处理"""
        try:
            # 🔧 新增：已知的wrapper标签模式
            known_wrappers = {
                'RUNNABLES': 'RUNNABLE-ENTITY',
                'INTERNAL-BEHAVIORS': 'SWC-INTERNAL-BEHAVIOR',
                'EXTERNAL-BEHAVIORS': 'SWC-EXTERNAL-BEHAVIOR',
                'PORTS': 'P-PORT-PROTOTYPE',
                'PROVIDED-PORTS': 'P-PORT-PROTOTYPE',
                'REQUIRED-PORTS': 'R-PORT-PROTOTYPE',
                'SW-COMPONENTS': 'APPLICATION-SW-COMPONENT-TYPE',
                'DATA-ELEMENTS': 'VARIABLE-DATA-PROTOTYPE',
                'ELEMENTS': 'AUTOSAR-ELEMENT',  # 通用wrapper
                'CONNECTORS': 'ASSEMBLY-SW-CONNECTOR',
                'MAPPINGS': 'DATA-MAPPING',
                'CONSTRAINTS': 'CONSTRAINT',
                'VARIANTS': 'VARIANT',
                'COMPOSITIONS': 'COMPOSITION-SW-COMPONENT-TYPE'
            }

            # 🔧 新增：文本内容映射（用于解决VALUE问题）
            text_content_elements = {
                'SD': 'VALUE',  # <SD>true</SD> -> SD should have VALUE attribute
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

                        # 🔧 处理wrapper映射
                        if xml_wrapper_tag:
                            self.wrapper_mappings[xml_wrapper_tag] = xml_tag
                            print(f"🔗 发现Wrapper映射: {xml_wrapper_tag} -> {xml_tag}")

                        # 构建原有映射关系
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

            # 🔧 合并已知wrapper模式
            for wrapper, item in known_wrappers.items():
                if wrapper not in self.wrapper_mappings:
                    self.wrapper_mappings[wrapper] = item

            # 🔧 设置文本内容映射
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

                    # 更新映射表
                    self.xml_to_attr_mapping[context_path] = attr_key
                    self.xml_to_attr_mapping[xml_tag] = attr_key
                    self.attr_to_xml_mapping[attr_key] = xml_tag

            print(f"✅ 加载约束映射成功")

        except Exception as e:
            print(f"⚠️  加载约束映射失败: {e}")

    def validate_semantics(self, xml_content: str) -> Dict:
        """执行SHACL语义验证 - 修正版（修复ValidationFailure问题）"""
        print("\n🔍 开始SHACL分级验证...")

        try:
            if len(self.shapes_graph) == 0:
                print("❌ SHACL shapes为空，无法执行验证")
                return {
                    "valid": False,
                    "structural_valid": False,
                    "semantic_compliance": "NONE",
                    "violation_count": 1,
                    "violation_stats": {"violations": 1, "warnings": 0, "info": 0},
                    "violations": [{"message": "SHACL shapes文件为空或加载失败", "severity": "Error"}],
                    "results_text": "No SHACL shapes available for validation"
                }

            # 1. XML转RDF - 🔧 使用修正版本
            print("📝 步骤1: 将XML转换为RDF图（增强Wrapper处理）...")
            if self.mapping_enabled:
                rdf_graph = self._xml_to_rdf_enhanced_fixed(xml_content)
            else:
                rdf_graph = self._xml_to_rdf_standard_fixed(xml_content)

            if len(rdf_graph) == 0:
                print("❌ XML转RDF失败")
                return {
                    "valid": False,
                    "structural_valid": False,
                    "semantic_compliance": "NONE",
                    "violation_count": 1,
                    "violation_stats": {"violations": 1, "warnings": 0, "info": 0},
                    "violations": [{"message": "XML转RDF失败，无法进行SHACL验证", "severity": "Error"}],
                    "results_text": "Failed to convert XML to RDF"
                }

            print(f"✅ RDF图生成成功，包含 {len(rdf_graph)} 个三元组")

            # 2. 执行SHACL验证 - 🔧 修正验证结果处理
            print("📝 步骤2: 执行SHACL约束验证...")

            try:
                # 🔧 关键修复：更安全的pyshacl调用
                validation_result = validate(
                    data_graph=rdf_graph,
                    shacl_graph=self.shapes_graph,
                    inference='rdfs',
                    abort_on_first=False,
                    debug=False
                )

                # 🔧 修复：正确处理不同类型的验证结果
                if isinstance(validation_result, tuple):
                    # 标准情况：(conforms, results_graph, results_text)
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
                    # 非标准情况：可能是ValidationFailure对象或其他
                    print(f"⚠️  非标准验证结果类型: {type(validation_result)}")
                    conforms = False
                    results_graph = None
                    results_text = str(validation_result)

            except Exception as validation_error:
                print(f"❌ SHACL验证执行失败: {validation_error}")
                return {
                    "valid": False,
                    "structural_valid": False,
                    "semantic_compliance": "ERROR",
                    "violation_count": 1,
                    "violation_stats": {"violations": 1, "warnings": 0, "info": 0},
                    "violations": [{"message": f"SHACL验证执行失败: {str(validation_error)}", "severity": "Error"}],
                    "results_text": str(validation_error)
                }

            print(f"✅ SHACL验证完成，整体符合性: {conforms}")

            # 3. 分级分析验证结果 - 🔧 修正违规信息提取
            violations = []
            violation_stats = {"violations": 0, "warnings": 0, "info": 0}

            if not conforms:
                print("📝 步骤3: 分级分析违规信息...")

                # 🔧 修复：检查results_graph类型并选择合适的提取方法
                if results_graph is not None and hasattr(results_graph, 'subjects'):
                    # 正常的RDF图对象
                    try:
                        if self.mapping_enabled:
                            violations = self._extract_violations_enhanced(results_graph)
                        else:
                            violations = self._extract_violations_standard(results_graph)
                    except Exception as extract_error:
                        print(f"⚠️  从RDF图提取违规信息失败: {extract_error}")
                        violations = self._extract_violations_from_text(results_text)
                else:
                    # results_graph无效，从文本提取
                    print("⚠️  results_graph无效，尝试从文本提取违规信息")
                    violations = self._extract_violations_from_text(results_text)

                # 🔧 按严重性分类统计
                violation_stats = self._categorize_violations(violations)

                print(f"📊 违规统计:")
                print(f"   ❌ 结构错误 (Violation): {violation_stats['violations']} 个")
                print(f"   ⚠️  语义警告 (Warning): {violation_stats['warnings']} 个")
                print(f"   ℹ️  格式建议 (Info): {violation_stats['info']} 个")

                # 显示关键违规
                critical_violations = [v for v in violations if v.get('severity') in ['Violation', 'Error']]
                if critical_violations:
                    print(f"\n❌ 关键结构错误（必须修复）:")
                    for i, violation in enumerate(critical_violations[:3], 1):
                        print(f"   {i}. {violation.get('message', 'Unknown violation')}")
                        if violation.get('focus_node'):
                            print(f"      📍 节点: {violation['focus_node']}")

            else:
                print("✅ 所有SHACL约束都满足")

            # 🔧 构建分级验证结果
            result = {
                "valid": conforms,
                "structural_valid": violation_stats['violations'] == 0,  # 结构是否有效
                "semantic_compliance": "FULL" if violation_stats['warnings'] == 0 else "PARTIAL",
                "violation_count": len(violations),
                "violation_stats": violation_stats,
                "violations": violations,
                "results_text": results_text if isinstance(results_text, str) else str(results_text),
                "rdf_triples": len(rdf_graph),
                "shapes_applied": len(self.shapes_graph)
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

            return result

        except Exception as e:
            print(f"❌ SHACL验证过程出错: {e}")
            import traceback
            traceback.print_exc()
            return {
                "valid": False,
                "structural_valid": False,
                "semantic_compliance": "ERROR",
                "violation_count": 1,
                "violation_stats": {"violations": 1, "warnings": 0, "info": 0},
                "violations": [{"message": f"SHACL验证错误: {str(e)}", "severity": "Error"}],
                "results_text": str(e)
            }

    def _extract_violations_from_text(self, results_text: str) -> List[Dict]:
        """🔧 新增：从验证结果文本提取违规信息"""
        violations = []

        if not results_text:
            return [{
                "severity": "Violation",
                "message": "SHACL validation failed but no details available",
                "focus_node": "unknown",
                "result_path": "unknown"
            }]

        try:
            # 尝试解析文本格式的违规信息
            text_str = str(results_text)

            # 查找常见的违规关键词
            if "violation" in text_str.lower() or "constraint" in text_str.lower():
                lines = text_str.split('\n')
                for line in lines:
                    if line.strip() and any(
                            keyword in line.lower() for keyword in ['violation', 'constraint', 'failed', 'error']):
                        violations.append({
                            "severity": "Violation",
                            "message": line.strip()[:200],  # 限制长度
                            "focus_node": "unknown",
                            "result_path": "unknown"
                        })

            # 如果没有找到具体违规，创建通用记录
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

    def _categorize_violations(self, violations: List[Dict]) -> Dict[str, int]:
        """按严重性对违规进行分类统计"""
        stats = {"violations": 0, "warnings": 0, "info": 0}

        for violation in violations:
            severity = violation.get("severity", "Violation")
            if severity == "Violation" or severity == "Error":
                stats["violations"] += 1
            elif severity == "Warning":
                stats["warnings"] += 1
            elif severity == "Info":
                stats["info"] += 1
            else:
                # 未知严重性默认为violations
                stats["violations"] += 1

        return stats

    def _xml_to_rdf_enhanced_fixed(self, xml_content: str) -> rdflib.Graph:
        """🔧 修正版：增强的XML到RDF转换，正确处理Wrapper标签和文本内容"""
        graph = rdflib.Graph()
        element_count = 0

        try:
            root = ET.fromstring(xml_content)
            print(f"📋 解析XML根元素: {root.tag}")

            # 统一使用 http://autosar.org/ 命名空间
            AUTOSAR = rdflib.Namespace("http://autosar.org/")
            graph.bind("autosar", AUTOSAR)

            def clean_element_name(tag):
                """清理元素名称，移除命名空间前缀"""
                if '}' in tag:
                    return tag.split('}')[1]
                return tag

            def is_wrapper_element(tag_name: str) -> bool:
                """🔧 判断是否为wrapper元素"""
                return tag_name in self.wrapper_mappings

            def get_expected_item_tag(wrapper_tag: str) -> str:
                """🔧 获取wrapper包含的实际item标签"""
                return self.wrapper_mappings.get(wrapper_tag, wrapper_tag)

            def should_treat_as_text_content(element) -> bool:
                """🔧 判断元素是否应被视为文本内容"""
                clean_tag = clean_element_name(element.tag)
                return (
                        element.text and element.text.strip() and
                        len(element) == 0 and  # 没有子元素
                        clean_tag in self.text_content_mappings
                )

            def xml_to_triples_enhanced_fixed(element, subject_uri=None, parent_class_id=None, depth=0):
                nonlocal element_count

                if depth > 20:  # 限制递归深度
                    return

                element_count += 1
                clean_tag = clean_element_name(element.tag)

                if subject_uri is None:
                    subject_uri = f"http://autosar.org/instance/{clean_tag}_{element_count}"

                subject = rdflib.URIRef(subject_uri)

                # 🔧 关键修改1：处理wrapper元素的透明化
                if is_wrapper_element(clean_tag):
                    print(f"🔗 处理Wrapper元素: {clean_tag}")

                    # 对于wrapper元素，我们不为wrapper本身创建类型声明
                    # 而是直接处理其子元素，让它们直接连接到wrapper的父元素

                    expected_item_tag = get_expected_item_tag(clean_tag)

                    for i, child in enumerate(element):
                        clean_child_tag = clean_element_name(child.tag)

                        # 如果子元素是期望的item类型，直接连接到wrapper的父节点
                        if clean_child_tag == expected_item_tag:
                            # 使用期望的标签名作为属性路径
                            child_uri = f"{subject_uri.rsplit('/', 1)[0]}/{expected_item_tag}_{i}"
                            child_subject = rdflib.URIRef(child_uri)

                            # 关键：使用期望的item标签作为从父元素到子元素的属性
                            parent_subject = rdflib.URIRef(subject_uri.rsplit('/', 1)[0])
                            predicate = AUTOSAR[expected_item_tag]
                            graph.add((parent_subject, predicate, child_subject))

                            print(f"   🔗 透明连接: {parent_subject} --{expected_item_tag}--> {child_subject}")

                            # 递归处理实际的item元素
                            xml_to_triples_enhanced_fixed(child, child_uri, parent_class_id, depth)
                        else:
                            # 非期望的子元素，正常处理
                            child_uri = f"{subject_uri}/{clean_child_tag}_{i}"
                            predicate = AUTOSAR[clean_child_tag]
                            child_subject = rdflib.URIRef(child_uri)
                            graph.add((subject, predicate, child_subject))
                            xml_to_triples_enhanced_fixed(child, child_uri, None, depth + 1)

                    return  # wrapper元素处理完毕，不继续下面的正常处理

                # 🔧 关键修改2：处理文本内容元素
                if should_treat_as_text_content(element):
                    print(f"📝 处理文本内容元素: {clean_tag} = '{element.text.strip()}'")

                    # 为文本内容元素创建类型声明
                    element_type_uri = AUTOSAR[clean_tag]
                    graph.add((subject, rdflib.RDF.type, element_type_uri))

                    # 🔧 关键修改：使用期望的属性名而不是通用的hasValue
                    expected_attr = self.text_content_mappings[clean_tag]
                    predicate = AUTOSAR[expected_attr]
                    obj = rdflib.Literal(element.text.strip())
                    graph.add((subject, predicate, obj))

                    print(f"   📝 文本映射: {clean_tag}.{expected_attr} = '{element.text.strip()}'")
                    return

                # 正常元素处理
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

                # 🔧 处理普通文本内容（非文本内容元素）
                if element.text and element.text.strip() and len(element) > 0:
                    # 有子元素但也有文本内容，使用hasValue
                    predicate = AUTOSAR["hasValue"]
                    obj = rdflib.Literal(element.text.strip())
                    graph.add((subject, predicate, obj))

                # 处理子元素 - 正常处理（非wrapper）
                for i, child in enumerate(element):
                    clean_child_tag = clean_element_name(child.tag)
                    child_uri = f"{subject_uri}/{clean_child_tag}_{i}"

                    # 直接使用XML标签作为属性路径
                    predicate = AUTOSAR[clean_child_tag]
                    child_subject = rdflib.URIRef(child_uri)
                    graph.add((subject, predicate, child_subject))

                    # 递归处理子元素
                    xml_to_triples_enhanced_fixed(child, child_uri, None, depth + 1)

            xml_to_triples_enhanced_fixed(root)
            print(f"📊 处理了 {element_count} 个XML元素")
            print(
                f"🔗 识别了 {len([e for e in [root] + list(root.iter()) if clean_element_name(e.tag) in self.wrapper_mappings])} 个Wrapper元素")

        except ET.ParseError as e:
            print(f"❌ XML解析错误: {e}")
        except Exception as e:
            print(f"❌ XML转RDF错误: {e}")

        return graph

    def _xml_to_rdf_standard_fixed(self, xml_content: str) -> rdflib.Graph:
        """🔧 修正版：标准的XML到RDF转换，基础wrapper和文本处理"""
        graph = rdflib.Graph()
        element_count = 0

        try:
            root = ET.fromstring(xml_content)
            print(f"📋 解析XML根元素: {root.tag}")

            # 统一使用 http://autosar.org/ 命名空间
            AUTOSAR = rdflib.Namespace("http://autosar.org/")
            graph.bind("autosar", AUTOSAR)

            def clean_element_name(tag):
                """清理元素名称，移除命名空间前缀"""
                if '}' in tag:
                    return tag.split('}')[1]
                return tag

            def is_likely_wrapper(element) -> bool:
                """🔧 基础wrapper检测（标准模式）"""
                clean_tag = clean_element_name(element.tag)
                # 简单的wrapper检测规则
                wrapper_patterns = ['RUNNABLES', 'INTERNAL-BEHAVIORS', 'PORTS', 'ELEMENTS', 'CONNECTORS']
                return clean_tag in wrapper_patterns and len(element) > 0

            def should_treat_as_text_content(element) -> bool:
                """🔧 基础文本内容检测"""
                return (
                        element.text and element.text.strip() and
                        len(element) == 0  # 没有子元素
                )

            def xml_to_triples_fixed(element, subject_uri=None, depth=0):
                nonlocal element_count

                if depth > 20:  # 限制递归深度
                    return

                element_count += 1
                clean_tag = clean_element_name(element.tag)

                if subject_uri is None:
                    subject_uri = f"http://autosar.org/instance/{clean_tag}_{element_count}"

                subject = rdflib.URIRef(subject_uri)

                # 🔧 基础wrapper处理（标准模式）
                if is_likely_wrapper(element):
                    print(f"🔗 检测到可能的Wrapper: {clean_tag}")

                    # 为wrapper创建类型声明
                    element_type_uri = AUTOSAR[clean_tag]
                    graph.add((subject, rdflib.RDF.type, element_type_uri))

                    # 处理wrapper的子元素，同时创建直接连接
                    for i, child in enumerate(element):
                        clean_child_tag = clean_element_name(child.tag)
                        child_uri = f"{subject_uri}/{clean_child_tag}_{i}"
                        child_subject = rdflib.URIRef(child_uri)

                        # 正常的wrapper->child连接
                        predicate = AUTOSAR[clean_child_tag]
                        graph.add((subject, predicate, child_subject))

                        # 🔧 额外创建parent->child的直接连接（绕过wrapper）
                        if '/' in subject_uri:
                            parent_uri = subject_uri.rsplit('/', 1)[0]
                            parent_subject = rdflib.URIRef(parent_uri)
                            direct_predicate = AUTOSAR[clean_child_tag]
                            graph.add((parent_subject, direct_predicate, child_subject))
                            print(
                                f"   🔗 创建直接连接: {parent_uri.split('/')[-1]} --{clean_child_tag}--> {child_subject}")

                        # 递归处理子元素
                        xml_to_triples_fixed(child, child_uri, depth + 1)

                    return

                # 🔧 文本内容处理
                if should_treat_as_text_content(element):
                    print(f"📝 处理文本内容: {clean_tag} = '{element.text.strip()}'")

                    element_type_uri = AUTOSAR[clean_tag]
                    graph.add((subject, rdflib.RDF.type, element_type_uri))

                    # 🔧 使用VALUE作为文本内容的属性名
                    predicate = AUTOSAR["VALUE"]
                    obj = rdflib.Literal(element.text.strip())
                    graph.add((subject, predicate, obj))
                    return

                # 正常元素处理
                element_type_uri = AUTOSAR[clean_tag]
                graph.add((subject, rdflib.RDF.type, element_type_uri))

                # 处理属性
                for attr_name, attr_value in element.attrib.items():
                    clean_attr = clean_element_name(attr_name)
                    predicate = AUTOSAR[clean_attr]
                    obj = rdflib.Literal(attr_value)
                    graph.add((subject, predicate, obj))

                # 处理普通文本内容
                if element.text and element.text.strip() and len(element) > 0:
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
        """增强的违规信息提取，包含XML元素映射 - 修正版"""
        violations = []

        try:
            # 🔧 修复：检查results_graph的有效性
            if not results_graph or not hasattr(results_graph, 'subjects'):
                raise ValueError("Invalid results_graph object")

            SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")

            # 🔧 修复：安全地获取ValidationResult
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

                # 🔧 修复：安全地遍历谓词对象
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

                            # 尝试将ATTR_ID映射回XML元素
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
                    # 继续处理下一个违规，而不是完全失败
                    continue

                if not violation_info["message"]:
                    constraint_comp = violation_info.get('constraint_component', 'unknown')
                    xml_element = violation_info.get('xml_element', 'unknown element')
                    violation_info["message"] = f"约束违规 ({constraint_comp}) - XML元素: {xml_element}"

                violations.append(violation_info)

        except Exception as e:
            print(f"⚠️  提取违规信息时出错: {e}")
            # 创建一个错误违规记录而不是抛出异常
            violations.append({
                "severity": "Error",
                "message": f"提取违规详情失败: {str(e)}",
                "focus_node": "unknown",
                "result_path": "unknown"
            })

        return violations

    def _extract_violations_standard(self, results_graph: rdflib.Graph) -> List[Dict]:
        """标准违规信息提取 - 修正版"""
        violations = []

        try:
            # 🔧 修复：检查results_graph的有效性
            if not results_graph or not hasattr(results_graph, 'subjects'):
                raise ValueError("Invalid results_graph object")

            SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")

            # 🔧 修复：安全地获取ValidationResult
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

                # 🔧 修复：安全地遍历谓词对象
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
                    # 继续处理下一个违规，而不是完全失败
                    continue

                if not violation_info["message"]:
                    constraint_comp = violation_info.get('constraint_component', 'unknown')
                    violation_info["message"] = f"约束违规 ({constraint_comp})"

                violations.append(violation_info)

        except Exception as e:
            print(f"⚠️  提取违规信息时出错: {e}")
            # 创建一个错误违规记录而不是抛出异常
            violations.append({
                "severity": "Error",
                "message": f"提取违规详情失败: {str(e)}",
                "focus_node": "unknown",
                "result_path": "unknown"
            })

        return violations