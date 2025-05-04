import os
import argparse
import json
from typing import Dict, List, Any

from document_processor import DocumentProcessor
from constraint_extractor import ConstraintExtractor
from entity_recognizer import EntityRecognizer
from logic_analyzer import LogicAnalyzer
from constraint_mapper import ConstraintMapper
from models import ConstraintRaw, ConstraintStructured
from utils import save_json


def main():
    parser = argparse.ArgumentParser(description='AUTOSAR规范文档解析工具')
    parser.add_argument('--input-dir', type=str, default='input', help='输入目录，包含规范文档和元数据')
    parser.add_argument('--output-dir', type=str, default='output', help='输出目录')
    parser.add_argument('--spec-file', type=str, default='autosar_spec.md', help='规范文档文件名')
    parser.add_argument('--metadata-file', type=str, default='unified_metadata.json', help='元数据文件名')
    args = parser.parse_args()

    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)

    # 构建完整路径
    metadata_path = os.path.join(args.input_dir, args.metadata_file)

    print(f"开始处理规范文档: {args.spec_file}")
    print(f"使用元数据: {metadata_path}")

    # 1. 初始化处理模块
    document_processor = DocumentProcessor(args.input_dir)
    constraint_extractor = ConstraintExtractor()
    entity_recognizer = EntityRecognizer(metadata_path)
    logic_analyzer = LogicAnalyzer()
    constraint_mapper = ConstraintMapper()

    # 2. 处理文档
    processed_text = document_processor.process(args.spec_file)

    # 3. 提取约束
    raw_constraints = constraint_extractor.extract_constraints(processed_text)
    print(f"从文档中提取了 {len(raw_constraints)} 个约束")

    # 4. 处理每个约束
    structured_constraints = []

    for raw_constraint in raw_constraints:
        print(f"处理约束: {raw_constraint.id}")

        # 5. 实体识别
        _, entities = entity_recognizer.recognize_entities(raw_constraint)
        print(f"  识别出 {len(entities)} 个实体")

        # 6. 逻辑分析
        logic_analysis = logic_analyzer.analyze_constraint_logic(raw_constraint, entities)
        print(f"  约束类型: {logic_analysis.get('constraint_type', 'Unknown')}")

        # 7. 结构化映射
        structured_constraint = constraint_mapper.map_to_structured(raw_constraint, logic_analysis)
        structured_constraints.append(structured_constraint)

    # 8. 保存结果
    constraints_output = [constraint.__dict__ for constraint in structured_constraints]
    output_path = os.path.join(args.output_dir, 'structured_constraints.json')
    save_json(constraints_output, output_path)

    print(f"处理完成，结果已保存到: {output_path}")


if __name__ == "__main__":
    main()