# doc_parser/nlp_pipeline.py
import spacy
from spacy.pipeline import EntityRuler

def build_nlp_pipeline(domain_terms: list, model_name: str = "en_core_web_trf"):
    """
    加载 spaCy 模型并配置领域规则。
    输入:
        domain_terms (list): 领域规则，列表中每个元素为{'label': 'XXX', 'pattern': 'YYY'}
        model_name (str): spaCy 模型名称，默认使用 en_core_web_trf
    输出:
        spacy.Language: 配置好的 NLP 流水线
    """
    nlp = spacy.load(model_name)
    ruler = nlp.add_pipe("entity_ruler", before="ner")
    ruler.add_patterns(domain_terms)
    return nlp
