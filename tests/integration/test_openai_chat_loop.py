"""tests/integration/test_openai_chat_loop.py — 第一条真实 LLM 链路集成测试。

目标：验证 User → WorkbenchController → Manager AI → Capability → OpenAI Provider → LLM → Response → UI 闭环。
- 使用 mock 替代真实 HTTP 调用。
- 验证 api_key 不随响应泄露。
- 验证错误状态可传播。
"""
from __future__ import annotations

from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from agent_workbench.controller import WorkbenchController
from agent_workbench.runtime.modules.model_module import ModelModule
from v6.runtime.enums import RuntimeState


def _make_openai_config(api_key: str = "sk-test-key") -> Dict[str, Any]:
    """构造一个用于测试的 OpenAI Provider 配置。"""
    return {
        "name": "openai-test",
        "type": "openai",
        "enabled": True,
        "api_key": api_key,
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "request_timeout": 30,
    }


def _mock_openai_client(response_text: str) -> MagicMock:
    """构造一个返回固定文本的 mock OpenAI 客户端。"""
    client = MagicMock()

    class _Delta:
        content = response_text

    class _Choice:
        delta = _Delta()

    class _Chunk:
        choices = [_Choice()]

    chunk = _Chunk()

    def _create_stream(*args, **kwargs):
        return iter([chunk])

    client.chat.completions.create.side_effect = _create_stream
    return client


@pytest.fixture
def controller() -> WorkbenchController:
    ctrl = WorkbenchController()
    ctrl.start()
    try:
        yield ctrl
    finally:
        ctrl.stop()


def _configure_openai_provider(controller: WorkbenchController, api_key: str) -> None:
    """为控制器配置 OpenAI Provider 并切换为默认 Provider。"""
    model_module = controller.runtime.module_registry.get("model")
    assert isinstance(model_module, ModelModule)

    config = _make_openai_config(api_key)
    provider = model_module._create_provider("openai")
    assert provider is not None
    provider.configure(config)

    model_module._providers[config["name"]] = provider
    model_module._default_provider = config["name"]


def test_openai_chat_loop_returns_mocked_response(controller: WorkbenchController) -> None:
    """普通聊天请求经 OpenAI Provider 返回 mock LLM 响应。"""
    expected_response = "你好，我是 OpenAI  mock 助手。"
    _configure_openai_provider(controller, "sk-test-key")

    with patch.object(
        controller.runtime.module_registry.get("model")._providers["openai-test"],
        "_get_client",
        return_value=_mock_openai_client(expected_response),
    ):
        ctx = controller.chat("你好")

    assert ctx.status == RuntimeState.COMPLETED
    assert expected_response in ctx.messages[-1].content

    # api_key 不应出现在任何可观测位置。
    ctx_str = str(ctx.to_dict())
    assert "sk-test-key" not in ctx_str


def test_openai_chat_loop_does_not_leak_api_key(controller: WorkbenchController) -> None:
    """验证 LLM 响应中不包含 api_key，且 Trace 中也不包含。"""
    expected_response = "当前时间：2026-07-09 12:00:00"
    _configure_openai_provider(controller, "sk-secret-12345")

    with patch.object(
        controller.runtime.module_registry.get("model")._providers["openai-test"],
        "_get_client",
        return_value=_mock_openai_client(expected_response),
    ):
        ctx = controller.chat("现在几点")

    assert ctx.status == RuntimeState.COMPLETED
    response = ctx.messages[-1].content
    assert "sk-secret-12345" not in response

    trace_str = str(ctx.trace.snapshot()) if ctx.trace else ""
    assert "sk-secret-12345" not in trace_str


def test_openai_provider_error_propagates_as_failed(controller: WorkbenchController) -> None:
    """Provider 调用失败时任务标记为 FAILED，且不泄露 api_key。"""
    _configure_openai_provider(controller, "sk-error-key")

    def _raise(*args, **kwargs):
        raise RuntimeError("mock openai request failed")

    failing_client = _mock_openai_client("")
    failing_client.chat.completions.create.side_effect = _raise

    with patch.object(
        controller.runtime.module_registry.get("model")._providers["openai-test"],
        "_get_client",
        return_value=failing_client,
    ):
        ctx = controller.chat("触发错误")

    assert ctx.status == RuntimeState.FAILED
    ctx_str = str(ctx.to_dict())
    assert "sk-error-key" not in ctx_str
