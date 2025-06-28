# fix_constraint_types.py - 修复约束类型问题
import sys

sys.path.insert(0, './src')

# 检查约束数据类型
from src.client.constraint_preparer import ConstraintPreparer


def test_constraint_types():
    preparer = ConstraintPreparer("src/constraint_graph/artifacts")

    # 测试约束信息
    constraint_info = preparer.prepare_constraint_info("mixed")

    print(f"🔍 约束类型检查:")
    print(f"   GBNF启用: {constraint_info.gbnf_enabled}")
    print(f"   语法规则类型: {type(constraint_info.grammar_rules)}")
    print(f"   语法规则长度: {len(constraint_info.grammar_rules) if constraint_info.grammar_rules else 0}")

    print(f"   FSM启用: {constraint_info.fsm_enabled}")
    print(f"   允许token类型: {type(constraint_info.allowed_tokens)}")
    print(f"   允许token长度: {len(constraint_info.allowed_tokens) if constraint_info.allowed_tokens else 0}")

    if constraint_info.allowed_tokens:
        print(f"   前5个token: {constraint_info.allowed_tokens[:5]}")


if __name__ == "__main__":
    test_constraint_types()