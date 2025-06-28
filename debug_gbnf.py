# debug_gbnf.py - 调试GBNF语法内容
import sys

sys.path.insert(0, './src')

from src.client.constraint_preparer import ConstraintPreparer


def debug_gbnf_content():
    preparer = ConstraintPreparer("src/constraint_graph/artifacts")

    # 获取原始GBNF内容
    raw_grammar = preparer.gbnf_grammar

    print(f"🔍 GBNF语法调试:")
    print(f"   总长度: {len(raw_grammar)}")
    print(f"   类型: {type(raw_grammar)}")

    # 检查前200字符
    print(f"\n📄 前200字符:")
    print(repr(raw_grammar[:200]))

    # 检查是否包含问题字符
    has_null = '\x00' in raw_grammar
    has_weird_chars = any(ord(c) > 127 for c in raw_grammar[:1000])

    print(f"\n🔍 内容检查:")
    print(f"   包含空字符: {has_null}")
    print(f"   包含非ASCII字符: {has_weird_chars}")

    # 检查行数和结构
    lines = raw_grammar.split('\n')
    print(f"   总行数: {len(lines)}")
    print(f"   空行数: {sum(1 for line in lines if not line.strip())}")

    # 查看前几行
    print(f"\n📄 前10行:")
    for i, line in enumerate(lines[:10]):
        print(f"   {i + 1}: {repr(line)}")

    # 测试strip操作
    try:
        stripped = raw_grammar.strip()
        print(f"\n✅ strip()操作成功，长度: {len(stripped)}")
    except Exception as e:
        print(f"\n❌ strip()操作失败: {e}")
        print(f"   错误类型: {type(e)}")


if __name__ == "__main__":
    debug_gbnf_content()