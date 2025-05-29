import os
from dotenv import load_dotenv

load_dotenv() # 从 .env 文件加载环境变量

# LLM API 配置
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_API_BASE = os.getenv("LLM_API_BASE")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME")


# LLM 上下文窗口和 Token 相关常量
MAX_CONTEXT_TOKENS = int(os.getenv("MAX_CONTEXT_TOKENS"))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS"))
TOKEN_BUFFER = int(os.getenv("TOKEN_BUFFER"))  # 保留的Token数量，避免超出限制
# 新增：为LLM输入内容设定的安全Token上限，以间接控制输出Token
# 这个值需要根据实际测试调整，3k输入对应8k输出是一个1:2.67的比例
# 假设 prompt 指令本身消耗一部分，我们为内容区设定一个值
SAFE_INPUT_CONTENT_MAX_TOKENS = int(os.getenv("SAFE_INPUT_CONTENT_MAX_TOKENS"))  # 1.5万Token


# 添加路径配置参数
INPUT_DIR = "input"
MD_FILENAME = "chapter2.md"
OUTPUT_DIR = "output"

# 文件名常量 (可以考虑版本号v5)
UNIFIED_METADATA_FILENAME = "unified_metadata.json"
OUTPUT_LINKED_CONSTRAINTS_FILENAME = "constraints_linked_v5.json"
OUTPUT_REVIEW_QUEUE_FILENAME = "review_queue_v5.csv"
OUTPUT_RAW_LLM_FILENAME = "constraints_raw_v5.jsonl" # 明确文件名

# LLM 的 Schema (V5 - 支持多目标)
CONSTRAINT_SCHEMA = {
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "完整的规范/约束ID，例如 TPS_SWCT_01032 或 constr_XYZ_001"
    },
    "id_type": {
      "type": "string",
      "enum": ["TPS_SWCT", "constr", "example"],
      "description": "ID的类型"
    },
    "title": {
      "type": "string",
      "description": "规范/约束的标题文本"
    },
    "targets": {
      "type": "array",
      "description": "约束所应用的目标实体列表",
      "items": {
        "type": "object",
        "properties": {
          "targetEntityName": {
            "type": "string",
            "description": "目标AUTOSAR类名或枚举名"
          },
          "entityType": {
            "type": "string",
            "enum": ["class", "enum"],
            "description": "目标实体的类型 ('class' 或 'enum')"
          },
          "targetAttributes": {
            "type": "array",
            "items": { "type": "string" },
            "description": "约束目标的具体属性/字面量名列表。如果针对整个类/枚举本身，则为 [\"_classLevel\"] (对于类) 或 [\"_enumLevel\"] (对于枚举)"
          }
        },
        "required": ["targetEntityName", "entityType", "targetAttributes"]
      }
    },
    "expression": {
      "type": "string",
      "description": "约束的详细文本描述，通常是 (cid:100) 和 (cid:99) 之间的内容，或约束的主体文本"
    },
    "references": {
      "type": "array",
      "items": { "type": "string" },
      "description": "约束末尾括号中引用的其他ID列表或约束表述中明确需要引用的表格id (如果存在)"
    },
    "constraint_type": {
      "type": "string",
      "enum": [
        "definition",
        "cardinality",
        "value_restriction",
        "format",
        "existence",
        "behavioral",
        "relationship",
        "ordering",
        "naming_convention",
        "xml_instantiation_example",
        "other"
      ],
      "description": "约束的语义类型。如果是XML示例，请使用 'xml_instantiation_example'"
    },
    "value": {
      "type": ["string", "number", "boolean", "null"],
      "description": "约束的具体值 (如果适用，例如基数的值、特定的限制值等)"
    },
    "scope_path": {
      "type": "array",
      "items": { "type": "string" },
      "description": "表示约束所属章节层级路径的字符串列表，从顶层章节到当前章节，例如 [\"Chapter 1\", \"Section 1.1\", \"Subsection 1.1.1\"]"
    },
    "xml_example_content": {
      "type": ["string", "null"],
      "description": "如果 constraint_type 是 'xml_instantiation_example'，则此字段包含提取的XML代码片段；否则为null。"
    }
  },
  "required": ["id", "id_type", "title", "expression", "targets", "constraint_type", "scope_path"]
}

# 正则表达式
CONSTRAINT_PATTERN = r"\[((?:TPS_SWCT|constr)_[A-Za-z0-9_]+?)\]\s*(.*?)\s*\(cid:100\)(.*?)\(cid:99\)\s*\((.*?)\)"
CLASS_ANNOTATION_PATTERN = r"#@CLASS:\s*(\S+)"
ENUM_ANNOTATION_PATTERN = r"#@ENUM:\s*(\S+)"
SECTION_ANNOTATION_PATTERN = r"#@SECTION:\s*(.*)"
SECTION_SPLIT_PATTERN = r"(^#@SECTION:.*?$)"

# 特殊属性值
CLASS_LEVEL_ATTR = "_classLevel"
ENUM_LEVEL_ATTR = "_enumLevel"

# 新增：父章节上下文注释的模式
PARENT_SECTION_CONTEXT_TAG = "PARENT_SECTION_CONTEXT"