"""agent_workbench/ui/workbench/view_schema_renderer.py — ViewSchema Qt 渲染器。

职责：
- 接收 ViewSchema + ModulePresentation + BindingContext。
- 驱动 Workbench 各 Host（ToolBar / StatusBar / Inspector / Workspace）按 Schema 布局。
- 通过 BindingContext 解析 Runtime 数据，Renderer 不直接访问 Runtime 对象。

注意：Renderer 依赖 Qt，但 ViewSchema / BindingContext 本身不依赖 Qt。未来可为 Web / CLI
提供不同 Renderer，共用同一套 ViewSchema + Binding。
"""
from __future__ import annotations

from agent_workbench.ui.workbench.binding_context import BindingContext
from agent_workbench.ui.workbench.presentation import (
    ActionPresentation,
    ModulePresentation,
    PropertyPresentation,
    StatisticPresentation,
)
from agent_workbench.ui.workbench.view_schema import StatusItemSchema, ToolbarGroupSchema, ViewSchema


class ViewSchemaRenderer:
    """将 ViewSchema + ModulePresentation + BindingContext 应用到 Workbench Qt Host。"""

    def __init__(self, workbench_ui, binding_context: BindingContext | None = None) -> None:
        """Args:
            workbench_ui: Workbench widget 实例（含 tool_bar / status_bar / inspector / workspace）。
            binding_context: 动态数据绑定上下文；为空时自动创建空上下文。
        """
        self._ui = workbench_ui
        self._binding = binding_context or BindingContext()

    @property
    def binding_context(self) -> BindingContext:
        return self._binding

    def render(self, schema: ViewSchema, presentation: ModulePresentation) -> None:
        """按 Schema 渲染完整 Workbench 布局。"""
        self._render_toolbar(schema, presentation)
        self._render_status_bar(schema, presentation)
        self._render_inspector(schema, presentation)
        self._render_workspace(schema, presentation)

    def refresh(self, schema: ViewSchema, presentation: ModulePresentation) -> None:
        """仅刷新受 Binding 影响的 UI 区域（StatusBar / Inspector properties）。"""
        self._render_status_bar(schema, presentation)
        self._render_inspector_values(schema, presentation)

    def _render_toolbar(self, schema: ViewSchema, presentation: ModulePresentation) -> None:
        """根据 ToolbarSchema 从 presentation.actions 中提取并排序 action。"""
        toolbar = schema.workspace.toolbar
        action_map = {action.name: action for action in presentation.actions}
        ordered_actions: list[ActionPresentation] = []

        for item in toolbar.items:
            if isinstance(item, ToolbarGroupSchema):
                for action_name in item.items:
                    if action_name in action_map:
                        ordered_actions.append(action_map[action_name])
            elif isinstance(item, str) and item in action_map:
                ordered_actions.append(action_map[item])

        # 未在 Schema 中声明的 action 追加到末尾，保证功能不丢失
        schema_names = {a.name for a in ordered_actions}
        for action in presentation.actions:
            if action.name not in schema_names:
                ordered_actions.append(action)

        self._ui.tool_bar.set_actions(ordered_actions)

    def _render_status_bar(self, schema: ViewSchema, presentation: ModulePresentation) -> None:
        """根据 StatusSchema 从 presentation.statistics 与 BindingContext 中提取统计项。"""
        stat_map = {stat.name: stat for stat in presentation.statistics}
        statistics: list[StatisticPresentation] = []

        for item in schema.workspace.status.items:
            stat = self._resolve_status_item(item, stat_map)
            if stat is not None:
                statistics.append(stat)

        # Schema 未声明的 statistics 追加到末尾
        schema_names = {item.name for item in schema.workspace.status.items}
        for stat in presentation.statistics:
            if stat.name not in schema_names:
                statistics.append(stat)

        self._ui.status_bar.set_statistics(statistics)

    def _resolve_status_item(
        self, item: StatusItemSchema, stat_map: dict[str, StatisticPresentation]
    ) -> StatisticPresentation | None:
        """解析单个 StatusItemSchema：支持 statistics / binding / runtime（兼容旧 schema）。"""
        if item.source == "binding" and item.binding is not None:
            value = self._binding.resolve(item.binding)
            return StatisticPresentation(
                name=item.name,
                label=item.name.replace("_", " ").title(),
                value=value if value is not None else "—",
            )
        if item.source == "statistics" and item.name in stat_map:
            return stat_map[item.name]
        if item.source == "runtime":
            # 兼容旧 schema：从 binding 的 runtime namespace 读取
            value = self._binding.resolve_path(f"runtime.{item.name}")
            return StatisticPresentation(
                name=item.name,
                label=item.name.replace("_", " ").title(),
                value=value if value is not None else "—",
            )
        return None

    def _render_inspector(self, schema: ViewSchema, presentation: ModulePresentation) -> None:
        """将 InspectorSchema 设置到 Inspector，并应用动态绑定后的 PresentationModel。"""
        bound_presentation = self._apply_property_bindings(presentation)
        self._ui.inspector.set_schema(schema.workspace.inspector)
        self._ui.inspector.set_object(bound_presentation)

    def _render_inspector_values(self, schema: ViewSchema, presentation: ModulePresentation) -> None:
        """仅刷新 Inspector 中的动态绑定值（不改变 schema / 布局）。"""
        bound_presentation = self._apply_property_bindings(presentation)
        self._ui.inspector.set_object(bound_presentation)

    def _apply_property_bindings(self, presentation: ModulePresentation) -> ModulePresentation:
        """为带有 binding 的 PropertyPresentation 注入 Runtime 当前值。"""
        if not any(prop.binding is not None for prop in presentation.properties):
            return presentation

        new_properties: list[PropertyPresentation] = []
        for prop in presentation.properties:
            if prop.binding is not None and not prop.editable:
                value = self._binding.resolve(prop.binding)
                if value is None:
                    value = prop.value
                new_properties.append(
                    PropertyPresentation(
                        name=prop.name,
                        label=prop.label,
                        type=prop.type,
                        value=value,
                        options=prop.options,
                        editable=prop.editable,
                        description=prop.description,
                        default_value=prop.default_value,
                        category=prop.category,
                        sensitive=prop.sensitive,
                        placeholder=prop.placeholder,
                        required=prop.required,
                        binding=prop.binding,
                    )
                )
            else:
                new_properties.append(prop)

        return ModulePresentation(
            id=presentation.id,
            type=presentation.type,
            name=presentation.name,
            description=presentation.description,
            icon=presentation.icon,
            properties=new_properties,
            statistics=presentation.statistics,
            actions=presentation.actions,
            tags=presentation.tags,
            enabled=presentation.enabled,
            order=presentation.order,
            category=presentation.category,
            view_schema_id=presentation.view_schema_id,
            children=presentation.children,
            connection=presentation.connection,
        )

    def _render_workspace(self, schema: ViewSchema, presentation: ModulePresentation) -> None:
        """根据 WorkspaceSchema 或 presentation 类型切换 Workspace。"""
        # Workspace 切换逻辑仍保留在 Controller 的静态映射中；Renderer 负责触发
        from agent_workbench.ui.workbench_ui_controller import WorkbenchUIController

        workspace_id = WorkbenchUIController._resolve_workspace_id(presentation)
        self._ui.workspace.switch_to(workspace_id)
