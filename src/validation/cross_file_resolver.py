# src/validation/cross_file_resolver.py
"""跨文件引用解析器"""

import xml.etree.ElementTree as ET
from collections import defaultdict
from typing import Dict, List, Optional, Any


class CrossFileResolver:
    """构建全局引用索引，支持跨ARXML文件的引用解析"""

    def __init__(self):
        self.global_index: Dict[str, Dict[str, Any]] = {}  # SHORT-NAME-PATH -> element info
        self.ref_registry: Dict[str, List[Dict]] = defaultdict(list)  # 所有REF元素
        self.file_map: Dict[str, str] = {}  # element path -> source file
        self.ns = {'ar': 'http://autosar.org/schema/r4.0'}

    def build_global_index(self, arxml_files: List[str]) -> None:
        """
        扫描所有ARXML文件，构建全局SHORT-NAME-PATH索引

        Args:
            arxml_files: ARXML文件路径列表
        """
        print(f"[CrossFileResolver] 构建全局索引，文件数: {len(arxml_files)}")

        for arxml_path in arxml_files:
            self._index_single_file(arxml_path)

        print(f"[CrossFileResolver] 索引完成: {len(self.global_index)} 个元素, {len(self.ref_registry)} 种REF类型")

    def _index_single_file(self, arxml_path: str) -> None:
        """索引单个ARXML文件"""
        try:
            tree = ET.parse(arxml_path)
            root = tree.getroot()

            # 移除命名空间前缀以简化处理
            self._strip_namespace(root)

            # 递归构建SHORT-NAME路径索引
            self._build_path_index(root, [], arxml_path)

            # 收集所有REF元素
            self._collect_refs(root, arxml_path)

        except Exception as e:
            print(f"[WARN] 索引文件失败 {arxml_path}: {e}")

    def _strip_namespace(self, elem: ET.Element) -> None:
        """移除XML命名空间前缀"""
        for el in elem.iter():
            if '}' in el.tag:
                el.tag = el.tag.split('}', 1)[1]
            # 清理属性中的命名空间
            attribs = list(el.attrib.items())
            for key, val in attribs:
                if '}' in key:
                    new_key = key.split('}', 1)[1]
                    del el.attrib[key]
                    el.attrib[new_key] = val

    def _build_path_index(self, elem: ET.Element, path_stack: List[str], source_file: str) -> None:
        """递归构建SHORT-NAME-PATH索引，支持重复检测"""
        short_name_elem = elem.find('SHORT-NAME')

        if short_name_elem is not None and short_name_elem.text:
            current_path = path_stack + [short_name_elem.text]
            full_path = '/' + '/'.join(current_path)

            # ✅ [新增] 检测重复路径
            if full_path in self.global_index:
                existing_file = self.global_index[full_path].get('source_file', '')
                if existing_file != source_file:
                    # 记录重复
                    if not hasattr(self, 'duplicate_paths'):
                        self.duplicate_paths = {}
                    if full_path not in self.duplicate_paths:
                        self.duplicate_paths[full_path] = [existing_file]
                    self.duplicate_paths[full_path].append(source_file)
                    print(f"[WARN] 重复的SHORT-NAME-PATH: {full_path}")
                    print(f"       文件1: {existing_file}")
                    print(f"       文件2: {source_file}")

            # 存储元素信息（后来的会覆盖之前的）
            self.global_index[full_path] = {
                'tag': elem.tag,
                'short_name': short_name_elem.text,
                'path': full_path,
                'source_file': source_file,
                'attributes': dict(elem.attrib),
                'children_tags': [child.tag for child in elem]
            }
            self.file_map[full_path] = source_file

            # 继续递归子元素
            for child in elem:
                if child.tag not in ['SHORT-NAME', 'LONG-NAME', 'DESC']:
                    self._build_path_index(child, current_path, source_file)
        else:
            # 非命名元素，继续递归但不更新路径
            for child in elem:
                self._build_path_index(child, path_stack, source_file)

    def get_duplicate_paths(self) -> Dict[str, List[str]]:
        """获取所有重复的SHORT-NAME-PATH及其来源文件"""
        return getattr(self, 'duplicate_paths', {})

    def _collect_refs(self, root: ET.Element, source_file: str) -> None:
        """收集所有REF元素"""
        for elem in root.iter():
            if elem.tag.endswith('-REF') or elem.tag.endswith('-TREF'):
                ref_info = {
                    'tag': elem.tag,
                    'text': elem.text.strip() if elem.text else '',
                    'dest': elem.get('DEST', ''),
                    'source_file': source_file
                }
                self.ref_registry[elem.tag].append(ref_info)

    def resolve_reference(self, ref_path: str) -> Optional[Dict[str, Any]]:
        """
        解析引用路径，返回目标元素信息

        Args:
            ref_path: SHORT-NAME-PATH (如 /Package/SubPackage/Element)

        Returns:
            目标元素信息字典，未找到返回None
        """
        return self.global_index.get(ref_path)

    def validate_all_refs(self) -> List[Dict[str, Any]]:
        """
        验证所有引用的完整性

        Returns:
            违规列表
        """
        violations = []

        for ref_type, refs in self.ref_registry.items():
            for ref in refs:
                if ref['text'] and not self.resolve_reference(ref['text']):
                    violations.append({
                        'type': 'UNRESOLVED_REFERENCE',
                        'ref_tag': ref_type,
                        'ref_path': ref['text'],
                        'expected_dest': ref['dest'],
                        'source_file': ref['source_file'],
                        'message': f"引用目标不存在: {ref['text']} (DEST={ref['dest']})"
                    })

        return violations

    def check_dest_type_match(self) -> List[Dict[str, Any]]:
        """
        检查REF的DEST属性是否与目标类型匹配

        Returns:
            类型不匹配列表
        """
        mismatches = []

        for ref_type, refs in self.ref_registry.items():
            for ref in refs:
                if ref['text']:
                    target = self.resolve_reference(ref['text'])
                    if target and ref['dest'] and target['tag'] != ref['dest']:
                        mismatches.append({
                            'type': 'DEST_TYPE_MISMATCH',
                            'ref_tag': ref_type,
                            'ref_path': ref['text'],
                            'declared_dest': ref['dest'],
                            'actual_type': target['tag'],
                            'source_file': ref['source_file'],
                            'message': f"DEST类型不匹配: 声明={ref['dest']}, 实际={target['tag']}"
                        })

        return mismatches

    def get_elements_by_type(self, element_type: str) -> List[Dict[str, Any]]:
        """获取所有指定类型的元素"""
        return [info for info in self.global_index.values() if info['tag'] == element_type]

    def export_for_smt(self) -> Dict[str, Any]:
        """
        导出SMT验证所需的全局状态

        Returns:
            SMT求解器可用的数据结构
        """
        return {
            'elements': self.global_index,
            'refs': dict(self.ref_registry),
            'element_count': len(self.global_index),
            'ref_count': sum(len(refs) for refs in self.ref_registry.values())
        }