"""agent_workbench/runtime/decision/interpreter.py — LLM Output → Intent。

设计约束：
- 只负责把 LLM 输出解析为 Intent，不调用 Runtime / Capability / Tool / Service。
- 禁止接受传统 function calling / tool calling 格式；LLM 不能绕过 Runtime Control Plane 直接选择 Tool。
- 无法解析时抛出 IntentError，不猜测。
"""
from __future__ import annotations

import json
from typing import Any

from agent_workbench.runtime.decision.schema import Intent, IntentError, IntentType, RuntimeMode


class Interpreter:
    """LLM 输出解释器。"""

    # 任何出现以下顶层键之一的输入，都被视为试图让 LLM 直接控制 Tool。
    _FORBIDDEN_TOOL_KEYS: frozenset[str] = frozenset(
        {"tool", "function", "tool_call", "function_call", "tool_calls", "functions"}
    )

    def interpret(self, raw: dict[str, Any] | str) -> Intent:
        """将 LLM 原始输出解析为 Intent。

        参数：
            raw: LLM 输出的 dict 或 JSON 字符串。

        异常：
            IntentError: 输入包含 tool/function calling 字段，或无法解析为合法 Intent。
        """
        data = self._normalize(raw)
        self._reject_tool_calling(data)
        return self._parse_intent(data)

    @staticmethod
    def _normalize(raw: dict[str, Any] | str) -> dict[str, Any]:
        """统一把输入转换为 dict。"""
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise IntentError(f"invalid JSON from LLM: {exc}") from exc
            if not isinstance(parsed, dict):
                raise IntentError("LLM output must be a JSON object")
            return parsed
        raise IntentError(f"unsupported LLM output type: {type(raw).__name__}")

    def _reject_tool_calling(self, data: dict[str, Any]) -> None:
        """拒绝任何让 LLM 直接选择 Tool 的输入格式。"""
        found = self._FORBIDDEN_TOOL_KEYS.intersection(data.keys())
        if found:
            raise IntentError(
                f"tool/function calling is not allowed in Runtime Decision Layer: {sorted(found)}"
            )

    def _parse_intent(self, data: dict[str, Any]) -> Intent:
        """从已清洗的 dict 构造 Intent。"""
        mode_value = str(data.get("mode", "chat")).lower()
        type_value = data.get("intent") or data.get("type")
        if not type_value:
            raise IntentError("missing 'intent' or 'type' field in LLM output")
        type_value = str(type_value).lower()

        try:
            mode = RuntimeMode(mode_value)
        except ValueError as exc:
            raise IntentError(f"unsupported runtime mode: {mode_value}") from exc

        try:
            intent_type = IntentType(type_value)
        except ValueError as exc:
            raise IntentError(f"unsupported intent type: {type_value}") from exc

        entities = data.get("entities", {})
        if not isinstance(entities, dict):
            raise IntentError("'entities' must be a dict")

        return Intent(
            mode=mode,
            type=intent_type,
            entities=dict(entities),
            raw_input=data.get("raw_input", ""),
        )
