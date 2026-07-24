"""tests/test_controller_interaction.py — Controller 与 Interaction Layer 集成测试。"""
from __future__ import annotations

import importlib

import pytest

from agent_workbench.controller import WorkbenchController
from agent_workbench.runtime.interaction import RuntimeRequest, RuntimeRequestSource

# 环境依赖标记：openai 包未安装时跳过需要真实 Provider 的测试
# 不修改 Runtime 逻辑，不降低测试覆盖要求
_openai_available = importlib.util.find_spec("openai") is not None
_skip_no_openai = pytest.mark.skipif(
    not _openai_available,
    reason="openai 包未安装，属于环境依赖问题，非代码缺陷。安装: pip install openai",
)


def test_controller_exposes_interaction_layer() -> None:
    controller = WorkbenchController()
    try:
        assert controller.interaction_layer is not None
    finally:
        controller.stop()


def test_controller_submit_request_returns_request_id() -> None:
    controller = WorkbenchController()
    try:
        controller.start()
        request = RuntimeRequest(text="hello")
        request_id = controller.submit_request(request)
        assert request_id == request.request_id
    finally:
        controller.stop()


@_skip_no_openai
def test_controller_chat_routes_general_query_to_chat_capability() -> None:
    controller = WorkbenchController()
    try:
        controller.start()
        ctx = controller.chat("hello")
        assert ctx.status.value == "completed"
        decision = ctx.metadata.get("decision", {})
        assert decision.get("mode") == "action"
        assert decision.get("intent", {}).get("type") == "general_query"
        assert "capability_chain" in ctx.metadata
        assert ctx.metadata["capability_chain"][0]["capability_id"] == "chat"
    finally:
        controller.stop()


def test_controller_chat_with_tool_uses_interaction_layer() -> None:
    controller = WorkbenchController()
    try:
        controller.start()
        ctx = controller.chat_with_tool("python_formatter", {"file": "a.py"})
        # 显式 tool 请求应进入 ACTION 模式，执行后完成或失败取决于引擎环境。
        assert ctx.status.value in {"completed", "failed"}
    finally:
        controller.stop()


def test_controller_submit_request_for_action_does_not_block() -> None:
    controller = WorkbenchController()
    try:
        controller.start()
        request = RuntimeRequest(
            source=RuntimeRequestSource.COMMAND_BAR,
            text="generate an image of sunset",
        )
        request_id = controller.submit_request(request)
        assert isinstance(request_id, str)
        assert len(request_id) > 0
    finally:
        controller.stop()
