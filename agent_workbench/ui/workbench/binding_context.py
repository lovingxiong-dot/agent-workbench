"""agent_workbench/ui/workbench/binding_context.py — Dynamic UI Binding Layer。

负责把 Runtime 状态按 ViewSchema 中声明的 BindingSource 路径注入到 UI。

设计约束：
- BindingContext 不依赖 Qt，只维护一个状态快照与路径解析器。
- Runtime / Provider / Task 等外部对象通过 Provider 注册到 Registry。
- Renderer 调用 resolve(binding_source) 获取当前值，无需知道数据来源。

数据流：
    Runtime / Task / Provider
            │
            ▼
    BindingProvider (按 namespace 注册)
            │
            ▼
    BindingContext
            │
            ▼
    ViewSchemaRenderer
            │
            ▼
    Qt Widgets
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from agent_workbench.ui.workbench.view_schema import BindingSource


@dataclass
class BindingProvider:
    """一个 Runtime 状态提供者。

    namespace: 路径前缀，例如 "runtime" / "task" / "session" / "agent"。
    getter: 接收 dot-path（不含 namespace）并返回当前值的函数。
    """

    namespace: str
    getter: Callable[[str], Any]


class BindingRegistry:
    """BindingProvider 注册表。"""

    def __init__(self) -> None:
        self._providers: dict[str, BindingProvider] = {}

    def register(self, provider: BindingProvider) -> None:
        """注册一个状态提供者。"""
        self._providers[provider.namespace] = provider

    def unregister(self, namespace: str) -> None:
        """注销一个状态提供者。"""
        self._providers.pop(namespace, None)

    def get(self, namespace: str) -> BindingProvider | None:
        return self._providers.get(namespace)


class BindingContext:
    """绑定上下文：按路径解析 BindingSource。"""

    def __init__(self, registry: BindingRegistry | None = None) -> None:
        self._registry = registry or BindingRegistry()
        self._static_values: dict[str, Any] = {}

    @property
    def registry(self) -> BindingRegistry:
        return self._registry

    def set_static(self, path: str, value: Any) -> None:
        """设置一个静态绑定值（用于无需 Runtime Provider 的场景）。"""
        self._static_values[path] = value

    def resolve(self, source: BindingSource | None) -> Any:
        """解析一个 BindingSource，返回当前值。

        路径格式："namespace.key1.key2"
        - 优先匹配已注册的 Provider。
        - 未找到 Provider 时，回退到静态值。
        - 都不存在时返回 None。
        """
        if source is None:
            return None
        path = source.path
        if path in self._static_values:
            value = self._static_values[path]
            return self._format(value, source.format)

        parts = path.split(".", 1)
        namespace = parts[0]
        sub_path = parts[1] if len(parts) > 1 else ""

        provider = self._registry.get(namespace)
        if provider is None:
            return None

        try:
            value = provider.getter(sub_path)
        except Exception:
            value = None
        return self._format(value, source.format)

    def resolve_path(self, path: str) -> Any:
        """直接通过路径解析值（便捷方法）。"""
        return self.resolve(BindingSource(path=path))

    @staticmethod
    def _format(value: Any, fmt: str | None) -> Any:
        """按 format 字符串格式化值；未指定则原样返回。"""
        if fmt is None or value is None:
            return value
        try:
            return fmt.format(value)
        except Exception:
            return value
