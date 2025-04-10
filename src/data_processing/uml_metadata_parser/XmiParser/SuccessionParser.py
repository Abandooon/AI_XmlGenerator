# -*- coding: utf-8 -*-
from lxml import etree
import networkx as nx
import matplotlib.pyplot as plt
import os


def build_inheritance_graph(input_path, output_dir):
    # 添加Graphviz路径到系统环境变量（路径根据实际安装位置调整）
    os.environ["PATH"] += os.pathsep + r'D:\Graphviz\bin'
    """构建继承关系图并生成优化布局的可视化"""
    os.makedirs(output_dir, exist_ok=True)
    output_image = os.path.join(output_dir, 'inheritance_graph.png')

    # 解析XML构建图结构
    tree = etree.parse(input_path)
    root = tree.getroot()
    G = nx.DiGraph()

    # 添加节点和边（与之前相同）
    for elem in root.xpath('//Element'):
        current_id = elem.get('xmi_id')
        current_name = elem.get('name')
        is_abstract = elem.get('isAbstract') == 'true'

        if not G.has_node(current_id):
            G.add_node(current_id,
                       name=current_name,
                       abstract=is_abstract,
                       label=f"{current_name}\n({current_id[:8]})")

        for gen in elem.xpath('./Generalization'):
            parent_id = gen.get('fatherXmiId')
            parent_name = gen.get('fatherName')
            parent_abstract = gen.get('fatherIsAbstract') == 'true'

            if not G.has_node(parent_id):
                G.add_node(parent_id,
                           name=parent_name,
                           abstract=parent_abstract,
                           label=f"{parent_name}\n({parent_id[:8]})")

            G.add_edge(current_id, parent_id)

    # 布局优化配置
    plt.figure(figsize=(30, 20))  # 增大画布尺寸

    # ========== 布局选择 ==========
    # 方案1：弹簧布局（适合复杂网络）
    pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)

    # 方案2：Kamada-Kawai布局（适合中等规模图）
    # pos = nx.kamada_kawai_layout(G)

    # 方案3：层次化布局（需要graphviz）
    # pos = nx.nx_agraph.graphviz_layout(G, prog='dot', args='-Grankdir=BT -Gnodesep=1.0 -Granksep=2.0')

    # ========== 可视化优化 ==========
    # 节点样式
    node_colors = ['#ff9999' if G.nodes[n]['abstract'] else '#99ccff' for n in G.nodes]
    node_sizes = [1200 if G.nodes[n]['abstract'] else 800 for n in G.nodes]

    # 绘制节点
    nx.draw_networkx_nodes(G, pos,
                           node_size=node_sizes,
                           node_color=node_colors,
                           alpha=0.9,
                           linewidths=1.5,
                           edgecolors='#333333')

    # 绘制边
    nx.draw_networkx_edges(G, pos,
                           arrowstyle='-|>',
                           arrowsize=25,
                           width=1.2,
                           edge_color='#666666',
                           connectionstyle='arc3,rad=0.1')  # 添加弧度避免重叠

    # 标签优化
    labels = nx.get_node_attributes(G, 'label')
    text = nx.draw_networkx_labels(G, pos,
                                   labels=labels,
                                   font_size=9,
                                   font_family='Microsoft YaHei',
                                   bbox=dict(facecolor='white',
                                             edgecolor='none',
                                             alpha=0.8))

    # 防止标签重叠
    for _, t in text.items():
        t.set_rotation(30)  # 标签旋转30度

    # 保存图像
    plt.savefig(output_image, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"优化布局图已生成：{output_image}")


if __name__ == "__main__":
    input_path = "input/generalizations.xml"
    output_dir = "output"
    build_inheritance_graph(input_path, output_dir)