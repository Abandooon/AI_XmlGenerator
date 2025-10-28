import json
import re
import statistics
import pandas as pd


def load_all_events(audit_path):
    """
    读取单个 ndjson 文件，返回一个 list[dict]。
    这个文件里包含多个会话（min/mid/full等），
    但所有内容都在同一个文件中。
    """
    events = []
    with open(audit_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    return events


def group_events_by_request_id(events):
    """
    根据 request_id 把事件分组。
    假设同一个 request_id 对应一次完整生成（一个 promote）。
    返回 dict[str, list[dict]]，key=request_id。
    """
    groups = {}
    for ev in events:
        rid = ev.get("request_id")
        if rid is None:
            # 有些 header 事件可能还没带 request_id，
            # 我们就跳过这种孤立行
            continue
        groups.setdefault(rid, []).append(ev)

    # 让每组事件按出现顺序/时间排序，方便后面分析
    # 优先按 step_number，如果没有则按原顺序保持不变
    for rid, evs in groups.items():
        def sort_key(e):
            if "step_number" in e and e.get("step_number") is not None:
                try:
                    return (0, int(e["step_number"]))
                except Exception:
                    pass
            # fallback: just keep stable order by index
            # (Python sort is stable so we can use enumerate index later if needed)
            return (1, 0)
        groups[rid] = sorted(evs, key=sort_key)

    return groups


def extract_tokens_from_state_id(state_id):
    """
    解析 current_state_id / previous_state_id 里的 "tokens=<num>"
    例如 "terminated=False;tokens=118" -> 118
    """
    if not isinstance(state_id, str):
        return None
    m = re.search(r"tokens=(\d+)", state_id)
    if m:
        return int(m.group(1))
    return None


def get_all_events_with_type(events, etype):
    """过滤所有 event_type == etype 的事件。"""
    return [ev for ev in events if ev.get("event_type") == etype]


def get_first_event_where(events, key, value):
    """
    工具函数：找到第一个满足 ev[key] == value 的事件。
    用来找 start_trail。
    """
    for ev in events:
        if ev.get(key) == value:
            return ev
    return None


def compute_metrics_for_request(events_for_one_request):
    """
    对单个 request_id (一次生成会话) 的审计事件求指标。
    返回字典，可直接进 DataFrame。
    """

    # ---- 基础信息 ----
    # request_id（组的 key 会再传进来，但多拿一遍以防需要）
    request_id = None
    for ev in events_for_one_request:
        if "request_id" in ev:
            request_id = ev["request_id"]
            break

    # 取所有带 event_type 的 runtime 事件
    runtime_events = [ev for ev in events_for_one_request if "event_type" in ev]

    # step_number 列表，用于检查连续性
    step_numbers = []
    for ev in runtime_events:
        if "step_number" in ev and ev["step_number"] is not None:
            try:
                step_numbers.append(int(ev["step_number"]))
            except Exception:
                pass

    # ---- 时间 / 延迟 (ms) ----
    # 我们用 "ts" 字段 (浮点秒)，拿 min/max 做 wall-clock 生成时延
    ts_values = []
    for ev in events_for_one_request:
        if "ts" in ev:
            try:
                ts_values.append(float(ev["ts"]))
            except Exception:
                pass

    if ts_values:
        start_ts = min(ts_values)
        end_ts = max(ts_values)
        latency_ms = (end_ts - start_ts) * 1000.0
    else:
        start_ts = None
        end_ts = None
        latency_ms = None

    # ---- termination / total_tokens ----
    termination_events = get_all_events_with_type(events_for_one_request, "termination")
    if termination_events:
        term_ev = termination_events[-1]
    else:
        term_ev = None

    total_tokens_reported = None
    last_state_tokens = None
    termination_ok = False

    if term_ev is not None:
        # 从 termination.metadata.total_tokens 取 token 数
        meta = term_ev.get("metadata", {})
        if isinstance(meta, dict) and "total_tokens" in meta:
            try:
                total_tokens_reported = int(meta["total_tokens"])
            except Exception:
                total_tokens_reported = None

        # 再从 current_state_id 抓 tokens=...
        current_state_id = term_ev.get("current_state_id")
        last_state_tokens = extract_tokens_from_state_id(current_state_id)

        # 两者一致性
        if (
            total_tokens_reported is not None
            and last_state_tokens is not None
            and total_tokens_reported == last_state_tokens
        ):
            termination_ok = True

    # ---- coverage_ok ----
    # coverage_ok = start_trail 存在 && termination_ok && step_number 连续
    start_trail_ev = get_first_event_where(events_for_one_request, "record_type", "start_trail")

    continuity_ok = False
    if step_numbers:
        # 去重排序后，检查是否没有缺口
        uniq_sorted = sorted(set(step_numbers))
        expected_len = uniq_sorted[-1] - uniq_sorted[0] + 1
        continuity_ok = (expected_len == len(uniq_sorted))

    coverage_ok = (
        start_trail_ev is not None
        and termination_ok
        and continuity_ok
    )

    # ---- allowed_tokens_count 指标 (L1约束力度) ----
    # 从 bitmask_update 事件中获取 allowed_tokens_count
    bitmask_events = get_all_events_with_type(events_for_one_request, "bitmask_update")
    allowed_counts = []
    for ev in bitmask_events:
        if "allowed_tokens_count" in ev:
            try:
                allowed_counts.append(int(ev["allowed_tokens_count"]))
            except Exception:
                pass

    if allowed_counts:
        allowed_tokens_median = statistics.median(allowed_counts)
        allowed_tokens_min = min(allowed_counts)
    else:
        allowed_tokens_median = None
        allowed_tokens_min = None

    # ---- trace_density ----
    # trace_density = 审计事件总数 / 接受的token数
    # “审计事件总数”这里用 runtime_events 的个数
    # 接受的token数用 total_tokens_reported
    if total_tokens_reported and total_tokens_reported > 0:
        trace_density = len(runtime_events) / float(total_tokens_reported)
    else:
        trace_density = None

    # ---- 组装结果 ----
    per_req = {
        "request_id": request_id,
        "latency_ms": latency_ms,
        "total_tokens": total_tokens_reported,
        "trace_density": trace_density,
        "allowed_tokens_median": allowed_tokens_median,
        "allowed_tokens_min": allowed_tokens_min,
        "coverage_ok": coverage_ok,
        "continuity_ok": continuity_ok,
        "termination_ok": termination_ok,
        "num_events": len(runtime_events),
        "start_ts": start_ts,
        "end_ts": end_ts,
    }

    return per_req


def summarize_overall(per_req_list):
    """
    把多次运行（例如 min/mid/full 三个 promote，或更多seed）
    汇总成策略级别的总体指标，用于主表单元格。
    """

    # 转成 DataFrame 方便聚合
    df = pd.DataFrame(per_req_list)

    # Audit trace coverage [%]
    if len(df) > 0:
        coverage_pct = 100.0 * (df["coverage_ok"].sum() / len(df))
    else:
        coverage_pct = None

    # Mean allowed-token set size@L1 [median_over_runs / min_over_runs]
    # 我们对各 run 的 allowed_tokens_median 再求中位数；
    # 对 allowed_tokens_min 取全局最小值。
    allowed_meds = [v for v in df["allowed_tokens_median"].tolist() if v is not None]
    allowed_mins = [v for v in df["allowed_tokens_min"].tolist() if v is not None]

    if allowed_meds:
        allowed_tokens_median_overall = statistics.median(allowed_meds)
    else:
        allowed_tokens_median_overall = None

    if allowed_mins:
        allowed_tokens_min_overall = min(allowed_mins)
    else:
        allowed_tokens_min_overall = None

    # Trace density 平均
    td_vals = [v for v in df["trace_density"].tolist() if v is not None]
    if td_vals:
        trace_density_mean = sum(td_vals) / len(td_vals)
    else:
        trace_density_mean = None

    # Latency 平均
    lat_vals = [v for v in df["latency_ms"].tolist() if v is not None]
    if lat_vals:
        latency_ms_mean = sum(lat_vals) / len(lat_vals)
    else:
        latency_ms_mean = None

    overall = {
        "coverage_pct": coverage_pct,
        "allowed_tokens_median_overall": allowed_tokens_median_overall,
        "allowed_tokens_min_overall": allowed_tokens_min_overall,
        "trace_density_mean": trace_density_mean,
        "latency_ms_mean": latency_ms_mean,
    }

    return df, pd.DataFrame([overall])


# =========================
# 主流程
# =========================
if __name__ == "__main__":
    # 你只需要改这里这个路径
    audit_path = "C:\\Users\\54239\\PycharmProjects\\AI_XmlGenerator\\src\\vllm\\vllm_modify\\data\\audit-logs\\audit.ndjson"

    # 1. 读整份 ndjson
    all_events = load_all_events(audit_path)

    # 2. 按 request_id 分组
    groups = group_events_by_request_id(all_events)

    # 3. 对每个 request_id 求指标
    per_req_list = []
    for rid, evs in groups.items():
        metrics = compute_metrics_for_request(evs)
        # 为了可追踪，也把 run_id（就是 request_id）写进去
        metrics["run_id"] = rid
        per_req_list.append(metrics)

    # 4. 汇总成主表要用的总体指标
    df_runs, df_summary = summarize_overall(per_req_list)

    # 5. 你可以自己决定是否落盘：
    df_runs.to_csv("C:\\Users\\54239\\PycharmProjects\\AI_XmlGenerator\\src\\vllm\\vllm_modify\\data\\per_run_metrics.csv", index=False)
    df_summary.to_csv("C:\\Users\\54239\\PycharmProjects\\AI_XmlGenerator\\src\\vllm\\vllm_modify\\data\\summary_metrics.csv", index=False)

    print("Per-run metrics:")
    print(df_runs)
    print("\nOverall summary (this is what goes in the main table):")
    print(df_summary)
