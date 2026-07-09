"""tests/v6/runtime/test_decision_layer.py — Runtime Decision Layer 集成测试。

覆盖 Commit 5 核心要求：
- LLM 只输出 Intent，不直接选择 Tool。
- GENERAL_QUERY 走 ACTION → chat Capability 进入 Runtime。
- ACTION 生成 CapabilityChain 并执行。
- 旧 Task 路径兼容。
- Tool Calling 污染被拒绝。
"""
from __future__ import annotations

import pytest

from agent_workbench.controller import WorkbenchController
from agent_workbench.runtime.capability import CapabilityRegistry
from agent_workbench.runtime.decision import (
    CapabilityResolver,
    Intent,
    IntentError,
    IntentType,
    Interpreter,
    ManagerAI,
    Policy,
    RuntimeDecision,
    RuntimeMode,
)
from v6.runtime.enums import RuntimeState
from v6.runtime.orchestrator import Orchestrator
from v6.runtime.user_request import UserRequest


@pytest.fixture
def controller() -> WorkbenchController:
    ctrl = WorkbenchController()
    ctrl.start()
    try:
        yield ctrl
    finally:
        ctrl.stop()


def test_general_query_enters_runtime_via_chat_capability(controller: WorkbenchController) -> None:
    """Test 1：普通聊天请求由 ACTION → chat Capability 进入 Runtime，调用默认 Provider。"""
    ctx = controller.chat("解释一下TCP")

    assert ctx.status == RuntimeState.COMPLETED
    decision = ctx.metadata.get("decision", {})
    assert decision["mode"] == "action"
    assert decision["intent"]["type"] == "general_query"
    assert "capability_chain" in ctx.metadata
    chain = ctx.metadata["capability_chain"]
    assert len(chain) == 1
    assert chain[0]["capability_id"] == "chat"
    assert chain[0]["engine_capability"] == "text_generation"


def test_action_image_generation(controller: WorkbenchController) -> None:
    """Test 2：ACTION + CREATE_ARTIFACT 路由到 image_generation 能力。"""
    ctx = controller.chat("生成日落图片")

    assert ctx.status == RuntimeState.COMPLETED
    decision = ctx.metadata.get("decision", {})
    assert decision["mode"] == "action"
    assert decision["intent"]["type"] == "create_artifact"
    assert "capability_chain" in ctx.metadata
    chain = ctx.metadata["capability_chain"]
    assert len(chain) == 1
    assert chain[0]["capability_id"] == "image_generation"


def test_action_python_analysis_chain(controller: WorkbenchController) -> None:
    """Test 3：ANALYZE + python 生成 coding.python 能力链。"""
    ctx = controller.chat("分析python代码")

    assert ctx.status == RuntimeState.COMPLETED
    decision = ctx.metadata.get("decision", {})
    assert decision["mode"] == "action"
    assert decision["intent"]["type"] == "analyze"

    chain = ctx.metadata.get("capability_chain", [])
    chain_ids = [step["capability_id"] for step in chain]
    assert chain_ids == [
        "coding.python.analysis",
        "coding.python.debugging",
        "coding.python.testing",
    ]


def test_legacy_task_path_still_works(controller: WorkbenchController) -> None:
    """Test 4：旧 Task → submit_task 路径继续可用。"""
    from v6.runtime.task import ChatTask

    task = ChatTask(text="hello")
    ctx = controller.submit_task(task)

    assert ctx.status == RuntimeState.COMPLETED


def test_interpreter_rejects_tool_calling() -> None:
    """Test 5：Interpreter 必须拒绝传统 function calling / tool calling 格式。"""
    interpreter = Interpreter()

    with pytest.raises(IntentError):
        interpreter.interpret({"tool": "image_generate", "arguments": {"prompt": "sunset"}})

    with pytest.raises(IntentError):
        interpreter.interpret({"function": "python_debugger", "parameters": {}})

    with pytest.raises(IntentError):
        interpreter.interpret({"tool_calls": [{"name": "image_generate"}]})


def test_decision_manager_resolves_to_decision() -> None:
    """DecisionManager.decide 生成正确的 RuntimeDecision。"""
    registry = CapabilityRegistry()
    registry.load_defaults()
    manager = ManagerAI()
    resolver = CapabilityResolver(registry)

    intent = manager.understand(UserRequest(text="生成日落图片"))
    route, chain = resolver.resolve(intent)
    decision = RuntimeDecision(
        mode=intent.mode,
        intent=intent,
        route=route,
        capability_chain=[step.to_dict() for step in chain] if chain else None,
    )

    assert decision.mode == RuntimeMode.ACTION
    assert decision.route == "capability://image_generation"
    assert decision.capability_chain is not None


def test_orchestrator_dispatch_chat_returns_none() -> None:
    """Orchestrator.dispatch 对 CHAT Decision 不创建 Task。"""
    orchestrator = Orchestrator()
    decision = RuntimeDecision(
        mode=RuntimeMode.CHAT,
        intent=Intent(mode=RuntimeMode.CHAT, type=IntentType.GENERAL_QUERY),
        route="capability://chat",
    )

    task_id = orchestrator.dispatch(decision)
    assert task_id is None


def test_orchestrator_dispatch_action_creates_task() -> None:
    """Orchestrator.dispatch 对 ACTION Decision 创建 Task 并携带 capability_chain。"""
    orchestrator = Orchestrator()
    decision = RuntimeDecision(
        mode=RuntimeMode.ACTION,
        intent=Intent(
            mode=RuntimeMode.ACTION,
            type=IntentType.ANALYZE,
            entities={"language": "python"},
        ),
        route="capability://coding.python",
        capability_chain=[
            {"capability_id": "coding.python.analysis", "engine_capability": "code_generation"},
            {"capability_id": "coding.python.debugging", "engine_capability": "code_generation"},
            {"capability_id": "coding.python.testing", "engine_capability": "code_generation"},
        ],
    )

    task_id = orchestrator.dispatch(decision)
    assert task_id is not None

    ctx = orchestrator.context(task_id)
    assert ctx is not None
    assert "capability_chain" in ctx.metadata
    assert len(ctx.metadata["capability_chain"]) == 3
