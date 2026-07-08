"""agent_workbench/runtime/decision/manager_ai.py — UserRequest → Intent。

设计约束：
- ManagerAI 是 Runtime Decision Layer 的入口：把外部用户请求转换为结构化 Intent。
- 当前阶段没有接入真实 LLM，使用基于规则的映射完成闭环；未来可替换为 LLM Interpreter。
- ManagerAI 内部调用 Interpreter，确保 LLM 输出不能携带 tool/function calling。
"""
from __future__ import annotations

from typing import Any

from agent_workbench.runtime.decision.interpreter import Interpreter
from agent_workbench.runtime.decision.schema import Intent, IntentType, RuntimeMode

from v6.runtime.user_request import UserRequest


class ManagerAI:
    """用户请求解释器：UserRequest → Intent。"""

    def __init__(self, interpreter: Interpreter | None = None) -> None:
        self._interpreter = interpreter or Interpreter()

    def understand(self, request: UserRequest) -> Intent:
        """将 UserRequest 转换为 Intent。

        当前阶段使用规则生成 LLM 输出 dict，再经 Interpreter 校验为 Intent。
        """
        raw_output = self._route_request(request)
        return self._interpreter.interpret(raw_output)

    def _route_request(self, request: UserRequest) -> dict[str, Any]:
        """基于规则生成伪 LLM 输出。"""
        text = (request.text or "").lower()

        if self._matches(text, ["生成", "画", "画一张", "创建图片", "生成图片", "generate image", "create image"]):
            return {
                "mode": "ACTION",
                "intent": "create_artifact",
                "entities": {"artifact": "image"},
                "raw_input": request.text or "",
            }

        if self._matches(text, ["分析", "解析", "review", "analyze python", "分析python", "分析 python"]):
            return {
                "mode": "ACTION",
                "intent": "analyze",
                "entities": {"language": "python"},
                "raw_input": request.text or "",
            }

        # 默认走 CHAT，不进入 Runtime 执行层。
        return {
            "mode": "CHAT",
            "intent": "general_query",
            "entities": {},
            "raw_input": request.text or "",
        }

    @staticmethod
    def _matches(text: str, patterns: list[str]) -> bool:
        """简单关键词匹配。"""
        for pattern in patterns:
            if pattern.lower() in text:
                return True
        return False
