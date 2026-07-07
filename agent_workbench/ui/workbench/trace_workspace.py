"""agent_workbench/ui/workbench/trace_workspace.py — Trace Workspace UI。

职责：
- 以 Tree 形式实时展示 Runtime Trace 事件。
- 列：Status / Time / Node / Action / Phase / Duration / Details。
- 根据 parent_id 构建层级，支持未来 Replay / Metrics / Timeline。

设计边界：
- UI 不拥有 Trace 数据，只作为观察者渲染。
- 显示元数据来自 trace_event_registry，不硬编码字符串映射。
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict

from PySide6.QtWidgets import (
    QHeaderView,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from agent_workbench.ui.workbench.trace_event_registry import (
    get_trace_event_meta,
    status_icon,
)


class TraceWorkspaceItem(QWidget):
    """Trace Workspace：树形展示 Runtime Trace。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._tree = QTreeWidget(self)
        self._tree.setColumnCount(7)
        self._tree.setHeaderLabels(
            ["Status", "Time", "Node", "Action", "Phase", "Duration", "Details"]
        )
        self._tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._tree.header().setStretchLastSection(True)
        self._tree.setAlternatingRowColors(True)

        self._layout.addWidget(self._tree)

        # step_id -> QTreeWidgetItem，用于按 parent_id 挂载子节点。
        self._items: Dict[str, QTreeWidgetItem] = {}

    def clear(self) -> None:
        """清空 Tree。"""
        self._tree.clear()
        self._items.clear()

    def append_event(self, step: Dict[str, Any]) -> None:
        """追加单条 TraceStep 到 Tree。

        Args:
            step: TraceStep 序列化后的字典。
        """
        action = step.get("action", "")
        meta = get_trace_event_meta(action)
        status = step.get("status") or meta.get("status", "success")

        item = QTreeWidgetItem()
        item.setText(0, status_icon(status))
        item.setText(1, self._format_time(step.get("timestamp", 0)))
        item.setText(2, str(step.get("node", "")))
        item.setText(3, meta.get("label", action))
        item.setText(4, str(step.get("phase", "")))
        item.setText(5, self._format_duration(step.get("duration_ms", 0.0)))
        item.setText(6, self._format_details(step.get("payload", {})))
        item.setToolTip(6, json.dumps(step.get("payload", {}), ensure_ascii=False, indent=2))

        step_id = step.get("step_id", "")
        parent_id = step.get("parent_id", "")
        self._items[step_id] = item

        if parent_id and parent_id in self._items:
            self._items[parent_id].addChild(item)
            self._items[parent_id].setExpanded(True)
        else:
            self._tree.addTopLevelItem(item)

        self._tree.scrollToBottom()

    def load_timeline(self, steps: list[Dict[str, Any]]) -> None:
        """加载完整 Timeline。"""
        self.clear()
        # 先按时间顺序添加，保证 parent 已存在。
        for step in steps:
            self.append_event(step)

    @staticmethod
    def _format_time(timestamp: float) -> str:
        if not timestamp:
            return "—"
        return time.strftime("%H:%M:%S", time.localtime(timestamp))

    @staticmethod
    def _format_duration(duration_ms: float) -> str:
        if not duration_ms:
            return "—"
        return f"{duration_ms:.1f}ms"

    @staticmethod
    def _format_details(payload: Dict[str, Any]) -> str:
        if not payload:
            return ""
        # 对 Chunk 事件做摘要，避免 Details 列过长。
        if "sequence" in payload and "chunk_length" in payload:
            return f"#{payload['sequence']} ({payload['chunk_length']} chars)"
        if "elapsed_ms" in payload:
            return f"{payload['elapsed_ms']:.1f}ms"
        # 对其他 payload 取前几个关键字段。
        summary = []
        for key in ("capability", "provider", "model", "service", "engine", "status", "messages_count"):
            if key in payload:
                summary.append(f"{key}={payload[key]}")
        if summary:
            return ", ".join(summary)
        text = json.dumps(payload, ensure_ascii=False)
        if len(text) > 80:
            text = text[:77] + "..."
        return text
