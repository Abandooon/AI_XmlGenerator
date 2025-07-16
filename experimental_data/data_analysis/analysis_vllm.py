# analysis_vllm_two_strategies.py
import json
from datetime import datetime
import numpy as np
import pandas as pd


# ---------- 1. 公共函数 ---------- #
def load_vllm_json(path: str) -> dict:
    """加载单个 vLLM 统计 JSON"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def classify_group(prompt_idx: int) -> str:
    """根据 prompt 序号划分组别"""
    if 1 <= prompt_idx <= 7:
        return 'full_promote'
    if 8 <= prompt_idx <= 14:
        return 'mid_promote'
    if 15 <= prompt_idx <= 20:
        return 'min_promote'
    return 'unknown'


def json_to_df(jdata: dict, method_name: str) -> pd.DataFrame:
    """把一个 vLLM JSON 转成扁平 DataFrame，并打上 Method 列"""
    rows = []
    ts = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    for p in jdata['prompts_details']:
        group = classify_group(p['prompt_index'])

        for sd in p['seed_details']:
            rows.append(
                {
                    'timestamp': ts,
                    'Method': method_name,
                    'Group': group,
                    'idx': p['prompt_index'],
                    'seed': sd['seed'],
                    'status': 'success' if sd['success'] else 'fail',
                    'elapsed_s': sd['generation_time'],        # 单次生成耗时
                    'input_tokens': sd['token_usage']['prompt_tokens'],
                    'output_tokens': sd['token_usage']['completion_tokens'],
                    'total_tokens': sd['token_usage']['total_tokens'],
                    'chars': sd['xml_length'],
                    'memory_delta': sd['memory_usage']['delta'],
                }
            )
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    """生成指定格式的汇总表"""
    out_rows = []

    for grp in sorted(df['Group'].unique()) + ['Overall']:
        g = df if grp == 'Overall' else df[df['Group'] == grp]
        if g.empty:
            continue
        out_rows.append(
            {
                'Method': g['Method'].iloc[0],
                'Group': grp,
                'Samples': len(g),
                'Pass Rate (%)': 100 * (g['status'] == 'success').mean(),
                'Avg Latency (s)': g['elapsed_s'].mean(),
                'Std Latency': g['elapsed_s'].std(ddof=0),
                'Avg Input Tokens': g['input_tokens'].mean(),
                'Avg Output Tokens': g['output_tokens'].mean(),
                'Avg Total Tokens': g['total_tokens'].mean(),
                'Avg Chars': g['chars'].mean(),
                'Memory Delta (MB)': g['memory_delta'].mean(),
                'Avg Generation Time (s)': g['elapsed_s'].mean(),  # 与 elapsed_s 等价
            }
        )
    return pd.DataFrame(out_rows).round(2)


# ---------- 2. 主流程 ---------- #
def main():
    # 路径可按需改成命令行参数
    FILE_GBNF = 'generation_stats_yaml_files_vllm_gbnf.json'
    FILE_RAG  = 'generation_stats_yaml_files_vllm_gbnf+rag.json'

    df_gbnf = json_to_df(load_vllm_json(FILE_GBNF), 'vLLM GBNF')
    df_rag  = json_to_df(load_vllm_json(FILE_RAG),  'vLLM GBNF+RAG')

    summary_gbnf = summarize(df_gbnf)
    summary_rag  = summarize(df_rag)

    # 合并展示
    summary_all = pd.concat([summary_gbnf, summary_rag], ignore_index=True)
    print('\n====== vLLM 两种策略汇总指标 ======')
    print(summary_all.to_string(index=False))

    # 保存明细 & 汇总 CSV
    df_gbnf.to_csv('detail_vllm_gbnf.csv', index=False)
    df_rag.to_csv('detail_vllm_gbnf+rag.csv', index=False)
    summary_all.to_csv('summary_vllm_two_strategies.csv', index=False)
    print('\n已生成 CSV：detail_* 与 summary_vllm_two_strategies.csv')


if __name__ == '__main__':
    main()
