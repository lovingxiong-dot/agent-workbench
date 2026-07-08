"""tests/v6/runtime/test_capability_registry_runtime.py — CapabilityRegistry 运行时索引测试。"""
from __future__ import annotations

from agent_workbench.runtime.interaction import RuntimeRequest, RuntimeRequestSource
from agent_workbench.runtime.capability import (
    CapabilityCategory,
    CapabilityContext,
    CapabilityDefinition,
    CapabilityExecutionState,
    CapabilityMode,
    CapabilityRegistry,
    CapabilityState,
    WorkspaceContext,
)


def test_registry_stores_and_retrieves_state() -> None:
    registry = CapabilityRegistry()
    registry.register(CapabilityDefinition(id="chat", category=CapabilityCategory.TEXT))
    state = CapabilityExecutionState(capability_id="chat", state=CapabilityState.RUNNING)
    registry.set_state("chat", state)
    assert registry.get_state("chat") is state


def test_registry_returns_none_for_missing_state() -> None:
    registry = CapabilityRegistry()
    assert registry.get_state("unknown") is None


def test_registry_stores_and_retrieves_context() -> None:
    registry = CapabilityRegistry()
    registry.register(CapabilityDefinition(id="image_generation", category=CapabilityCategory.IMAGE))
    context = CapabilityContext(
        origin="workspace_session",
        workspace=WorkspaceContext(workspace_id="ws-1"),
    )
    registry.set_context("image_generation", context)
    assert registry.get_context("image_generation") is context


def test_registry_stores_and_retrieves_provider_binding() -> None:
    registry = CapabilityRegistry()
    registry.register(CapabilityDefinition(id="chat", category=CapabilityCategory.TEXT))
    registry.bind_provider("chat", "echo")
    assert registry.get_provider_binding("chat") == "echo"


def test_registry_clear_runtime_does_not_remove_definition() -> None:
    registry = CapabilityRegistry()
    registry.register(CapabilityDefinition(id="chat", category=CapabilityCategory.TEXT))
    registry.set_state("chat", CapabilityExecutionState(capability_id="chat", state=CapabilityState.RUNNING))
    registry.bind_provider("chat", "echo")

    registry.clear_runtime("chat")
    assert registry.get_state("chat") is None
    assert registry.get_provider_binding("chat") is None
    assert registry.get("chat") is not None


def test_registry_build_context_returns_origin() -> None:
    registry = CapabilityRegistry()
    registry.register(
        CapabilityDefinition(
            id="chat",
            category=CapabilityCategory.TEXT,
            supported_modes=[CapabilityMode.CHAT],
        )
    )
    request = RuntimeRequest(
        source=RuntimeRequestSource.GLOBAL_CHAT,
        text="hello",
    )
    context = registry.build_context("chat", request)
    assert context is not None
    assert context.origin == "global_chat"


def test_registry_build_context_returns_none_for_unknown_capability() -> None:
    registry = CapabilityRegistry()
    request = RuntimeRequest(source=RuntimeRequestSource.GLOBAL_CHAT, text="hello")
    assert registry.build_context("unknown", request) is None
