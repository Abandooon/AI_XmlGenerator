"""
完整的XML标签格式解决方案
================================

问题分析：
- FSM: 使用原始XML格式 "APPLICATION-SW-COMPONENT-TYPE"
- GBNF: 规则名必须小写 "application_sw_component_type"
- LLM: 输出原始XML格式 "APPLICATION-SW-COMPONENT-TYPE"

解决方案：建立格式映射系统，保持各组件内部一致性
"""

from typing import Dict, Set

class TagFormatManager:
    """XML标签格式管理器 - 统一处理各种格式转换"""

    def __init__(self):
        # 格式映射缓存
        self._original_to_gbnf_cache: Dict[str, str] = {}
        self._gbnf_to_original_cache: Dict[str, str] = {}

    def original_to_gbnf_rule(self, xml_tag: str) -> str:
        """原始XML标签 -> GBNF规则名

        "APPLICATION-SW-COMPONENT-TYPE" -> "application_sw_component_type"
        """
        if xml_tag in self._original_to_gbnf_cache:
            return self._original_to_gbnf_cache[xml_tag]

        if not xml_tag:
            result = "empty_tag"
        else:
            # 转小写，连字符变下划线
            result = xml_tag.lower().replace("-", "_")

            # 确保以字母开头
            if not result[0].isalpha():
                result = "tag_" + result

            # 清理非法字符
            result = re.sub(r'[^a-z0-9_]', '_', result)
            result = re.sub(r'_+', '_', result)  # 合并多个下划线
            result = result.strip('_')

            # 特殊情况处理
            if not result:
                result = "unknown_tag"

        self._original_to_gbnf_cache[xml_tag] = result
        self._gbnf_to_original_cache[result] = xml_tag
        return result

    def original_to_gbnf_token(self, xml_tag: str) -> str:
        """原始XML标签 -> GBNF TOKEN名

        "APPLICATION-SW-COMPONENT-TYPE" -> "APPLICATION_SW_COMPONENT_TYPE"
        """
        if not xml_tag:
            return "EMPTY_TAG"

        # TOKEN名：替换连字符为下划线，保持大写
        return xml_tag.replace("-", "_")

    def gbnf_rule_to_original(self, rule_name: str) -> str:
        """GBNF规则名 -> 原始XML标签"""
        if rule_name in self._gbnf_to_original_cache:
            return self._gbnf_to_original_cache[rule_name]

        # 尝试反向转换：下划线变连字符，转大写
        result = rule_name.upper().replace("_", "-")
        return result

    def create_format_mapping(self, xml_tags: Set[str]) -> Dict[str, Dict[str, str]]:
        """为一组XML标签创建完整的格式映射表"""
        mapping = {
            "original_to_gbnf_rule": {},
            "original_to_gbnf_token": {},
            "gbnf_rule_to_original": {},
            "original_to_fsm": {},  # FSM使用原始格式
        }

        for tag in xml_tags:
            gbnf_rule = self.original_to_gbnf_rule(tag)
            gbnf_token = self.original_to_gbnf_token(tag)

            mapping["original_to_gbnf_rule"][tag] = gbnf_rule
            mapping["original_to_gbnf_token"][tag] = gbnf_token
            mapping["gbnf_rule_to_original"][gbnf_rule] = tag
            mapping["original_to_fsm"][tag] = tag  # FSM保持原始格式

        return mapping


# 全局格式管理器实例
tag_format_manager = TagFormatManager()

def normalize_for_gbnf(xml_tag: str) -> str:
    """专用于GBNF的标签规范化函数"""
    return tag_format_manager.original_to_gbnf_rule(xml_tag)

def normalize_for_fsm(xml_tag: str) -> str:
    """专用于FSM的标签规范化函数（保持原始格式）"""
    return xml_tag  # FSM使用原始格式

def normalize_for_token(xml_tag: str) -> str:
    """专用于GBNF TOKEN的标签规范化函数"""
    return tag_format_manager.original_to_gbnf_token(xml_tag)


# 🔥 修复后的GrammarExporter
"""grammar_exporter.py - 使用格式管理器的完整修复版本"""

import json
import pathlib
import re
from typing import Dict, List, Set

from cli import BUILD_CFG

# ---------------------------------------------------------------------------
# Configuration ----------------------------------------------------------------
# ---------------------------------------------------------------------------
_MAX_ENUM = BUILD_CFG.get("limits", {}).get("max_enum", 64)

# ---------------------------------------------------------------------------
# Helpers ---------------------------------------------------------------------
# ---------------------------------------------------------------------------

def _iter_jsonl(fp: pathlib.Path):
    """Yield parsed JSON objects from a .jsonl file (if present)."""
    if not fp.exists():
        return
    for ln in fp.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln:
            yield json.loads(ln)


class GrammarExporter:
    """Convert raw_* canonical files into a single autosar.gbnf file.

    🔥 使用TagFormatManager的完全修复版本
    """

    def __init__(
        self,
        out_dir: str | pathlib.Path,
        *,
        roots: List[str] | None = None,
        raw_dir: str | pathlib.Path,
    ) -> None:
        self.out_dir = pathlib.Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

        self.raw_dir = pathlib.Path(raw_dir)
        self.roots: List[str] = roots or []

        # 🔥 使用全局格式管理器
        self.format_manager = tag_format_manager

        # In‑memory buffers
        self._lines: List[str] = []
        self._emitted_tokens: Set[str] = set()
        self._emitted_rules: Set[str] = set()
        self._value_pool: Dict[str, Set[str]] = {}

    def _write_token(self, token: str, literal: str) -> None:
        """Emit a TOKEN line once."""
        if token in self._emitted_tokens:
            return
        self._lines.append(f'{token}: "{literal}"')
        self._emitted_tokens.add(token)

    def _write_rule(self, rule: str, production: str) -> None:
        """Emit a parser rule line once."""
        # 🔥 验证规则名格式
        if not re.match(r'^[a-z][a-z0-9_]*$', rule):
            print(f"❌ 警告：规则名格式不符合GBNF规范: '{rule}'")
            # 不自动修复，让调用者处理

        line = f"{rule} ::= {production}"
        if line in self._emitted_rules:
            return

        self._lines.append(line)
        self._emitted_rules.add(line)

    def _add_enum_values(self, base_tag: str, vals: List[str]) -> None:
        """🔥 基于原始标签生成枚举规则"""
        if not vals or len(vals) > _MAX_ENUM:
            return

        # 枚举规则名：原始标签转GBNF格式 + "_value"
        rule_name = self.format_manager.original_to_gbnf_rule(base_tag) + "_value"
        self._value_pool.setdefault(rule_name, set()).update(vals)

    def export(self) -> pathlib.Path:
        """🔥 使用格式管理器的导出函数"""
        print(f"🚀 开始导出GBNF文件（使用格式管理器）...")

        # 完全重新初始化
        self._lines = []
        self._emitted_tokens.clear()
        self._emitted_rules.clear()
        self._value_pool.clear()

        # 添加文件头
        self._lines.append("; Auto-generated GBNF with Format Manager")

        print(f"📋 根标签: {self.roots}")

        # 按正确顺序生成
        self._emit_roots()
        self._emit_from_raw()
        self._flush_enum_rules()

        # 验证和输出
        content = "\n".join(self._lines)
        validation_errors = self._validate_gbnf_syntax(content)

        if validation_errors:
            print("❌ GBNF语法验证失败:")
            for error in validation_errors[:10]:
                print(f"   - {error}")
        else:
            print("✅ GBNF语法验证通过")

        print(f"📊 生成统计:")
        print(f"   总行数: {len(self._lines)}")
        print(f"   TOKEN数: {len(self._emitted_tokens)}")
        print(f"   规则数: {len(self._emitted_rules)}")

        # 写入文件
        out_path = self.out_dir / "autosar.gbnf"
        out_path.write_text(content, encoding="utf-8")
        print(f"📁 文件已保存: {out_path}")

        # 预览
        print(f"📄 文件预览 (前20行):")
        for i, line in enumerate(self._lines[:20], 1):
            print(f"   {i:2d}: {line}")
        if len(self._lines) > 20:
            print(f"   ... (还有 {len(self._lines) - 20} 行)")

        return out_path

    def _emit_roots(self) -> None:
        """🔥 使用格式管理器的根规则生成"""
        print(f"🔧 生成根规则，根标签数量: {len(self.roots)}")

        root_rule_names: List[str] = []

        for original_tag in self.roots:
            print(f"📝 处理根标签: '{original_tag}'")

            # 🔥 使用格式管理器进行转换
            gbnf_rule_name = self.format_manager.original_to_gbnf_rule(original_tag)
            gbnf_token_name = self.format_manager.original_to_gbnf_token(original_tag)

            print(f"   原始标签: {original_tag}")
            print(f"   GBNF规则名: {gbnf_rule_name}")
            print(f"   GBNF TOKEN名: {gbnf_token_name}")

            # 验证转换结果
            if not re.match(r'^[a-z][a-z0-9_]*$', gbnf_rule_name):
                print(f"❌ 规则名格式验证失败: {gbnf_rule_name}")
                continue

            # 1. TOKEN定义：GBNF_TOKEN_NAME: "原始标签"
            self._write_token(gbnf_token_name, original_tag)
            print(f"   ✅ TOKEN定义: {gbnf_token_name}: \"{original_tag}\"")

            # 2. 规则定义：gbnf_rule_name ::= GBNF_TOKEN_NAME
            self._write_rule(gbnf_rule_name, gbnf_token_name)
            print(f"   ✅ 规则定义: {gbnf_rule_name} ::= {gbnf_token_name}")

            # 3. 添加到start规则列表
            root_rule_names.append(gbnf_rule_name)

        # 4. 生成start规则
        if root_rule_names:
            start_rule = "start ::= " + " | ".join(root_rule_names)
            if len(self._lines) > 0:
                self._lines.insert(1, start_rule)
            else:
                self._lines.append(start_rule)
            print(f"   ✅ Start规则: {start_rule}")
        else:
            if len(self._lines) > 0:
                self._lines.insert(1, "start ::= dummy_root")
            else:
                self._lines.append("start ::= dummy_root")
            self._write_rule("dummy_root", '"DUMMY"')
            print(f"   ⚠️ 使用默认start规则")

        print(f"🎉 根规则生成完成，共 {len(root_rule_names)} 个根规则")

    def _emit_from_raw(self) -> None:
        """🔥 使用格式管理器处理raw数据"""
        raw_dir = self.raw_dir
        print(f"🔧 开始处理raw数据...")

        # 枚举处理
        enum_map: Dict[int, List[str]] = {}
        enum_file = raw_dir / "raw_enums.jsonl"
        if enum_file.exists():
            for rec in _iter_jsonl(enum_file):
                values = rec.get("values") or []
                if not (values and len(values) <= _MAX_ENUM):
                    continue
                eid = rec.get("enumId", rec.get("enum_id"))
                try:
                    enum_map[int(eid)] = values
                except (TypeError, ValueError):
                    continue

        print(f"📋 加载了 {len(enum_map)} 个枚举定义")

        # 收集所有已处理的规则名（避免重复）
        processed_rule_names = set()

        # 添加根规则到已处理集合
        for root_tag in self.roots:
            root_rule_name = self.format_manager.original_to_gbnf_rule(root_tag)
            processed_rule_names.add(root_rule_name)

        # 处理类标签
        class_count = 0
        classes_file = raw_dir / "raw_classes.jsonl"

        if classes_file.exists():
            for rec in _iter_jsonl(classes_file):
                original_tag = rec.get("xml_tag")
                if not original_tag:
                    continue

                # 🔥 使用格式管理器转换
                gbnf_rule_name = self.format_manager.original_to_gbnf_rule(original_tag)
                gbnf_token_name = self.format_manager.original_to_gbnf_token(original_tag)

                # 避免重复
                if gbnf_rule_name in processed_rule_names:
                    continue

                processed_rule_names.add(gbnf_rule_name)
                self._write_token(gbnf_token_name, original_tag)
                self._write_rule(gbnf_rule_name, gbnf_token_name)
                class_count += 1

        print(f"✅ 处理了 {class_count} 个类标签")

        # 处理属性标签（简化版本）
        attr_count = 0
        attributes_file = raw_dir / "raw_attributes.jsonl"

        if attributes_file.exists():
            for rec in _iter_jsonl(attributes_file):
                original_tag = rec.get("xml_tag")
                if not original_tag:
                    continue

                is_attr = bool(rec.get("isXmlAttr", False))

                # 暂时跳过XML属性
                if is_attr:
                    continue

                # 🔥 使用格式管理器转换
                gbnf_rule_name = self.format_manager.original_to_gbnf_rule(original_tag)
                gbnf_token_name = self.format_manager.original_to_gbnf_token(original_tag)

                # 避免重复
                if gbnf_rule_name in processed_rule_names:
                    continue

                processed_rule_names.add(gbnf_rule_name)
                self._write_token(gbnf_token_name, original_tag)
                self._write_rule(gbnf_rule_name, gbnf_token_name)
                attr_count += 1

                # 处理枚举值
                enum_vals: List[str] = []
                if rec.get("allowedValues"):
                    enum_vals = rec["allowedValues"][:_MAX_ENUM]
                elif rec.get("typeId"):
                    try:
                        eid = int(rec.get("typeId", -1))
                        enum_vals = enum_map.get(eid, [])
                    except (TypeError, ValueError):
                        pass

                if enum_vals and 2 <= len(enum_vals) <= _MAX_ENUM:
                    self._add_enum_values(original_tag, enum_vals)

        print(f"✅ 处理了 {attr_count} 个属性标签")

    def _flush_enum_rules(self) -> None:
        """输出枚举规则"""
        enum_count = 0
        for rule_name, literals in sorted(self._value_pool.items()):
            if not literals:
                continue

            # 限制枚举数量
            sorted_literals = sorted(literals)
            if len(sorted_literals) > 20:
                sorted_literals = sorted_literals[:20]

            alts = " | ".join(f'"{v}"' for v in sorted_literals)
            self._write_rule(rule_name, alts)
            enum_count += 1

        print(f"✅ 生成了 {enum_count} 个枚举规则")

    def _validate_gbnf_syntax(self, content: str) -> List[str]:
        """验证GBNF语法"""
        errors = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith(';'):
                continue

            # 检查规则格式
            if ' ::= ' in line:
                rule_name = line.split(' ::= ')[0].strip()

                # 检查规则名格式
                if not re.match(r'^[a-z][a-z0-9_]*$', rule_name):
                    errors.append(f"第{i}行: 规则名格式错误: {rule_name}")

            # 检查TOKEN格式
            elif ': ' in line and not line.startswith(' '):
                token_parts = line.split(': ', 1)
                if len(token_parts) == 2:
                    token_name, token_value = token_parts

                    if not re.match(r'^[A-Z][A-Z0-9_]*$', token_name):
                        errors.append(f"第{i}行: TOKEN名格式错误: {token_name}")

                    if not (token_value.startswith('"') and token_value.endswith('"')):
                        errors.append(f"第{i}行: TOKEN值格式错误: {token_value}")

        return errors

    @staticmethod
    def run(
        raw_dir: str | pathlib.Path,
        out_path: str | pathlib.Path,
        *,
        roots: List[str] | None = None,
    ) -> pathlib.Path:
        out_dir = pathlib.Path(out_path)
        if out_dir.suffix:
            out_dir = out_dir.parent
        exporter = GrammarExporter(out_dir, roots=roots, raw_dir=raw_dir)
        return exporter.export()


# 🔥 测试和验证函数
def test_format_conversion():
    """测试格式转换功能"""
    test_tags = [
        "APPLICATION-SW-COMPONENT-TYPE",
        "SHORT-NAME",
        "INTERNAL-BEHAVIORS",
        "P-PORT-PROTOTYPE"
    ]

    print("🧪 格式转换测试:")
    for tag in test_tags:
        gbnf_rule = tag_format_manager.original_to_gbnf_rule(tag)
        gbnf_token = tag_format_manager.original_to_gbnf_token(tag)
        back_to_original = tag_format_manager.gbnf_rule_to_original(gbnf_rule)

        print(f"原始: {tag}")
        print(f"  -> GBNF规则: {gbnf_rule}")
        print(f"  -> GBNF TOKEN: {gbnf_token}")
        print(f"  -> 反向转换: {back_to_original}")
        print()

if __name__ == "__main__":
    test_format_conversion()