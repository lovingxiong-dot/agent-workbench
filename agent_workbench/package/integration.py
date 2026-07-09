"""agent_workbench/package/integration.py — Package → Metadata / ViewSchema 桥接。

职责：
- 将 PackageInfo 转换为 Cross-layer MetadataDefinition。
- 将 Package 的 view_schema.json 解析为 ViewSchema 对象。
- 将 MetadataDefinition 适配为 UI ModulePresentation。

设计约束：
- 不依赖 Qt。
- Package 无权注册 Renderer。
- 对 UI 层的导入全部延迟到方法内部，避免 package 子模块被导入时触发 UI 初始化。
"""
from __future__ import annotations

from typing import Any

from agent_workbench.metadata import (
    MetadataAction,
    MetadataDefinition,
    MetadataProperty,
    MetadataStatistics,
)
from agent_workbench.metadata.types import ValueType
from agent_workbench.package.package_info import PackageInfo


class PackageIntegration:
    """Package 内容到 Workbench 消费模型的集成器。"""

    def __init__(self, metadata_adapter: Any = None) -> None:
        if metadata_adapter is None:
            from agent_workbench.ui.workbench.metadata_adapter import (
                PresentationMetadataAdapter,
            )

            metadata_adapter = PresentationMetadataAdapter()
        self._metadata_adapter = metadata_adapter

    def to_metadata_definition(self, package: PackageInfo) -> MetadataDefinition:
        """将 PackageInfo.metadata 字典转换为 MetadataDefinition。"""
        meta = package.metadata
        if not isinstance(meta, dict):
            meta = {}

        return MetadataDefinition(
            id=meta.get("id") or package.manifest.id,
            type=meta.get("type", "agent"),
            name=meta.get("name", package.manifest.id),
            description=meta.get("description", ""),
            icon=meta.get("icon", ""),
            properties=[self._build_property(p) for p in meta.get("properties", [])],
            statistics=[self._build_statistic(s) for s in meta.get("statistics", [])],
            actions=[self._build_action(a) for a in meta.get("actions", [])],
            tags=list(meta.get("tags", [])),
            enabled=meta.get("enabled", True),
        )

    def to_module_presentation(self, package: PackageInfo) -> "ModulePresentation":
        """将 PackageInfo 转换为 UI ModulePresentation。"""
        definition = self.to_metadata_definition(package)
        presentation = self._metadata_adapter.adapt(definition)
        view_schema_id = ""
        if isinstance(package.view_schema, dict):
            view_schema_id = package.view_schema.get("schema_id", "")
        if view_schema_id:
            presentation.view_schema_id = view_schema_id
        return presentation

    def to_view_schema(self, package: PackageInfo) -> Any | None:
        """将 PackageInfo.view_schema 字典解析为 ViewSchema。"""
        from agent_workbench.ui.workbench.view_schema import (
            BindingSource,
            InspectorSchema,
            InspectorTabSchema,
            StatusItemSchema,
            StatusSchema,
            ToolbarGroupSchema,
            ToolbarSchema,
            ViewSchema,
            WorkspaceSchema,
        )

        data = package.view_schema
        if not isinstance(data, dict):
            return None
        try:
            return self._build_view_schema(
                data,
                view_schema_cls=ViewSchema,
                workspace_schema_cls=WorkspaceSchema,
                toolbar_schema_cls=ToolbarSchema,
                toolbar_group_schema_cls=ToolbarGroupSchema,
                inspector_schema_cls=InspectorSchema,
                inspector_tab_schema_cls=InspectorTabSchema,
                status_schema_cls=StatusSchema,
                status_item_schema_cls=StatusItemSchema,
                binding_source_cls=BindingSource,
            )
        except (KeyError, TypeError):
            return None

    @staticmethod
    def _build_property(data: dict[str, Any]) -> MetadataProperty:
        value_type = data.get("value_type", ValueType.STRING)
        if isinstance(value_type, str):
            try:
                value_type = ValueType(value_type)
            except ValueError:
                value_type = ValueType.STRING
        return MetadataProperty(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            value_type=value_type,
            current_value=data.get("current_value"),
            default_value=data.get("default_value"),
            options=list(data.get("options", [])),
            editable=data.get("editable", True),
            sensitive=data.get("sensitive", False),
            category=data.get("category", ""),
        )

    @staticmethod
    def _build_statistic(data: dict[str, Any]) -> MetadataStatistics:
        return MetadataStatistics(
            id=data.get("id", ""),
            name=data.get("name", ""),
            value=data.get("value"),
            unit=data.get("unit", ""),
        )

    @staticmethod
    def _build_action(data: dict[str, Any]) -> MetadataAction:
        return MetadataAction(
            id=data.get("id", ""),
            label=data.get("label", ""),
            description=data.get("description", ""),
            icon=data.get("icon", ""),
            enabled=data.get("enabled", True),
        )

    @staticmethod
    def _build_view_schema(
        data: dict[str, Any],
        *,
        view_schema_cls,
        workspace_schema_cls,
        toolbar_schema_cls,
        toolbar_group_schema_cls,
        inspector_schema_cls,
        inspector_tab_schema_cls,
        status_schema_cls,
        status_item_schema_cls,
        binding_source_cls,
    ) -> Any:
        workspace_data = data.get("workspace", {})
        return view_schema_cls(
            schema_id=data["schema_id"],
            name=data.get("name", ""),
            description=data.get("description", ""),
            workspace=workspace_schema_cls(
                toolbar=PackageIntegration._build_toolbar(
                    workspace_data.get("toolbar", {}),
                    toolbar_schema_cls=toolbar_schema_cls,
                    toolbar_group_schema_cls=toolbar_group_schema_cls,
                ),
                inspector=PackageIntegration._build_inspector(
                    workspace_data.get("inspector", {}),
                    inspector_schema_cls=inspector_schema_cls,
                    inspector_tab_schema_cls=inspector_tab_schema_cls,
                ),
                status=PackageIntegration._build_status(
                    workspace_data.get("status", {}),
                    status_schema_cls=status_schema_cls,
                    status_item_schema_cls=status_item_schema_cls,
                    binding_source_cls=binding_source_cls,
                ),
                docks=[],
            ),
        )

    @staticmethod
    def _build_toolbar(
        data: dict[str, Any],
        *,
        toolbar_schema_cls,
        toolbar_group_schema_cls,
    ) -> Any:
        items: list[Any] = []
        for item in data.get("items", []):
            if isinstance(item, str):
                items.append(item)
            elif isinstance(item, dict):
                items.append(
                    toolbar_group_schema_cls(
                        name=item.get("name", ""),
                        items=list(item.get("items", [])),
                    )
                )
        return toolbar_schema_cls(items=items)

    @staticmethod
    def _build_inspector(
        data: dict[str, Any],
        *,
        inspector_schema_cls,
        inspector_tab_schema_cls,
    ) -> Any:
        tabs = [
            inspector_tab_schema_cls(
                id=tab.get("id", ""),
                title=tab.get("title", ""),
                source=tab.get("source", "properties"),
                categories=tab.get("categories"),
                collapsed=tab.get("collapsed", False),
            )
            for tab in data.get("tabs", [])
        ]
        return inspector_schema_cls(tabs=tabs, default_tab=data.get("default_tab", "properties"))

    @staticmethod
    def _build_status(
        data: dict[str, Any],
        *,
        status_schema_cls,
        status_item_schema_cls,
        binding_source_cls,
    ) -> Any:
        items: list[Any] = []
        for item in data.get("items", []):
            binding_data = item.get("binding")
            binding = None
            if isinstance(binding_data, dict):
                binding = binding_source_cls(
                    path=binding_data.get("path", ""),
                    format=binding_data.get("format"),
                )
            items.append(
                status_item_schema_cls(
                    name=item.get("name", ""),
                    source=item.get("source", "statistics"),
                    binding=binding,
                )
            )
        return status_schema_cls(items=items)
