# SHACL约束跳过统计报告
生成时间: D:\PycharmProjects\AI_XmlGenerator\src\constraint_graph

## 总体统计
- 总约束数: 4236
- 成功处理: 3705
- 跳过约束: 531
- 跳过率: 12.54%

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

## 问题诊断建议

### 如果跳过率较高 (>20%)：
1. 检查 roots.json 配置，确保包含所有必要的根类
2. 验证 KG 数据完整性，确保类映射关系正确
3. 检查 token_extractor 的类发现算法是否遗漏某些分支

### 常见的缺失类型：
- PORT-PROTOTYPE 相关类 (端口定义)
- INTERFACE 相关类 (接口定义)
- DATA-TYPE 相关类 (数据类型)
- SYSTEM 相关类 (系统级元素)

### 建议的 roots.json 扩展：
```json
{
  "roots": [
    "APPLICATION-SW-COMPONENT-TYPE",
    "ADAPTIVE-APPLICATION-SW-COMPONENT-TYPE",
    "PORT-PROTOTYPE",
    "SENDER-RECEIVER-INTERFACE",
    "CLIENT-SERVER-INTERFACE",
    "APPLICATION-DATA-TYPE",
    "SYSTEM",
    "ECU-INSTANCE"
  ]
}
```

详细信息请查看: shacl_skipped_constraints.json