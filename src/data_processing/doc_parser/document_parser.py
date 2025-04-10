from src.data_processing.doc_parser import cleaner, loader, nlp_pipeline, extractor, extract_result_xml_generator


def parse_document(file_path: str, domain_terms: list, model_name: str = "en_core_web_trf") -> str:
    """
    统一调用各模块，实现从文档加载、预处理、信息抽取到 XML 生成的完整流程。
    输入:
        file_path (str): Word 文档路径
        domain_terms (list): 领域规则列表
        model_name (str): spaCy 模型名称
    输出:
        str: 生成的 XML 字符串
    """
    raw_text = loader.load_document(file_path)
    clean = cleaner.clean_text(raw_text)
    nlp = nlp_pipeline.build_nlp_pipeline(domain_terms, model_name)
    info = extractor.aggregate_information(clean, nlp)
    xml_output = extract_result_xml_generator.convert_info_to_xml(info)
    return xml_output
