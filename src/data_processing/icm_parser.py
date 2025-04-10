from doc_parser.document_parser import parse_document

if __name__ == "__main__":
    ## 领域术语示例,调用处理文档的模块
    domain_terms = [
        {"label": "AUTOSAR_COMPONENT", "pattern": "ECU"},
        {"label": "AUTOSAR_INTERFACE", "pattern": "CAN"},
        {"label": "AUTOSAR_COMPONENT", "pattern": "SWC"}
    ]
    file_path = "path/to/autosar_document.docx"  # 替换成实际路径
    xml_output = parse_document(file_path, domain_terms)
    print(xml_output)

    ## 处理输入层其他信息,调用uml_metadata_parser模块
