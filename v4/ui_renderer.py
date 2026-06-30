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
    def __init__(self, message_bus, chat_view, status_indicator=None, conversation_list=None, capacity_label=None, queue_bar=None, current_session_provider=None, parent=None):
        super().__init__(parent)
        self._bus = message_bus
        self._chat_view = chat_view
        self._status_indicator = status_indicator
        self._conversation_list = conversation_list
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
        """从 AI 回复提取思考过程，返回 (折叠 HTML, 剩余正文)。"""
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
            f'<div class="fold-block" id="{fold_id}">'
            f'<a class="fold-header" href="fold://toggle/{fold_id}">▶ 思考过程  [{done}/{total} 已完成]</a>'
            f'<div class="fold-body" id="{fold_id}-body">{task_html}</div></div>'
        )
        return html_fold, "\n".join(body_lines).strip()

    def _build_tool_fold(self, event) -> str:
        """构建工具执行折叠块。"""
        name = event.tool_name or "unknown"
        elapsed = event.elapsed_ms or 0
        success = getattr(event, "success", True)
        icon = "✓" if success else "✗"
        cls = "tool-ok" if success else "tool-fail"
        args_json = html.escape(json.dumps(event.args or {}, ensure_ascii=False, indent=2))
        result_text = event.result or ""
        fold_id = f"tool-{id(event)}"

        output_fold = ""
        if len(result_text) > 200:
            preview = html.escape(result_text[:200])
            full = html.escape(result_text)
            lines = result_text.count("\n") + 1
            output_fold = (
                f'<div class="fold-block" id="{fold_id}-out">'
                f'<a class="fold-header" href="fold://toggle/{fold_id}-out">▶ 内部命令输出  [{lines} 行]</a>'
                f'<div class="fold-body" id="{fold_id}-out-body"><pre class="cmd-full">{full}</pre></div></div>'
            )
        else:
            output_fold = f'<pre class="cmd-output">{html.escape(result_text)}</pre>'

        return (
            f'<div class="tool-entry {cls}">'
            f'<span class="tool-icon">{icon}</span>'
            f'<span class="tool-name">{html.escape(name)}</span>'
            f'<span class="tool-time">{elapsed}ms</span>'
            f'<div class="fold-block" id="{fold_id}">'
            f'<a class="fold-header" href="fold://toggle/{fold_id}">▶ 参数</a>'
            f'<div class="fold-body" id="{fold_id}-body"><pre class="tool-args">{args_json}</pre></div></div>'
            f'</div>'
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
                border_color = getattr(self._chat_view, "_theme", {}).get("border", "#3e3e42")
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
            try: self._conversation_list.refresh(event.sessions)
            except: pass

    def _handle_update_session_badge(self, event):
        if self._conversation_list:
            try: self._conversation_list.update_badge(event.session_id, event.phase)
            except: pass
