## 图内术语及正文翻译对应

|中文|英文|说明|
|---|---|---|
|解码中的干预|Decoding interventions|短线表示无约束最高分词元被生成约束排除的步骤。|
|生成进度，按输出步数归一化|Decoding progress (% of output steps)|位置为 100 × (原始零基步骤编号 + 1) / 总步数。|
|结构验收|Structural acceptance|对应该实验的结构验收终点，不称为完整正确率。|
|仅在提示中提供约束|Prompt only|图中对应 U。|
|受约束解码|Constrained decoding|图中对应 G，与已有正文术语一致。|
|严格成功率|Strict success rate (%)|对应铁路实验的严格成功终点。|
|生成与修复|Generation and repair|图 8(a) 的初始生成及两种修复条件。|
|注入故障的修复|Repair of injected faults|图 8(b) 的受控损坏输入与修复。|
|大语言模型对比|LLM comparison|图 8(c)，避免与候选模型混淆。|
|自修复／验证反馈修复|self-repair / repair with validation feedback|正文翻译沿用已确认术语；图中条件缩写保持 G0/GS/GF、S/V/F。|

Luna、Terra、AUTOSAR 案例编号和各实验条件的标识保持原样。中文图注中的“每案例三次运行”保留，图中合并显示不改变样本量。
