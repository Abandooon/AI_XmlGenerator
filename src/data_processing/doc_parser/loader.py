# doc_parser/loader.py
import docx

def load_document(file_path: str) -> str:
    """
    加载 Word 文档，提取所有段落文本（跳过图片和表格）。
    输入:
        file_path (str): Word 文档路径
    输出:
        str: 拼接后的原始文本
    """
    doc = docx.Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip() != ""]
    return "\n".join(paragraphs)
