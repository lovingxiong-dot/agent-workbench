"""agent_workbench/ui/workbench/trace_event_registry.py — TraceEvent 显示元数据注册表。

职责：
- 为每个 TraceEvent 提供 UI 无关的显示元数据（label / icon / level / status）。
- UI 不维护字符串映射，新增事件只需在此注册即可自动渲染。

设计边界：
- 元数据只描述 Runtime 事件，不包含 editor/inspector/widget/dock 等 UI 概念。
- level 来自 v6.runtime.enums.TRACE_EVENT_LEVEL，保证 Runtime 与 UI 一致。
"""
from __future__ import annotations

from typing import Any, Dict

from v6.runtime.enums import TRACE_EVENT_LEVEL, TraceEvent


# 事件默认显示元数据。后续可扩展 color / severity / group / order。
TRACE_EVENT_META: Dict[str, Dict[str, Any]] = {
    TraceEvent.TASK_START.value: {
        "label": "Task Start",
        "icon": "▶",
        "status": "running",
    },
    TraceEvent.TASK_FINISH.value: {
        "label": "Task Finish",
        "icon": "✓",
        "status": "success",
    },
    TraceEvent.TASK_ERROR.value: {
        "label": "Task Failed",
        "icon": "✕",
        "status": "failed",
    },
    TraceEvent.CAPABILITY_RESOLVED.value: {
        "label": "Capability Resolved",
        "icon": "◎",
        "status": "success",
    },
    TraceEvent.ENGINE_SELECTED.value: {
        "label": "Engine Selected",
        "icon": "⚙",
        "status": "success",
    },
    TraceEvent.ENGINE_START.value: {
        "label": "Engine Start",
        "icon": "⚙",
        "status": "running",
    },
    TraceEvent.ENGINE_END.value: {
        "label": "Engine End",
        "icon": "⚙",
        "status": "success",
    },
    TraceEvent.EXECUTION_STARTED.value: {
        "label": "Execution Started",
        "icon": "➤",
        "status": "running",
    },
    TraceEvent.EXECUTION_PROGRESS.value: {
        "label": "Execution Progress",
        "icon": "···",
        "status": "running",
    },
    TraceEvent.EXECUTION_FINISHED.value: {
        "label": "Execution Finished",
        "icon": "✓",
        "status": "success",
    },
    TraceEvent.PROVIDER_SELECTED.value: {
        "label": "Provider Selected",
        "icon": "☁",
        "status": "success",
    },
    TraceEvent.SERVICE_SELECTED.value: {
        "label": "Service Selected",
        "icon": "☁",
        "status": "success",
    },
    TraceEvent.MODEL_SELECTED.value: {
        "label": "Model Selected",
        "icon": "◇",
        "status": "success",
    },
    TraceEvent.REQUEST_SENT.value: {
        "label": "Request Sent",
        "icon": "➤",
        "status": "success",
    },
    TraceEvent.FIRST_TOKEN.value: {
        "label": "First Token",
        "icon": "⚡",
        "status": "success",
    },
    TraceEvent.CHUNK_RECEIVED.value: {
        "label": "Chunk",
        "icon": "···",
        "status": "success",
    },
    TraceEvent.STREAM_FINISHED.value: {
        "label": "Stream Finished",
        "icon": "✓",
        "status": "success",
    },
    TraceEvent.ENGINE_INPUT_READ.value: {
        "label": "Input Read",
        "icon": "➤",
        "status": "success",
    },
}


def get_trace_event_meta(action: str) -> Dict[str, Any]:
    """获取指定 TraceEvent 的显示元数据；未注册时返回默认值。"""
    meta = TRACE_EVENT_META.get(action, {
        "label": action.replace("_", " ").title(),
        "icon": "•",
        "status": "success",
    })
    # 从 Runtime 层级映射补全 level，保证 UI 与 Runtime 一致。
    try:
        level = TRACE_EVENT_LEVEL.get(TraceEvent(action), "runtime")
    except ValueError:
        level = "runtime"
    result = dict(meta)
    result["level"] = level
    return result


def status_icon(status: str) -> str:
    """根据状态返回展示图标。"""
    mapping = {
        "pending": "○",
        "running": "●",
        "success": "✓",
        "failed": "✕",
    }
    return mapping.get(status, "•")
