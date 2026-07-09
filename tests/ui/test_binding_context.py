"""Tests for BindingContext — Dynamic UI Binding Layer (no Qt required)."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent_workbench.ui.workbench.binding_context import BindingContext, BindingProvider, BindingRegistry
from agent_workbench.ui.workbench.view_schema import BindingSource


class TestBindingRegistry:
    def test_register_and_get_provider(self) -> None:
        registry = BindingRegistry()
        provider = BindingProvider(namespace="runtime", getter=lambda path: "ok")
        registry.register(provider)
        assert registry.get("runtime") is provider

    def test_get_missing_provider_returns_none(self) -> None:
        registry = BindingRegistry()
        assert registry.get("missing") is None

    def test_unregister_provider(self) -> None:
        registry = BindingRegistry()
        provider = BindingProvider(namespace="task", getter=lambda path: "done")
        registry.register(provider)
        registry.unregister("task")
        assert registry.get("task") is None


class TestBindingContext:
    def test_resolve_via_provider(self) -> None:
        context = BindingContext()
        context.registry.register(
            BindingProvider(namespace="runtime", getter=lambda path: {"status": "online"}.get(path))
        )
        source = BindingSource(path="runtime.status")
        assert context.resolve(source) == "online"

    def test_resolve_nested_path(self) -> None:
        context = BindingContext()
        context.registry.register(
            BindingProvider(
                namespace="task",
                getter=lambda path: {"executor": {"state": "running"}}.get(path),
            )
        )
        source = BindingSource(path="task.executor")
        assert context.resolve(source) == {"state": "running"}

    def test_resolve_static_value(self) -> None:
        context = BindingContext()
        context.set_static("session.title", "Hello")
        source = BindingSource(path="session.title")
        assert context.resolve(source) == "Hello"

    def test_resolve_with_format(self) -> None:
        context = BindingContext()
        context.registry.register(
            BindingProvider(namespace="runtime", getter=lambda path: 12.3456 if path == "latency" else None)
        )
        source = BindingSource(path="runtime.latency", format="{:.2f} ms")
        assert context.resolve(source) == "12.35 ms"

    def test_resolve_none_source_returns_none(self) -> None:
        context = BindingContext()
        assert context.resolve(None) is None

    def test_resolve_missing_provider_returns_none(self) -> None:
        context = BindingContext()
        source = BindingSource(path="unknown.value")
        assert context.resolve(source) is None

    def test_resolve_provider_exception_returns_none(self) -> None:
        context = BindingContext()
        context.registry.register(
            BindingProvider(namespace="runtime", getter=lambda path: (_ for _ in ()).throw(RuntimeError("boom")))
        )
        source = BindingSource(path="runtime.anything")
        assert context.resolve(source) is None

    def test_resolve_path_convenience(self) -> None:
        context = BindingContext()
        context.set_static("foo.bar", "baz")
        assert context.resolve_path("foo.bar") == "baz"

    def test_format_failure_returns_raw_value(self) -> None:
        context = BindingContext()
        context.set_static("x.value", object())
        source = BindingSource(path="x.value", format="{:.2f}")
        assert context.resolve(source) is context._static_values["x.value"]

    def test_static_values_take_precedence_over_provider(self) -> None:
        context = BindingContext()
        context.registry.register(
            BindingProvider(namespace="runtime", getter=lambda path: "provider")
        )
        context.set_static("runtime.status", "static")
        source = BindingSource(path="runtime.status")
        assert context.resolve(source) == "static"


class TestBindingSource:
    def test_default_format_is_none(self) -> None:
        source = BindingSource(path="runtime.status")
        assert source.format is None

    def test_format_storage(self) -> None:
        source = BindingSource(path="runtime.latency", format="{:.2f} ms")
        assert source.format == "{:.2f} ms"
