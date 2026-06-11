"""AUTOSAR ARXML Generator - Gradio Web UI (Gradio 6 兼容版)

本版本改动:
1. 适配 Gradio 6 API:
   - Chatbot 移除 type= 参数(messages 已是唯一格式)
   - show_copy_button -> buttons=["copy"]
   - theme 从 Blocks() 移到 launch()
2. 新增「🔍 验证」标签页, 集成 src/validation 的 AutosarValidator:
   - 可验证 Round2 生成的文件 / 配置中的XML实例 / 手动上传的XML
   - 结构化展示 XSD / SHACL / SMT 各验证器结果
   - 错误定位: 自动从错误信息提取行号, 展示出错位置附近的XML源码片段
3. Round2 完成后可自动触发验证(可在验证页关闭)
4. 沿用 gr.State 会话隔离、文档上传、反馈轮次管理、文件下载、统计面板
"""

import re
import time
import traceback
from pathlib import Path

import gradio as gr

from llm_rag_generator_human import LLMRAGGenerator

generator = LLMRAGGenerator()

MAX_FEEDBACK_ROUNDS = 5

STAGE_LABELS = {
    "idle": "🟢 空闲 - 请输入需求(可先上传文档)",
    "round1_running": "🏗️ Round 1 - 架构设计中...",
    "awaiting_feedback": "💭 等待反馈 - 请确认设计或提出修改意见",
    "round2_running": "⚙️ Round 2 - 详细生成中...",
    "validating": "🔍 正在验证生成的ARXML...",
    "done": "🎉 已完成 - 可下载文件、查看验证结果或开始新会话",
}

EXAMPLE_PROMPTS = [
    "设计一个温度监控AUTOSAR组件，能够从温度传感器读取数据，进行处理分析，并输出温度状态信息给其他组件使用。",
    "设计一个多组件电机控制AUTOSAR系统，包括传感器数据采集组件、控制算法处理组件、执行器控制组件，实现完整的闭环控制。",
    "设计一个车载通信网关AUTOSAR系统，需要多个组件处理不同的通信协议(CAN, LIN, Ethernet)，包括协议转换、路由管理、安全检查等功能。",
]


# ===========================================================================
# 验证模块集成
# ===========================================================================

_validator = None
_validator_error = None


def find_validation_config():
    """按 run_validation.py 的优先级查找验证配置文件"""
    import yaml
    candidates = [
        "main_config.yaml",
        "config/main_config.yaml",
        "validation_config.yaml",
        "config/validation_config.yaml",
    ]
    for c in candidates:
        p = Path(c)
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
                if cfg and "file_paths" in cfg:
                    return str(p)
            except Exception:
                continue
    return None


def get_validator():
    """懒加载 AutosarValidator, 失败时记录原因而不是让整个UI崩溃"""
    global _validator, _validator_error
    if _validator is not None:
        return _validator
    if _validator_error is not None:
        return None
    try:
        import sys
        project_root = Path.cwd()
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        from src.validation.main_validator import AutosarValidator
        _validator = AutosarValidator(find_validation_config())
        return _validator
    except Exception as e:
        _validator_error = f"{type(e).__name__}: {e}"
        return None


def list_validatable_files(state=None):
    """收集可验证的XML文件: 本次生成的 + 配置中的xml_instances + xml_instance目录"""
    files = []
    if state:
        files += [p for p in state.get("output_files", [])
                  if p.lower().endswith((".arxml", ".xml"))]
    validator = get_validator()
    if validator is not None:
        files += list(getattr(validator, "available_xml_files", []) or [])
    inst_dir = Path("xml_instance")
    if inst_dir.exists():
        files += [str(p) for p in inst_dir.glob("*.arxml")]
        files += [str(p) for p in inst_dir.glob("*.xml")]
    # 去重并只保留存在的文件
    seen, result = set(), []
    for f in files:
        key = str(Path(f).resolve())
        if key not in seen and Path(f).exists():
            seen.add(key)
            result.append(str(f))
    return result


# ---- 错误定位 -------------------------------------------------------------

LINE_PATTERNS = [
    re.compile(r"[Ll]ine[:\s]+(\d+)"),       # "line 42" / "Line: 42"
    re.compile(r"行[:\s]*(\d+)"),             # "第42行" / "行: 42"
    re.compile(r":(\d+):\d+"),                # "file.arxml:42:7"
]


def extract_error_lines(text):
    """从错误信息文本中提取所有行号"""
    lines = []
    for pat in LINE_PATTERNS:
        lines += [int(m) for m in pat.findall(text or "")]
    return sorted(set(lines))


def xml_context_snippet(xml_path, line_no, context=4):
    """返回出错行附近的源码片段, 出错行用 >>> 标记"""
    try:
        all_lines = Path(xml_path).read_text(
            encoding="utf-8", errors="replace").splitlines()
    except Exception as e:
        return f"(无法读取源文件: {e})"
    start = max(0, line_no - 1 - context)
    end = min(len(all_lines), line_no + context)
    out = []
    for i in range(start, end):
        marker = ">>>" if (i + 1) == line_no else "   "
        out.append(f"{marker} {i + 1:>5} | {all_lines[i]}")
    return "\n".join(out)


def collect_error_messages(obj, bucket):
    """递归收集验证结果中所有疑似错误信息的字符串"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and k.lower() in (
                    "error", "errors", "message", "reason", "detail",
                    "details", "violation", "violations"):
                bucket.append(v)
            else:
                collect_error_messages(v, bucket)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            if isinstance(item, str):
                bucket.append(item)
            else:
                collect_error_messages(item, bucket)


def render_validation_result(result, xml_path):
    """把单文件验证结果渲染成Markdown: 总览 + 各验证器明细 + 错误定位片段"""
    lines = []
    success = bool(result.get("success"))
    icon = "✅ 通过" if success else "❌ 未通过"
    lines.append(f"### {icon} — `{Path(xml_path).name}`\n")

    # 各验证器明细 (兼容多种结果结构)
    detail = None
    for key in ("results", "validators", "details", "validation_results"):
        if isinstance(result.get(key), dict):
            detail = result[key]
            break
    if detail:
        lines.append("| 验证器 | 结果 | 信息 |")
        lines.append("|---|---|---|")
        for name, sub in detail.items():
            if isinstance(sub, dict):
                ok = sub.get("success", sub.get("passed", sub.get("valid")))
                status = "✅" if ok else ("❌" if ok is not None else "❓")
                errs = []
                collect_error_messages(sub, errs)
                info = ("; ".join(errs)[:200] or "-").replace("\n", " ")
            else:
                status = "✅" if sub else "❌"
                info = "-"
            lines.append(f"| {name} | {status} | {info} |")
        lines.append("")

    # 收集全部错误信息并做行号定位
    errors = []
    collect_error_messages(result, errors)
    errors = [e for e in dict.fromkeys(errors) if e]  # 去重保序

    if errors:
        lines.append(f"#### ⚠️ 错误详情 ({len(errors)}条)\n")
        located = 0
        for idx, err in enumerate(errors[:20], 1):  # 最多展示20条
            lines.append(f"**{idx}.** {err}\n")
            for ln in extract_error_lines(err)[:3]:
                located += 1
                lines.append(f"📍 定位到第 **{ln}** 行:")
                lines.append("```xml")
                lines.append(xml_context_snippet(xml_path, ln))
                lines.append("```")
        if len(errors) > 20:
            lines.append(f"\n... 其余 {len(errors) - 20} 条错误已省略")
        if located == 0:
            lines.append("\nℹ️ 错误信息中未包含行号，无法在源码中精确定位。")
    elif not success:
        lines.append("⚠️ 验证未通过，但未能从结果中解析出具体错误信息。\n")
        lines.append("原始结果:\n```\n" + repr(result)[:1500] + "\n```")

    return "\n".join(lines)


def run_validation(selected_files, uploaded_xml):
    """验证标签页的执行入口"""
    validator = get_validator()
    if validator is None:
        return (
            "## ❌ 验证模块不可用\n\n"
            f"```\n{_validator_error}\n```\n\n"
            "请检查:\n"
            "1. `src/validation/main_validator.py` 是否存在\n"
            "2. 依赖是否安装: `xmlschema`, `rdflib`, `pyshacl`, `pyyaml` "
            "(可选 `z3-solver`)\n"
            "3. `main_config.yaml` 是否包含 `file_paths` 配置"
        )

    targets = list(selected_files or [])
    if uploaded_xml:
        for f in uploaded_xml:
            targets.append(f if isinstance(f, str) else f.name)
    targets = [t for t in dict.fromkeys(targets) if Path(t).exists()]

    if not targets:
        return "ℹ️ 请先选择或上传要验证的 ARXML/XML 文件。"

    sections = [f"## 🔍 验证报告 ({len(targets)} 个文件)\n"]
    passed = 0
    for xml_path in targets:
        try:
            result = validator.validate_single_file(xml_path)
            if result.get("success"):
                passed += 1
            sections.append(render_validation_result(result, xml_path))
        except Exception as e:
            sections.append(
                f"### ❌ 验证异常 — `{Path(xml_path).name}`\n```\n{e}\n```")
        sections.append("\n---\n")

    summary = ("🎉 全部通过!" if passed == len(targets)
               else f"⚠️ {passed}/{len(targets)} 个文件通过验证")
    sections.insert(1, f"**总览**: {summary}\n")
    return "\n".join(sections)


def refresh_file_choices(state):
    files = list_validatable_files(state)
    return gr.update(choices=files, value=[])


# ===========================================================================
# 会话状态
# ===========================================================================

def new_state():
    return {
        "session_id": None,
        "stage": "idle",
        "feedback_count": 0,
        "documents": [],
        "round1_tokens": 0,
        "round2_tokens": 0,
        "output_files": [],
    }


def stats_markdown(state):
    sid = state["session_id"]
    sid_text = sid[:8] + "..." if sid else "无"
    total = state["round1_tokens"] + state["round2_tokens"]
    docs = state["documents"]
    docs_text = "\n".join(f"- {Path(p).name}" for p in docs) if docs else "无"
    return (
        f"**会话ID**: `{sid_text}`\n\n"
        f"**反馈轮次**: {state['feedback_count']} / {MAX_FEEDBACK_ROUNDS}\n\n"
        f"**Token 使用**\n"
        f"- Round 1: {state['round1_tokens']}\n"
        f"- Round 2: {state['round2_tokens']}\n"
        f"- 总计: {total}\n\n"
        f"**已上传文档**:\n{docs_text}"
    )


def ui_outputs(state, history, files_visible=None):
    stage_text = STAGE_LABELS.get(state["stage"], state["stage"])
    files = state["output_files"]
    return (
        history,
        state,
        stage_text,
        stats_markdown(state),
        gr.update(value=files if files else None,
                  visible=bool(files) if files_visible is None else files_visible),
    )


# ===========================================================================
# 文档上传
# ===========================================================================

def handle_upload(files, state, history):
    history = history or []
    if not files:
        return ui_outputs(state, history)

    if not getattr(generator, "file_upload_enabled", False):
        history.append({
            "role": "assistant",
            "content": ("❌ 文档上传功能未启用（当前为纯对话模式）。\n\n"
                        "请在配置文件中设置 `enable_file_upload: true` 后重启。"),
        })
        return ui_outputs(state, history)

    ok, failed = [], []
    for f in files:
        path = f if isinstance(f, str) else f.name
        try:
            is_valid, error_msg = generator.document_processor.validate_file(path)
            if is_valid:
                state["documents"].append(path)
                ok.append(Path(path).name)
            else:
                failed.append(f"{Path(path).name}: {error_msg}")
        except Exception as e:
            failed.append(f"{Path(path).name}: {e}")

    lines = ["## 📁 文档上传结果"]
    if ok:
        lines.append("✅ 成功: " + ", ".join(ok))
    if failed:
        lines.append("❌ 失败:\n" + "\n".join(f"- {x}" for x in failed))
    if state["documents"]:
        lines.append(f"\n📚 当前共 {len(state['documents'])} 个文档，"
                     "输入需求后系统将结合文档内容进行设计。")
    history.append({"role": "assistant", "content": "\n\n".join(lines)})
    return ui_outputs(state, history)


def clear_documents(state, history):
    history = history or []
    if not state["documents"]:
        history.append({"role": "assistant", "content": "ℹ️ 没有已上传的文档。"})
        return ui_outputs(state, history)
    try:
        if generator.document_processor:
            generator.document_processor.cleanup_all_files()
    except Exception:
        pass
    n = len(state["documents"])
    state["documents"].clear()
    history.append({"role": "assistant", "content": f"🗑️ 已清除 {n} 个文档。"})
    return ui_outputs(state, history)


# ===========================================================================
# 核心对话流程
# ===========================================================================

def run_round2(state, history, auto_validate):
    """执行 Round2; auto_validate=True 时完成后立即验证生成文件"""
    state["stage"] = "round2_running"
    history.append({"role": "assistant",
                    "content": "⚙️ Round 2: 正在查询KG、生成Schema并产出ARXML，请稍候..."})
    yield ui_outputs(state, history)

    result = generator.conversation_manager.process_round2(state["session_id"])

    state["round2_tokens"] = result.get("stats", {}).get("total_tokens", 0)
    output_files = [p for p in result.get("output_files", []) if Path(p).exists()]
    state["output_files"] = output_files

    files_text = "\n".join(f"- `{Path(p).name}`" for p in output_files) or "(无)"
    total_stats = result.get("total_stats", {})
    history[-1] = {
        "role": "assistant",
        "content": (
            "## 🎉 Round 2 完成\n\n"
            f"{result.get('message', '')}\n\n"
            f"### 📁 输出文件 ({len(output_files)}个)\n{files_text}\n\n"
            f"### 📈 会话统计\n"
            f"- 总Token: {total_stats.get('total_tokens', '-')}\n"
            f"- Round1 Token: {total_stats.get('round1_tokens', '-')}\n"
            f"- Round2 Token: {total_stats.get('round2_tokens', '-')}"
        ),
    }

    # ---- 自动验证生成的ARXML ----
    xml_outputs = [p for p in output_files
                   if p.lower().endswith((".arxml", ".xml"))]
    if auto_validate and xml_outputs:
        state["stage"] = "validating"
        history.append({"role": "assistant",
                        "content": f"🔍 正在验证 {len(xml_outputs)} 个生成的ARXML文件..."})
        yield ui_outputs(state, history)

        report = run_validation(xml_outputs, None)
        history[-1] = {"role": "assistant", "content": report}
        history.append({"role": "assistant",
                        "content": "💡 完整验证与错误定位可在 **🔍 验证** 标签页中查看和重跑。"})
    elif auto_validate:
        history.append({"role": "assistant",
                        "content": "ℹ️ 输出中没有 .arxml/.xml 文件，已跳过自动验证。"})

    state["stage"] = "done"
    history.append({"role": "assistant",
                    "content": "👉 可在右侧下载文件，或点击 **🔄 新建会话** 开始下一个设计。"})
    yield ui_outputs(state, history)


def process_message(message, history, state, auto_validate):
    history = history or []
    message = (message or "").strip()
    if not message:
        yield ui_outputs(state, history)
        return

    history.append({"role": "user", "content": message})

    try:
        # ---------- 新需求 -> 创建会话 + Round1 ----------
        if state["stage"] in ("idle", "done"):
            if state["stage"] == "done":
                docs = state["documents"]
                state.update(new_state())
                state["documents"] = docs

            state["stage"] = "round1_running"
            doc_hint = (f"(结合 {len(state['documents'])} 个文档)"
                        if state["documents"] else "")
            history.append({"role": "assistant",
                            "content": f"🏗️ Round 1: 正在进行架构设计{doc_hint}，请稍候..."})
            yield ui_outputs(state, history)

            kwargs = {"user_input": message, "user_id": "web_user"}
            if state["documents"] and getattr(generator, "file_upload_enabled", False):
                kwargs["document_files"] = state["documents"]
            result = generator.conversation_manager.start_conversation(**kwargs)
            state["session_id"] = result["session_id"]

            round1 = generator.conversation_manager.process_round1(state["session_id"])
            state["round1_tokens"] = round1.get("stats", {}).get("total_tokens", 0)
            state["stage"] = "awaiting_feedback"
            state["feedback_count"] = 0

            design = round1.get("design", {})
            comp_n = len(design.get("component_plan", []))
            intf_n = len(design.get("interface_plan", []))

            history[-1] = {
                "role": "assistant",
                "content": (
                    "## ✅ Round 1 架构设计完成\n\n"
                    f"🔧 设计结果: **{comp_n}** 个组件, **{intf_n}** 个接口\n\n"
                    f"{round1['presentation']}\n\n---\n\n"
                    f"{round1['confirmation_prompt']}\n\n"
                    "💡 可点击下方 **✅ 确认设计** 按钮，或直接输入修改意见，例如:"
                    "「修改组件名称为XXX」「增加一个传感器组件」「删除第二个接口」。"
                ),
            }
            yield ui_outputs(state, history)
            return

        # ---------- 等待反馈 ----------
        if state["stage"] == "awaiting_feedback":
            state["feedback_count"] += 1
            fb = generator.conversation_manager.handle_user_feedback(
                session_id=state["session_id"], feedback=message)

            history.append({"role": "assistant", "content": fb["response"]})
            yield ui_outputs(state, history)

            if fb["can_proceed"]:
                yield from run_round2(state, history, auto_validate)
            elif state["feedback_count"] >= MAX_FEEDBACK_ROUNDS:
                history.append({
                    "role": "assistant",
                    "content": (f"⚠️ 已达到最大反馈轮次 ({MAX_FEEDBACK_ROUNDS})。\n\n"
                                "可点击 **⏭️ 使用当前设计继续** 强制进入 Round 2，"
                                "或点击 **🔄 新建会话** 重新开始。"),
                })
                yield ui_outputs(state, history)
            else:
                history.append({
                    "role": "assistant",
                    "content": (f"📝 请继续提供反馈 "
                                f"({state['feedback_count']}/{MAX_FEEDBACK_ROUNDS})，"
                                "或点击 **✅ 确认设计**。"),
                })
                yield ui_outputs(state, history)
            return

        history.append({"role": "assistant",
                        "content": "⏳ 当前任务仍在执行，请等待完成后再操作。"})
        yield ui_outputs(state, history)

    except Exception as e:
        state["stage"] = "awaiting_feedback" if state["session_id"] else "idle"
        history.append({
            "role": "assistant",
            "content": (f"❌ 发生错误:\n```\n{e}\n```\n"
                        "可重试上一步操作，或点击 **🔄 新建会话** 重新开始。"),
        })
        traceback.print_exc()
        yield ui_outputs(state, history)


def confirm_design(history, state, auto_validate):
    if state["stage"] != "awaiting_feedback":
        history = history or []
        history.append({"role": "assistant",
                        "content": "ℹ️ 当前没有等待确认的设计。"})
        yield ui_outputs(state, history)
        return
    yield from process_message("确认", history, state, auto_validate)


def force_proceed(history, state, auto_validate):
    history = history or []
    if state["stage"] != "awaiting_feedback" or not state["session_id"]:
        history.append({"role": "assistant",
                        "content": "ℹ️ 当前没有可强制继续的设计。"})
        yield ui_outputs(state, history)
        return
    try:
        from src.llm_generation.core.conversation_manager import ConversationState
        session_info = generator.conversation_manager._get_session_info(
            state["session_id"])
        if session_info:
            session_info["state"] = ConversationState.ROUND1_COMPLETED
            session_info["final_confirmation_time"] = time.time()
        history.append({"role": "assistant", "content": "✅ 设计已强制确认。"})
        yield from run_round2(state, history, auto_validate)
    except Exception as e:
        history.append({"role": "assistant",
                        "content": f"❌ 强制确认失败: {e}"})
        yield ui_outputs(state, history)


def reset_session(state):
    try:
        if state["session_id"]:
            generator.conversation_manager.cleanup_session(state["session_id"])
    except Exception:
        pass
    state = new_state()
    history = [{"role": "assistant",
                "content": "🔄 已新建会话。请输入需求描述，或先上传文档。"}]
    return ui_outputs(state, history, files_visible=False)


# ===========================================================================
# 界面布局
# ===========================================================================

with gr.Blocks(title="AUTOSAR ARXML Generator") as demo:

    gr.Markdown(
        "# 🚗 AUTOSAR ARXML Generator\n"
        "**Round 1** 架构设计(可多轮反馈) → **Round 2** 生成ARXML → **验证** XSD/SHACL/SMT"
    )

    state = gr.State(new_state())
    stage_badge = gr.Markdown(STAGE_LABELS["idle"])

    with gr.Tabs():
        # =================== Tab 1: 生成 ===================
        with gr.Tab("💬 生成"):
            with gr.Row():
                with gr.Column(scale=3):
                    chatbot = gr.Chatbot(height=560, buttons=["copy"])

                    msg = gr.Textbox(
                        placeholder="请描述AUTOSAR组件需求，或对架构设计提出反馈...",
                        show_label=False, lines=2,
                    )
                    with gr.Row():
                        send_btn = gr.Button("📤 发送", variant="primary")
                        confirm_btn = gr.Button("✅ 确认设计")
                        force_btn = gr.Button("⏭️ 使用当前设计继续")
                        reset_btn = gr.Button("🔄 新建会话")

                    gr.Examples(examples=EXAMPLE_PROMPTS, inputs=msg,
                                label="💡 示例需求")

                with gr.Column(scale=1):
                    auto_validate_cb = gr.Checkbox(
                        value=True,
                        label="Round 2 完成后自动验证ARXML",
                    )
                    with gr.Accordion("📁 上传需求文档", open=True):
                        gr.Markdown("支持 PDF / Word / TXT / MD / 图片，最大20MB")
                        doc_upload = gr.File(
                            file_count="multiple",
                            file_types=[".pdf", ".doc", ".docx", ".txt", ".md",
                                        ".png", ".jpg", ".jpeg", ".gif", ".webp"],
                            label="拖拽或点击上传",
                        )
                        clear_docs_btn = gr.Button("🗑️ 清除已上传文档", size="sm")

                    output_files = gr.Files(label="📦 生成的文件 (点击下载)",
                                            visible=False, interactive=False)
                    stats_panel = gr.Markdown(stats_markdown(new_state()))

        # =================== Tab 2: 验证 ===================
        with gr.Tab("🔍 验证"):
            gr.Markdown(
                "## ARXML 验证 (XSD Schema / SHACL Shapes / SMT 约束)\n"
                "选择本次生成的文件或上传XML进行验证；"
                "验证未通过时会自动从错误信息提取行号并显示出错位置的源码片段。"
            )
            with gr.Row():
                with gr.Column(scale=1):
                    file_choices = gr.CheckboxGroup(
                        choices=list_validatable_files(),
                        label="选择要验证的文件",
                    )
                    refresh_btn = gr.Button("🔄 刷新文件列表", size="sm")
                    xml_upload = gr.File(
                        file_count="multiple",
                        file_types=[".arxml", ".xml"],
                        label="或上传 ARXML/XML 文件",
                    )
                    validate_btn = gr.Button("🚀 开始验证", variant="primary")
                with gr.Column(scale=2):
                    validation_report = gr.Markdown(
                        "ℹ️ 验证结果将显示在这里。")

    # ---------------- 事件绑定 ----------------
    outputs = [chatbot, state, stage_badge, stats_panel, output_files]
    chat_inputs = [msg, chatbot, state, auto_validate_cb]

    msg.submit(fn=process_message, inputs=chat_inputs,
               outputs=outputs).then(lambda: "", outputs=msg)
    send_btn.click(fn=process_message, inputs=chat_inputs,
                   outputs=outputs).then(lambda: "", outputs=msg)

    confirm_btn.click(fn=confirm_design,
                      inputs=[chatbot, state, auto_validate_cb],
                      outputs=outputs)
    force_btn.click(fn=force_proceed,
                    inputs=[chatbot, state, auto_validate_cb],
                    outputs=outputs)
    reset_btn.click(fn=reset_session, inputs=state, outputs=outputs)

    doc_upload.upload(fn=handle_upload, inputs=[doc_upload, state, chatbot],
                      outputs=outputs)
    clear_docs_btn.click(fn=clear_documents, inputs=[state, chatbot],
                         outputs=outputs)

    refresh_btn.click(fn=refresh_file_choices, inputs=state,
                      outputs=file_choices)
    validate_btn.click(fn=run_validation,
                       inputs=[file_choices, xml_upload],
                       outputs=validation_report)


if __name__ == "__main__":
    demo.queue()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        theme=gr.themes.Soft(),   # Gradio 6: theme 移到 launch()
    )