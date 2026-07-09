"""agent_workbench/ui/workbench/view_schema_registry.py — ViewSchema 注册表。

提供默认布局协议，并支持按 module type / view_schema_id 解析。

设计原则：
- 默认 Schema 只描述「常见模块类型」的通用布局。
- 具体 Capability 可以通过 Metadata 声明自己的 `view_schema_id` 覆盖默认布局。
- Registry 不依赖 Qt，只返回纯数据 ViewSchema。
"""
from __future__ import annotations

from agent_workbench.ui.workbench.presentation import ModulePresentation
from agent_workbench.ui.workbench.view_schema import (
    BindingSource,
    DockSchema,
    InspectorSchema,
    InspectorTabSchema,
    StatusItemSchema,
    StatusSchema,
    ToolbarGroupSchema,
    ToolbarSchema,
    ViewSchema,
    WorkspaceSchema,
)


class ViewSchemaRegistry:
    """ViewSchema 注册表。"""

    def __init__(self) -> None:
        self._schemas: dict[str, ViewSchema] = {}
        self._register_defaults()

    def register(self, schema: ViewSchema) -> None:
        """注册一个 ViewSchema。"""
        self._schemas[schema.schema_id] = schema

    def get(self, schema_id: str) -> ViewSchema | None:
        """按 ID 获取已注册 Schema。"""
        return self._schemas.get(schema_id)

    def resolve(self, pres: ModulePresentation) -> ViewSchema:
        """根据 ModulePresentation 解析最合适的 ViewSchema。

        优先级：
        1. pres.view_schema_id 显式指定。
        2. 按 pres.type 推断默认 schema。
        3. 回退到 generic_workspace。
        """
        if pres.view_schema_id and pres.view_schema_id in self._schemas:
            return self._schemas[pres.view_schema_id]
        inferred = self._infer_schema_id(pres)
        return self._schemas.get(inferred, self._schemas["generic_workspace"])

    @staticmethod
    def _infer_schema_id(pres: ModulePresentation) -> str:
        if pres.type == "settings":
            return "settings_workspace"
        if pres.type == "trace":
            return "trace_workspace"
        if pres.type == "workspace":
            if pres.id == "chat":
                return "chat_workspace"
            if pres.id == "skill":
                return "skill_workspace"
            if pres.id == "tool":
                return "tool_workspace"
        if pres.type in ("model", "memory", "prompt", "strategy"):
            return "config_workspace"
        return "generic_workspace"

    def _register_defaults(self) -> None:
        """注册 Workbench 内置默认布局。"""
        self.register(_build_chat_workspace())
        self.register(_build_settings_workspace())
        self.register(_build_trace_workspace())
        self.register(_build_config_workspace())
        self.register(_build_skill_workspace())
        self.register(_build_tool_workspace())
        self.register(_build_generic_workspace())


def _build_chat_workspace() -> ViewSchema:
    return ViewSchema(
        schema_id="chat_workspace",
        name="Chat Workspace",
        description="对话工作区：输入框、历史消息、快捷操作。",
        workspace=WorkspaceSchema(
            toolbar=ToolbarSchema(items=[]),
            inspector=InspectorSchema(
                tabs=[
                    InspectorTabSchema(id="properties", title="Session", source="properties"),
                    InspectorTabSchema(id="statistics", title="Stats", source="statistics"),
                ],
                default_tab="properties",
            ),
            status=StatusSchema(
                items=[
                    StatusItemSchema(name="runtime", source="binding", binding=BindingSource(path="runtime.status")),
                    StatusItemSchema(name="provider", source="binding", binding=BindingSource(path="runtime.provider")),
                    StatusItemSchema(name="model", source="binding", binding=BindingSource(path="runtime.model")),
                    StatusItemSchema(name="session", source="binding", binding=BindingSource(path="runtime.session")),
                ]
            ),
        ),
    )


def _build_settings_workspace() -> ViewSchema:
    return ViewSchema(
        schema_id="settings_workspace",
        name="Settings Workspace",
        description="配置工作区：分组展示属性，顶部提供保存/重置/应用操作。",
        workspace=WorkspaceSchema(
            toolbar=ToolbarSchema(
                items=[
                    ToolbarGroupSchema(name="primary", items=["save", "apply", "reset"]),
                ]
            ),
            inspector=InspectorSchema(
                tabs=[
                    InspectorTabSchema(id="properties", title="Settings", source="properties"),
                    InspectorTabSchema(id="actions", title="Actions", source="actions"),
                ],
                default_tab="properties",
            ),
            status=StatusSchema(
                items=[
                    StatusItemSchema(name="runtime", source="binding", binding=BindingSource(path="runtime.status")),
                ]
            ),
        ),
    )


def _build_trace_workspace() -> ViewSchema:
    return ViewSchema(
        schema_id="trace_workspace",
        name="Trace Workspace",
        description="追踪工作区：展示执行链路、耗时、Token 统计。",
        workspace=WorkspaceSchema(
            toolbar=ToolbarSchema(items=["refresh", "export", "clear"]),
            inspector=InspectorSchema(
                tabs=[
                    InspectorTabSchema(id="statistics", title="Metrics", source="statistics"),
                    InspectorTabSchema(id="properties", title="Details", source="properties"),
                ],
                default_tab="statistics",
            ),
            status=StatusSchema(
                items=[
                    StatusItemSchema(name="runtime", source="binding", binding=BindingSource(path="runtime.status")),
                    StatusItemSchema(name="latency", source="binding", binding=BindingSource(path="runtime.latency", format="{:.2f} ms")),
                ]
            ),
            docks=[
                DockSchema(region="right", title="Trace Tree", tab_source="properties"),
            ],
        ),
    )


def _build_config_workspace() -> ViewSchema:
    return ViewSchema(
        schema_id="config_workspace",
        name="Config Workspace",
        description="通用配置型模块：属性、统计、操作三栏。",
        workspace=WorkspaceSchema(
            toolbar=ToolbarSchema(
                items=[
                    ToolbarGroupSchema(name="primary", items=["save", "refresh"]),
                ]
            ),
            inspector=InspectorSchema(
                tabs=[
                    InspectorTabSchema(id="properties", title="Properties", source="properties"),
                    InspectorTabSchema(id="statistics", title="Statistics", source="statistics"),
                    InspectorTabSchema(id="actions", title="Actions", source="actions"),
                ],
                default_tab="properties",
            ),
            status=StatusSchema(
                items=[
                    StatusItemSchema(name="runtime", source="binding", binding=BindingSource(path="runtime.status")),
                ]
            ),
        ),
    )


def _build_skill_workspace() -> ViewSchema:
    return ViewSchema(
        schema_id="skill_workspace",
        name="Skill Workspace",
        description="技能工作区：脚本、参数、测试运行。",
        workspace=WorkspaceSchema(
            toolbar=ToolbarSchema(
                items=[
                    ToolbarGroupSchema(name="primary", items=["run", "edit", "delete"]),
                    ToolbarGroupSchema(name="secondary", items=["export", "duplicate"]),
                ]
            ),
            inspector=InspectorSchema(
                tabs=[
                    InspectorTabSchema(id="properties", title="Config", source="properties"),
                    InspectorTabSchema(id="actions", title="Actions", source="actions"),
                ],
                default_tab="properties",
            ),
            status=StatusSchema(
                items=[
                    StatusItemSchema(name="runtime", source="binding", binding=BindingSource(path="runtime.status")),
                ]
            ),
        ),
    )


def _build_tool_workspace() -> ViewSchema:
    return ViewSchema(
        schema_id="tool_workspace",
        name="Tool Workspace",
        description="工具工作区：参数输入、执行、结果查看。",
        workspace=WorkspaceSchema(
            toolbar=ToolbarSchema(
                items=[
                    ToolbarGroupSchema(name="primary", items=["run", "test"]),
                    ToolbarGroupSchema(name="secondary", items=["docs", "settings"]),
                ]
            ),
            inspector=InspectorSchema(
                tabs=[
                    InspectorTabSchema(id="properties", title="Parameters", source="properties"),
                    InspectorTabSchema(id="actions", title="Actions", source="actions"),
                ],
                default_tab="properties",
            ),
            status=StatusSchema(
                items=[
                    StatusItemSchema(name="runtime", source="binding", binding=BindingSource(path="runtime.status")),
                ]
            ),
        ),
    )


def _build_generic_workspace() -> ViewSchema:
    return ViewSchema(
        schema_id="generic_workspace",
        name="Generic Workspace",
        description="默认工作区：无专属布局时的兜底。",
        workspace=WorkspaceSchema(
            toolbar=ToolbarSchema(items=[]),
            inspector=InspectorSchema(
                tabs=[
                    InspectorTabSchema(id="properties", title="Properties", source="properties"),
                    InspectorTabSchema(id="statistics", title="Statistics", source="statistics"),
                    InspectorTabSchema(id="actions", title="Actions", source="actions"),
                ],
                default_tab="properties",
            ),
            status=StatusSchema(
                items=[
                    StatusItemSchema(name="runtime", source="binding", binding=BindingSource(path="runtime.status")),
                    StatusItemSchema(name="provider", source="binding", binding=BindingSource(path="runtime.provider")),
                    StatusItemSchema(name="model", source="binding", binding=BindingSource(path="runtime.model")),
                ]
            ),
        ),
    )
