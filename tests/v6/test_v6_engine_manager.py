"""tests/v6/test_v6_engine_manager.py — EngineManager 单元测试。"""
from __future__ import annotations

import pytest

from v6.runtime.engine_manager import EngineManager


class FakeEngine:
    def __init__(self, name: str) -> None:
        self.name = name

    def run(self, ctx: object) -> None:
        ctx.metadata = {"engine": self.name}  # type: ignore[attr-defined]


def test_register_and_get_engine():
    manager = EngineManager()
    engine = FakeEngine("inference")
    manager.register("inference", engine)

    assert manager.has("inference")
    assert manager.get("inference") is engine


def test_get_missing_engine_returns_none():
    manager = EngineManager()
    assert manager.get("missing") is None
    assert not manager.has("missing")


def test_names_lists_registered_engines():
    manager = EngineManager()
    manager.register("inference", FakeEngine("inference"))
    manager.register("memory", FakeEngine("memory"))

    names = manager.names()
    assert "inference" in names
    assert "memory" in names
    assert len(names) == 2


def test_unregister_removes_engine():
    manager = EngineManager()
    manager.register("tool", FakeEngine("tool"))

    assert manager.unregister("tool") is True
    assert not manager.has("tool")
    assert manager.unregister("tool") is False


def test_clear_removes_all_engines():
    manager = EngineManager()
    manager.register("a", FakeEngine("a"))
    manager.register("b", FakeEngine("b"))

    manager.clear()
    assert manager.names() == []
    assert not manager.has("a")
    assert not manager.has("b")


def test_engine_run_modifies_context():
    manager = EngineManager()
    engine = FakeEngine("inference")
    manager.register("inference", engine)

    class Ctx:
        def __init__(self) -> None:
            self.metadata: dict[str, object] = {}

    ctx = Ctx()
    manager.get("inference").run(ctx)
    assert ctx.metadata == {"engine": "inference"}


def test_register_overwrites_existing_engine():
    manager = EngineManager()
    first = FakeEngine("first")
    second = FakeEngine("second")
    manager.register("key", first)
    manager.register("key", second)

    assert manager.get("key") is second
