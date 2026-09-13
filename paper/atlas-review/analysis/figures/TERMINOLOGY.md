# Plot terminology

| 中文 | English | Meaning in these experiments |
| --- | --- | --- |
| 解码中的干预 | Decoding interventions | A short mark identifies a step at which the unconstrained top-ranked token was disallowed by the generation constraints. |
| 生成进度，按输出步数归一化 | Decoding progress (% of output steps) | Position is 100 × (zero-based source step + 1) / total steps. |
| 结构验收 | Structural acceptance | The local AUTOSAR-vLLM structural endpoint; it is not a complete correctness rate. |
| 仅在提示中提供约束 | Prompt only | Condition U in the local decoding experiment. |
| 受约束解码 | Constrained decoding | Condition G in the local decoding experiment. |
| 严格成功率 | Strict success rate (%) | The railway experiment's strict success endpoint. |
| 生成与修复 | Generation and repair | Initial generation and its two repair conditions in railway panel (a). |
| 注入故障的修复 | Repair of injected faults | Controlled-damage inputs and their repairs in railway panel (b). |
| 大语言模型对比 | LLM comparison | The two language-model configurations in railway panel (c), distinct from the candidate domain models being generated. |
| 自修复／验证反馈修复 | self-repair / repair with validation feedback | The repair conditions; identifiers G0/GS/GF and S/V/F retain their experiment-specific definitions. |

Luna, Terra, AUTOSAR case IDs and condition identifiers are preserved. In the local decoding plot, one row merges three traces only when their recorded positions and counts match. This display choice does not change the number of runs or the structural-acceptance denominator.
