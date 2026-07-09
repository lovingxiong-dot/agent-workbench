"""agent_workbench/ui/workbench_ui_controller.py — V6 UI 与 Agent Workbench Runtime 的桥梁。

设计边界：
- 复用 v6.ui_controller.UIController 的 Session/Chat/Config 服务与信号契约，
  保证会话管理、消息历史等基础能力可工作。
- 聊天请求不再提交给 v6 LocalRuntimeAdapter，而是转发给
  agent_workbench.controller.WorkbenchController，使 Inspector 中调整的模型、
  Prompt、工具、Memory 等参数真正影响当前对话。
- Workbench UI（Navigator / WorkspaceHost / Inspector / StatusBar / CommandBar）
  通过信号与本控制器交互；控制器不持有 UI 具体类型，只通过 host 引用访问。
"""
from __future__ import annotations

import os
import threading
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from PySide6.QtWidgets import QDialog, QWidget

from v6.runtime.adapter import IRuntimeAdapter
from v6.runtime.context import RuntimeContext
from v6.runtime.event_bus import RuntimeEvent, RuntimeEventType
from v6.ui_controller import UIController

from agent_workbench.controller import WorkbenchController
from agent_workbench.conversation import ConversationService
from agent_workbench.package import PackageIntegration, PackageRegistry
from agent_workbench.ui.configuration import ConfigCategory, ConfigurationManager
from agent_workbench.ui.dialogs import (
    AddMcpDialog,
    AddMemoryDialog,
    AddPromptDialog,
    AddProviderDialog,
    AddSkillDialog,
    AddWorkflowDialog,
)
from agent_workbench.runtime.modules.model_module import ModelModule
from agent_workbench.ui.workbench import WorkbenchHost
from agent_workbench.ui.workbench.binding_context import BindingContext, BindingProvider
from agent_workbench.ui.workbench.chat_workspace import ChatWorkspaceItem
from agent_workbench.ui.workbench.generic_workspace import GenericWorkspaceItem
from agent_workbench.ui.workbench.metadata_adapter import PresentationMetadataAdapter
from agent_workbench.ui.workbench.presentation import (
    ActionPresentation,
    ModulePresentation,
    PropertyPresentation,
    StatisticPresentation,
)
from agent_workbench.ui.workbench.trace_workspace import TraceWorkspaceItem
from agent_workbench.ui.workbench.view_schema_registry import ViewSchemaRegistry
from agent_workbench.ui.workbench.view_schema_renderer import ViewSchemaRenderer
from agent_workbench.ui.workbench.welcome_workspace import WelcomeWorkspaceItem

if TYPE_CHECKING:
    from v6.services.chat_service import ChatService
    from v6.services.config_service import ConfigService
    from v6.services.session_service import SessionService


class NoopRuntimeAdapter(IRuntimeAdapter):
    """占位 Runtime Adapter，避免 v6 UIController 自行启动额外的 AgentRuntime。"""

    def __init__(self) -> None:
        self._callbacks: dict[str, list[Callable[[RuntimeEvent], None]]] = {}

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def submit(self, ctx: RuntimeContext) -> str:
        return ctx.task_id

    def cancel(self, task_id: str) -> bool:
        return True

    def subscribe(self, event_type: str, callback: Callable[[RuntimeEvent], None]) -> None:
        self._callbacks.setdefault(event_type, []).append(callback)


class WorkbenchUIController(UIController):
    """Agent Workbench 专用 UI 控制器。"""

    def __init__(
        self,
        parent=None,
        config_service: "ConfigService | None" = None,
        session_service: "SessionService | None" = None,
        chat_service: "ChatService | None" = None,
        workbench: WorkbenchController | None = None,
        data_dir: str | os.PathLike | None = None,
        workbench_host: WorkbenchHost | None = None,
        config_path: str | None = None,
        packages_dir: str | os.PathLike | None = None,
    ) -> None:
        self._workbench = workbench or WorkbenchController(config_path=config_path)
        self._host = workbench_host
        self._chat_workspace: ChatWorkspaceItem | None = None
        self._trace_workspace: TraceWorkspaceItem | None = None
        self._generic_workspace: GenericWorkspaceItem | None = None
        self._welcome_workspace: WelcomeWorkspaceItem | None = None
        self._metadata_adapter = PresentationMetadataAdapter()
        self._view_schema_registry = ViewSchemaRegistry()
        self._binding_context = BindingContext()
        self._register_runtime_binding_provider()
        self._view_schema_renderer: ViewSchemaRenderer | None = None
        self._current_module_id: str | None = None
        self._presentations: dict[str, ModulePresentation] = {}
        self._config_manager = ConfigurationManager()
        self._register_configuration_categories()
        self._packages_dir = self._resolve_packages_dir(packages_dir, config_path)
        self._package_registry = PackageRegistry(self._packages_dir)
        self._package_integration = PackageIntegration(self._metadata_adapter)
        self._workbench = workbench or WorkbenchController(
            config_path=config_path,
            package_registry=self._package_registry,
        )
        super().__init__(
            parent=parent,
            config_service=config_service,
            session_service=session_service,
            chat_service=chat_service,
            adapter=NoopRuntimeAdapter(),
            data_dir=data_dir,
        )
        self._conversation_service = ConversationService(self._session, self._chat)

    def _register_runtime_binding_provider(self) -> None:
        """将 Workbench Runtime 核心状态注册为 BindingProvider。"""

        def runtime_getter(path: str) -> Any:
            status = self._runtime_status()
            return status.get(path)

        self._binding_context.registry.register(BindingProvider(namespace="runtime", getter=runtime_getter))

    @property
    def workbench_controller(self) -> WorkbenchController:
        """暴露给 UI 使用的 Workbench 控制器。"""
        return self._workbench

    @property
    def interaction_layer(self):
        """暴露 Interaction Boundary Layer，供未来 UI 组件非阻塞提交请求。"""
        return self._workbench.interaction_layer

    def _provider_types(self) -> list[str]:
        """从 ModelModule 注册表获取当前支持的所有 Provider 类型。"""
        model_module = self._workbench.runtime.module_registry.get("model")
        if isinstance(model_module, ModelModule):
            return model_module.provider_types()
        return ["echo", "openai"]

    def _register_configuration_categories(self) -> None:
        """注册所有 Settings 配置分类并绑定新增对话框。"""
        categories = [
            ConfigCategory(
                category_id="model",
                title="AI Models",
                icon="🤖",
                config_path="model.providers",
                dialog_factory=lambda: AddProviderDialog(
                    self._host, provider_types=self._provider_types()
                ),
            ),
            ConfigCategory(
                category_id="mcp",
                title="MCP",
                icon="🔌",
                config_path="mcp.servers",
                dialog_factory=lambda: AddMcpDialog(self),
            ),
            ConfigCategory(
                category_id="skill",
                title="Skills",
                icon="🧩",
                config_path="skill.registry",
                dialog_factory=lambda: AddSkillDialog(self),
            ),
            ConfigCategory(
                category_id="workflow",
                title="Workflows",
                icon="🔄",
                config_path="workflow.templates",
                dialog_factory=lambda: AddWorkflowDialog(self),
            ),
            ConfigCategory(
                category_id="prompt",
                title="Prompts",
                icon="📝",
                config_path="prompt.templates",
                dialog_factory=lambda: AddPromptDialog(self),
            ),
            ConfigCategory(
                category_id="memory",
                title="Memory",
                icon="🧠",
                config_path="memory.configs",
                dialog_factory=lambda: AddMemoryDialog(self),
            ),
            ConfigCategory(
                category_id="knowledge",
                title="Knowledge",
                icon="📚",
                config_path="knowledge.bases",
                dialog_factory=None,
            ),
        ]
        for category in categories:
            self._config_manager.register(category)

    def startup(self) -> None:
        """启动 Workbench Runtime、初始化 Workbench UI、复用 v6 UI 初始化流程。"""
        self._workbench.start()
        self._load_packages()
        super().startup()
        self._setup_workbench_ui()
        self._wire_workbench_signals()
        self._refresh_navigator()
        self._refresh_status_bar()
        self._workbench.runtime.config.changed.connect(self._on_config_changed)
        self._subscribe_config_changes()

        # 订阅 Runtime EventBus 流式事件，映射到 UI 信号
        event_bus = self._workbench.core_runtime.event_bus
        event_bus.subscribe(RuntimeEventType.AI_CHUNK, self._on_ai_chunk)
        event_bus.subscribe(RuntimeEventType.AI_END, self._on_ai_end)
        event_bus.subscribe(RuntimeEventType.ENGINE_FAILED, self._on_engine_failed)

        # 没有激活会话时进入 Welcome / Home Workspace
        if not self._active_sid:
            self._show_welcome()

    def shutdown(self) -> None:
        """停止 Workbench Runtime，然后停止 v6 Adapter 占位。"""
        super().shutdown()
        self._workbench.stop()

    def _load_packages(self) -> None:
        """发现、加载并注册所有 Agent Packages 及其 ViewSchema。

        已加载但本次扫描未发现的 Package 会被自动卸载，使删除包后 Navigator
        可自动刷新。
        """
        try:
            manifests = self._package_registry.discover()
        except Exception:  # pragma: no cover - defensive
            return

        loaded_ids = {p.manifest.id for p in self._package_registry.list()}
        discovered_ids = {m.id for m in manifests}
        for package_id in loaded_ids - discovered_ids:
            self._package_registry.unload(package_id)

        for manifest in manifests:
            try:
                package = self._package_registry.load(manifest)
            except Exception:  # pragma: no cover - defensive
                continue
            view_schema = self._package_integration.to_view_schema(package)
            if view_schema is not None:
                self._view_schema_registry.register(view_schema)

    def _show_welcome(self) -> None:
        """显示 Welcome / Home Workspace。"""
        if self._host is None or self._welcome_workspace is None:
            return
        self._refresh_welcome()
        self._host.workbench.workspace.switch_to("welcome")
        self._host.workbench.inspector.set_schema(None)
        self._host.workbench.inspector.set_object(None)
        self._host.workbench.tool_bar.set_actions([])
        self._refresh_status_bar()

    def _refresh_welcome(self) -> None:
        """刷新 Welcome 页面上的动态内容。"""
        if self._welcome_workspace is None:
            return
        agents = [
            (p.manifest.id, p.metadata.get("name", p.manifest.id))
            for p in self._package_registry.list()
        ]
        self._welcome_workspace.set_installed_agents(agents)

        recent: list[str] = []
        for _gid, _title, sessions in self._conversation_service.list_groups():
            for session in sessions:
                recent.append(session.get("title") or session.get("sid", "Untitled"))
        self._welcome_workspace.set_recent_projects(recent[:10])

        project_path = self._project_path or ""
        project_name = os.path.basename(project_path) if project_path else "—"
        parent_dir = str(Path(project_path).parent) + os.sep if project_path else "—"
        self._welcome_workspace.set_project(project_name, parent_dir)

    def _on_welcome_new_agent(self) -> None:
        """Welcome 页面点击 + New Agent → 创建新会话并切换到 Chat Workspace。"""
        self.on_new_session()
        if self._host is not None and self._chat_workspace is not None:
            self._host.workbench.workspace.switch_to("chat")

    def _on_welcome_install_agent(self) -> None:
        """Welcome 页面点击 + Install Agent → 打开 packages 目录（占位）。"""
        import subprocess

        packages_dir = self._packages_dir
        try:
            subprocess.Popen(f'explorer "{packages_dir}"')
        except Exception:  # pragma: no cover - defensive
            pass

    def _on_welcome_documentation(self, key: str) -> None:
        """Welcome 页面点击文档链接（占位）。"""
        # 未来可打开对应文档页面或外部浏览器
        pass

    @staticmethod
    def _resolve_packages_dir(
        packages_dir: str | os.PathLike | None, config_path: str | None
    ) -> str:
        """解析 packages 目录：优先使用显式传入，其次从 config_path 推导，最后使用默认位置。"""
        if packages_dir is not None:
            return str(packages_dir)
        if config_path is not None:
            return str(Path(config_path).resolve().parent.parent / "packages")
        here = Path(__file__).resolve().parent.parent.parent
        return str(here / "packages")

    def _setup_workbench_ui(self) -> None:
        """装配 Workbench UI：Workspace、信号连接、状态栏初始化。"""
        if self._host is None:
            return

        # 注册 Workspace；切换逻辑由 PresentationModel 驱动
        self._chat_workspace = ChatWorkspaceItem()
        self._host.workbench.workspace.register_workspace("chat", self._chat_workspace)

        self._trace_workspace = TraceWorkspaceItem()
        self._host.workbench.workspace.register_workspace("trace", self._trace_workspace)

        self._generic_workspace = GenericWorkspaceItem()
        self._host.workbench.workspace.register_workspace("generic", self._generic_workspace)

        self._welcome_workspace = WelcomeWorkspaceItem()
        self._host.workbench.workspace.register_workspace("welcome", self._welcome_workspace)
        self._welcome_workspace.new_agent_requested.connect(self._on_welcome_new_agent)
        self._welcome_workspace.install_agent_requested.connect(self._on_welcome_install_agent)
        self._welcome_workspace.documentation_requested.connect(self._on_welcome_documentation)

        # ViewSchema Renderer：统一驱动 ToolBar / StatusBar / Inspector / Workspace
        self._view_schema_renderer = ViewSchemaRenderer(self._host.workbench, self._binding_context)

        # ToolBar → Inspector 同一条 action 通道
        self._host.workbench.tool_bar_action_triggered.connect(self._on_tool_bar_action_triggered)

        # CommandBar → 发送消息
        self._host.workbench.command_submitted.connect(self.on_send_msg)

        # Runtime 状态 → TitleBar
        self._host.set_status(True)

        # UIController 聊天信号 → ChatWorkspaceItem
        self.sign_chat_user.connect(self._chat_workspace.append_user)
        self.sign_chat_ai.connect(self._chat_workspace.append_ai)
        self.sign_stream_chunk.connect(self._chat_workspace.stream_chunk)
        self.sign_stream_end.connect(self._chat_workspace.stream_end)
        self.sign_set_streaming.connect(self._chat_workspace.set_streaming)
        self.sign_tool_executed.connect(self._chat_workspace.tool_executed)
        self.sign_confirm_required.connect(self._chat_workspace.confirm_required)

        # 订阅 Runtime Trace 事件
        event_bus = self._workbench.core_runtime.event_bus
        for event_type in (
            RuntimeEventType.TASK_STARTED,
            RuntimeEventType.CAPABILITY_RESOLVED,
            RuntimeEventType.ENGINE_SELECTED,
            RuntimeEventType.EXECUTION_STARTED,
            RuntimeEventType.PROVIDER_SELECTED,
            RuntimeEventType.REQUEST_SENT,
            RuntimeEventType.FIRST_TOKEN,
            RuntimeEventType.CHUNK_RECEIVED,
            RuntimeEventType.STREAM_FINISHED,
            RuntimeEventType.EXECUTION_FINISHED,
            RuntimeEventType.ENGINE_COMPLETED,
            RuntimeEventType.TASK_COMPLETED,
            RuntimeEventType.TASK_FAILED,
        ):
            event_bus.subscribe(event_type, self._on_trace_event)

        # 加载当前会话历史到 Chat Workspace
        if self._active_sid:
            self._load_session_history_to_workspace(self._active_sid)

    def _wire_workbench_signals(self) -> None:
        """连接 Workbench 骨架信号到控制器。"""
        if self._host is None:
            return
        workbench = self._host.workbench
        workbench.selection_changed.connect(self._on_selection_changed)
        workbench.property_changed.connect(self._on_property_changed)
        workbench.action_triggered.connect(self._on_action_triggered)
        workbench.navigator.add_requested.connect(self._on_add_requested)

    def _refresh_navigator(self) -> None:
        """从 ModulePresentation 列表重建 Navigator，移除硬编码 tab 注册。"""
        if self._host is None:
            return
        nav = self._host.workbench.navigator
        self._presentations.clear()

        presentations = self._build_navigator_presentations()
        nav.load_presentations(presentations)
        self._refresh_welcome()

    def _build_navigator_presentations(self) -> list[ModulePresentation]:
        """构造 Navigator 所需的 ModulePresentation 列表。

        包含固定功能 Workspace、已加载的 Agent Packages 与 Settings 配置分类；
        新增 Workspace 或 Package 时只需修改数据源，无需改动 Navigator。
        """
        presentations: list[ModulePresentation] = [
            ModulePresentation(id="chat", type="workspace", name="Chat", icon="💬", category="workspace"),
            ModulePresentation(id="skill", type="workspace", name="Skills", icon="🛠", category="workspace"),
            ModulePresentation(id="tool", type="workspace", name="Tools", icon="🔧", category="workspace"),
        ]
        for package in self._package_registry.list():
            pres = self._package_integration.to_module_presentation(package)
            pres.category = "agent"
            presentations.append(pres)
        for category in self._config_manager.list_categories():
            presentations.append(
                ModulePresentation(
                    id=category.category_id,
                    type="settings",
                    name=category.title,
                    icon=category.icon,
                    category="settings",
                )
            )
        return presentations

    def _on_add_requested(self, category_id: str) -> None:
        """Settings 分类 '+' 按钮 → 弹出配置对话框并追加到对应配置路径。"""
        category = self._config_manager.get(category_id)
        if category is None or category.dialog_factory is None:
            return

        dialog = category.dialog_factory()
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        item = dialog.result()
        if not item:
            return

        current = self._workbench.get_config_value(category.config_path, [])
        current.append(item)
        self._workbench.set_config_value(category.config_path, current)

    def _on_selection_changed(self, module_id: str) -> None:
        """Navigator 选中变化 → ViewSchemaRenderer 统一驱动各 UI Host。"""
        self._current_module_id = module_id
        pres = self._presentations.get(module_id)
        if pres is None:
            meta = self._workbench.get_module_metadata(module_id)
            if meta is not None:
                pres = self._metadata_adapter.adapt(meta)
                self._presentations[module_id] = pres
        if pres is None:
            package = self._package_registry.get(module_id)
            if package is not None:
                pres = self._package_integration.to_module_presentation(package)
                pres.category = "agent"
                self._presentations[module_id] = pres
        if pres is not None and self._host is not None and self._view_schema_renderer is not None:
            schema = self._view_schema_registry.resolve(pres)
            self._view_schema_renderer.render(schema, pres)
            # 兜底：generic workspace 需要额外传入模块信息
            workspace_id = self._resolve_workspace_id(pres)
            if workspace_id == "generic" and self._generic_workspace is not None:
                self._generic_workspace.set_module(pres.name, pres.description)

    def _runtime_status(self) -> dict[str, str]:
        """构造当前 Runtime 核心状态字典，供 ViewSchemaRenderer 使用。"""
        overview = self._workbench.get_overview()
        providers = self._workbench.get_config_value("model.providers", [])
        default_provider = overview.get("default_provider", "—")
        model_name = "—"
        for p in providers:
            if p.get("name") == default_provider:
                model_name = p.get("config", {}).get("model", "—")
                break
        return {
            "runtime": "online" if self._workbench.core_runtime.running else "stopped",
            "provider": default_provider,
            "model": model_name,
            "profile": overview.get("current_profile", "—"),
            "session": self._active_sid or "—",
            "memory": f"{overview.get('memory_count', 0)} records",
            "latency": "—",
        }

    def _switch_workspace(self, pres: ModulePresentation) -> None:
        """根据 ModulePresentation 类型切换到对应 Workspace（保留给 Renderer 调用）。"""
        if self._host is None:
            return
        workspace_id = self._resolve_workspace_id(pres)
        self._host.workbench.workspace.switch_to(workspace_id)

    @staticmethod
    def _resolve_workspace_id(pres: ModulePresentation) -> str:
        """将 ModulePresentation 映射为 Workspace ID。

        - workspace 类型按 id 切换（chat / skill / tool）。
        - settings / config 类型统一进入 generic（未来可扩展为 ConfigWorkspace）。
        - trace 类型进入 trace。
        - 其他进入 generic。
        """
        if pres.type == "trace":
            return "trace"
        if pres.type == "workspace":
            return pres.id if pres.id in ("chat", "skill", "tool") else "generic"
        return "generic"

    def _on_tool_bar_action_triggered(self, action_name: str) -> None:
        """ToolBar 按钮触发与 Inspector Action 同一条处理通道。"""
        if self._current_module_id is not None:
            self._on_action_triggered(self._current_module_id, action_name)

    def _on_property_changed(self, module_id: str, prop_name: str, value: object) -> None:
        """Inspector 属性变化 → ConfigStore 热更新 → Module 生效。"""
        if module_id == "config" and prop_name == "raw":
            # Config 原始 YAML 不自动写入，通过 Save 动作触发
            return

        pres = self._presentations.get(module_id)
        prop_type = "string"
        if pres is not None:
            prop = next((p for p in pres.properties if p.name == prop_name), None)
            if prop is not None:
                prop_type = prop.type

        converted = self._convert_property_value(value, prop_type)
        config_path = f"{module_id}.{prop_name}"
        self._workbench.set_config_value(config_path, converted)

        self._refresh_status_bar()
        self._on_selection_changed(module_id)

    def _convert_property_value(self, value: object, prop_type: str) -> object:
        """根据属性类型转换 Inspector 提交的值。"""
        if prop_type == "boolean":
            return bool(value)
        if prop_type == "number":
            try:
                return int(value)  # type: ignore[arg-type]
            except (ValueError, TypeError):
                try:
                    return float(value)  # type: ignore[arg-type]
                except (ValueError, TypeError):
                    return value
        return str(value)

    def _on_action_triggered(self, module_id: str, action_name: str) -> None:
        """Inspector 操作按钮 → Runtime / Package 动作。"""
        if module_id == "runtime":
            if action_name == "start":
                self._workbench.start()
            elif action_name == "stop":
                self._workbench.stop()
            elif action_name == "reload":
                runtime = self._workbench.runtime
                runtime.config._load()
                runtime.module_registry.apply_all(runtime.config)
        elif module_id == "config" and action_name == "save":
            pres = self._presentations.get("config")
            if pres is not None:
                raw_prop = next((p for p in pres.properties if p.name == "raw"), None)
                if raw_prop is not None:
                    import yaml
                    try:
                        data = yaml.safe_load(raw_prop.value)
                        if isinstance(data, dict):
                            self._workbench.runtime.config.replace(data)
                    except yaml.YAMLError:
                        pass
        elif self._package_registry.get(module_id) is not None:
            self._workbench.execute_agent_action(module_id, action_name)
            # 移除缓存的 Presentation，使下次重新构建时读取最新 statistics。
            self._presentations.pop(module_id, None)
        self._refresh_status_bar()
        self._on_selection_changed(module_id)

    def on_session_action(self, action: str, sid: str) -> None:
        """重写 v6 UIController：删除最后一个会话后自动回到 Welcome。"""
        super().on_session_action(action, sid)
        if action == "delete" and not self._active_sid:
            self._show_welcome()

    def _refresh_status_bar(self) -> None:
        """通过 ViewSchemaRenderer 刷新 StatusBar（无选中项时使用全局 Workbench Schema）。"""
        if self._host is None or self._view_schema_renderer is None:
            return
        schema = self._view_schema_registry.get("generic_workspace")
        if schema is None:
            return
        workbench_presentation = ModulePresentation(
            id="workbench",
            type="workbench",
            name="Workbench",
        )
        self._view_schema_renderer.render(schema, workbench_presentation)

    def _on_config_changed(self, path: str, value: object) -> None:
        """ConfigStore 通用变更信号 → 刷新 Navigator 与 StatusBar。"""
        self._refresh_navigator()
        self._refresh_status_bar()

    def _subscribe_config_changes(self) -> None:
        """订阅 ConfigStore 变更，刷新 StatusBar 与 Inspector。"""
        runtime = self._workbench.runtime
        for ns in runtime.module_registry.namespaces():
            runtime.config.subscribe(ns, lambda _path, _value, ns=ns: self._on_config_change(ns))

    def _on_config_change(self, namespace: str) -> None:
        """ConfigStore 变更通知 → 刷新 StatusBar 与当前 Inspector。"""
        self._refresh_status_bar()
        if self._current_module_id == namespace:
            self._presentations.pop(namespace, None)
            self._on_selection_changed(namespace)

    def _load_session_history_to_workspace(self, sid: str) -> None:
        """把当前会话历史加载到 Chat Workspace。"""
        if self._chat_workspace is None:
            return
        ctx = self._new_ctx(sid)
        self._chat.load(ctx)
        for msg in ctx.messages:
            if msg.role == "user":
                self._chat_workspace.append_user(msg.content)
            elif msg.role == "assistant":
                self._chat_workspace.append_ai(msg.content, "")

    def _load_session_view(self, sid: str) -> None:
        """加载会话标题与历史；空标题时显示默认占位。"""
        session = self._session.manager.get(sid)
        title = session.get("title") if session else ""
        if not title:
            title = self._conversation_service.DEFAULT_TITLE
        self.sign_set_title.emit(title, self._project_path)

        self._load_session_history_to_workspace(sid)

    def on_session_selected(self, sid: str) -> None:
        """切换会话：更新激活会话并刷新 Chat Workspace。"""
        super().on_session_selected(sid)
        if self._chat_workspace is not None:
            self._chat_workspace.clear_chat()
            self._load_session_history_to_workspace(sid)

    def on_new_session(self) -> None:
        """新建会话：通过 ConversationService 创建空标题会话，并清空 Chat Workspace。"""
        sid = self._conversation_service.create_conversation()
        self._active_sid = sid
        self._reload_sessions()
        self.sign_set_active_session.emit(sid)
        self.sign_set_title.emit(self._conversation_service.DEFAULT_TITLE, self._project_path)
        if self._chat_workspace is not None:
            self._chat_workspace.clear_chat()

    def on_settings_requested(self) -> None:
        """设置按钮占位（未来可切换 Inspector 到 Config 模块）。"""
        pass

    def _on_trace_event(self, event: RuntimeEvent) -> None:
        """Runtime Trace 事件 → Trace Workspace 追加最新步骤。"""
        if self._trace_workspace is None or not event.task_id:
            return
        timeline = self._workbench.trace_timeline(event.task_id)
        if timeline:
            self._trace_workspace.append_event(timeline[-1])

    def _on_ai_chunk(self, event: RuntimeEvent) -> None:
        """Runtime AI_CHUNK 事件 → UI 流式片段信号。"""
        with self._lock:
            if event.task_id != self._current_task_id:
                return
            text = event.payload.get("text", "")
            self._ai_parts.append(text)
        self.sign_stream_chunk.emit(text)

    def _finalize_stream(self, error: str | None = None) -> None:
        """原子化结束当前流式输出；确保 UI 终止信号只发射一次。"""
        with self._lock:
            if not self._streaming or getattr(self, "_stream_finalized", False):
                return
            self._stream_finalized = True
            self._streaming = False
            self._current_task_id = None
            self._current_session_id = None
            self._ai_parts = []
        if error:
            self.sign_chat_ai.emit(error, "error")
        self.sign_stream_end.emit()
        self.sign_set_streaming.emit(False)

    def _on_ai_end(self, event: RuntimeEvent) -> None:
        """Runtime AI_END 事件 → 结束当前流式输出。"""
        if event.task_id != self._current_task_id:
            return
        self._finalize_stream()

    def _on_engine_failed(self, event: RuntimeEvent) -> None:
        """Runtime ENGINE_FAILED 事件 → 显示错误并结束流式输出。"""
        if event.task_id != self._current_task_id:
            return
        error = event.payload.get("error", "生成失败")
        self._finalize_stream(f"[错误: {error}]")

    def on_send_msg(self, text: str) -> None:
        """用户发送消息：持久化用户消息并提交到 WorkbenchController 在后台线程执行。"""
        if not self._active_sid:
            self.on_new_session()
        sid = self._active_sid
        if sid is None:
            return

        self._conversation_service.store_user_message(sid, text)

        task_id = uuid.uuid4().hex
        with self._lock:
            self._streaming = True
            self._current_task_id = task_id
            self._current_session_id = sid
            self._ai_parts = []
            self._stream_finalized = False

        self.sign_chat_user.emit(text)
        self.sign_set_streaming.emit(True)

        def _run() -> None:
            error_message: str | None = None
            try:
                final_ctx = self._workbench.chat(text, session_id=sid, task_id=task_id)
                response = ""
                for msg in reversed(final_ctx.messages):
                    if msg.role == "assistant":
                        response = msg.content
                        break
                if final_ctx.status.value == "failed" or not response:
                    error_message = "[生成失败]"
                else:
                    generated_title = self._conversation_service.store_assistant_message(sid, response)
                    if generated_title:
                        self.sign_set_title.emit(generated_title, self._project_path)
                        self._reload_sessions()
                    with self._lock:
                        finalized = self._stream_finalized
                    if not finalized:
                        # 非流式路径（如 CHAT 模式）直接显示完整回复
                        self.sign_chat_ai.emit(response, "")
            except Exception as exc:
                error_message = f"[错误: {exc}]"
            finally:
                self._finalize_stream(error_message)

        self._workbench_thread = threading.Thread(target=_run, daemon=True)
        self._workbench_thread.start()
