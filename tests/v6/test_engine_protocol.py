"""tests/v6/test_engine_protocol.py — Engine Protocol、Descriptor 与异常测试。"""
from __future__ import annotations

from typing import Any

import pytest

from v6.runtime.context import RuntimeContext
from v6.runtime.engine_state import EngineState
from v6.runtime.engines.protocol import EngineDescriptor, EngineNotReadyError


class FakeEngine:
    """符合 Engine Protocol 的最小实现。"""

    name = "fake"

    def __init__(self) -> None:
        self.loaded = False
        self.initialized = False
        self.executed = False
        self.shut_down = False
        self.last_ctx: Any = None

    def load(self) -> None:
        self.loaded = True

    def initialize(self, ctx: RuntimeContext) -> None:
        self.initialized = True
        self.last_ctx = ctx

    def health_check(self) -> EngineState:
        return EngineState.READY

    def execute(self, ctx: RuntimeContext) -> Any:
        self.executed = True
        self.last_ctx = ctx
        return {"engine": self.name, "request": ctx.request}

    def shutdown(self) -> None:
        self.shut_down = True


def test_engine_descriptor_defaults() -> None:
    desc = EngineDescriptor(name="llm")
    assert desc.name == "llm"
    assert desc.version == "0.0.0"
    assert desc.capabilities == []
    assert desc.dependencies == []
    assert desc.state == EngineState.CREATED
    assert desc.instance is None


def test_engine_descriptor_with_metadata() -> None:
    engine = FakeEngine()
    desc = EngineDescriptor(
        name="vision",
        version="1.2.0",
        capabilities=["image", "ocr"],
        dependencies=["memory"],
        state=EngineState.READY,
        instance=engine,
        metadata={"provider": "openai"},
    )
    assert desc.name == "vision"
    assert desc.version == "1.2.0"
    assert desc.capabilities == ["image", "ocr"]
    assert desc.dependencies == ["memory"]
    assert desc.state == EngineState.READY
    assert desc.instance is engine
    assert desc.metadata["provider"] == "openai"


def test_fake_engine_implements_protocol() -> None:
    engine = FakeEngine()
    assert hasattr(engine, "name")
    assert hasattr(engine, "load")
    assert hasattr(engine, "initialize")
    assert hasattr(engine, "health_check")
    assert hasattr(engine, "execute")
    assert hasattr(engine, "shutdown")


def test_engine_execute_receives_runtime_context() -> None:
    engine = FakeEngine()
    ctx = RuntimeContext.new()
    ctx.request = {"prompt": "hello"}

    result = engine.execute(ctx)
    assert result == {"engine": "fake", "request": {"prompt": "hello"}}


def test_engine_not_ready_error_message() -> None:
    err = EngineNotReadyError("llm", EngineState.CREATED, [EngineState.READY, EngineState.RUNNING])
    message = str(err)
    assert "llm" in message
    assert "created" in message
    assert "ready" in message
    assert "running" in message


def test_engine_not_ready_error_for_missing_state() -> None:
    err = EngineNotReadyError("llm", None, [EngineState.READY])
    message = str(err)
    assert "missing" in message
