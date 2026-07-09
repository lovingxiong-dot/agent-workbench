"""agent_workbench/ui/workbench/view_schema_renderer.py — ViewSchema Qt 渲染器。

职责：
- 接收 ViewSchema + ModulePresentation。
- 驱动 Workbench 各 Host（ToolBar / StatusBar / Inspector / Workspace）按 Schema 布局。
- 不处理业务逻辑，只负责「按 Schema 摆放已有 Presentation 数据」。

注意：Renderer 依赖 Qt，但 ViewSchema 本身不依赖 Qt。未来可为 Web / CLI 提供
不同 Renderer，共用同一套 ViewSchema。
"""
from __future__ import annotations

from agent_workbench.ui.workbench.presentation import (
    ActionPresentation,
    ModulePresentation,
    StatisticPresentation,
)
from agent_workbench.ui.workbench.view_schema import StatusItemSchema, ToolbarGroupSchema, ViewSchema


class ViewSchemaRenderer:
    """将 ViewSchema + ModulePresentation 应用到 Workbench Qt Host。"""

    def __init__(self, workbench_ui) -> None:
        """Args:
            workbench_ui: Workbench widget 实例（含 tool_bar / status_bar / inspector / workspace）。
        """
        self._ui = workbench_ui

    def render(self, schema: ViewSchema, presentation: ModulePresentation, runtime_status: dict[str, str] | None = None) -> None:
        """按 Schema 渲染完整 Workbench 布局。"""
        self._render_toolbar(schema, presentation)
        self._render_status_bar(schema, presentation, runtime_status or {})
        self._render_inspector(schema, presentation)
        self._render_workspace(schema, presentation)

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

    def _render_status_bar(
        self,
        schema: ViewSchema,
        presentation: ModulePresentation,
        runtime_status: dict[str, str],
    ) -> None:
        """根据 StatusSchema 从 presentation.statistics 与 runtime_status 中提取统计项。"""
        stat_map = {stat.name: stat for stat in presentation.statistics}
        statistics: list[StatisticPresentation] = []

        for item in schema.workspace.status.items:
            if item.source == "runtime" and item.name in runtime_status:
                statistics.append(
                    StatisticPresentation(
                        name=item.name,
                        label=item.name.capitalize(),
                        value=runtime_status[item.name],
                    )
                )
            elif item.source == "statistics" and item.name in stat_map:
                statistics.append(stat_map[item.name])

        # Schema 未声明的 statistics 追加到末尾
        schema_names = {item.name for item in schema.workspace.status.items}
        for stat in presentation.statistics:
            if stat.name not in schema_names:
                statistics.append(stat)

        self._ui.status_bar.set_statistics(statistics)

    def _render_inspector(self, schema: ViewSchema, presentation: ModulePresentation) -> None:
        """将 InspectorSchema 设置到 Inspector，再渲染 PresentationModel。"""
        self._ui.inspector.set_schema(schema.workspace.inspector)
        self._ui.inspector.set_object(presentation)

    def _render_workspace(self, schema: ViewSchema, presentation: ModulePresentation) -> None:
        """根据 WorkspaceSchema 或 presentation 类型切换 Workspace。"""
        # Workspace 切换逻辑仍保留在 Controller 的静态映射中；Renderer 负责触发
        from agent_workbench.ui.workbench_ui_controller import WorkbenchUIController

        workspace_id = WorkbenchUIController._resolve_workspace_id(presentation)
        self._ui.workspace.switch_to(workspace_id)
