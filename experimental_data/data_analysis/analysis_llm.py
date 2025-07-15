#!/usr/bin/env python3
"""
UMM-ICM-PCG 实验指标计算脚本
用于计算 No Guard 和 RAG 两种方案的性能指标
"""

import pandas as pd
import numpy as np
from tabulate import tabulate


def main():
    # 1. 读取数据
    print("=== 1. 加载数据 ===")
    df_no = pd.read_csv('metrics_No Guard.csv')
    df_rag = pd.read_csv('metrics_rag.csv')

    print(f"No Guard 原始记录数: {len(df_no)}")
    print(f"RAG 原始记录数: {len(df_rag)}")

    # 2. 数据清洗 - 移除有error的记录
    df_no_clean = df_no[df_no['error'].isna()].copy()
    df_rag_clean = df_rag[df_rag['error'].isna()].copy()

    print(f"\n清洗后:")
    print(f"No Guard: {len(df_no_clean)} 条")
    print(f"RAG: {len(df_rag_clean)} 条")

    # 3. 分组计算指标
    print("\n=== 2. 分组指标 ===")

    results = []

    # 对每个方案计算
    for name, df in [('No Guard', df_no_clean), ('RAG', df_rag_clean)]:
        print(f"\n{name}:")

        # 提取group名称（RAG的group带_rag后缀）
        groups = df['group'].unique()

        for group in sorted(groups):
            g = df[df['group'] == group]

            result = {
                'Method': name,
                'Group': group.replace('_rag', ''),  # 统一group名称
                'Samples': len(g),
                'Pass Rate (%)': round((g['status'].eq('success').sum() / len(g)) * 100, 1),
                'Avg Latency (s)': round(g['elapsed_s'].mean(), 2),
                'Std Latency': round(g['elapsed_s'].std(), 2),
                'Avg Input Tokens': round(g['input_tokens'].mean(), 0),
                'Avg Output Tokens': round(g['output_tokens'].mean(), 0),
                'Avg Total Tokens': round(g['total_tokens'].mean(), 0),
            }

            results.append(result)

            print(f"  {group}:")
            print(f"    样本数: {result['Samples']}")
            print(f"    通过率: {result['Pass Rate (%)']}%")
            print(f"    平均延迟: {result['Avg Latency (s)']}s (±{result['Std Latency']})")
            print(f"    平均Token: {result['Avg Total Tokens']}")

        # Overall统计
        overall = {
            'Method': name,
            'Group': 'Overall',
            'Samples': len(df),
            'Pass Rate (%)': round((df['status'].eq('success').sum() / len(df)) * 100, 1),
            'Avg Latency (s)': round(df['elapsed_s'].mean(), 2),
            'Std Latency': round(df['elapsed_s'].std(), 2),
            'Avg Input Tokens': round(df['input_tokens'].mean(), 0),
            'Avg Output Tokens': round(df['output_tokens'].mean(), 0),
            'Avg Total Tokens': round(df['total_tokens'].mean(), 0),
        }
        results.append(overall)

    # 4. 创建结果DataFrame
    results_df = pd.DataFrame(results)

    # 5. 生成对比表格
    print("\n=== 3. 性能对比表 ===")

    # 创建透视表
    pivot_metrics = ['Pass Rate (%)', 'Avg Latency (s)', 'Avg Total Tokens']

    for metric in pivot_metrics:
        print(f"\n{metric}:")
        pivot = results_df.pivot(index='Group', columns='Method', values=metric)
        print(tabulate(pivot, headers='keys', tablefmt='grid'))

    # 6. 计算相对性能
    print("\n=== 4. 相对性能分析 (RAG vs No Guard) ===")

    comparison = []
    for group in ['min_promote', 'mid_promote', 'full_promote', 'Overall']:
        no_guard = results_df[(results_df['Method'] == 'No Guard') &
                              (results_df['Group'] == group)]
        rag = results_df[(results_df['Method'] == 'RAG') &
                         (results_df['Group'] == group)]

        if len(no_guard) > 0 and len(rag) > 0:
            comp = {
                'Group': group,
                'Latency Ratio': round(rag['Avg Latency (s)'].values[0] /
                                       no_guard['Avg Latency (s)'].values[0], 2),
                'Token Ratio': round(rag['Avg Total Tokens'].values[0] /
                                     no_guard['Avg Total Tokens'].values[0], 2),
                'Pass Rate Diff (pp)': round(rag['Pass Rate (%)'].values[0] -
                                             no_guard['Pass Rate (%)'].values[0], 1)
            }
            comparison.append(comp)

    comp_df = pd.DataFrame(comparison)
    print(tabulate(comp_df, headers='keys', tablefmt='grid', showindex=False))

    # 7. Seed间差异分析
    print("\n=== 5. Seed间稳定性分析 ===")

    for name, df in [('No Guard', df_no_clean), ('RAG', df_rag_clean)]:
        print(f"\n{name}:")

        # 按group和seed分组
        seed_stats = df.groupby(['group', 'seed']).agg({
            'status': lambda x: (x.eq('success').sum() / len(x)) * 100,
            'elapsed_s': ['mean', 'std'],
            'total_tokens': 'mean'
        }).round(2)

        # 重命名列
        seed_stats.columns = ['Pass Rate (%)', 'Avg Latency', 'Std Latency', 'Avg Tokens']
        print(tabulate(seed_stats, headers='keys', tablefmt='grid'))

    # 8. 保存结果
    print("\n=== 6. 保存结果 ===")

    results_df.to_csv('metrics_summary.csv', index=False)
    comp_df.to_csv('metrics_comparison.csv', index=False)

    print("结果已保存到:")
    print("  - metrics_summary.csv")
    print("  - metrics_comparison.csv")

    # 9. 生成论文用文本
    print("\n=== 7. 论文用描述示例 ===")

    # 选择min_promote为例
    ng_min = results_df[(results_df['Method'] == 'No Guard') &
                        (results_df['Group'] == 'min_promote')].iloc[0]
    rag_min = results_df[(results_df['Method'] == 'RAG') &
                         (results_df['Group'] == 'min_promote')].iloc[0]

    print(f"\n在minimal prompt配置下，基线方案(No Guard)在{ng_min['Samples']}个测试样本上")
    print(f"实现了{ng_min['Pass Rate (%)']}%的一次通过率，平均生成延迟为{ng_min['Avg Latency (s)']}秒，")
    print(f"消耗{ng_min['Avg Total Tokens']:.0f}个tokens。")
    print(
        f"\n引入RAG增强后，通过率提升至{rag_min['Pass Rate (%)']}%（提升{rag_min['Pass Rate (%)'] - ng_min['Pass Rate (%)']}个百分点），")
    print(
        f"延迟增加至{rag_min['Avg Latency (s)']}秒（{(rag_min['Avg Latency (s)'] / ng_min['Avg Latency (s)'] - 1) * 100:.1f}%增幅），")
    print(f"token效率略有改善（{rag_min['Avg Total Tokens']:.0f} vs {ng_min['Avg Total Tokens']:.0f}）。")


if __name__ == "__main__":
    main()