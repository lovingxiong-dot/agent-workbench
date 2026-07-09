"""agent_workbench/ui/workbench/metadata_adapter.py — Metadata → PresentationModel 适配器。

这是 Runtime 与 UI 之间的唯一翻译层：
- 输入：Runtime 提供的 Capability Metadata（不知道 UI 存在）。
- 输出：UI 层 PresentationModel（不知道 RuntimeModule 存在）。
"""
from __future__ import annotations

from agent_workbench.metadata import (
    MetadataAction,
    MetadataDefinition,
    MetadataProperty,
    MetadataStatistics,
)
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


class MetadataAdapter:
    """将 Runtime Capability Metadata 转换为 UI PresentationModel。

    同时兼容旧 ModuleMetadata（v6.10.x）与新 MetadataDefinition（v6.11.x），
    让 Runtime 模块可以逐步迁移。
    """

    def adapt(self, metadata: ModuleMetadata | MetadataDefinition) -> ModulePresentation:
        return ModulePresentation(
            id=metadata.id,
            type=metadata.type,
            name=metadata.name,
            description=metadata.description,
            icon=metadata.icon,
            properties=[self._adapt_property(p) for p in metadata.properties],
            statistics=[self._adapt_statistic(s) for s in metadata.statistics],
            actions=[self._adapt_action(a) for a in metadata.actions],
        )

    def _adapt_property(self, prop) -> PropertyPresentation:
        if isinstance(prop, MetadataProperty):
            return PropertyPresentation(
                name=prop.id,
                label=prop.name,
                type=prop.value_type if isinstance(prop.value_type, str) else prop.value_type.value,
                value=prop.current_value,
                options=list(prop.options or []),
                editable=prop.editable,
                description=prop.description,
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
                format=stat.unit or "text",
                description="",
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
            )
        # Legacy ActionMetadata
        return ActionPresentation(
            name=action.name,
            label=action.label,
            icon=action.icon,
            description=action.description,
        )
