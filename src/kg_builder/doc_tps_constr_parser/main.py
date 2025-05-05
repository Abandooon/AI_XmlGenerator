import os
import json
from datetime import datetime
from typing import Dict, List, Any

from logging_utils import StepLogger
from document_processor import DocumentProcessor
from flexible_extractor import FlexibleConstraintExtractor
from entity_recognizer import EntityRecognizer
from logic_analyzer import LogicAnalyzer
from constraint_mapper import ConstraintMapper
from models import ConstraintRaw, Entity, ConstraintStructured
from utils import save_json


# 用于将对象转换为可序列化的字典
def _to_dict(obj):
    if isinstance(obj, list):
        return [_to_dict(item) if hasattr(item, '__dict__') else item for item in obj]
    elif hasattr(obj, '__dict__'):
        result = {}
        for key, val in obj.__dict__.items():
            if isinstance(val, list):
                result[key] = [_to_dict(item) if hasattr(item, '__dict__') else item for item in val]
            elif hasattr(val, '__dict__'):
                result[key] = _to_dict(val)
            else:
                result[key] = val
        return result
    else:
        return obj


def main():
    # 创建步骤日志器
    logger = StepLogger(enable=True)

    # 直接指定输入输出目录
    logger.step("设置输入/输出目录")
    input_dir = "input"  # 相对于当前工作目录的input文件夹
    output_dir = "output"  # 相对于当前工作目录的output文件夹
    debug_dir = os.path.join(output_dir, "debug")  # 用于存储中间结果的目录

    logger.log(f"输入目录: {input_dir}")
    logger.log(f"输出目录: {output_dir}")
    logger.log(f"调试目录: {debug_dir}")

    # 检查目录
    logger.step("检查输入/输出目录")

    if not os.path.exists(input_dir):
        logger.log(f"错误: 输入目录 '{input_dir}' 不存在")
        logger.log(f"尝试创建输入目录...")
        try:
            os.makedirs(input_dir)
            logger.log(f"已创建输入目录，请将文档放入 '{input_dir}' 目录后重新运行")
            return
        except Exception as e:
            logger.log(f"创建输入目录失败: {str(e)}")
            return

    if not os.path.exists(output_dir):
        logger.log(f"创建输出目录 '{output_dir}'")
        os.makedirs(output_dir)

    if not os.path.exists(debug_dir):
        logger.log(f"创建调试目录 '{debug_dir}'")
        os.makedirs(debug_dir)

    # 检查是否存在元数据文件
    metadata_file = os.path.join(input_dir, "unified_metadata.json")
    if not os.path.exists(metadata_file):
        logger.log(f"警告: 元数据文件 '{metadata_file}' 不存在")
        logger.log(f"实体识别功能可能无法正常工作，建议提供元数据文件")
        # 创建一个空的元数据文件以避免错误
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump({"groups": {}, "simpleTypes": {}}, f)
        logger.log(f"已创建空元数据文件，可以稍后替换为实际数据")

    # 查找文档文件
    logger.step("查找输入文档")
    doc_files = []
    for file in os.listdir(input_dir):
        if file.endswith('.txt') or file.endswith('.md'):
            doc_files.append(os.path.join(input_dir, file))

    if not doc_files:
        logger.log(f"警告: 在 '{input_dir}' 目录中未找到.txt或.md文件")
        logger.log(f"请将要处理的文档放入 '{input_dir}' 目录后重新运行")
        return

    logger.log(f"找到 {len(doc_files)} 个文档文件")
    for i, file in enumerate(doc_files):
        logger.log(f"  文件 {i + 1}: {os.path.basename(file)}")

    # 初始化结果存储
    all_results = {
        "raw_constraints": [],
        "constraints_with_entities": [],
        "logic_analyses": [],
        "structured_constraints": []
    }

    # 初始化处理器
    try:
        logger.step("初始化处理组件")
        doc_processor = DocumentProcessor(input_dir)
        logger.log("文档处理器初始化完成")

        extractor = FlexibleConstraintExtractor(debug=True, max_debug_length=100)
        logger.log("约束提取器初始化完成")

        try:
            entity_recognizer = EntityRecognizer(metadata_file)
            logger.log("实体识别器初始化完成")
            entity_recognition_enabled = True
        except Exception as e:
            logger.log(f"初始化实体识别器失败: {str(e)}")
            logger.log("将跳过实体识别步骤")
            entity_recognition_enabled = False

        logic_analyzer = LogicAnalyzer()
        logger.log("逻辑分析器初始化完成")

        constraint_mapper = ConstraintMapper()
        logger.log("约束映射器初始化完成")
    except Exception as e:
        logger.log(f"初始化处理组件失败: {str(e)}")
        return

    # 处理每个文档
    for doc_index, doc_file in enumerate(doc_files):
        doc_name = os.path.basename(doc_file)
        doc_base = os.path.splitext(doc_name)[0]

        logger.step(f"处理文档 {doc_index + 1}/{len(doc_files)}: {doc_name}")

        # 1. 读取和预处理文档
        logger.log("读取和预处理文档")
        try:
            doc_content = doc_processor.preprocess_document(doc_file)
            logger.log(f"成功加载文档，长度: {len(doc_content)} 字符")

            # 保存预处理后的文档
            preprocessed_path = os.path.join(debug_dir, f"{doc_base}_preprocessed.txt")
            with open(preprocessed_path, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            logger.log(f"已保存预处理文档到: {preprocessed_path}")
        except Exception as e:
            logger.log(f"文档处理失败: {str(e)}")
            continue

        # 2. 提取约束
        logger.log("提取约束")
        try:
            constraints = extractor.extract_constraints(doc_content)
            logger.log(f"从 {doc_name} 提取了 {len(constraints)} 个约束")

            # 保存原始约束
            raw_constraints_path = os.path.join(debug_dir, f"{doc_base}_raw_constraints.json")
            save_json([_to_dict(c) for c in constraints], raw_constraints_path)
            logger.log(f"已保存原始约束到: {raw_constraints_path}")

            # 保存为可读文本格式
            raw_constraints_txt_path = os.path.join(debug_dir, f"{doc_base}_raw_constraints.txt")
            with open(raw_constraints_txt_path, 'w', encoding='utf-8') as f:
                for i, c in enumerate(constraints):
                    f.write(f"======== 约束 #{i + 1} ========\n")
                    f.write(f"ID: {c.id}\n")
                    f.write(f"标题: {c.title[:300]}...\n" if len(c.title) > 300 else f"标题: {c.title}\n")
                    f.write(f"正文: {c.body[:500]}...\n" if len(c.body) > 500 else f"正文: {c.body}\n")
                    if c.explanation:
                        f.write(f"解释: {c.explanation[:300]}...\n" if len(
                            c.explanation) > 300 else f"解释: {c.explanation}\n")
                    if c.reference_id:
                        f.write(f"引用ID: {c.reference_id}\n")
                    f.write("\n\n")
            logger.log(f"已保存可读格式原始约束到: {raw_constraints_txt_path}")

            # 添加到总结果
            all_results["raw_constraints"].extend(constraints)
        except Exception as e:
            logger.log(f"约束提取失败: {str(e)}")
            continue

        # 3. 实体识别
        logger.step("识别实体")
        constraints_with_entities = []
        all_entities = []

        if entity_recognition_enabled and constraints:
            try:
                all_doc_entities = []
                for i, constraint in enumerate(constraints):
                    logger.log(f"处理约束 {i + 1}/{len(constraints)}: {constraint.id}")
                    try:
                        constraint_with_entity, entities = entity_recognizer.recognize_entities(constraint)

                        logger.log(f"在约束 {constraint.id} 中识别到 {len(entities)} 个实体")
                        constraints_with_entities.append(constraint_with_entity)
                        all_doc_entities.append(entities)
                        all_entities.extend(entities)
                    except Exception as e:
                        logger.log(f"约束 {constraint.id} 的实体识别失败: {str(e)}")
                        constraints_with_entities.append(constraint)
                        all_doc_entities.append([])

                # 保存实体识别结果
                entities_path = os.path.join(debug_dir, f"{doc_base}_entities.json")
                save_json([_to_dict(e) for e in all_entities], entities_path)
                logger.log(f"已保存实体识别结果到: {entities_path}")

                # 保存为可读文本格式
                entities_txt_path = os.path.join(debug_dir, f"{doc_base}_entities.txt")
                with open(entities_txt_path, 'w', encoding='utf-8') as f:
                    for i, (constraint, entities) in enumerate(zip(constraints, all_doc_entities)):
                        f.write(f"======== 约束 #{i + 1}: {constraint.id} ========\n")
                        if entities:
                            for j, entity in enumerate(entities):
                                f.write(f"  实体 #{j + 1}:\n")
                                f.write(f"    文本: {entity.text}\n")
                                f.write(f"    类型: {entity.type}\n")
                                f.write(f"    位置: {entity.start}-{entity.end}\n")
                                if entity.parent:
                                    f.write(f"    父元素: {entity.parent}\n")
                                f.write("\n")
                        else:
                            f.write("  未识别到实体\n\n")
                logger.log(f"已保存可读格式实体识别结果到: {entities_txt_path}")

                # 添加到总结果
                all_results["constraints_with_entities"].extend(constraints_with_entities)
            except Exception as e:
                logger.log(f"实体识别阶段失败: {str(e)}")
                constraints_with_entities = constraints
        else:
            logger.log("跳过实体识别步骤")
            constraints_with_entities = constraints

        if not constraints_with_entities:
            constraints_with_entities = constraints
            logger.log("未能识别实体，使用原始约束继续处理")

        # 4. 逻辑分析
        logger.step("分析约束逻辑")
        logic_analyses = []

        try:
            for i, (constraint, entities) in enumerate(zip(constraints_with_entities,
                                                           all_doc_entities if entity_recognition_enabled and all_doc_entities else
                                                           [[]] * len(constraints_with_entities))):
                logger.log(f"分析约束 {i + 1}/{len(constraints_with_entities)}: {constraint.id}")
                try:
                    logic_analysis = logic_analyzer.analyze_constraint_logic(constraint, entities)
                    logic_analyses.append(logic_analysis)

                    logger.log(f"约束 {constraint.id} 的逻辑类型: {logic_analysis.get('constraint_type', 'Unknown')}")
                    if logic_analysis.get('conditions'):
                        logger.log(f"  有 {len(logic_analysis['conditions'])} 个条件表达式")
                    if logic_analysis.get('prohibitions'):
                        logger.log(f"  有 {len(logic_analysis['prohibitions'])} 个禁止表达式")
                    if logic_analysis.get('non_overlapping'):
                        logger.log(f"  包含不重叠约束")
                    if logic_analysis.get('permissions'):
                        logger.log(f"  包含许可表达式")
                except Exception as e:
                    logger.log(f"约束 {constraint.id} 的逻辑分析失败: {str(e)}")
                    logic_analyses.append({"constraint_type": "Generic"})

            # 保存逻辑分析结果
            analyses_path = os.path.join(debug_dir, f"{doc_base}_logic_analyses.json")
            save_json(logic_analyses, analyses_path)
            logger.log(f"已保存逻辑分析结果到: {analyses_path}")

            # 保存为可读文本格式
            analyses_txt_path = os.path.join(debug_dir, f"{doc_base}_logic_analyses.txt")
            with open(analyses_txt_path, 'w', encoding='utf-8') as f:
                for i, (constraint, analysis) in enumerate(zip(constraints_with_entities, logic_analyses)):
                    f.write(f"======== 约束 #{i + 1}: {constraint.id} ========\n")
                    f.write(f"约束类型: {analysis.get('constraint_type', 'Generic')}\n")

                    if analysis.get('conditions'):
                        f.write(f"条件表达式: {len(analysis['conditions'])} 个\n")
                        for j, cond in enumerate(analysis['conditions']):
                            f.write(f"  条件 #{j + 1}: {cond}\n")

                    if analysis.get('prohibitions'):
                        f.write(f"禁止表达式: {len(analysis['prohibitions'])} 个\n")
                        for j, prohib in enumerate(analysis['prohibitions']):
                            f.write(f"  禁止 #{j + 1}: {prohib}\n")

                    if analysis.get('non_overlapping'):
                        f.write(f"不重叠约束: {analysis['non_overlapping']}\n")

                    if analysis.get('permissions'):
                        f.write(f"许可表达式: {analysis['permissions']}\n")

                    if analysis.get('scope'):
                        f.write(f"作用域: {analysis['scope']}\n")

                    f.write("\n\n")
            logger.log(f"已保存可读格式逻辑分析结果到: {analyses_txt_path}")

            # 添加到总结果
            all_results["logic_analyses"].extend(logic_analyses)
        except Exception as e:
            logger.log(f"逻辑分析阶段失败: {str(e)}")
            logic_analyses = [{"constraint_type": "Generic"}] * len(constraints_with_entities)

        # 5. 结构化映射
        logger.step("结构化映射")
        structured_constraints = []

        try:
            for i, (constraint, analysis) in enumerate(zip(constraints_with_entities, logic_analyses)):
                logger.log(f"映射约束 {i + 1}/{len(constraints_with_entities)}: {constraint.id}")
                try:
                    structured = constraint_mapper.map_to_structured(constraint, analysis)
                    structured_constraints.append(structured)
                    logger.log(f"约束 {constraint.id} 成功映射为 {structured.type} 类型")
                except Exception as e:
                    logger.log(f"约束 {constraint.id} 的结构化映射失败: {str(e)}")
                    # 创建一个基本的结构化约束
                    structured = ConstraintStructured(
                        id=constraint.id,
                        type="Generic",
                        title=constraint.title,
                        body=constraint.body,
                        source_id=constraint.id,
                        explanation=constraint.explanation,
                        reference_id=constraint.reference_id
                    )
                    structured_constraints.append(structured)

            # 保存结构化约束结果
            structured_path = os.path.join(debug_dir, f"{doc_base}_structured_constraints.json")
            save_json([_to_dict(s) for s in structured_constraints], structured_path)
            logger.log(f"已保存结构化约束到: {structured_path}")

            # 保存为可读文本格式
            structured_txt_path = os.path.join(debug_dir, f"{doc_base}_structured_constraints.txt")
            with open(structured_txt_path, 'w', encoding='utf-8') as f:
                for i, s in enumerate(structured_constraints):
                    f.write(f"======== 约束 #{i + 1}: {s.id} ========\n")
                    f.write(f"类型: {s.type}\n")
                    f.write(f"标题: {s.title[:200]}...\n" if len(s.title) > 200 else f"标题: {s.title}\n")
                    f.write(f"源ID: {s.source_id}\n")

                    if s.condition:
                        if isinstance(s.condition, list):
                            f.write(f"条件表达式: {len(s.condition)} 个\n")
                            for j, cond in enumerate(s.condition):
                                f.write(f"  条件 #{j + 1}: {_to_dict(cond)}\n")
                        else:
                            f.write(f"条件表达式: {_to_dict(s.condition)}\n")

                    if s.prohibition:
                        f.write(f"禁止表达式: {len(s.prohibition)} 个\n")
                        for j, prohib in enumerate(s.prohibition):
                            f.write(f"  禁止 #{j + 1}: {_to_dict(prohib)}\n")

                    if s.non_overlapping:
                        f.write(f"不重叠约束: {_to_dict(s.non_overlapping)}\n")

                    if s.permission:
                        f.write(f"许可表达式: {_to_dict(s.permission)}\n")

                    if s.reference_id:
                        f.write(f"引用ID: {s.reference_id}\n")

                    f.write("\n\n")
            logger.log(f"已保存可读格式结构化约束到: {structured_txt_path}")

            # 添加到总结果
            all_results["structured_constraints"].extend(structured_constraints)
        except Exception as e:
            logger.log(f"结构化映射阶段失败: {str(e)}")

    # 6. 输出最终结果
    logger.step("保存最终结果")

    # 保存原始约束文本输出
    if all_results["raw_constraints"]:
        output_path = os.path.join(output_dir, "extracted_constraints.txt")
        logger.log(f"保存 {len(all_results['raw_constraints'])} 个原始约束到 {output_path}")

        with open(output_path, 'w', encoding='utf-8') as f:
            for i, c in enumerate(all_results["raw_constraints"]):
                f.write(f"======== 约束 #{i + 1} ========\n")
                f.write(f"ID: {c.id}\n")
                f.write(f"标题: {c.title[:300]}...\n" if len(c.title) > 300 else f"标题: {c.title}\n")
                f.write(f"正文: {c.body[:500]}...\n" if len(c.body) > 500 else f"正文: {c.body}\n")
                if c.explanation:
                    f.write(
                        f"解释: {c.explanation[:300]}...\n" if len(c.explanation) > 300 else f"解释: {c.explanation}\n")
                if c.reference_id:
                    f.write(f"引用ID: {c.reference_id}\n")
                f.write("\n\n")
    else:
        logger.log("未提取到任何约束")

    # 保存结构化约束JSON输出
    if all_results["structured_constraints"]:
        structured_output_path = os.path.join(output_dir, "structured_constraints.json")
        logger.log(f"保存 {len(all_results['structured_constraints'])} 个结构化约束到 {structured_output_path}")

        # 将结构化约束转换为可序列化的字典
        structured_dicts = [_to_dict(sc) for sc in all_results["structured_constraints"]]
        save_json(structured_dicts, structured_output_path)
    else:
        logger.log("未生成任何结构化约束")

    # 保存处理统计信息
    stats = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "processed_documents": len(doc_files),
        "document_names": [os.path.basename(f) for f in doc_files],
        "raw_constraints_count": len(all_results["raw_constraints"]),
        "structured_constraints_count": len(all_results["structured_constraints"]),
        "entity_recognition_enabled": entity_recognition_enabled,
        "entities_count": len(all_entities) if entity_recognition_enabled else 0
    }

    stats_path = os.path.join(output_dir, "processing_stats.json")
    save_json(stats, stats_path)
    logger.log(f"已保存处理统计信息到 {stats_path}")

    logger.finish()


if __name__ == "__main__":
    main()