# 论文位置索引

由本次 LaTeX 编译生成；正文、附录与参考文献共 36 页。标签保持不变，以下页码对应当前 PDF。

[阅读稿](main.pdf) · [源文件](main.tex)

| 标题 | 稳定标签 | 编号 | PDF 页码 |
| --- | --- | --- | --- |
| 引言 | `sec:introduction` | 1 | [第 1 页](main.pdf#page=1) |
| 相关工作 | `sec:related` | 2 | [第 3 页](main.pdf#page=3) |
| 模型转换与一致模型生成 | `sec:related-2-1` | 2.1 | [第 3 页](main.pdf#page=3) |
| 大模型辅助建模与模型实例构造 | `sec:related-2-2` | 2.2 | [第 4 页](main.pdf#page=4) |
| 结构化约束获取与可追溯性 | `sec:related-2-3` | 2.3 | [第 5 页](main.pdf#page=5) |
| 受约束解码与验证反馈修复 | `sec:related-2-4` | 2.4 | [第 5 页](main.pdf#page=5) |
| 元模型引导的分层约束生成方法 | `sec:method` | 3 | [第 6 页](main.pdf#page=6) |
| 适用范围与方法概述 | `sec:method-3-1` | 3.1 | [第 6 页](main.pdf#page=6) |
| 领域准备与单次任务执行。ICM、生成映射和验证器在领域准备阶段形成，供不同任务复用；任务绑定确定本次生成、检索和检查的内容。L1 限制生成过程，L2 检查构造后的结果并驱动修复，任务验收依据原始需求确定 | `fig:1` | 1 | [第 7 页](main.pdf#page=7) |
| 提取与转换元模型信息 | `sec:method-3-2` | 3.2 | [第 8 页](main.pdf#page=8) |
| 元模型引导的约束抽取与 ICM 构建 | `sec:method-3-3` | 3.3 | [第 8 页](main.pdf#page=8) |
| 元模型引导的约束抽取与 ICM 构建 | `eq:icm` | 1 | [第 8 页](main.pdf#page=8) |
| 从已有领域元模型及自然语言规范构建 ICM。元模型表示提供抽取术语、自动链接依据及结构信息；链接异常交由人工处理，ICM 保存约束内容、元素关联、来源和后续用途 | `fig:2` | 2 | [第 9 页](main.pdf#page=9) |
| ICM 约束记录的主要信息 | `tab:1` | 1 | [第 9 页](main.pdf#page=9) |
| ICM 约束的三类用途 | `tab:2` | 2 | [第 9 页](main.pdf#page=9) |
| ICM 的信息与关联。元模型表示 M 提供领域元素及关系，约束记录 C 表达规则内容，关联 A 连接约束与其作用元素，来源信息 P 支持回查。下方三类用途共用这些信息，不构成额外的元模型层次 | `fig:3` | 3 | [第 10 页](main.pdf#page=10) |
| 绑定本次任务的对象与要求 | `sec:method-3-4` | 3.4 | [第 10 页](main.pdf#page=10) |
| 动态组装生成约束 | `alg:assembly` | 1 | [第 11 页](main.pdf#page=11) |
| 组装生成约束与受约束解码 | `sec:method-3-5` | 3.5 | [第 11 页](main.pdf#page=11) |
| 动态组装生成约束 | `sec:method-3-5-1` | 3.5.1 | [第 11 页](main.pdf#page=11) |
| 受约束解码如何参与实例模型生成 | `sec:method-3-5-2` | 3.5.2 | [第 11 页](main.pdf#page=11) |
| 从生成结果到模型与序列化制品 | `sec:method-3-5-3` | 3.5.3 | [第 12 页](main.pdf#page=12) |
| 生成后验证与任务验收 | `sec:method-3-6` | 3.6 | [第 12 页](main.pdf#page=12) |
| 任务绑定与 L1 执行。（a）结合任务需求、ICM 和已有模型上下文组装生成约束、检索内容及检查配置；（b）展示语法编译、允许词元筛选和状态更新。完整输出经结构验证与模型装配后进入 L2 | `fig:4` | 4 | [第 13 页](main.pdf#page=13) |
| 依据验证反馈修复模型 | `sec:method-3-7` | 3.7 | [第 14 页](main.pdf#page=14) |
| 领域适配与可追溯性 | `sec:method-3-8` | 3.8 | [第 14 页](main.pdf#page=14) |
| 实验评价 | `sec:evaluation` | 4 | [第 14 页](main.pdf#page=14) |
| 研究问题与评价设置 | `sec:eval-4-1` | 4.1 | [第 14 页](main.pdf#page=14) |
| L2 驱动的修复与复验。失败诊断用于定位修改对象，允许操作限制修复范围；修改后重建并复验，原任务要求贯穿接纳过程。自动处理结束后仍未解决的问题交由人工处理 | `fig:5` | 5 | [第 15 页](main.pdf#page=15) |
| 领域适配接口 | `tab:3` | 3 | [第 15 页](main.pdf#page=15) |
| AUTOSAR：约束组织与工程模型生成 | `sec:eval-4-2` | 4.2 | [第 16 页](main.pdf#page=16) |
| 需求来源与生成流程 | `sec:eval-4-2-1` | 4.2.1 | [第 16 页](main.pdf#page=16) |
| 从 ICM 到一次检查 | `sec:eval-4-2-2` | 4.2.2 | [第 16 页](main.pdf#page=16) |
| 实验设计及规模 | `tab:4` | 4 | [第 17 页](main.pdf#page=17) |
| 周期 Runnable 约束从规范来源到模型对象及检查结果的关联。R 表示 RE\_Com\_Full\_Baseline，E 表示 TE\_Com\_Full\_Baseline；任务要求的 10 ms 在制品中表示为 0.01 s | `fig:6` | 6 | [第 17 页](main.pdf#page=17) |
| 生成结果与运行代价 | `sec:eval-4-2-3` | 4.2.3 | [第 17 页](main.pdf#page=17) |
| AUTOSAR 完整生成流程的结果 | `tab:5` | 5 | [第 18 页](main.pdf#page=18) |
| AUTOSAR-vLLM：生成约束对解码的实际干预 | `sec:eval-4-3` | 4.3 | [第 18 页](main.pdf#page=18) |
| 铁路：生成后验证与受限修复 | `sec:eval-4-4` | 4.4 | [第 18 页](main.pdf#page=18) |
| 任务、验证器与比较条件 | `sec:eval-4-4-1` | 4.4.1 | [第 18 页](main.pdf#page=18) |
| AUTOSAR-vLLM 的过程与结果。（a）每个案例三次审计生成中的干预位置，短线表示无约束最高分词元被语法限制排除。（b）同一案例在提示约束与受约束解码下通过结构验收的次数 | `fig:7` | 7 | [第 19 页](main.pdf#page=19) |
| 主要结果与失败解释 | `sec:eval-4-4-2` | 4.4.2 | [第 19 页](main.pdf#page=19) |
| 铁路模型结果。（a）72 个初始生成起点上的两种修复。（b）144 个受控损坏输入上的自修复、验证反馈与增加局部定位的修复。（c）同一 24 个任务及固定种子上的 Luna 与 Terra 比较 | `fig:8` | 8 | [第 20 页](main.pdf#page=20) |
| 第二模型补充 | `sec:eval-4-4-3` | 4.4.3 | [第 20 页](main.pdf#page=20) |
| 国际私法：结构化法律决策中的分层检查 | `sec:eval-4-5` | 4.5 | [第 20 页](main.pdf#page=20) |
| 有效性讨论 | `sec:eval-4-6` | 4.6 | [第 21 页](main.pdf#page=21) |
| 结论 | `sec:conclusion` | 5 | [第 21 页](main.pdf#page=21) |
| PIL 主要结果 | `tab:6` | 6 | [第 22 页](main.pdf#page=22) |
| 数据与代码可用性 | `sec:data-availability` | 5 | [第 23 页](main.pdf#page=23) |
| AUTOSAR 工程生成与修复 | `app:A` | A | [第 23 页](main.pdf#page=23) |
| 需求设计与生成设置 | `app:A-1` | A.1 | [第 23 页](main.pdf#page=23) |
| 规范约束抽取、ICM 与验证器 | `app:A-2` | A.2 | [第 23 页](main.pdf#page=23) |
| AUTOSAR 需求设计及来源 | `tab:A1` | A1 | [第 24 页](main.pdf#page=24) |
| AUTOSAR 规范约束抽取与链接规格 | `tab:A2` | A2 | [第 24 页](main.pdf#page=24) |
| 核心故障与替代故障 | `app:A-3` | A.3 | [第 25 页](main.pdf#page=25) |
| 贯穿案例 周期组件的构造与事件引用恢复 | `app:A-4` | A.4 | [第 25 页](main.pdf#page=25) |
| 核心故障修复结果 | `tab:A3` | A3 | [第 26 页](main.pdf#page=26) |
| 运行前声明的替代操作 | `tab:A4` | A4 | [第 26 页](main.pdf#page=26) |
| AUTOSAR-vLLM 解码干预 | `app:B` | B | [第 26 页](main.pdf#page=26) |
| 比较条件与执行设置 | `app:B-1` | B.1 | [第 26 页](main.pdf#page=26) |
| 分层结果与运行代价 | `app:B-2` | B.2 | [第 26 页](main.pdf#page=26) |
| 各案例层次的结构验收结果 | `tab:B1` | B1 | [第 27 页](main.pdf#page=27) |
| 词元与请求时间 | `tab:B2` | B2 | [第 27 页](main.pdf#page=27) |
| 铁路模型生成与修复 | `app:C` | C | [第 27 页](main.pdf#page=27) |
| 模型来源与检查 | `app:C-1` | C.1 | [第 27 页](main.pdf#page=27) |
| 条件与补充集合 | `app:C-2` | C.2 | [第 27 页](main.pdf#page=27) |
| 六条原生查询 | `tab:C1` | C1 | [第 28 页](main.pdf#page=28) |
| 实验集合与严格成功 | `tab:C2` | C2 | [第 28 页](main.pdf#page=28) |
| 第二模型及运行代价 | `app:C-3` | C.3 | [第 28 页](main.pdf#page=28) |
| 铁路主实验的成功率差及区间 | `tab:C3` | C3 | [第 29 页](main.pdf#page=29) |
| 两模型的同任务结果 | `tab:C4` | C4 | [第 29 页](main.pdf#page=29) |
| 贯穿案例 两条服务路径的关系修复 | `app:C-4` | C.4 | [第 29 页](main.pdf#page=29) |
| 国际私法决策 | `app:D` | D | [第 30 页](main.pdf#page=30) |
| 案例与比较条件 | `app:D-1` | D.1 | [第 30 页](main.pdf#page=30) |
| 审计与结果 | `app:D-2` | D.2 | [第 30 页](main.pdf#page=30) |
| 生成条件 | `tab:D1` | D1 | [第 31 页](main.pdf#page=31) |
| 四组结果 每组 180 个结果 | `tab:D2` | D2 | [第 31 页](main.pdf#page=31) |
| 贯穿案例 选法院协议的类型修订 | `app:D-3` | D.3 | [第 31 页](main.pdf#page=31) |
| PIL 主要复合终点的成功率差及区间 | `tab:D3` | D3 | [第 32 页](main.pdf#page=32) |
| 定向专家复核 | `app:D-4` | D.4 | [第 32 页](main.pdf#page=32) |
