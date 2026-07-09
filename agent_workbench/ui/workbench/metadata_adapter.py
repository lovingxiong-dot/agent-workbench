"""agent_workbench/ui/workbench/metadata_adapter.py — Metadata → PresentationModel 适配器。

这是 Runtime 与 UI 之间的唯一翻译层：
- 输入：Runtime 提供的 Capability / Resource Metadata（不知道 UI 存在）。
- 输出：UI 层 PresentationModel（不知道 RuntimeModule 存在）。

实现者：PresentationMetadataAdapter 实现了 agent_workbench.metadata.adapter.MetadataAdapter Protocol。
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from agent_workbench.metadata import (
    MetadataAction,
    MetadataDefinition,
    MetadataProperty,
    MetadataStatistics,
    ResourceDefinition,
)
from agent_workbench.metadata.adapter import MetadataAdapter as MetadataAdapterProtocol
from agent_workbench.metadata.types import ValueType
from agent_workbench.runtime.metadata import (
    ActionMetadata,
    ModuleMetadata,
    PropertyMetadata,
    StatisticMetadata,
)
from agent_workbench.ui.workbench.presentation import (
    ActionPresentation,
    ModulePresentation,
    PropertyPresentation,
    StatisticPresentation,
)


class PresentationMetadataAdapter:
    """将 Runtime Capability / Resource Metadata 转换为 UI PresentationModel。

    同时兼容旧 ModuleMetadata（v6.10.x）与新 MetadataDefinition（v6.11.x），
    让 Runtime 模块可以逐步迁移。
    """

    def adapt(self, metadata: ModuleMetadata | MetadataDefinition) -> ModulePresentation:
        """将 Capability Metadata 转换为 ModulePresentation。"""
        module_type = metadata.type
        explicit_schema_id = getattr(metadata, "view_schema_id", "")
        view_schema_id = explicit_schema_id or self._infer_view_schema_id(module_type, metadata.id)
        return ModulePresentation(
            id=metadata.id,
            type=module_type,
            name=metadata.name,
            description=metadata.description,
            icon=metadata.icon,
            properties=[self._adapt_property(p) for p in metadata.properties],
            statistics=[self._adapt_statistic(s) for s in metadata.statistics],
            actions=[self._adapt_action(a) for a in metadata.actions],
            tags=list(getattr(metadata, "tags", [])),
            enabled=getattr(metadata, "enabled", True),
            category="",
            view_schema_id=view_schema_id,
        )

    def adapt_resource(self, resource: ResourceDefinition) -> ModulePresentation:
        """将 ResourceDefinition 转换为 ModulePresentation，供 Navigator / Inspector 统一渲染。"""
        return ModulePresentation(
            id=resource.id,
            type=resource.type if isinstance(resource.type, str) else str(resource.type.value),
            name=resource.name,
            description=resource.description,
            icon=resource.icon,
            properties=[self._adapt_property(p) for p in resource.properties],
            statistics=[self._adapt_statistic(s) for s in resource.statistics],
            actions=[self._adapt_action(a) for a in resource.actions],
            tags=list(resource.tags),
            enabled=resource.enabled,
            category="resource",
            connection=asdict(resource.connection),
        )

    def _adapt_property(self, prop) -> PropertyPresentation:
        if isinstance(prop, MetadataProperty):
            return PropertyPresentation(
                name=prop.id,
                label=prop.name,
                type=self._stringify_value_type(prop.value_type),
                value=prop.current_value,
                default_value=prop.default_value,
                options=list(prop.options or []),
                editable=prop.editable,
                description=prop.description,
                category=prop.category,
                sensitive=prop.sensitive,
            )
        # Legacy PropertyMetadata
        return PropertyPresentation(
            name=prop.name,
            label=prop.label,
            type=prop.type,
            value=prop.value,
            options=list(prop.options or []),
            editable=prop.editable,
            description=prop.description,
        )

    def _adapt_statistic(self, stat) -> StatisticPresentation:
        if isinstance(stat, MetadataStatistics):
            return StatisticPresentation(
                name=stat.id,
                label=stat.name,
                value=stat.value,
                unit=stat.unit or "text",
                timestamp=stat.timestamp,
            )
        # Legacy StatisticMetadata
        return StatisticPresentation(
            name=stat.name,
            label=stat.label,
            value=stat.value,
            format=stat.format,
            description=stat.description,
        )

    def _adapt_action(self, action) -> ActionPresentation:
        if isinstance(action, MetadataAction):
            return ActionPresentation(
                name=action.id,
                label=action.label,
                icon=action.icon,
                description=action.description,
                enabled=action.enabled,
            )
        # Legacy ActionMetadata
        return ActionPresentation(
            name=action.name,
            label=action.label,
            icon=action.icon,
            description=action.description,
        )

    @staticmethod
    def _stringify_value_type(value_type: Any) -> str:
        """把 ValueType 枚举或字符串统一转换为 UI 可用的字符串。"""
        if isinstance(value_type, ValueType):
            return value_type.value
        if isinstance(value_type, str):
            return value_type
        if value_type is None:
            return ValueType.STRING.value
        return str(value_type)

    @staticmethod
    def _infer_view_schema_id(module_type: str, module_id: str) -> str:
        """根据 module 类型推断默认 ViewSchema ID。

        与 ViewSchemaRegistry._infer_schema_id 保持对齐，只负责生成默认值。
        """
        if module_type == "settings":
            return "settings_workspace"
        if module_type == "trace":
            return "trace_workspace"
        if module_type == "workspace":
            if module_id == "chat":
                return "chat_workspace"
            if module_id == "skill":
                return "skill_workspace"
            if module_id == "tool":
                return "tool_workspace"
        if module_type in ("model", "memory", "prompt", "strategy"):
            return "config_workspace"
        return "generic_workspace"


# Runtime-checkable Protocol 注册：PresentationMetadataAdapter 满足 MetadataAdapter 协议。
if hasattr(MetadataAdapterProtocol, "register"):
    MetadataAdapterProtocol.register(PresentationMetadataAdapter)


# 向后兼容别名：旧代码导入 MetadataAdapter 时仍指向 PresentationMetadataAdapter。
MetadataAdapter = PresentationMetadataAdapter
