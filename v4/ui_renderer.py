"""
ui_renderer.py — v4 UI 渲染器

订阅 MessageBus 的 ui.* 事件，统一更新：
- ChatView（当前会话的消息、流式、Phase UI）
- 状态栏 / capacity 指示器
- ConversationList（会话状态徽章）

原则：只处理 UI 表现，不持有业务状态。
事件过滤：只处理当前会话的事件，其余丢弃。
"""
import html
import json
import re
from typing import Callable, Optional
from PySide6.QtCore import QObject

from .event_bus import MessageBus
from .events import *


class UIRenderer(QObject):
    def __init__(self, message_bus, chat_view, status_indicator=None, conversation_list=None, right_panel=None, capacity_label=None, queue_bar=None, current_session_provider=None, parent=None):
        super().__init__(parent)
        self._bus = message_bus
        self._chat_view = chat_view
        self._status_indicator = status_indicator
        self._conversation_list = conversation_list
        self._right_panel = right_panel
        self._capacity_label = capacity_label
        self._queue_bar = queue_bar
        self._current_session_provider = current_session_provider
        self._bus.subscribe_namespace("ui", self._on_ui_event)

    def _current_session_id(self):
        return self._current_session_provider() if self._current_session_provider else None

    def _is_current(self, event):
        return event.session_id == self._current_session_id()

    def _on_ui_event(self, event):
        handler = getattr(self, f"_handle_{event.name}", None)
        if handler:
            try:
                handler(event)
            except Exception as e:
                print(f"UIRenderer error: {e}", flush=True)

    def _handle_append_user(self, event):
        if self._is_current(event): self._chat_view.append_user(event.text)

    def _handle_append_system(self, event):
        if self._is_current(event): self._chat_view.append_system(event.text)

    def _handle_stream_chunk(self, event):
        if self._is_current(event): self._chat_view.append_chunk(event.chunk)

    def _handle_finalize_stream(self, event):
        if self._is_current(event): self._chat_view.finalize_stream()

    def _handle_set_streaming(self, event):
        if self._is_current(event): self._chat_view.set_streaming(event.active)

    def _handle_clear_phase(self, event):
        if self._is_current(event): self._chat_view.clear_phase_ui()

    def _handle_clear_chat(self, event):
        if self._is_current(event): self._chat_view.clear_chat()

    def _handle_show_confirm(self, event):
        if self._is_current(event): self._chat_view.show_confirmation(event.task_list)

    def _handle_hide_confirm(self, event):
        if self._is_current(event): self._chat_view.hide_confirmation()

    def _handle_set_send_enabled(self, event):
        if self._is_current(event) and hasattr(self._chat_view, "set_send_enabled"):
            self._chat_view.set_send_enabled(event.enabled)

    def _handle_update_queue_bar(self, event):
        if self._is_current(event) and self._queue_bar:
            self._queue_bar.setVisible(event.visible)
            if event.visible: self._queue_bar.setText(event.bar_text)

    def _handle_focus_input(self, event):
        if self._is_current(event) and hasattr(self._chat_view, "input_field"):
            self._chat_view.input_field.setFocus()

    # ── 右栏事件处理 ──────────────────────────────────

    def _handle_open_file(self, event):
        if self._right_panel and event.path:
            try:
                self._right_panel.open_file(event.path)
            except Exception as e:
                print(f"UIRenderer open_file error: {e}", flush=True)

    def _handle_update_terminal(self, event):
        if self._right_panel:
            try:
                self._right_panel.update_terminal(event.text)
            except Exception as e:
                print(f"UIRenderer update_terminal error: {e}", flush=True)

    def _handle_right_panel_tab(self, event):
        if self._right_panel and event.tab_name:
            try:
                self._right_panel.switch_tab(event.tab_name)
            except Exception as e:
                print(f"UIRenderer right_panel_tab error: {e}", flush=True)

    def _handle_load_url(self, event):
        if self._right_panel and event.url:
            try:
                self._right_panel.load_url(event.url)
            except Exception as e:
                print(f"UIRenderer load_url error: {e}", flush=True)

    def _handle_update_file_reader(self, event):
        if not self._right_panel:
            return
        try:
            if event.path:
                self._right_panel.file_reader.open_file(event.path)
            elif event.content:
                self._right_panel.file_reader.set_content(event.content)
        except Exception as e:
            print(f"UIRenderer update_file_reader error: {e}", flush=True)

    def _handle_analyze_project(self, event):
        """触发「帮我分析当前项目」：向当前会话发送用户消息。"""
        sid = self._current_session_id() or event.session_id
        if sid:
            self._bus.emit(UserSendEvent(
                session_id=sid,
                user_text="帮我分析当前项目",
            ))

    # ── 折叠渲染辅助 ──────────────────────────────────

    def _parse_execute_steps(self, text: str) -> list[dict]:
        """从 AI execute 文本中解析步骤列表。

        匹配模式:
        - ✓ / [x] / done → 状态 done
        - ⟳ / ▶ / running → 状态 running
        - ○ / [ ] / pending → 状态 pending

        返回: [{"status": "done|running|pending", "name": "...", "detail": "..."}, ...]
        """
        lines = text.split("\n")
        steps = []
        step_pattern = re.compile(
            r'^\s*(?P<icon>✓|⟳|▶|○|✔|✗|❌|⏳)\s+(?P<name>.+?)(?:\s*[-–—]\s*(?P<detail>.+))?\s*$'
        )
        # 也匹配 markdown checkbox: - [x] ... / - [ ] ...
        checkbox_pattern = re.compile(
            r'^\s*-?\s*\[(?P<mark>[xX\s])\]\s+(?P<name>.+?)(?:\s*[-–—]\s*(?P<detail>.+))?\s*$'
        )
        for line in lines:
            m = step_pattern.match(line)
            if m:
                icon = m.group("icon")
                if icon in ("✓", "✔"):
                    status = "done"
                elif icon in ("⟳", "▶", "⏳"):
                    status = "running"
                elif icon in ("○",):
                    status = "pending"
                elif icon in ("✗", "❌"):
                    status = "fail"
                else:
                    status = "pending"
                steps.append({
                    "status": status,
                    "name": m.group("name").strip(),
                    "detail": (m.group("detail") or "").strip(),
                })
                continue
            m = checkbox_pattern.match(line)
            if m:
                status = "done" if m.group("mark").lower() == "x" else "pending"
                steps.append({
                    "status": status,
                    "name": m.group("name").strip(),
                    "detail": (m.group("detail") or "").strip(),
                })
        return steps

    def _build_step_bar(self, steps: list[dict]) -> str:
        """将步骤列表渲染为步骤条 HTML。"""
        if not steps:
            return ""
        icons = {"done": "✓", "running": "⟳", "pending": "○", "fail": "✗"}
        rows = []
        for s in steps:
            icon = icons.get(s["status"], "○")
            name = html.escape(s["name"])
            detail = f' <span class="step-detail">{html.escape(s["detail"])}</span>' if s["detail"] else ""
            rows.append(f'<div class="step {s["status"]}"><span class="step-icon">{icon}</span> <span class="step-name">{name}</span>{detail}</div>')
        return "".join(rows)

    def _build_thinking_fold(self, ai_text: str) -> tuple[str, str]:
        """从 AI 回复提取思考过程，返回 (折叠 HTML, 剩余正文)。
        
        精确对齐 SVG：
        ┌─ 362×22 rx=4 fill=#16213e ───────────────┐
        │ ▶ 思考过程                    [5/7 已完成] │
        └───────────────────────────────────────────┘
        """
        lines = ai_text.split("\n")
        tasks = []
        in_thinking = False
        body_lines = []
        for line in lines:
            stripped = line.strip()
            if re.search(r"(思考过程|Thinking|thought process)", stripped, re.IGNORECASE):
                in_thinking = True
                continue
            if in_thinking:
                if any(stripped.startswith(p) for p in ("[x]", "[ ]", "✓", "✗", "- [x]", "- [ ]")):
                    tasks.append(stripped)
                    continue
                if stripped == "":
                    in_thinking = False
            body_lines.append(line)

        if not tasks:
            return "", ai_text

        done = sum(1 for t in tasks if any(k in t for k in ("[x]", "✓", "- [x]")))
        total = len(tasks)

        task_html = "\n".join(
            f'<div class="think-task {"done" if any(k in t for k in ("[x]", "✓", "- [x]")) else ""}">{html.escape(t)}</div>'
            for t in tasks
        )
        fold_id = f"think-{id(tasks)}"
        html_fold = (
            f'<div class="fold-block" id="{fold_id}" style="border-radius:4px;">'
            f'<a class="fold-header" href="fold://toggle/{fold_id}" style="display:block;padding:4px 8px;">'
            f'▶ 思考过程 <span style="font-size:10px;color:#6a6a8a;margin-left:8px;">[{done}/{total} 已完成]</span></a>'
            f'<div class="fold-body" id="{fold_id}-body" style="padding:4px 8px;">{task_html}</div></div>'
        )
        return html_fold, "\n".join(body_lines).strip()

    def _build_tool_fold(self, event) -> str:
        """构建工具执行条目，精确对齐 SVG：
        ┌─ 4px 左 bar ─┬─ ✓ run_command ─── 0.8s ─ ▶ 参数 ─┐
        """
        name = event.tool_name or "unknown"
        elapsed = event.elapsed_ms or 0
        elapsed_s = f"{elapsed / 1000:.1f}s" if elapsed >= 100 else f"{elapsed}ms"
        success = getattr(event, "success", True)
        icon = "✓" if success else "✗"
        icon_color = "#4ec9b0" if success else "#f14c4c"
        args_json = html.escape(json.dumps(event.args or {}, ensure_ascii=False, indent=2))
        result_text = event.result or ""
        fold_id = f"tool-{id(event)}"

        # 内部命令输出折叠块（SVG: collapsed 22px bar）
        output_fold = ""
        if len(result_text) > 200:
            preview = html.escape(result_text[:200])
            full = html.escape(result_text)
            lines = result_text.count("\n") + 1
            output_fold = (
                f'<div class="fold-block" id="{fold_id}-out" style="border-radius:4px;">'
                f'<a class="fold-header" href="fold://toggle/{fold_id}-out" style="display:block;padding:4px 8px;">'
                f'▶ 内部命令输出 <span style="font-size:10px;color:#6a6a8a;margin-left:8px;">[{lines} 行]</span></a>'
                f'<div class="fold-body" id="{fold_id}-out-body"><pre class="cmd-full">{full}</pre></div></div>'
            )
        elif result_text:
            output_fold = f'<pre class="cmd-output">{html.escape(result_text)}</pre>'

        # 参数折叠块
        args_fold = (
            f'<a class="fold-header" href="fold://toggle/{fold_id}" '
            f'style="display:inline;color:#569cd6;font-size:9px;font-family:\'Cascadia Code\',Consolas,monospace;'
            f'text-decoration:none;cursor:pointer;">▶ 参数</a>'
            f'<div class="fold-block" id="{fold_id}" style="border-radius:4px;display:inline;">'
            f'<div class="fold-body" id="{fold_id}-body"><pre class="tool-args">{args_json}</pre></div></div>'
        )

        # SVG 对齐：table 布局，4px 左边条 + 工具条目行
        return (
            f'<table cellspacing="0" cellpadding="0" border="0" style="margin:0;">'
            f'<tr>'
            f'<td style="width:4px;background-color:#2a2a4a;border-radius:2px;"></td>'
            f'<td style="padding:1px 8px;font-family:\'Cascadia Code\',Consolas,monospace;font-size:10px;">'
            f'<span style="color:{icon_color};">{icon}</span> '
            f'<span style="color:#d4d4d4;">{html.escape(name)}</span> '
            f'<span style="color:#6a6a8a;font-size:9px;">{elapsed_s}</span> '
            f'{args_fold}'
            f'</td>'
            f'</tr>'
            f'</table>'
            f'{output_fold}'
        )

    # ── 事件处理覆写 ──────────────────────────────────

    def _handle_append_ai(self, event):
        if not self._is_current(event):
            return
        text = event.text or ""
        thinking_fold, body = self._build_thinking_fold(text)
        phase = getattr(self, "_current_phase", "")

        # execute 阶段：解析步骤条，插入阶段面板
        if phase == "execute":
            steps = self._parse_execute_steps(body)
            if steps:
                step_html = self._build_step_bar(steps)
                border_color = getattr(self._chat_view, "_theme", {}).get("border", "#cccccc")
                body = step_html if not body.strip() else f'{step_html}<hr style="border:0.5px solid {border_color};margin:8px 0;">{body}'

        self._chat_view.append_ai(body, phase=phase, thinking_fold=thinking_fold)

    def _handle_append_tool(self, event):
        if not self._is_current(event):
            return
        tool_html = self._build_tool_fold(event)
        self._chat_view.append_tool_fold(tool_html)

    def _handle_set_phase(self, event):
        if not self._is_current(event):
            return
        self._current_phase = event.phase
        if hasattr(self._chat_view, "set_phase_indicator"):
            self._chat_view.set_phase_indicator(event.phase, event.task_count)
        if hasattr(self._chat_view, "set_current_phase"):
            self._chat_view.set_current_phase(event.phase)

    def _handle_set_active_session(self, event):
        if self._conversation_list:
            try:
                self._conversation_list.set_active_session(event.active_session_id)
            except Exception as e:
                print(f"UIRenderer set_active_session error: {e}", flush=True)

    def _handle_update_session_list(self, event):
        if self._conversation_list:
            try:
                self._conversation_list.refresh(event.sessions)
            except Exception as e:
                print(f"UIRenderer update_session_list error: {e}", flush=True)

    def _handle_update_session_badge(self, event):
        if self._conversation_list:
            try: self._conversation_list.update_badge(event.session_id, event.phase)
            except: pass
