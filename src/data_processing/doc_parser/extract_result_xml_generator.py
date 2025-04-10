# doc_parser/xml_generator.py
import xml.etree.ElementTree as ET


def convert_info_to_xml(info: dict) -> str:
    """
    将信息字典转换为 XML 格式。
    输入:
        info (dict): 包含 'entities' 和 'relationships'
    输出:
        str: XML 字符串
    """
    root = ET.Element("Document")
    entities_el = ET.SubElement(root, "Entities")
    for ent in info.get("entities", []):
        ent_el = ET.SubElement(entities_el, "Entity")
        ent_el.set("label", ent["label"])
        ent_el.set("start", str(ent["start"]))
        ent_el.set("end", str(ent["end"]))
        ent_el.text = ent["text"]

    relationships_el = ET.SubElement(root, "Relationships")
    for rel in info.get("relationships", []):
        rel_el = ET.SubElement(relationships_el, "Relationship")
        rel_el.set("relation", rel["relation"])
        subject_el = ET.SubElement(rel_el, "Subject")
        subject_el.text = rel["subject"]
        object_el = ET.SubElement(rel_el, "Object")
        object_el.text = rel["object"]

    return ET.tostring(root, encoding="unicode")
