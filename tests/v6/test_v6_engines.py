"""tests/v6/test_v6_engines.py — 八大引擎单元测试。

验证原则：
- 所有 Engine 实现统一 run(ctx) 接口。
- RuntimeContext 是唯一状态对象，Engine 只修改自身负责字段。
- 所有引擎可独立构造和测试，不依赖真实 LLM / 工具。

注意：使用 asyncio.run() 运行异步引擎，避免引入 pytest-asyncio 依赖。
"""
from __future__ import annotations

import asyncio

import pytest

from v6.runtime.context import RuntimeContext
from v6.runtime.engines import (
    CompressionStrategy,
    ContextEngine,
    InferenceEngine,
    MemoryEngine,
    MetricsEngine,
    PhaseEngine,
    PolicyEngine,
    PromptEngine,
    ToolEngine,
)
from v6.runtime.engines.interfaces import Engine
from v6.runtime.types import ChatMessage


@pytest.fixture
def ctx():
    return RuntimeContext(task_id="t-1", session_id="s-1")


# ─────────────────────────────────────────────────────────
# 接口与构造
# ─────────────────────────────────────────────────────────


def test_all_engines_inherit_engine_base():
    for cls in (
        ContextEngine,
        PromptEngine,
        InferenceEngine,
        ToolEngine,
        PhaseEngine,
        MemoryEngine,
        MetricsEngine,
        PolicyEngine,
    ):
        assert issubclass(cls, Engine)
        assert hasattr(cls, "run")


def test_context_engine_builds_messages(ctx):
    ctx.metadata.update(
        {
            "user_input": "hello",
            "chat_history": [ChatMessage(role="user", content="prev")],
            "system_prompt": "You are helpful.",
            "max_tokens": 8192,
        }
    )
    engine = ContextEngine()
    result = asyncio.run(engine.run(ctx))
    assert result is ctx
    assert len(ctx.messages) == 3
    assert ctx.messages[0].role == "system"
    assert ctx.messages[2].role == "user"
    assert ctx.messages[2].content == "hello"


def test_context_engine_compresses_when_over_threshold(ctx):
    long_history = [ChatMessage(role="user", content="x" * 2000) for _ in range(10)]
    ctx.metadata.update(
        {
            "user_input": "hi",
            "chat_history": long_history,
            "system_prompt": "sys",
            "max_tokens": 100,
        }
    )
    engine = ContextEngine()
    asyncio.run(engine.run(ctx))
    assert len(ctx.messages) < 13


def test_prompt_engine_builds_system_prompt(ctx):
    ctx.mode = "coder"
    ctx.phase = "analyze"
    ctx.metadata["user_profile"] = {"name": "Alice"}
    ctx.metadata["workspace_context"] = "Project: V6"

    engine = PromptEngine(base_prompts={"coder": "You are a coder."})
    asyncio.run(engine.run(ctx))

    prompt = ctx.metadata["system_prompt"]
    assert "You are a coder." in prompt
    assert "Analysis Phase" in prompt
    assert "Alice" in prompt
    assert "Project: V6" in prompt


def test_phase_engine_advances_phase(ctx):
    ctx.mode = "craft"
    ctx.phase = "analyze"
    engine = PhaseEngine()
    asyncio.run(engine.run(ctx))
    assert ctx.phase == "confirm"


def test_phase_engine_initializes_phase(ctx):
    ctx.mode = "plan"
    ctx.phase = ""
    engine = PhaseEngine()
    asyncio.run(engine.run(ctx))
    assert ctx.phase == "analyze"


def test_memory_engine_stores_and_retrieves(ctx):
    ctx.session_id = "s-mem"
    ctx.messages = [
        ChatMessage(role="user", content="hello"),
        ChatMessage(role="assistant", content="hi"),
    ]
    ctx.metadata["memory_query"] = "hello"
    ctx.metadata["memory_top_k"] = 2

    engine = MemoryEngine()
    asyncio.run(engine.run(ctx))

    assert "retrieved" in ctx.memory
    assert len(ctx.memory["retrieved"]) == 2
    assert ctx.metadata["memory_context"] == ""


def test_metrics_engine_records_from_metadata(ctx):
    ctx.metadata["metric_records"] = [
        {"namespace": "test", "name": "latency", "value": 100},
        {"namespace": "test", "name": "latency", "value": 200},
    ]
    engine = MetricsEngine()
    asyncio.run(engine.run(ctx))

    assert "test" in ctx.metrics
    assert ctx.metrics["test"]["latency"]["count"] == 2
    assert engine.get("test", "latency", "avg") == 150


def test_policy_engine_makes_decisions(ctx):
    ctx.metadata["policy_query"] = "app.last_model"
    ctx.metadata["query_features"] = {"complexity": "high"}
    ctx.metadata["session_metrics"] = {"token_count": 9000, "max_tokens": 10000}

    engine = PolicyEngine(config={"app": {"last_model": "qwen3:4b"}})
    asyncio.run(engine.run(ctx))

    assert ctx.metadata["policy_result"] == "qwen3:4b"
    assert ctx.metadata["selected_model"] == "qwen3:4b"
    assert ctx.metadata["should_compress"] is True


def test_tool_engine_executes_registered_tools(ctx):
    async def add(args):
        return args["a"] + args["b"]

    engine = ToolEngine(tool_map={"add": add})
    ctx.metadata["tool_calls"] = [{"name": "add", "args": {"a": 1, "b": 2}}]
    asyncio.run(engine.run(ctx))

    results = ctx.metadata["tool_results"]
    assert len(results) == 1
    assert results[0].success is True
    assert results[0].result == "3"


def test_tool_engine_blocks_unregistered_tool(ctx):
    engine = ToolEngine()
    ctx.metadata["tool_calls"] = [{"name": "unknown", "args": {}}]
    asyncio.run(engine.run(ctx))

    results = ctx.metadata["tool_results"]
    assert len(results) == 1
    assert results[0].success is False


def test_inference_engine_without_registry_records_error(ctx):
    engine = InferenceEngine()
    ctx.messages = [ChatMessage(role="user", content="hi")]
    ctx.model = "test-model"
    ctx.metadata["timeout"] = 0.1
    asyncio.run(engine.run(ctx))

    assert ctx.metadata["response"] == ""
    metrics = ctx.metadata["inference_metrics"]
    assert metrics.success is False
    assert metrics.error_code != ""


def test_engine_run_returns_same_context(ctx):
    """验证 Engine 返回同一个 RuntimeContext 实例。"""
    engine = PhaseEngine()
    result = asyncio.run(engine.run(ctx))
    assert result is ctx


def test_chat_message_is_plain_dataclass():
    """ChatMessage 是纯净数据类，不携带 V4 兼容方法（如 to_langchain）。"""
    msg = ChatMessage(role="system", content="hello")
    assert msg.role == "system"
    assert msg.content == "hello"
    assert not hasattr(msg, "to_langchain")


def test_runtime_context_is_state_container_not_manager(ctx):
    """RuntimeContext 只保存状态，不提供业务方法。"""
    forbidden = {"call_llm", "execute_tool", "save_memory", "select_model"}
    methods = {name for name in dir(ctx) if callable(getattr(ctx, name)) and not name.startswith("_")}
    assert not forbidden & methods, f"RuntimeContext 不应包含业务方法: {forbidden & methods}"


def test_runtime_context_clone_is_independent(ctx):
    """clone() 返回深拷贝副本，修改原对象不影响副本。"""
    ctx.add_message("user", "hello")
    cloned = ctx.clone()
    assert cloned is not ctx
    assert cloned.messages[0].content == "hello"
    ctx.add_message("assistant", "hi")
    assert len(cloned.messages) == 1
    assert len(ctx.messages) == 2


def test_runtime_context_snapshot_is_deep_copy(ctx):
    """snapshot() 返回当前状态的深拷贝快照。"""
    ctx.add_message("user", "hello")
    snap = ctx.snapshot()
    ctx.add_message("assistant", "hi")
    assert len(snap["messages"]) == 1
    assert len(ctx.messages) == 2


def test_runtime_context_restore_rollback(ctx):
    """restore(snapshot) 可回滚到之前状态。"""
    ctx.add_message("user", "hello")
    snap = ctx.snapshot()
    ctx.add_message("assistant", "hi")
    ctx.phase = "execute"
    ctx.restore(snap)
    assert len(ctx.messages) == 1
    assert ctx.messages[0].content == "hello"
    assert ctx.phase == ""


def test_runtime_context_freeze_alias(ctx):
    """freeze() 是 snapshot() 的别名，语义为不可变快照。"""
    ctx.add_message("user", "hello")
    frozen = ctx.freeze()
    ctx.add_message("assistant", "hi")
    assert len(frozen["messages"]) == 1


def test_runtime_context_reset_keeps_identity(ctx):
    """reset() 保留 task_id 等标识，清空状态。"""
    ctx.session_id = "sid-1"
    ctx.phase = "plan"
    ctx.add_message("user", "hello")
    ctx.reset()
    assert ctx.task_id
    assert ctx.session_id == "sid-1"
    assert ctx.phase == ""
    assert not ctx.messages


def test_engines_do_not_call_each_other(ctx):
    """Engine 之间零耦合，只通过 RuntimeContext 共享状态。"""
    import asyncio

    class EngineA(Engine):
        async def run(self, ctx):
            ctx.metadata["a_ran"] = True
            return ctx

    class EngineB(Engine):
        async def run(self, ctx):
            assert ctx.metadata.get("a_ran")  # 通过 ctx 读取 A 的结果
            ctx.metadata["b_ran"] = True
            return ctx

    a = EngineA()
    b = EngineB()
    # Runtime 编排：A 先执行，B 后执行；Engine 之间不直接调用
    ctx = asyncio.run(a.run(ctx))
    ctx = asyncio.run(b.run(ctx))
    assert ctx.metadata["a_ran"]
    assert ctx.metadata["b_ran"]
