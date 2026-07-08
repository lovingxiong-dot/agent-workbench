"""tests/v6/runtime/test_runtime_decision_contract.py — RuntimeDecision 契约冻结测试。

v6.9.4-alpha Contract Freeze：
- 验证 RuntimeDecision 可被 UI / MCP / Local Agent 三类入口共同生成。
- 验证 RuntimeDecision 只携带基础类型（str / dict / list），不持有 Capability / Task / UI 对象。
- 验证 RuntimeDecision → Orchestrator 边界稳定（dispatch 接受并生成 Task）。
"""
from __future__ import annotations

import pytest

from agent_workbench.runtime.decision import (
    Intent,
    IntentType,
    RuntimeDecision,
    RuntimeMode,
)
from v6.runtime.orchestrator import Orchestrator


def _make_image_decision() -> RuntimeDecision:
    """UI / Controller 入口构造的 RuntimeDecision。"""
    return RuntimeDecision(
        mode=RuntimeMode.ACTION,
        intent=Intent(
            mode=RuntimeMode.ACTION,
            type=IntentType.CREATE_ARTIFACT,
            entities={"artifact": "image", "style": "sunset"},
            raw_input="生成日落图片",
        ),
        route="capability://image_generation",
        capability_chain=[
            {"capability_id": "image_generation", "engine_capability": "image_generation"}
        ],
    )


def _make_mcp_decision() -> RuntimeDecision:
    """MCP 入口构造的 RuntimeDecision：外部 tool 请求被 Decision Layer 转换后的形态。"""
    return RuntimeDecision(
        mode=RuntimeMode.ACTION,
        intent=Intent(
            mode=RuntimeMode.ACTION,
            type=IntentType.EXECUTE_ACTION,
            entities={"action": "search", "query": "weather"},
            raw_input="mcp://search/weather",
        ),
        route="capability://search",
        payload={"source": "mcp", "version": "1.0"},
    )


def _make_local_agent_decision() -> RuntimeDecision:
    """Local Agent 入口构造的 RuntimeDecision：自主 Agent 提交的内部请求。"""
    return RuntimeDecision(
        mode=RuntimeMode.WORKFLOW,
        intent=Intent(
            mode=RuntimeMode.WORKFLOW,
            type=IntentType.ANALYZE,
            entities={"language": "python", "project": "agent_workbench"},
            raw_input="分析项目代码",
        ),
        route="workflow://default",
        execution_plan={"planner": "default", "max_steps": 5},
    )


@pytest.mark.parametrize(
    "factory,expected_mode,expected_route",
    [
        (_make_image_decision, RuntimeMode.ACTION, "capability://image_generation"),
        (_make_mcp_decision, RuntimeMode.ACTION, "capability://search"),
        (_make_local_agent_decision, RuntimeMode.WORKFLOW, "workflow://default"),
    ],
)
def test_runtime_decision_can_be_constructed_by_all_entry_points(factory, expected_mode, expected_route) -> None:
    """RuntimeDecision 可被 UI、MCP、Local Agent 三类入口统一构造。"""
    decision = factory()

    assert isinstance(decision, RuntimeDecision)
    assert decision.mode == expected_mode
    assert decision.route == expected_route
    assert decision.intent.mode == expected_mode


def test_runtime_decision_only_carries_primitive_data() -> None:
    """RuntimeDecision 不持有 Capability / Task / UI 对象，只携带基础类型。"""
    decision = _make_image_decision()

    data = decision.to_dict()
    assert isinstance(data["mode"], str)
    assert isinstance(data["intent"], dict)
    assert isinstance(data["route"], str)
    assert isinstance(data["capability_chain"], list)
    for item in data["capability_chain"]:
        assert isinstance(item, dict)
        assert isinstance(item["capability_id"], str)
        assert isinstance(item["engine_capability"], str)


def test_runtime_decision_roundtrip_is_stable() -> None:
    """RuntimeDecision 的序列化/反序列化是稳定的，这是 ABI 的基础要求。"""
    original = _make_image_decision()
    restored = RuntimeDecision.from_dict(original.to_dict())

    assert restored.mode == original.mode
    assert restored.intent.type == original.intent.type
    assert restored.route == original.route
    assert restored.capability_chain == original.capability_chain


def test_orchestrator_accepts_runtime_decision_from_all_entry_points() -> None:
    """Orchestrator.dispatch 接受来自任意入口的 RuntimeDecision。"""
    orchestrator = Orchestrator()

    for factory in (_make_image_decision, _make_mcp_decision, _make_local_agent_decision):
        decision = factory()
        task_id = orchestrator.dispatch(decision)

        if decision.mode == RuntimeMode.CHAT:
            assert task_id is None
        else:
            assert task_id is not None
            ctx = orchestrator.context(task_id)
            assert ctx is not None
            assert ctx.metadata["decision"] == decision.to_dict()
