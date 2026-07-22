"""agent_workbench/runtime/interaction/mapper.py — RuntimeEvent → InteractionEvent 转换器。

职责：
- 将内部 RuntimeEventType 翻译为 UI 层 InteractionEventType。
- 不依赖任何 UI 渲染实现，也不直接调用 Renderer。
- 只返回 InteractionEvent 或 None（无法识别的事件）。
"""
from __future__ import annotations

from v6.runtime.event_bus import RuntimeEvent, RuntimeEventType

from agent_workbench.presentation.protocols.interaction.event import InteractionEvent, InteractionEventType


class RuntimeEventMapper:
    """Runtime 事件到 UI 事件的映射器。"""

    def map(self, event: RuntimeEvent) -> InteractionEvent | None:
        """将 RuntimeEvent 转换为 InteractionEvent。

        无法识别或不关心的事件返回 None。
        payload 为 None 时按空 dict 处理；source 缺失时回退为 "unknown"。
        """
        payload = event.payload if isinstance(event.payload, dict) else {}
        request_id = self._extract_request_id(event)
        source = payload.get("source") or "unknown"

        match event.type:
            case RuntimeEventType.USER_MESSAGE:
                return InteractionEvent(
                    type=InteractionEventType.MESSAGE_USER,
                    request_id=request_id,
                    source=source,
                    task_id=event.task_id,
                    payload={"text": payload.get("text", "")},
                )
            case RuntimeEventType.AI_CHUNK:
                return InteractionEvent(
                    type=InteractionEventType.MESSAGE_DELTA,
                    request_id=request_id,
                    source=source,
                    task_id=event.task_id,
                    payload={"text": payload.get("text", "")},
                )
            case RuntimeEventType.AI_END:
                return InteractionEvent(
                    type=InteractionEventType.MESSAGE_COMPLETE,
                    request_id=request_id,
                    source=source,
                    task_id=event.task_id,
                    payload={
                        "text": payload.get("text"),
                        "status": payload.get("status", "completed"),
                    },
                )
            case RuntimeEventType.TASK_STARTED:
                return InteractionEvent(
                    type=InteractionEventType.TASK_STARTED,
                    request_id=request_id,
                    source=source,
                    task_id=event.task_id,
                    payload={"task_type": payload.get("task_type")},
                )
            case RuntimeEventType.TASK_COMPLETED | RuntimeEventType.TASK_FAILED:
                return InteractionEvent(
                    type=InteractionEventType.TASK_FINISHED,
                    request_id=request_id,
                    source=source,
                    task_id=event.task_id,
                    payload={"status": "completed" if event.type == RuntimeEventType.TASK_COMPLETED else "failed"},
                )
            case RuntimeEventType.CAPABILITY_CHAIN_STEP_STARTED:
                return InteractionEvent(
                    type=InteractionEventType.CAPABILITY_STEP,
                    request_id=request_id,
                    source=source,
                    task_id=event.task_id,
                    payload={
                        "index": payload.get("step_index", 0),
                        "capability_id": payload.get("capability_id"),
                        "total": payload.get("total_steps", 1),
                    },
                )
            case RuntimeEventType.ENGINE_SELECTED | RuntimeEventType.PROVIDER_SELECTED | RuntimeEventType.EXECUTION_STARTED:
                return InteractionEvent(
                    type=InteractionEventType.STATUS_UPDATE,
                    request_id=request_id,
                    source=source,
                    task_id=event.task_id,
                    payload=self._build_status_payload(event),
                )
            case RuntimeEventType.TOOL_STARTED:
                return InteractionEvent(
                    type=InteractionEventType.TOOL_STARTED,
                    request_id=request_id,
                    source=source,
                    task_id=event.task_id,
                    payload={
                        "name": payload.get("tool") or payload.get("name"),
                        "args": payload.get("args", {}),
                    },
                )
            case RuntimeEventType.TOOL_COMPLETED:
                return InteractionEvent(
                    type=InteractionEventType.TOOL_COMPLETED,
                    request_id=request_id,
                    source=source,
                    task_id=event.task_id,
                    payload={
                        "name": payload.get("tool") or payload.get("name"),
                        "result": payload.get("result", {}),
                        "status": payload.get("status", "ok"),
                    },
                )
            case RuntimeEventType.ENGINE_FAILED | RuntimeEventType.TOOL_FAILED | RuntimeEventType.ERROR:
                return InteractionEvent(
                    type=InteractionEventType.ERROR,
                    request_id=request_id,
                    source=source,
                    task_id=event.task_id,
                    payload={"message": self._extract_error_message(event)},
                )
            case _:
                return None

    @staticmethod
    def _extract_request_id(event: RuntimeEvent) -> str:
        """从 payload 中提取 request_id，没有则回退到 task_id。"""
        if isinstance(event.payload, dict):
            return event.payload.get("request_id") or event.task_id or "unknown"
        return event.task_id or "unknown"

    @staticmethod
    def _build_status_payload(event: RuntimeEvent) -> dict:
        """为 STATUS_UPDATE 构造可读的 title/details。"""
        payload = event.payload if isinstance(event.payload, dict) else {}
        if event.type == RuntimeEventType.ENGINE_SELECTED:
            return {
                "title": "选择执行引擎",
                "details": f"engine={payload.get('engine')}, capability={payload.get('capability')}",
            }
        if event.type == RuntimeEventType.PROVIDER_SELECTED:
            return {
                "title": "选择 Provider",
                "details": str(payload.get("provider")),
            }
        return {
            "title": "开始执行",
            "details": str(payload),
        }

    @staticmethod
    def _extract_error_message(event: RuntimeEvent) -> str:
        """从失败事件中提取错误信息。"""
        payload = event.payload if isinstance(event.payload, dict) else {}
        if not payload:
            return str(event.payload) if event.payload is not None else "unknown error"
        return payload.get("error") or payload.get("message") or payload.get("reason") or str(payload)
