# SMT约束跳过统计报告
生成时间: D:\PycharmProjects\AI_XmlGenerator\src\constraint_graph

## 总体统计
- 总约束数: 4140
- 成功处理: 3609
- 跳过约束: 531
- 跳过率: 12.83%

## 按跳过原因分类
- Missing target class mapping: 531 个

## 按约束类别分类
- semantic: 531 个

## 按约束类型分类
- behavioral: 206 个
- definition: 33 个
- relationship: 157 个
- value_restriction: 71 个
- other: 4 个
- existence: 30 个
- cardinality: 22 个
- naming_convention: 4 个
- ordering: 4 个

## SMT特定问题诊断

### SMT约束生成的特殊要求：
1. 实体名称必须是有效的SMT标识符
2. 属性名称必须能转换为SMT函数名
3. 类映射关系必须完整，支持SMT类型推理

### 常见SMT约束失败原因：
- 实体类型无法映射到SMT Sort
- 属性名称包含SMT不支持的字符
- 缺少数值类型的约束信息

详细信息请查看: smt_skipped_constraints.json