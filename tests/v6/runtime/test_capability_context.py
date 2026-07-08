"""tests/v6/runtime/test_capability_context.py — CapabilityContext 契约测试。"""
from __future__ import annotations

from agent_workbench.runtime.interaction import RuntimeRequest, RuntimeRequestSource
from agent_workbench.runtime.capability import (
    AttachmentContext,
    CapabilityCategory,
    CapabilityContext,
    CapabilityDefinition,
    CapabilityMode,
    DefaultCapabilityContextBuilder,
    ExecutionContext,
    SelectionContext,
    WorkspaceContext,
)


def test_workspace_context_defaults() -> None:
    ctx = WorkspaceContext()
    assert ctx.workspace_id is None
    assert ctx.open_files == []


def test_attachment_context_defaults() -> None:
    ctx = AttachmentContext()
    assert ctx.items == []


def test_selection_context_defaults() -> None:
    ctx = SelectionContext()
    assert ctx.path is None
    assert ctx.text is None


def test_execution_context_defaults() -> None:
    ctx = ExecutionContext()
    assert ctx.parameters == {}
    assert ctx.environment == {}


def test_capability_context_typed_subcontexts() -> None:
    ctx = CapabilityContext(
        origin="global_chat",
        workspace=WorkspaceContext(workspace_id="ws-1"),
        attachments=AttachmentContext(items=[{"name": "a.png"}]),
        selection=SelectionContext(path="main.py", text="def foo():"),
        execution=ExecutionContext(parameters={"size": "1024x1024"}),
    )
    assert ctx.origin == "global_chat"
    assert ctx.workspace.workspace_id == "ws-1"
    assert ctx.attachments.items[0]["name"] == "a.png"
    assert ctx.selection.path == "main.py"
    assert ctx.execution.parameters["size"] == "1024x1024"


def test_default_builder_extracts_origin_from_runtime_request() -> None:
    builder = DefaultCapabilityContextBuilder()
    definition = CapabilityDefinition(
        id="image_generation",
        category=CapabilityCategory.IMAGE,
        supported_modes=[CapabilityMode.ACTION],
    )
    request = RuntimeRequest(
        source=RuntimeRequestSource.WORKSPACE_SESSION,
        text="generate a cat image",
    )
    context = builder.build(definition, request)
    assert context.origin == "workspace_session"


def test_default_builder_extracts_origin_from_metadata() -> None:
    builder = DefaultCapabilityContextBuilder()
    definition = CapabilityDefinition(id="chat")
    request = type("Request", (), {"metadata": {"source": "command_bar"}})()
    context = builder.build(definition, request)
    assert context.origin == "command_bar"


def test_default_builder_origin_empty_when_no_source() -> None:
    builder = DefaultCapabilityContextBuilder()
    definition = CapabilityDefinition(id="chat")
    request = type("Request", (), {"metadata": {}})()
    context = builder.build(definition, request)
    assert context.origin == ""
