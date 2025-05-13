import os
from dotenv import load_dotenv

load_dotenv() # 从 .env 文件加载环境变量

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1") # 默认为官方地址
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "deepseek-chat") # 或者 deepseek-coder 等，根据你使用的模型调整

# LLM 的 Schema (如 design_docV4.md 中所定义)
# schema_v4.json 的内容，作为Python字典
CONSTRAINT_SCHEMA = {
  "type": "object",
  "properties": {
    "id": { "type": "string", "description": "完整的规范/约束ID，如 TPS_SWCT_01032 或 constr_XYZ_001" },
    "id_type": { "type": "string", "enum": ["TPS_SWCT", "constr"], "description": "ID的类型" },
    "title": { "type": "string", "description": "规范/约束的标题文本" },
    "targetClass": { "type": ["string", "null"], "description": "约束目标AUTOSAR类名 (如果目标是类)" },
    "targetEnum": { "type": ["string", "null"], "description": "约束目标AUTOSAR枚举名 (如果目标是枚举)" },
    "targetAttribute": { "type": "string", "description": "约束目标的具体属性/字面量名，或特殊值 '_classLevel', '_enumLevel'" },
    # targetRef 会在 linker_validator 中生成，LLM 不需要直接生成
    "expression": { "type": "string", "description": "约束的详细文本描述 (cid:100) 和 (cid:99) 之间的内容" },
    "references": {
      "type": "array",
      "items": { "type": "string" },
      "description": "约束末尾括号中引用的其他ID列表"
    },
    "constraint_type": { "type": "string", "description": "约束的语义类型 (如 cardinality, value_restriction, definition, etc.)" },
    "value": { "type": ["string", "number", "boolean", "null"], "description": "约束的具体值" },
    "scope_section": { "type": ["string", "null"], "description": "从 #@SECTION 提取的章节信息" },
    "parent_id": { "type": ["string", "null"], "description": "如果通过 #@Hierarchical 标注识别，则为父约束的ID" },
    "rawSourceText": { "type": "string", "description": "LLM处理的原始约束文本块"},
    # confidence 会由LLM输出或后续评估
  },
  "required": ["id", "id_type", "title", "expression"] # LLM 必须保证的核心必填字段
}

# 文件名常量
UNIFIED_METADATA_FILENAME = "unified_metadata.json"
OUTPUT_LINKED_CONSTRAINTS_FILENAME = "constraints_linked_v4.json"
OUTPUT_REVIEW_QUEUE_FILENAME = "review_queue_v4.csv"

# 正则表达式
# 示例: [TPS_SWCT_01032] CompositionSwComponentType (cid:100) ... (cid:99)(RS_SWCT_00190)
# 更稳健的正则，允许标题中包含各种字符，并正确捕获括号内的引用
CONSTRAINT_PATTERN = r"\[((?:TPS_SWCT|constr)_[A-Za-z0-9_]+?)\]\s*(.*?)\s*\(cid:100\)(.*?)\(cid:99\)\s*\((.*?)\)"
# 用于解析 #@CLASS: ClassName, #@ENUM: EnumName, #@SECTION: Section Name
CLASS_ANNOTATION_PATTERN = r"#@CLASS:\s*(\S+)"
ENUM_ANNOTATION_PATTERN = r"#@ENUM:\s*(\S+)"
SECTION_ANNOTATION_PATTERN = r"#@SECTION:\s*(.*)"
HIERARCHICAL_ANNOTATION_PATTERN = r"#@Hierarchical"

# 特殊属性值
CLASS_LEVEL_ATTR = "_classLevel" # 代表类级别约束的特殊属性名
ENUM_LEVEL_ATTR = "_enumLevel"   # 代表枚举级别约束的特殊属性名