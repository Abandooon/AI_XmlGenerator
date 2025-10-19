# -*- coding: utf-8 -*-
"""
Private International Law (Brussels I bis) — API-only A/B 实验（路由+判别归一+修复写回）
"""
import re, json, argparse, time, random
from typing import Dict, Any, List, Tuple
from pathlib import Path

# === 依你项目结构调整此导入 ===
from src.llm_generation.llm.openai_client import OpenAIClient

ROOT = Path(__file__).resolve().parent
PIL_DIR = ROOT
DATA = PIL_DIR / "data" / "experiment_dataset.jsonl"
ARTS = PIL_DIR / "kb" / "articles_index.json"
RULES = PIL_DIR / "rules" / "rule_priority_table.json"
SCHEMA = PIL_DIR / "schema" / "decision_schema.json"

# === Promote: expected forum_type from evidence set (uses rules/rule_priority_table.json) ===
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
        if cat == "exclusive"  and has("Art.24"): return "exclusive"
        if cat == "agreement"  and has("Art.25"): return "agreement"
        if cat == "special"    and any(x.startswith("Art.7") for x in s): return "special"
        if cat == "general"    and "Art.4" in s: return "general"
        if cat == "appearance" and has("Art.26"): return "appearance"
    return "none"



# ------- Provision → Category + Promote-Hit -------
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
    """根据证据先选的条文集合，按优先序计算应当的类别。"""
    cats = set(provision_category(e) for e in evidence)
    # 规则表中的命名到类别的映射
    order_map = {
        "exclusive_Art24":"exclusive",
        "agreement_Art25_31":"agreement",
        "special_Art7":"special",
        "general_Art4":"general",
        "appearance_Art26":"appearance"
    }
    # 特判：无协议但出现 Art.31（先受理）→ lis_penden
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


# ---------- IO ----------
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

# ---------- 指标 ----------
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

# ---------- Baseline 解析 ----------
def map_baseline_conclusion(text: str) -> Tuple[str, str]:
    t = norm(text)
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

# ---------- 规则校验 ----------
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

# ---------- Prompts ----------
EVIDENCE_PROMPT = """你是法律研究助理。请在候选条文内选择本案“可能相关”的条例条号，按 JSON 对象输出：
{{"evidence": ["Art.24(1)","Art.25(1)"]}}
候选（只能从中选）：{candidates_json}
事实：{facts}
选择要点：{policy}
严格要求：返回的 evidence 必须是候选的子集；不得添加其他条文；只输出 JSON 对象。"""


DECISION_PROMPT = """任务：根据“证据先选”的条文，在给定 JSON Schema 下生成结论。
必须遵守：
- legal_basis 必须来自上一步 evidence（不得新增条文）；
- 命中 Art.24(x) → forum_type="exclusive"，并移除 Art.25/Art.7/Art.4；
- 命中 Art.25(1) 且存在平行诉讼 → 同时处理 Art.31(1)/31(3)；
- Art.25 形式要件缺失（missing_facts 含 "form_requirement"）→ 结论 "Abstain_Insufficient_Info"；
- forum 用简短可验证表述（如 "Spain courts (property location)"），reasoning 50-120 字中文。
事实：{facts}
证据先选：{evidence}
只输出 JSON（符合 Schema）。"""

BASELINE_PROMPT = """你是法律研究助理。阅读事实后，直接回答“由哪国/哪地法院有管辖”，并引用条例条号（如 Art.24(1)/Art.25(1)/Art.7(1)(b)/Art.31(1) 等），中文简述 2-3 句理由。
只需要普通自然语言段落，不需要 JSON。
事实：{facts}"""

# ---------- 决策对象清洗 ----------
def coerce_decision(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, str):
        try: obj = json.loads(obj)
        except Exception: obj = {}
    if not isinstance(obj, dict): obj = {}
    def get_s(k, default=""):
        v = obj.get(k); return v if isinstance(v, str) else default
    lb = obj.get("legal_basis", [])
    if isinstance(lb, str):
        try: lb = json.loads(lb)
        except Exception: lb = [lb]
    if isinstance(lb, dict): lb = [lb]
    norm_lb = []
    if isinstance(lb, list):
        for it in lb:
            if isinstance(it, str):
                norm_lb.append({"provision": it, "eli": "", "granularity": "paragraph"})
            elif isinstance(it, dict) and "provision" in it:
                norm_lb.append({
                    "provision": str(it.get("provision","")),
                    "eli": str(it.get("eli","")),
                    "granularity": it.get("granularity","paragraph") if it.get("granularity") in ["article","paragraph","item"] else "paragraph"
                })
    trace = obj.get("trace", {})
    if isinstance(trace, str):
        try: trace = json.loads(trace)
        except Exception: trace = {}
    if not isinstance(trace, dict): trace = {}
    evid = trace.get("evidence_ids"); evid = evid if isinstance(evid, list) else []
    run = trace.get("decode_run") if isinstance(trace.get("decode_run"), str) else "coerced"
    return {
        "conclusion": get_s("conclusion") or "Abstain_Insufficient_Info",
        "forum": get_s("forum"),
        "forum_type": get_s("forum_type") if get_s("forum_type") in ["exclusive","agreement","special","general","lis_penden","appearance","none"] else "none",
        "legal_basis": norm_lb,
        "reasoning": get_s("reasoning"),
        "missing_facts": obj.get("missing_facts") if isinstance(obj.get("missing_facts"), list) else [],
        "trace": {"evidence_ids": evid, "decode_run": run}
    }

# ---------- Router：更精细的候选+硬门槛 ----------
def router_from_cf(cf: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any], str]:
    candidates, notes = set(), []
    hard = {"force_abstain_for_form": False, "exclusive": False}

    sm = (cf or {}).get("subject_matter")
    choice = (cf or {}).get("choice_of_court")
    parallel = (cf or {}).get("parallel_actions") or (cf or {}).get("related_actions")
    protected = (cf or {}).get("protected_category")
    appearance = (cf or {}).get("appearance")
    defendant_in_eu = (cf or {}).get("defendant_in_EU")

    # --- 专属 24 ---
    if sm == "rights_in_rem_in_immovable_property":
        candidates.add("Art.24(1)"); notes.append("不动产物权专属优先"); hard["exclusive"] = True
    elif sm == "validity_of_entries_in_public_register":
        candidates.add("Art.24(3)"); notes.append("登记簿专属"); hard["exclusive"] = True
    elif sm == "company_constitution_or_org_decisions":
        candidates.add("Art.24(2)"); notes.append("公司机关决议专属"); hard["exclusive"] = True
    elif sm == "ip_registration_or_validity":
        candidates.add("Art.24(4)"); notes.append("需登记 IP 专属"); hard["exclusive"] = True
    elif sm == "enforcement_of_judgment":
        candidates.add("Art.24(5)"); notes.append("执行程序专属"); hard["exclusive"] = True

    # --- 协议 25 + 平行 31 ---
    if choice and not hard["exclusive"]:
        candidates.add("Art.25(1)")
        if parallel:
            candidates.add("Art.31(1)"); candidates.add("Art.31(3)")
        if not (choice.get("form_requirement")):
            hard["force_abstain_for_form"] = True; notes.append("Art.25 形式要件缺失→拒答")

    # --- 无协议但平行/相关 → 也要给 31 ---
    if (parallel is True) and not choice:
        candidates.add("Art.31(1)")

    # --- 特别 7 ---
    if (cf or {}).get("contract_type") in ["sale_of_goods","services"]:
        candidates.add("Art.7(1)(b)")
    if (cf or {}).get("tort"): candidates.add("Art.7(2)")
    if (cf or {}).get("branch_agency_establishment"): candidates.add("Art.7(5)")
    if (cf or {}).get("trust_domicile"): candidates.add("Art.7(6)")

    # --- 一般 4（仅在未触发 7/24/25/31 时补上） ---
    if defendant_in_eu is True and not ({"Art.7(1)(b)","Art.7(2)","Art.7(5)","Art.7(6)"} & candidates) and not candidates:
        candidates.add("Art.4")

    # --- 出庭 26 ---
    if appearance:
        candidates.add("Art.26(1)")
        if protected: candidates.add("Art.26(2)")

    if not candidates:
        candidates = {"Art.4","Art.7(1)(b)","Art.24(1)","Art.25(1)","Art.31(1)"}

    policy = "；".join(notes) if notes else "严格从候选中选择。专属(24)覆盖协议(25)/特别(7)/一般(4)；存在平行则纳入 Art.31。"
    return sorted(candidates), hard, policy

# ---------- 文章元数据 ----------
def build_articles_map(articles: List[Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
    return {a["provision"]: {"eli": a["eli"], "granularity": a["granularity"]} for a in articles}

def ensure_eli(pred: Dict[str, Any], amap: Dict[str, Dict[str, str]]):
    fixed = []
    for it in pred.get("legal_basis", []):
        prov = it.get("provision","")
        meta = amap.get(prov, {"eli":"", "granularity":"paragraph"})
        it["eli"] = it.get("eli") or meta["eli"]
        it["granularity"] = it.get("granularity") if it.get("granularity") in ["article","paragraph","item"] else meta["granularity"]
        fixed.append(it)
    pred["legal_basis"] = fixed

# ---------- forum 生成 ----------
def forum_from_cf(cf: Dict[str, Any], forum_type: str) -> str:
    if forum_type == "exclusive":
        if cf.get("property_location"): return f'{cf["property_location"]} courts (property location)'
        if cf.get("register_location"): return f'{cf["register_location"]} courts (register location)'
        if cf.get("company_seat"): return f'{cf["company_seat"]} courts (company seat)'
        if cf.get("ip_register_state"): return f'{cf["ip_register_state"]} courts (IP register)'
        if cf.get("enforcement_place"): return f'{cf["enforcement_place"]} courts (place of enforcement)'
    if forum_type == "special":
        if cf.get("place_of_delivery"): return f'{cf["place_of_delivery"]} courts (place of delivery)'
        if cf.get("place_of_performance"): return f'{cf["place_of_performance"]} courts (place of performance)'
        if cf.get("harm_place"): return f'{cf["harm_place"]} courts (place of harm)'
        if cf.get("establishment_place"): return f'{cf["establishment_place"]} courts (establishment place)'
        if cf.get("trust_domicile"): return f'{cf["trust_domicile"]} courts (trust domicile)'
    if forum_type == "agreement":
        ch = (cf.get("choice_of_court") or {}).get("designated_court")
        if ch: return f'{ch} courts (chosen)'
    if forum_type == "general":
        if cf.get("defendant_domicile"): return f'{cf["defendant_domicile"]} courts (defendant domicile)'
    return ""

# ---------- 判别归一 + 修复写回（核心） ----------
def repair_decision(pred: Dict[str, Any], cf: Dict[str, Any], amap: Dict[str, Dict[str,str]]) -> Tuple[Dict[str, Any], List[str]]:
    issues = []
    def has(prefix: str) -> bool:
        return any(x["provision"].startswith(prefix) for x in pred.get("legal_basis", []))
    def keep_only(prefixes: List[str]):
        pred["legal_basis"] = [x for x in pred["legal_basis"] if any(x["provision"].startswith(p) for p in prefixes)]

    has24 = has("Art.24"); has25 = has("Art.25"); has7 = any(has(p) for p in ["Art.7(1)","Art.7(2)","Art.7(5)","Art.7(6)"])
    has31 = has("Art.31"); has4 = has("Art.4"); has26 = has("Art.26")
    parallel = cf.get("parallel_actions") or cf.get("related_actions")
    choice = (cf or {}).get("choice_of_court") or {}
    form_ok = bool(choice.get("form_requirement"))

    # 1) 专属 → exclusive，剔除 25/7/4
    if has24:
        keep_only(["Art.24"])
        pred["forum_type"] = "exclusive"
        pred["conclusion"] = "Court_of_X_has_jurisdiction"
        issues.append("override_by_Art24")

    # 2) lis pendens（无协议也成立）→ 只保留 31，归并 lis_penden
    if not has24 and has31 and not has25:
        keep_only(["Art.31"])
        pred["forum_type"] = "lis_penden"
        pred["conclusion"] = "Stay_for_first_seised"
        issues.append("force_lis_penden_by_Art31")

    # 3) 协议：有平行 → 需要 31；无平行 → chosen 有管辖
    if not has24 and has25:
        pred["forum_type"] = "agreement"
        if parallel and not has31:
            pred["legal_basis"].append({"provision":"Art.31(1)","eli":"","granularity":"paragraph"})
            pred["legal_basis"].append({"provision":"Art.31(3)","eli":"","granularity":"paragraph"})
            issues.append("add_Art31_for_agreement")
        pred["conclusion"] = "Decline_in_favor_of_chosen_court" if parallel else "Court_of_X_has_jurisdiction"
        # 25 形式要件缺失 → 拒答
        if not form_ok:
            pred["conclusion"] = "Abstain_Insufficient_Info"
            mf = set(pred.get("missing_facts", [])); mf.add("form_requirement"); pred["missing_facts"] = sorted(mf)
            issues.append("forced_abstention_form_missing")

    # 4) 特别 vs 一般：命中 7 且不含 24/25/31 → special，并剔除 4
    if not has24 and not has25 and not has31 and has7:
        keep_only(["Art.7"])
        pred["forum_type"] = "special"
        pred["conclusion"] = "Court_of_X_has_jurisdiction"
        issues.append("promote_special_over_general")

    # 5) 非 EU 被告 → 回成员国法
    if cf.get("defendant_in_EU") is False:
        pred["conclusion"] = "No_EU_jurisdiction_use_member_state_law"
        pred["forum_type"] = "none"
        pred["legal_basis"] = []
        issues.append("fallback_member_state_law")

    # 6) 出庭：不得突破专属；保护性未告知 → 拒答（若出现）
    if has26 and pred.get("forum_type") == "exclusive":
        keep_only(["Art.24"])  # 出庭不允许覆盖
        issues.append("appearance_cannot_override_exclusive")
    if (cf.get("protected_category") and cf.get("appearance") and not cf.get("informed_of_rights")):
        pred["conclusion"] = "Abstain_Insufficient_Info"
        mf = set(pred.get("missing_facts", [])); mf.add("notification_of_right_to_contest"); pred["missing_facts"] = sorted(mf)
        issues.append("protected_party_notification_missing")

    # forum 填充 + ELI/粒度
    if not pred.get("forum"):
        pred["forum"] = forum_from_cf(cf, pred.get("forum_type",""))
    ensure_eli(pred, amap)

    # 二次规则校验（兜底）
    rv = rule_validate(pred)
    if not rv["ok"]:
        issues.extend(rv["issues"])
    return pred, issues

# ---------- LLM 交互 ----------
EVIDENCE_SCHEMA = {"type":"object","additionalProperties":False,"required":["evidence"],"properties":{"evidence":{"type":"array","items":{"type":"string"}}}}

def run_baseline(client: OpenAIClient, facts: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    text, in_tok, out_tok, ttl = client.generate_text(
        prompt=BASELINE_PROMPT.format(facts=facts),
        system_message="Be precise and cite exact article numbers."
    )
    provisions = extract_provisions_from_text(text)
    conclusion, forum_type = map_baseline_conclusion(text)
    pred = {
        "conclusion": conclusion, "forum": "", "forum_type": forum_type,
        "legal_basis": [{"provision": p, "eli": "", "granularity": "paragraph"} for p in provisions],
        "reasoning": text.strip()[:400], "missing_facts": [],
        "trace": {"evidence_ids": provisions, "decode_run": "baseline_free_text"}
    }
    # 在 run_baseline 返回前：
    promote_hit = metric_promote_hit(provisions, conclusion and map_baseline_conclusion(text)[1], load_json(RULES))
    return pred, {"in": in_tok, "out": out_tok, "ttl": ttl, "promote_hit": promote_hit}


def run_framework(client: OpenAIClient, facts: str, cf: Dict[str, Any], schema_obj: Dict[str, Any],
                  articles: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    candidates, hard, policy = router_from_cf(cf)
    candidates_json = json.dumps(candidates, ensure_ascii=False)
    ev_obj, in1, out1, ttl1 = client.generate_with_schema(
        prompt=EVIDENCE_PROMPT.format(facts=facts, candidates_json=candidates_json, policy=policy),
        schema=EVIDENCE_SCHEMA
    )

    evidence = []
    if isinstance(ev_obj, dict) and isinstance(ev_obj.get("evidence"), list):
        evidence = [str(x) for x in ev_obj["evidence"] if isinstance(x, str)]
    if not evidence: evidence = candidates[:]  # 兜底

    # ... run_framework 内，evidence 计算完成后
    links_cf = cf  # oracle 元模型直接作为 trace（不写入 pred 以免破坏 Schema）
    promote_hit = metric_promote_hit(evidence, None, load_json(RULES))  # 先用证据的预期类别；最终用预测类别再算一次见下

    # 把“应拒答”的缺口显式带入（有助于模型在第二阶段更稳）
    missing_hint = []
    if hard["force_abstain_for_form"]:
        missing_hint.append("form_requirement")

    dec_raw, in2, out2, ttl2 = client.generate_with_schema(
        prompt=DECISION_PROMPT.format(facts=facts, evidence=json.dumps(evidence, ensure_ascii=False)),
        schema=schema_obj
    )
    pred = coerce_decision(dec_raw)
    amap = build_articles_map(articles)

    # 把缺口写回（如果路由已经判定）
    if missing_hint:
        mf = set(pred.get("missing_facts", [])); mf.update(missing_hint); pred["missing_facts"] = sorted(mf)
        if pred.get("conclusion") != "Abstain_Insufficient_Info":
            pred["conclusion"] = "Abstain_Insufficient_Info"

    # 判别归一 + 修复写回（核心）
    pred_fixed, repair_issues = repair_decision(pred, cf, amap)

    usage = {"in": in1+in2, "out": out1+out2, "ttl": ttl1+ttl2}
    aux = {"evidence": evidence, "policy": policy, "Repaired": len(repair_issues) > 0, "repair_issues": repair_issues}
    # 在 run_framework 的 return 前增加：
    promote_hit = metric_promote_hit(evidence, pred_fixed.get("forum_type", ""), load_json(RULES))
    aux.update({"trace_cf": links_cf, "promote_hit": promote_hit})

    return pred_fixed, usage, aux

# ---------- 主流程 ----------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["baseline","framework","both"], default="both")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    random.seed(args.seed)

    dataset = load_jsonl(DATA)
    articles = load_json(ARTS)["articles"]
    rules = load_json(RULES)  # <-- 新增：用于 Promote-Hit
    schema_obj = load_json(SCHEMA)
    client = OpenAIClient()

    rows = []
    n = min(args.limit, len(dataset))
    for i in range(n):
        item = dataset[i]
        gold = item["expected_output"]
        facts = item["facts_text"]
        cf = item.get("connecting_factors", {})

        if args.mode in ("baseline", "both"):
            pred_b, usage_b = run_baseline(client, facts)
            # 以 baseline 的 legal_basis 作为“证据集合”估计 promote 期望
            ev_b = [x["provision"] for x in pred_b.get("legal_basis", [])] or pred_b.get("trace", {}).get(
                "evidence_ids", [])
            exp_cat_b = expected_forum_from_evidence(ev_b, rules)
            promote_hit_b = int(exp_cat_b == (pred_b.get("forum_type") or ""))

            rows.append({
                "id": item["id"], "mode": "baseline",
                "Legal-Correct@1": metric_legal_correct(pred_b, gold),
                "Citation-Precision": metric_citation_precision(pred_b, gold),
                "Abstention-Quality": metric_abstention_quality(pred_b, gold),
                "Promote-Hit": promote_hit_b,  # <-- 新增
                "Schema-Pass": 0, "Rule-OK": 0,
                "tokens_in": usage_b["in"], "tokens_out": usage_b["out"], "tokens_total": usage_b["ttl"],
                "pred": pred_b, "gold": gold,
                "trace_cf": cf  # <-- 新增：oracle 元模型
            })

        if args.mode in ("framework", "both"):
            pred_f, usage_f, aux = run_framework(client, facts, cf, schema_obj, articles)

            schema_valid = True
            try:
                from jsonschema import validate
                validate(instance=pred_f, schema=schema_obj)
            except Exception:
                schema_valid = False
            rv = rule_validate(pred_f)

            # 用“证据先选”的 evidence 计算 Promote-Hit（前置 promote 的遵循度）
            ev_f = aux.get("evidence", [])
            exp_cat_f = expected_forum_from_evidence(ev_f, rules)
            promote_hit_f = int(exp_cat_f == (pred_f.get("forum_type") or ""))

            rows.append({
                "id": item["id"], "mode": "framework",
                "Legal-Correct@1": metric_legal_correct(pred_f, gold),
                "Citation-Precision": metric_citation_precision(pred_f, gold),
                "Abstention-Quality": metric_abstention_quality(pred_f, gold),
                "Promote-Hit": promote_hit_f,  # <-- 新增
                "Schema-Pass": metric_schema_pass(schema_valid),
                "Rule-OK": int(rv["ok"]),
                "tokens_in": usage_f["in"], "tokens_out": usage_f["out"], "tokens_total": usage_f["ttl"],
                "pred": pred_f, "gold": gold,
                "evidence": ev_f, "policy": aux.get("policy", ""),
                "Repaired": aux.get("Repaired", False), "repair_issues": aux.get("repair_issues", []),
                "trace_cf": cf  # <-- 新增：oracle 元模型
            })

        time.sleep(0.03)

    def agg(mode: str, key: str) -> float:
        xs = [r[key] for r in rows if r["mode"] == mode]
        return sum(xs) / max(1, len(xs))

    modes = ["baseline","framework"] if args.mode == "both" else [args.mode]
    print("\n=== Overall Metrics ===")
    for m in modes:
        print(f"\n[{m}] on {n} samples")
        print("  Legal-Correct@1    :", round(agg(m, "Legal-Correct@1"), 3))
        print("  Citation-Precision :", round(agg(m, "Citation-Precision"), 3))
        print("  Abstention-Quality :", round(agg(m, "Abstention-Quality"), 3))
        print("  Promote-Hit        :", round(agg(m, "Promote-Hit"), 3))  # ← 只打印一次

        if m == "framework":
            print("  Schema-Pass        :", round(agg(m, "Schema-Pass"), 3))
            print("  Rule-OK            :", round(agg(m, "Rule-OK"), 3))

        print("  Avg Tokens (total) :", round(agg(m, "tokens_total"), 1))

    out_path = ROOT / "pil_results.jsonl"
    ensure_dir(out_path)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nSaved per-sample results to: {out_path}")
    print("Fields: id, mode, metrics..., pred, gold, evidence/policy/Repaired/repair_issues (framework only)")

if __name__ == "__main__":
    main()
