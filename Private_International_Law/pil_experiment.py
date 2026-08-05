# -*- coding: utf-8 -*-
"""
Private International Law (Brussels I bis) — 三方法对比实验（增强诊断版）
"""
import argparse
import json
import math
import random
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Any, List, Tuple

from src.llm_generation.llm.openai_client import OpenAIClient

ROOT = Path(__file__).resolve().parent
PIL_DIR = ROOT
DATA = PIL_DIR / "data" / "experiment_dataset.jsonl"
ARTS = PIL_DIR / "kb" / "articles_index.json"
RULES = PIL_DIR / "rules" / "rule_priority_table.json"
SCHEMA = PIL_DIR / "schema" / "decision_schema.json"
PROVISIONS = PIL_DIR / "kb" / "brussels_provisions.jsonl"


# ============== 诊断日志系统 ==============
class DiagnosticLogger:
    """诊断日志收集器"""

    def __init__(self):
        self.logs = defaultdict(list)
        self.error_cases = defaultdict(list)

    def log(self, category: str, case_id: int, message: str, data: Any = None):
        """记录日志"""
        entry = {
            "case_id": case_id,
            "message": message,
            "data": data
        }
        self.logs[category].append(entry)

    def log_error(self, mode: str, case_id: int, pred: Dict, gold: Dict, details: str = ""):
        """记录错误案例"""
        self.error_cases[mode].append({
            "case_id": case_id,
            "pred_conclusion": pred.get("conclusion"),
            "gold_conclusion": gold.get("conclusion"),
            "pred_forum_type": pred.get("forum_type"),
            "gold_forum_type": gold.get("forum_type"),
            "pred_provisions": [x["provision"] for x in pred.get("legal_basis", [])],
            "gold_provisions": [x["provision"] for x in gold.get("legal_basis", [])],
            "details": details
        })

    def summary(self):
        """生成诊断摘要"""
        print("\n" + "=" * 80)
        print("DIAGNOSTIC SUMMARY".center(80))
        print("=" * 80)

        # RAG检索质量
        if "rag_retrieval" in self.logs:
            print("\n【RAG检索质量分析】")
            rag_logs = self.logs["rag_retrieval"]

            # 统计检索命中率
            hit_counts = []
            for log in rag_logs:
                retrieved = set(log['data']['retrieved'])
                gold = set(log['data']['gold_provisions'])
                hit = len(retrieved & gold)
                hit_counts.append((hit, len(gold), log['case_id']))

            avg_hit_rate = sum(h for h, g, _ in hit_counts) / sum(g for _, g, _ in hit_counts)
            print(f"  平均检索命中率: {avg_hit_rate:.1%}")
            print(f"  完全命中案例: {sum(1 for h, g, _ in hit_counts if h == g)} / {len(hit_counts)}")
            print(f"  完全失效案例: {sum(1 for h, _, _ in hit_counts if h == 0)} / {len(hit_counts)}")

            # 显示典型失败案例
            print("\n  典型失败案例:")
            failures = [(c, h, g) for h, g, c in hit_counts if h == 0][:3]
            for case_id, hit, gold_count in failures:
                log = next(l for l in rag_logs if l['case_id'] == case_id)
                print(f"    Case {case_id}:")
                print(f"      检索到: {log['data']['retrieved'][:3]}")
                print(f"      实际需要: {log['data']['gold_provisions']}")
                print(f"      查询: {log['data']['query'][:50]}...")

        # Token统计异常
        if "token_stats" in self.logs:
            print("\n【Token统计分析】")
            for mode in ["baseline", "rag", "prism"]:
                mode_logs = [l for l in self.logs["token_stats"] if l['data']['mode'] == mode]
                if mode_logs:
                    avg_in = sum(l['data']['in'] for l in mode_logs) / len(mode_logs)
                    avg_out = sum(l['data']['out'] for l in mode_logs) / len(mode_logs)
                    print(f"  {mode.upper()}:")
                    print(f"    Avg Input:  {avg_in:.0f} tokens")
                    print(f"    Avg Output: {avg_out:.0f} tokens")
                    print(f"    Avg Total:  {avg_in + avg_out:.0f} tokens")

        # 错误案例分布
        print("\n【错误案例分布】")
        for mode in ["baseline", "rag", "prism"]:
            errors = self.error_cases[mode]
            if errors:
                print(f"\n  {mode.upper()} ({len(errors)} errors):")

                # 按错误类型分类
                conclusion_errors = sum(1 for e in errors if e['pred_conclusion'] != e['gold_conclusion'])
                forum_type_errors = sum(1 for e in errors if e['pred_forum_type'] != e['gold_forum_type'])

                print(f"    结论错误: {conclusion_errors}")
                print(f"    法院类型错误: {forum_type_errors}")

                # 显示前3个典型错误
                print(f"    典型案例:")
                for e in errors[:3]:
                    print(f"      Case {e['case_id']}: "
                          f"pred={e['pred_forum_type']}, gold={e['gold_forum_type']}")

        # PRISM弃权质量
        if "prism_abstention" in self.logs:
            print("\n【PRISM弃权质量分析】")
            abstain_logs = self.logs["prism_abstention"]

            should_abstain = [l for l in abstain_logs if l['data']['should_abstain']]
            did_abstain = [l for l in abstain_logs if l['data']['did_abstain']]

            print(f"  应弃权案例: {len(should_abstain)}")
            print(f"  实际弃权: {len(did_abstain)}")

            # 找出错误案例
            false_negatives = [l for l in should_abstain if not l['data']['did_abstain']]
            false_positives = [l for l in abstain_logs if l['data']['did_abstain'] and not l['data']['should_abstain']]

            if false_negatives:
                print(f"\n  漏弃权案例 ({len(false_negatives)}):")
                for l in false_negatives[:3]:
                    print(f"    Case {l['case_id']}: {l['data']['reason']}")

            if false_positives:
                print(f"\n  误弃权案例 ({len(false_positives)}):")
                for l in false_positives[:3]:
                    print(f"    Case {l['case_id']}: {l['data']['reason']}")


logger = DiagnosticLogger()


# ============== RAG检索器（保持不变）==============
class SimpleRAGRetriever:
    def __init__(self, provisions_path: Path):
        self.provisions = self._load_provisions(provisions_path)
        self.idf = self._compute_idf()

    def _load_provisions(self, path: Path) -> List[Dict[str, Any]]:
        provisions = []
        if not path.exists():
            print(f"Warning: {path} not found. RAG will not work properly.")
            return provisions
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    provisions.append(json.loads(line))
        return provisions

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        tokens = re.findall(r'[\u4e00-\u9fff]|[a-z]+', text)
        return tokens

    def _compute_idf(self) -> Dict[str, float]:
        doc_count = len(self.provisions)
        term_doc_count = Counter()

        for prov in self.provisions:
            doc_text = prov.get('text_zh', '') + ' ' + ' '.join(prov.get('keywords', []))
            tokens = set(self._tokenize(doc_text))
            for token in tokens:
                term_doc_count[token] += 1

        idf = {}
        for term, count in term_doc_count.items():
            idf[term] = math.log(doc_count / (1 + count))
        return idf

    def _compute_tfidf(self, query_tokens: List[str], doc_tokens: List[str]) -> float:
        query_tf = Counter(query_tokens)
        doc_tf = Counter(doc_tokens)

        score = 0.0
        for term in query_tf:
            if term in doc_tf:
                tf_query = query_tf[term]
                tf_doc = doc_tf[term]
                idf = self.idf.get(term, 0)
                score += tf_query * tf_doc * idf

        query_norm = math.sqrt(sum((query_tf[t] * self.idf.get(t, 0)) ** 2 for t in query_tf))
        doc_norm = math.sqrt(sum((doc_tf[t] * self.idf.get(t, 0)) ** 2 for t in doc_tf))

        if query_norm > 0 and doc_norm > 0:
            score = score / (query_norm * doc_norm)

        return score

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.provisions:
            return []

        query_tokens = self._tokenize(query)
        scores = []

        for prov in self.provisions:
            doc_text = prov.get('text_zh', '') + ' ' + ' '.join(prov.get('keywords', []))
            doc_tokens = self._tokenize(doc_text)
            score = self._compute_tfidf(query_tokens, doc_tokens)
            scores.append((score, prov))

        scores.sort(reverse=True, key=lambda x: x[0])
        return [prov for score, prov in scores[:top_k]]


# ============== 原有辅助函数 ==============
def expected_forum_from_evidence(evidence: List[str], rules: Dict[str, Any]) -> str:
    s = set(evidence or [])
    has = lambda pfx: any(x.startswith(pfx) for x in s)
    only31 = (any(x.startswith("Art.31") for x in s) and
              not has("Art.25") and not has("Art.24") and
              not any(x.startswith("Art.7") for x in s) and
              "Art.4" not in s and not has("Art.26"))
    if only31:
        return "lis_penden"

    order = rules.get("priority_order", [])

    def token_to_cat(tok: str) -> str:
        if tok.startswith("exclusive_"): return "exclusive"
        if tok.startswith("agreement_"): return "agreement"
        if tok.startswith("special_"): return "special"
        if tok.startswith("general_"): return "general"
        if tok.startswith("appearance_"): return "appearance"
        return "none"

    for tok in order:
        cat = token_to_cat(tok)
        if cat == "exclusive" and has("Art.24"): return "exclusive"
        if cat == "agreement" and has("Art.25"): return "agreement"
        if cat == "special" and any(x.startswith("Art.7") for x in s): return "special"
        if cat == "general" and "Art.4" in s: return "general"
        if cat == "appearance" and has("Art.26"): return "appearance"
    return "none"


def provision_category(p: str) -> str:
    p = str(p)
    if p.startswith("Art.24"): return "exclusive"
    if p.startswith("Art.25"): return "agreement"
    if p.startswith("Art.7"):  return "special"
    if p.startswith("Art.4"):  return "general"
    if p.startswith("Art.31"): return "lis_penden"
    if p.startswith("Art.26"): return "appearance"
    return "none"


def expected_category_from_evidence(evidence: list, priority_order: list) -> str:
    cats = set(provision_category(e) for e in evidence)
    order_map = {
        "exclusive_Art24": "exclusive",
        "agreement_Art25_31": "agreement",
        "special_Art7": "special",
        "general_Art4": "general",
        "appearance_Art26": "appearance"
    }
    if "lis_penden" in cats and "agreement" not in cats:
        return "lis_penden"
    for k in priority_order:
        c = order_map.get(k)
        if c and c in cats:
            return c
    return "none"


def metric_promote_hit(evidence: list, pred_forum_type: str, rules: dict) -> int:
    exp = expected_category_from_evidence(evidence, rules.get("priority_order", []))
    return int(exp == (pred_forum_type or "none"))


def load_json(p: Path) -> Any:
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(p: Path) -> List[Dict[str, Any]]:
    out = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def ensure_dir(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)


def norm(s: str) -> str:
    return (s or "").strip().lower()


def extract_provisions_from_text(text: str) -> List[str]:
    pats = re.findall(r"Art\.\s*\d+(?:\(\d+\))?(?:\([a-z]\))?", text, flags=re.I)
    return sorted(set([re.sub(r"\s+", "", p).replace("art.", "Art.") for p in pats]))


def metric_legal_correct(pred: Dict[str, Any], gold: Dict[str, Any]) -> int:
    return int(norm(pred.get("conclusion")) == norm(gold.get("conclusion")) and
               norm(pred.get("forum_type")) == norm(gold.get("forum_type")))


def metric_citation_precision(pred: Dict[str, Any], gold: Dict[str, Any]) -> float:
    gold_set = {x["provision"] for x in gold.get("legal_basis", [])}
    pred_set = {x["provision"] for x in pred.get("legal_basis", [])}
    if not pred_set: return 0.0
    inter = len(gold_set & pred_set)
    return inter / len(pred_set)


def metric_abstention_quality(pred: Dict[str, Any], gold: Dict[str, Any]) -> int:
    need_abstain = norm(gold.get("conclusion")) == "abstain_insufficient_info"
    did_abstain = norm(pred.get("conclusion")) == "abstain_insufficient_info"
    return int(need_abstain == did_abstain)


def metric_schema_pass(valid: bool) -> int:
    return int(bool(valid))


def map_baseline_conclusion(text: str, rules: Dict[str, Any]) -> Tuple[str, str]:
    """
    统一用“抽取到的条文”→“论坛类型/结论”的优先级映射来判断，
    仅在未抽取到任何条文时，才回退到中文关键词启发式。
    """
    t = norm(text)
    provisions = extract_provisions_from_text(text)
    s = set(provisions)
    has = lambda pfx: any(p.startswith(pfx) for p in s)
    has7 = any(p.startswith("Art.7") for p in s)

    # —— 条文优先：与规则优先级保持一致 ——
    # 1) 专属管辖 Art.24(*) > 其他
    if has("Art.24"):
        return "Court_of_X_has_jurisdiction", "exclusive"

    # 2) 选择法院 Art.25(1)（若含 Art.31 同时存在则仍属 agreement 类别；是否 stay 由 PRISM 层面处理）
    if has("Art.25"):
        # 形式要件缺失 → 应弃权
        if any(k in t for k in ["无效", "不足", "形式要件", "未书面", "缺失"]):
            return "Abstain_Insufficient_Info", "none"
        # 含/不含 Art.31 均归入 agreement（基于规则表“agreement_Art25_31”的抽象类别）
        return "Decline_in_favor_of_chosen_court", "agreement"

    # 3) 仅有 Art.31（lis pendens）→ stay
    if has("Art.31") and not has7 and not has("Art.4") and not has("Art.26"):
        return "Stay_for_first_seised", "lis_penden"

    # 4) 特别管辖 Art.7(*)
    if has7:
        return "Court_of_X_has_jurisdiction", "special"

    # 5) 一般管辖 Art.4
    if "Art.4" in s:
        return "Court_of_X_has_jurisdiction", "general"

    # 6) 出庭 Art.26（基线/RAG难以严格判断其效力与限制，这里保守为“信息不足”）
    if has("Art.26"):
        return "Abstain_Insufficient_Info", "none"

    # —— 兜底（未抽到条文时）——
    if "先受理" in t or "让渡" in t or "中止" in t:
        return "Stay_for_first_seised", "lis_penden"
    if any(k in t for k in ["不动产", "登记簿", "公司", "商标", "专属", "执行"]):
        return "Court_of_X_has_jurisdiction", "exclusive"
    if "协议" in t or "约定" in t or "选择法院" in t:
        if any(k in t for k in ["无效", "不足", "形式要件", "未书面", "缺失"]):
            return "Abstain_Insufficient_Info", "none"
        return "Decline_in_favor_of_chosen_court", "agreement"
    if any(k in t for k in ["交付地", "履行地", "侵权", "分公司", "信托"]):
        return "Court_of_X_has_jurisdiction", "special"
    if "被告住所" in t or "一般管辖" in t:
        return "Court_of_X_has_jurisdiction", "general"
    if "出庭" in t or "缺席" in t:
        return "Abstain_Insufficient_Info", "none"
    return "Abstain_Insufficient_Info", "none"



def rule_validate(pred: Dict[str, Any]) -> Dict[str, Any]:
    basis = {x["provision"] for x in pred.get("legal_basis", [])}
    forum_type = pred.get("forum_type", "")
    issues = []

    def has(pfx: str) -> bool:
        return any(b.startswith(pfx) for b in basis)

    if has("Art.24") and (has("Art.25") or has("Art.7") or has("Art.4")):
        issues.append("Exclusive(Art.24) must override others; remove Art.25/Art.7/Art.4")
    if has("Art.25") and (has("Art.7") or has("Art.4")) and not has("Art.31"):
        issues.append("Agreement(Art.25) selected without lis pendens handling (Art.31)")
    if has("Art.24") and forum_type == "appearance":
        issues.append("Appearance(Art.26) cannot override exclusives (Art.24)")
    return {"ok": len(issues) == 0, "issues": issues}


EVIDENCE_PROMPT = """你是法律研究助理。请在候选条文内选择本案"可能相关"的条例条号，按 JSON 对象输出：
{{"evidence": ["Art.24(1)","Art.25(1)"]}}
候选（只能从中选）：{candidates_json}
事实：{facts}
选择要点：{policy}
严格要求：返回的 evidence 必须是候选的子集；不得添加其他条文；只输出 JSON 对象。"""

DECISION_PROMPT = """任务：根据"证据先选"的条文，在给定 JSON Schema 下生成结论。
必须遵守：
- legal_basis 必须来自上一步 evidence（不得新增条文）；
- 命中 Art.24(x) → forum_type="exclusive"，并移除 Art.25/Art.7/Art.4；
- 命中 Art.25(1) 且存在平行诉讼 → 同时处理 Art.31(1)/31(3)；
- Art.25 形式要件缺失（missing_facts 含 "form_requirement"）→ 结论 "Abstain_Insufficient_Info"；
- forum 用简短可验证表述（如 "Spain courts (property location)"），reasoning 50-120 字中文。
事实：{facts}
证据先选：{evidence}
只输出 JSON（符合 Schema）。"""

BASELINE_PROMPT = """你是法律研究助理。阅读事实后，直接回答"由哪国/哪地法院有管辖"，并引用条例条号（如 Art.24(1)/Art.25(1)/Art.7(1)(b)/Art.31(1) 等），中文简述 2-3 句理由。
只需要普通自然语言段落，不需要 JSON。
事实：{facts}"""

RAG_PROMPT = """你是法律研究助理。根据提供的Brussels I bis条例相关条款，判断本案的管辖法院。

**检索到的相关法律条款：**
{retrieved_provisions}

**案件事实：**
{facts}

**任务：**
基于上述条款，直接回答"由哪国/哪地法院有管辖"，并引用条款号（如Art.24(1)/Art.25(1)等），中文简述2-3句理由。
只需要普通自然语言段落，不需要JSON。"""


def coerce_decision(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, str):
        try:
            obj = json.loads(obj)
        except Exception:
            obj = {}
    if not isinstance(obj, dict): obj = {}

    def get_s(k, default=""):
        v = obj.get(k);
        return v if isinstance(v, str) else default

    lb = obj.get("legal_basis", [])
    if isinstance(lb, str):
        try:
            lb = json.loads(lb)
        except Exception:
            lb = [lb]
    if isinstance(lb, dict): lb = [lb]
    norm_lb = []
    if isinstance(lb, list):
        for it in lb:
            if isinstance(it, str):
                norm_lb.append({"provision": it, "eli": "", "granularity": "paragraph"})
            elif isinstance(it, dict) and "provision" in it:
                norm_lb.append({
                    "provision": str(it.get("provision", "")),
                    "eli": str(it.get("eli", "")),
                    "granularity": it.get("granularity", "paragraph") if it.get("granularity") in ["article",
                                                                                                   "paragraph",
                                                                                                   "item"] else "paragraph"
                })
    trace = obj.get("trace", {})
    if isinstance(trace, str):
        try:
            trace = json.loads(trace)
        except Exception:
            trace = {}
    if not isinstance(trace, dict): trace = {}
    evid = trace.get("evidence_ids");
    evid = evid if isinstance(evid, list) else []
    run = trace.get("decode_run") if isinstance(trace.get("decode_run"), str) else "coerced"
    return {
        "conclusion": get_s("conclusion") or "Abstain_Insufficient_Info",
        "forum": get_s("forum"),
        "forum_type": get_s("forum_type") if get_s("forum_type") in ["exclusive", "agreement", "special", "general",
                                                                     "lis_penden", "appearance", "none"] else "none",
        "legal_basis": norm_lb,
        "reasoning": get_s("reasoning"),
        "missing_facts": obj.get("missing_facts") if isinstance(obj.get("missing_facts"), list) else [],
        "trace": {"evidence_ids": evid, "decode_run": run}
    }


def router_from_cf(cf: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any], str]:
    candidates, notes = set(), []
    hard = {"force_abstain_for_form": False, "exclusive": False}

    sm = (cf or {}).get("subject_matter")
    choice = (cf or {}).get("choice_of_court")
    parallel = (cf or {}).get("parallel_actions") or (cf or {}).get("related_actions")
    protected = (cf or {}).get("protected_category")
    appearance = (cf or {}).get("appearance")
    defendant_in_eu = (cf or {}).get("defendant_in_EU")

    if sm == "rights_in_rem_in_immovable_property":
        candidates.add("Art.24(1)");
        notes.append("不动产物权专属优先");
        hard["exclusive"] = True
    elif sm == "validity_of_entries_in_public_register":
        candidates.add("Art.24(3)");
        notes.append("登记簿专属");
        hard["exclusive"] = True
    elif sm == "company_constitution_or_org_decisions":
        candidates.add("Art.24(2)");
        notes.append("公司机关决议专属");
        hard["exclusive"] = True
    elif sm == "ip_registration_or_validity":
        candidates.add("Art.24(4)");
        notes.append("需登记 IP 专属");
        hard["exclusive"] = True
    elif sm == "enforcement_of_judgment":
        candidates.add("Art.24(5)");
        notes.append("执行程序专属");
        hard["exclusive"] = True

    if choice and not hard["exclusive"]:
        candidates.add("Art.25(1)")
        if parallel:
            candidates.add("Art.31(1)");
            candidates.add("Art.31(3)")
        if not (choice.get("form_requirement")):
            hard["force_abstain_for_form"] = True;
            notes.append("Art.25 形式要件缺失→拒答")

    if (parallel is True) and not choice:
        candidates.add("Art.31(1)")

    if (cf or {}).get("contract_type") in ["sale_of_goods", "services"]:
        candidates.add("Art.7(1)(b)")
    if (cf or {}).get("tort"): candidates.add("Art.7(2)")
    if (cf or {}).get("branch_agency_establishment"): candidates.add("Art.7(5)")
    if (cf or {}).get("trust_domicile"): candidates.add("Art.7(6)")

    if defendant_in_eu is True and not (
            {"Art.7(1)(b)", "Art.7(2)", "Art.7(5)", "Art.7(6)"} & candidates) and not candidates:
        candidates.add("Art.4")

    if appearance:
        candidates.add("Art.26(1)")
        if protected: candidates.add("Art.26(2)")

    policy = "; ".join(notes) if notes else "standard_routing"
    return sorted(candidates), hard, policy


def build_articles_map(arts: List[Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
    return {a["provision"]: {"eli": a["eli"], "granularity": a["granularity"]} for a in arts}


def forum_from_cf(cf: Dict[str, Any], forum_type: str) -> str:
    if forum_type == "exclusive":
        loc = (cf.get("property_location") or cf.get("register_location") or
               cf.get("company_seat") or cf.get("ip_register_state") or cf.get("enforcement_place"))
        return f"{loc} courts" if loc else "Specified courts"
    if forum_type == "agreement":
        cc = cf.get("choice_of_court") or {}
        dc = cc.get("designated_court")
        return f"{dc} courts (chosen)" if dc else "Chosen courts"
    return ""


def ensure_eli(pred: Dict[str, Any], amap: Dict[str, Dict[str, str]]):
    for lb in pred.get("legal_basis", []):
        prov = lb.get("provision")
        if prov in amap and not lb.get("eli"):
            lb["eli"] = amap[prov]["eli"]
            if lb.get("granularity") not in ["article", "paragraph", "item"]:
                lb["granularity"] = amap[prov]["granularity"]


def repair_decision(pred: Dict[str, Any], cf: Dict[str, Any], amap: Dict[str, Dict[str, str]]) -> Tuple[
    Dict[str, Any], List[str]]:
    issues = []
    basis_set = {x["provision"] for x in pred.get("legal_basis", [])}

    def has(pfx: str) -> bool:
        return any(b.startswith(pfx) for b in basis_set)

    if has("Art.24"):
        pred["forum_type"] = "exclusive"
        if has("Art.25") or has("Art.7") or has("Art.4"):
            pred["legal_basis"] = [x for x in pred["legal_basis"]
                                   if not (x["provision"].startswith("Art.25") or
                                           x["provision"].startswith("Art.7") or
                                           x["provision"].startswith("Art.4"))]
            issues.append("Removed Art.25/Art.7/Art.4 (overridden by Art.24 exclusivity)")
            basis_set = {x["provision"] for x in pred["legal_basis"]}

    if has("Art.25") and not has("Art.24"):
        pred["forum_type"] = "agreement"
        if cf.get("parallel_actions") and not has("Art.31"):
            pred["legal_basis"].append({"provision": "Art.31(3)", "eli": "", "granularity": "paragraph"})
            issues.append("Added Art.31(3) for parallel actions with Art.25")

    if not pred.get("forum"):
        pred["forum"] = forum_from_cf(cf, pred.get("forum_type", ""))
    ensure_eli(pred, amap)

    rv = rule_validate(pred)
    if not rv["ok"]:
        issues.extend(rv["issues"])
    return pred, issues


EVIDENCE_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["evidence"],
                   "properties": {"evidence": {"type": "array", "items": {"type": "string"}}}}


# ============== 方法1：Baseline ==============
def run_baseline(client: OpenAIClient, facts: str, rules: Dict[str, Any], case_id: int, gold: Dict[str, Any],
                 verbose: bool = False) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if verbose:
        print(f"\n{'=' * 60}")
        print(f"BASELINE - Case {case_id}")
        print(f"{'=' * 60}")
        print(f"Facts: {facts[:100]}...")

    # 让纯LLM直接回答（无检索、无结构约束）
    text, in_tok, out_tok, ttl = client.generate_text(
        prompt=BASELINE_PROMPT.format(facts=facts),
        system_message="Be precise and cite exact article numbers."
    )

    if verbose:
        print(f"\nGenerated text:\n{text[:300]}...")
        print(f"\nTokens: in={in_tok}, out={out_tok}, total={ttl}")

    # 从自由文本中解析它'自己声称'的结论 / forum_type / forum
    conclusion, forum_type, forum_guess = parse_llm_free_answer(text)

    # 模型声称引用了哪些条文
    provisions = extract_provisions_from_text(text)

    if verbose:
        print(f"\nParsed conclusion (raw self-claim): {conclusion}")
        print(f"Parsed forum_type (raw self-claim): {forum_type}")
        print(f"Parsed forum guess: {forum_guess}")
        print(f"Extracted provisions: {provisions}")
        print(f"Gold provisions: {[x['provision'] for x in gold['legal_basis']]}")

    pred = {
        "conclusion": conclusion,
        "forum": forum_guess,
        "forum_type": forum_type,
        "legal_basis": [
            {"provision": p, "eli": "", "granularity": "paragraph"}
            for p in provisions
        ],
        "reasoning": text.strip()[:400],
        "missing_facts": [],
        "trace": {
            "evidence_ids": provisions,
            "decode_run": "baseline_free_text"
        }
    }

    # Promote-Hit: 检查“模型声称的 forum_type”是否跟它自己引用的条文优先级一致
    promote_hit = metric_promote_hit(provisions, forum_type, rules)

    logger.log("token_stats", case_id, "baseline token usage", {
        "mode": "baseline",
        "in": in_tok, "out": out_tok, "total": ttl
    })

    return pred, {
        "in": in_tok, "out": out_tok, "ttl": ttl,
        "promote_hit": promote_hit
    }



# ============== 方法2：RAG（增强诊断）==============
def run_rag(client: OpenAIClient, facts: str, retriever: SimpleRAGRetriever, rules: Dict[str, Any],
            case_id: int, gold: Dict[str, Any], verbose: bool = False) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if verbose:
        print(f"\n{'=' * 60}")
        print(f"RAG - Case {case_id}")
        print(f"{'=' * 60}")
        print(f"Facts: {facts[:100]}...")

    # 1. RAG检索（但这只是把条文塞进提示里，仍是自由回答，非结构化约束）
    retrieved = retriever.retrieve(facts, top_k=5)

    if verbose:
        print(f"\n检索到 {len(retrieved)} 个条款:")
        for i, p in enumerate(retrieved, 1):
            print(f"  {i}. {p['provision']} - {p['title']}")

    gold_provisions = [x["provision"] for x in gold.get("legal_basis", [])]
    retrieved_provisions = [p['provision'] for p in retrieved]

    logger.log("rag_retrieval", case_id, "retrieval quality", {
        "query": facts[:100],
        "retrieved": retrieved_provisions,
        "gold_provisions": gold_provisions,
        "hit_count": len(set(retrieved_provisions) & set(gold_provisions)),
        "gold_count": len(gold_provisions)
    })

    # 2. 构造提示，把检索到的条文(原文片段)喂给模型
    if retrieved:
        provisions_text = "\n\n".join([
            f"【{p['provision']} - {p['title']}】\n{p['text_zh']}"
            for p in retrieved
        ])
    else:
        provisions_text = "（未检索到相关条款）"

    full_prompt = RAG_PROMPT.format(
        retrieved_provisions=provisions_text,
        facts=facts
    )

    # 3. 生成自由回答（注意：依然不是结构化JSON，依然允许出错）
    text, in_tok, out_tok, ttl = client.generate_text(
        prompt=full_prompt,
        system_message="Be precise and cite exact article numbers from the provided provisions."
    )

    if verbose:
        print(f"\nGenerated text:\n{text[:300]}...")
        print(f"\nTokens: in={in_tok}, out={out_tok}, total={ttl}")

    # 4. 直接解析模型自己的说法（不校正）
    conclusion, forum_type, forum_guess = parse_llm_free_answer(text)

    # 它声称引用了哪些条文
    provisions = extract_provisions_from_text(text)

    pred = {
        "conclusion": conclusion,
        "forum": forum_guess,
        "forum_type": forum_type,
        "legal_basis": [
            {"provision": p, "eli": "", "granularity": "paragraph"}
            for p in provisions
        ],
        "reasoning": text.strip()[:400],
        "missing_facts": [],
        "trace": {
            "evidence_ids": provisions,
            "decode_run": "rag_retrieval",
            "retrieved": retrieved_provisions
        }
    }

    # Promote-Hit 现在衡量的是：模型自己声称的 forum_type vs. 它自己列出来的条文，是否一致
    promote_hit = metric_promote_hit(provisions, forum_type, rules)

    logger.log("token_stats", case_id, "rag token usage", {
        "mode": "rag",
        "in": in_tok, "out": out_tok, "total": ttl,
        "prompt_length": len(full_prompt),
        "retrieved_count": len(retrieved)
    })

    return pred, {
        "in": in_tok, "out": out_tok, "ttl": ttl,
        "promote_hit": promote_hit,
        "retrieved_count": len(retrieved)
    }



# ============== 方法3：PRISM（增强诊断）==============
def run_prism(client: OpenAIClient, facts: str, cf: Dict[str, Any], schema_obj: Dict[str, Any],
              articles: List[Dict[str, Any]], rules: Dict[str, Any],
              case_id: int, gold: Dict[str, Any], verbose: bool = False) -> Tuple[
    Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    if verbose:
        print(f"\n{'=' * 60}")
        print(f"PRISM - Case {case_id}")
        print(f"{'=' * 60}")

    # 1. 路由
    candidates, hard, policy = router_from_cf(cf)
    candidates_json = json.dumps(candidates, ensure_ascii=False)

    # 2. 证据选择
    ev_obj, in1, out1, ttl1 = client.generate_with_schema(
        prompt=EVIDENCE_PROMPT.format(facts=facts, candidates_json=candidates_json, policy=policy),
        schema=EVIDENCE_SCHEMA
    )
    evidence = []
    if isinstance(ev_obj, dict) and isinstance(ev_obj.get("evidence"), list):
        evidence = [str(x) for x in ev_obj["evidence"] if isinstance(x, str)]
    if not evidence:
        evidence = candidates[:]

    links_cf = cf
    missing_hint = []
    if hard["force_abstain_for_form"]:
        missing_hint.append("form_requirement")

    # 3. 约束解码
    dec_raw, in2, out2, ttl2 = client.generate_with_schema(
        prompt=DECISION_PROMPT.format(facts=facts, evidence=json.dumps(evidence, ensure_ascii=False)),
        schema=schema_obj
    )
    pred = coerce_decision(dec_raw)
    amap = build_articles_map(articles)

    # 4. Hard gates处理
    if missing_hint:
        mf = set(pred.get("missing_facts", []))
        mf.update(missing_hint)
        pred["missing_facts"] = sorted(mf)
        if pred.get("conclusion") != "Abstain_Insufficient_Info":
            pred["conclusion"] = "Abstain_Insufficient_Info"

    # 5. 修复
    pred_fixed, repair_issues = repair_decision(pred, cf, amap)

    usage = {"in": in1 + in2, "out": out1 + out2, "ttl": ttl1 + ttl2}

    # —— 修改：Promote-Hit 以“最终 legal_basis”计算（与 Baseline/RAG 口径一致）——
    lb_for_promote = [x["provision"] for x in pred_fixed.get("legal_basis", [])]
    promote_hit = metric_promote_hit(lb_for_promote, pred_fixed.get("forum_type", ""), rules)

    # 记录弃权质量
    gold_should_abstain = norm(gold.get("conclusion")) == "abstain_insufficient_info"
    pred_did_abstain = norm(pred_fixed.get("conclusion")) == "abstain_insufficient_info"
    logger.log("prism_abstention", case_id, "abstention check", {
        "should_abstain": gold_should_abstain,
        "did_abstain": pred_did_abstain,
        "reason": f"hard_gates={hard}, missing_hint={missing_hint}, repair={len(repair_issues) > 0}"
    })

    logger.log("token_stats", case_id, "prism token usage", {
        "mode": "prism", "in": in1 + in2, "out": out1 + out2, "total": ttl1 + ttl2
    })

    aux = {
        "evidence": evidence, "policy": policy,
        "Repaired": len(repair_issues) > 0, "repair_issues": repair_issues,
        "trace_cf": links_cf, "promote_hit": promote_hit
    }

    return pred_fixed, usage, aux


def parse_llm_free_answer(text: str) -> Tuple[str, str, str]:
    """
    从 LLM 自然语言回答中直接解析:
    - conclusion: 模型自己声称的结论 (不自动降级为弃权)
    - forum_type: 模型自己声称的管辖类型 (不靠条文反推)
    - forum: 模型提到的具体法院/法域 (如果能提取就放进 pred['forum'])

    解析是启发式的，但只读模型的话，不替模型校正/兜底为更合理答案。
    """
    t = norm(text)

    # 1) forum_type: 直接看模型措辞
    forum_type = "none"
    if "专属管辖" in t:
        forum_type = "exclusive"
    elif "约定管辖" in t or "协议选择法院" in t or "选择法院协议" in t or "双方约定的法院" in t or "协议指定法院" in t:
        forum_type = "agreement"
    elif "先受理" in t or "lis pendens" in t or "第一受理法院" in t or "应中止后提起的诉讼" in t:
        forum_type = "lis_penden"
    elif "特别管辖" in t or "特殊管辖" in t:
        forum_type = "special"
    elif "一般管辖" in t:
        forum_type = "general"
    elif "出庭" in t or "应诉" in t or "appearance" in t:
        forum_type = "appearance"

    # 2) conclusion: 直接按模型态度判断
    #    a. 明确说无法判断/信息不足 → 视为弃权
    if any(phrase in t for phrase in [
        "信息不足", "资料不足", "事实不足", "无法确定", "无法判断", "不能确定", "无法明确", "难以判断", "无法最终判断"
    ]):
        conclusion = "Abstain_Insufficient_Info"

    #    b. lis pendens / 先受理优先 → stay
    elif any(phrase in t for phrase in [
        "先受理", "第一受理法院", "应中止", "后提起的诉讼应中止", "应由先受理法院优先审理", "优先由首先受理的法院"
    ]):
        conclusion = "Stay_for_first_seised"

    #    c. 双方约定法院优先审理
    elif any(phrase in t for phrase in [
        "应提交至双方约定的法院", "应交由约定法院", "尊重选择法院协议", "由当事人约定的法院审理", "由约定法院专属管辖"
    ]):
        conclusion = "Decline_in_favor_of_chosen_court"

    #    d. 显式说“X法院有管辖权/享有管辖权/具有专属管辖权/一般管辖权”
    elif "法院" in t and any(phrase in t for phrase in [
        "有管辖权", "享有管辖权", "具有管辖权", "拥有管辖权", "有专属管辖权", "具有专属管辖权",
        "有一般管辖权", "享有一般管辖权"
    ]):
        conclusion = "Court_of_X_has_jurisdiction"

    else:
        #    e. fallback：如果 forum_type 暗示一种特定机制，则给对应的典型结论
        if forum_type == "lis_penden":
            conclusion = "Stay_for_first_seised"
        elif forum_type == "agreement":
            conclusion = "Decline_in_favor_of_chosen_court"
        elif forum_type in ["exclusive", "special", "general", "appearance"]:
            conclusion = "Court_of_X_has_jurisdiction"
        else:
            # 最后才放弃
            conclusion = "Abstain_Insufficient_Info"

    # 3) forum: 尝试从句子中提取“由X法院管辖/审理”
    forum_guess = ""
    m = re.search(r"(?:由|应由|提交至|应提交至|应交由)([^。；\n，,]*?法院)[^。；\n，,]*(?:管辖|审理)", text)
    if m:
        forum_guess = m.group(1).strip()

    return conclusion, forum_type, forum_guess

# ============== 主流程 ==============
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["baseline", "rag", "prism", "all"], default="all")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--verbose", action="store_true", help="显示详细日志（仅显示前3个案例）")
    parser.add_argument("--analyze", action="store_true", help="运行后显示详细分析")
    args = parser.parse_args()
    random.seed(args.seed)

    dataset = load_jsonl(DATA)
    articles = load_json(ARTS)["articles"]
    rules = load_json(RULES)
    schema_obj = load_json(SCHEMA)
    client = OpenAIClient()

    retriever = None
    if args.mode in ("rag", "all"):
        if not PROVISIONS.exists():
            raise FileNotFoundError(f"RAG knowledge base not found: {PROVISIONS}\n"
                                    f"Please ensure brussels_provisions.jsonl is in kb/ directory")
        retriever = SimpleRAGRetriever(PROVISIONS)
        print(f"✓ Loaded {len(retriever.provisions)} provisions for RAG")

        # 测试检索
        if args.verbose:
            print("\n【RAG检索测试】")
            test_queries = [
                ("不动产物权纠纷", ["Art.24(1)"]),
                ("选择法院协议", ["Art.25(1)"]),
                ("买卖合同交付地", ["Art.7(1)(b)"])
            ]
            for query, expected in test_queries:
                test_retrieved = retriever.retrieve(query, top_k=3)
                print(f"  Query: '{query}'")
                print(f"    Retrieved: {[p['provision'] for p in test_retrieved]}")
                print(f"    Expected: {expected}")
                print(f"    Match: {'✓' if expected[0] in [p['provision'] for p in test_retrieved] else '✗'}")

    rows = []
    n = min(args.limit, len(dataset))

    print(f"\n{'=' * 60}")
    print(f"Running experiment: mode={args.mode}, samples={n}")
    print(f"{'=' * 60}\n")

    for i in range(n):
        item = dataset[i]
        gold = item["expected_output"]
        facts = item["facts_text"]
        cf = item.get("connecting_factors", {})

        # 详细日志仅显示前3个案例
        verbose = args.verbose and i < 3

        print(f"[{i + 1}/{n}] Processing case {item['id']}...")

        if args.mode in ("baseline", "all"):
            pred_b, usage_b = run_baseline(client, facts, rules, item['id'], gold, verbose)
            ev_b = [x["provision"] for x in pred_b.get("legal_basis", [])]
            exp_cat_b = expected_forum_from_evidence(ev_b, rules)
            promote_hit_b = int(exp_cat_b == (pred_b.get("forum_type") or ""))

            legal_correct = metric_legal_correct(pred_b, gold)
            if not legal_correct:
                logger.log_error("baseline", item['id'], pred_b, gold,
                                 f"provisions={ev_b}")

            rows.append({
                "id": item["id"], "mode": "baseline",
                "Legal-Correct@1": legal_correct,
                "Citation-Precision": metric_citation_precision(pred_b, gold),
                "Abstention-Quality": metric_abstention_quality(pred_b, gold),
                "Promote-Hit": promote_hit_b,
                "Schema-Pass": 0, "Rule-OK": 0,
                "tokens_in": usage_b["in"], "tokens_out": usage_b["out"], "tokens_total": usage_b["ttl"],
                "pred": pred_b, "gold": gold, "trace_cf": cf
            })

        if args.mode in ("rag", "all"):
            pred_r, usage_r = run_rag(client, facts, retriever, rules, item['id'], gold, verbose)
            ev_r = [x["provision"] for x in pred_r.get("legal_basis", [])]
            exp_cat_r = expected_forum_from_evidence(ev_r, rules)
            promote_hit_r = int(exp_cat_r == (pred_r.get("forum_type") or ""))

            legal_correct = metric_legal_correct(pred_r, gold)
            if not legal_correct:
                logger.log_error("rag", item['id'], pred_r, gold,
                                 f"retrieved={pred_r.get('trace', {}).get('retrieved', [])}")

            rows.append({
                "id": item["id"], "mode": "rag",
                "Legal-Correct@1": legal_correct,
                "Citation-Precision": metric_citation_precision(pred_r, gold),
                "Abstention-Quality": metric_abstention_quality(pred_r, gold),
                "Promote-Hit": promote_hit_r,
                "Schema-Pass": 0, "Rule-OK": 0,
                "tokens_in": usage_r["in"], "tokens_out": usage_r["out"], "tokens_total": usage_r["ttl"],
                "pred": pred_r, "gold": gold,
                "retrieved": pred_r.get("trace", {}).get("retrieved", []),
                "retrieved_count": usage_r.get("retrieved_count", 0)
            })

        if args.mode in ("prism", "all"):
            pred_p, usage_p, aux_p = run_prism(client, facts, cf, schema_obj, articles, rules,
                                               item['id'], gold, verbose)

            schema_valid = True
            try:
                from jsonschema import validate
                validate(instance=pred_p, schema=schema_obj)
            except Exception:
                schema_valid = False
            rv = rule_validate(pred_p)

            ev_p = aux_p.get("evidence", [])
            exp_cat_p = expected_forum_from_evidence(ev_p, rules)
            promote_hit_p = int(exp_cat_p == (pred_p.get("forum_type") or ""))

            legal_correct = metric_legal_correct(pred_p, gold)
            if not legal_correct:
                logger.log_error("prism", item['id'], pred_p, gold,
                                 f"evidence={ev_p}, repair={aux_p.get('repair_issues', [])}")

            rows.append({
                "id": item["id"], "mode": "prism",
                "Legal-Correct@1": legal_correct,
                "Citation-Precision": metric_citation_precision(pred_p, gold),
                "Abstention-Quality": metric_abstention_quality(pred_p, gold),
                "Promote-Hit": promote_hit_p,
                "Schema-Pass": metric_schema_pass(schema_valid),
                "Rule-OK": int(rv["ok"]),
                "tokens_in": usage_p["in"], "tokens_out": usage_p["out"], "tokens_total": usage_p["ttl"],
                "pred": pred_p, "gold": gold,
                "evidence": ev_p, "policy": aux_p.get("policy", ""),
                "Repaired": aux_p.get("Repaired", False), "repair_issues": aux_p.get("repair_issues", []),
                "trace_cf": cf
            })

        time.sleep(0.03)

    # ============== 结果汇总 ==============
    def agg(mode: str, key: str) -> float:
        xs = [r[key] for r in rows if r["mode"] == mode]
        return sum(xs) / max(1, len(xs))

    modes_map = {
        "baseline": "Baseline (纯LLM)",
        "rag": "RAG (LLM+检索)",
        "prism": "PRISM (框架)"
    }

    modes = []
    if args.mode == "all":
        modes = ["baseline", "rag", "prism"]
    else:
        modes = [args.mode]

    print("\n" + "=" * 80)
    print(f"{'EXPERIMENT RESULTS':^80}")
    print("=" * 80)

    for m in modes:
        print(f"\n【{modes_map[m]}】 on {n} samples")
        print("-" * 60)
        print(f"  Legal-Correct@1    : {agg(m, 'Legal-Correct@1'):.3f}")
        print(f"  Citation-Precision : {agg(m, 'Citation-Precision'):.3f}")
        print(f"  Abstention-Quality : {agg(m, 'Abstention-Quality'):.3f}")
        print(f"  Promote-Hit        : {agg(m, 'Promote-Hit'):.3f}")

        if m in ("prism",):
            print(f"  Schema-Pass        : {agg(m, 'Schema-Pass'):.3f}")
            print(f"  Rule-OK            : {agg(m, 'Rule-OK'):.3f}")

        print(f"  Avg Tokens (total) : {agg(m, 'tokens_total'):.1f}")

        if m == "rag":
            avg_retrieved = sum(r.get("retrieved_count", 0) for r in rows if r["mode"] == "rag") / max(1,
                                                                                                       len([r for r in
                                                                                                            rows if r[
                                                                                                                "mode"] == "rag"]))
            print(f"  Avg Retrieved      : {avg_retrieved:.1f} provisions")

    if args.mode == "all":
        print("\n" + "=" * 80)
        print(f"{'COMPARATIVE SUMMARY':^80}")
        print("=" * 80)
        print(f"{'Metric':<25} {'Baseline':<15} {'RAG':<15} {'PRISM':<15}")
        print("-" * 80)

        metrics = [
            ("Legal-Correct@1", "Legal-Correct@1"),
            ("Citation-Precision", "Citation-Precision"),
            ("Abstention-Quality", "Abstention-Quality"),
            ("Promote-Hit", "Promote-Hit"),
            ("Schema-Pass", "Schema-Pass"),
            ("Rule-OK", "Rule-OK"),
            ("Avg Tokens", "tokens_total")
        ]

        for label, key in metrics:
            b_val = agg("baseline", key)
            r_val = agg("rag", key)
            p_val = agg("prism", key)

            if key in ["Schema-Pass", "Rule-OK"]:
                print(f"{label:<25} {'--':<15} {'--':<15} {p_val:.3f}")
            elif key == "tokens_total":
                print(f"{label:<25} {b_val:.0f}{'':>10} {r_val:.0f}{'':>10} {p_val:.0f}")
            else:
                print(f"{label:<25} {b_val:.3f}{'':>10} {r_val:.3f}{'':>10} {p_val:.3f}")

    out_path = ROOT / "pil_results.jsonl"
    ensure_dir(out_path)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\n✓ Saved detailed results to: {out_path}")
    print(f"  Fields: id, mode, metrics, pred, gold, evidence/retrieved (mode-specific)")
    print("=" * 80 + "\n")

    # ============== 诊断分析 ==============
    if args.analyze or args.verbose:
        logger.summary()


if __name__ == "__main__":
    main()