"""agent_workbench/metadata/adapter.py — Metadata adapter skeleton.

This module owns the *contract* of adapting MetadataDefinition into another
representation. Concrete adapters (e.g., UI PresentationModel adapters) live in
their respective consumer layers and implement this contract.

The metadata package itself does NOT import any consumer layer.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from agent_workbench.metadata.model import MetadataDefinition


@runtime_checkable
class MetadataAdapter(Protocol):
    """跨层适配器协议。

    实现者接收 `MetadataDefinition`，返回目标层的数据表示。
    返回值类型由实现者决定：Workbench 返回 PresentationModel，CLI 返回
    可打印字典，Plugin 返回序列化结构，等等。
    """

    def adapt(self, definition: MetadataDefinition) -> Any:
        """将 MetadataDefinition 转换为目标表示。"""
        ...


class IdentityMetadataAdapter:
    """默认实现：原样返回 MetadataDefinition。

    用于不需要转换的消费端，或作为自定义 Adapter 的基类。
    """

    def adapt(self, definition: MetadataDefinition) -> MetadataDefinition:
        return definition
