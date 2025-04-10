# doc_parser/extractor.py
def extract_entities(text: str, nlp) -> list:
    """
    使用 spaCy 流水线对文本进行命名实体识别。
    输入:
        text (str): 清洗后的文本
        nlp (spacy.Language): 配置好的 NLP 流水线
    输出:
        list[dict]: 实体列表，每个实体包含 'text', 'label', 'start', 'end'
    """
    doc = nlp(text)
    return [{
        "text": ent.text,
        "label": ent.label_,
        "start": ent.start_char,
        "end": ent.end_char
    } for ent in doc.ents]

def extract_relationships(text: str, nlp) -> list:
    """
    对文本进行关系抽取（此处仅为简化示例）。
    输入:
        text (str): 清洗后的文本
        nlp (spacy.Language): 配置好的 NLP 流水线
    输出:
        list[dict]: 关系列表，每个关系包含 'subject', 'relation', 'object'
    """
    doc = nlp(text)
    # 这里只是示例，可使用依存分析等实际方法
    return [{
        "subject": "主体示例",
        "relation": "关系示例",
        "object": "客体示例"
    } for _ in doc.sents]

def aggregate_information(text: str, nlp) -> dict:
    """
    综合实体识别和关系抽取，构建结构化信息。
    输入:
        text (str): 清洗后的文本
        nlp (spacy.Language): NLP 流水线
    输出:
        dict: {'entities': [...], 'relationships': [...]}
    """
    return {
        "entities": extract_entities(text, nlp),
        "relationships": extract_relationships(text, nlp)
    }
