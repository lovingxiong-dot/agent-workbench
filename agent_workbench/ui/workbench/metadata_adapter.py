"""agent_workbench/ui/workbench/metadata_adapter.py — Metadata → PresentationModel 适配器。

这是 Runtime 与 UI 之间的唯一翻译层：
- 输入：Runtime 提供的 Capability Metadata（不知道 UI 存在）。
- 输出：UI 层 PresentationModel（不知道 RuntimeModule 存在）。
"""
from __future__ import annotations

from agent_workbench.runtime.metadata import ModuleMetadata
from agent_workbench.ui.workbench.presentation import (
    ActionPresentation,
    ModulePresentation,
    PropertyPresentation,
    StatisticPresentation,
)


class MetadataAdapter:
    """将 Runtime Capability Metadata 转换为 UI PresentationModel。"""

    def adapt(self, metadata: ModuleMetadata) -> ModulePresentation:
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

    @staticmethod
    def _adapt_property(prop) -> PropertyPresentation:
        return PropertyPresentation(
            name=prop.name,
            label=prop.label,
            type=prop.type,
            value=prop.value,
            options=list(prop.options or []),
            editable=prop.editable,
            description=prop.description,
        )

    @staticmethod
    def _adapt_statistic(stat) -> StatisticPresentation:
        return StatisticPresentation(
            name=stat.name,
            label=stat.label,
            value=stat.value,
            format=stat.format,
            description=stat.description,
        )

    @staticmethod
    def _adapt_action(action) -> ActionPresentation:
        return ActionPresentation(
            name=action.name,
            label=action.label,
            icon=action.icon,
            description=action.description,
        )
