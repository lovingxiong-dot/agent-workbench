"""
AppContext — 全局服务容器

集中管理 AI Agent Workbench 的所有核心服务，简化 MainWindow 初始化，
统一服务生命周期与依赖顺序，避免服务间循环初始化。
"""
import os
import sys
from typing import Optional

from services.config_service import ConfigService
from services.session_service import SessionService
from services.project_service import ProjectService
from services.context_service import ContextService
from services.interpreter_service import InterpreterService
from services.activity_service import ActivityService
from services.theme_service import ThemeService
from services.metrics_collector import MetricsCollector
from services.task_service import TaskService
from core.event_bus import MessageBus
from workers.task_capacity import TaskCapacity
from agent_engine import ModeManager, LLMRegistry, MemoryManager
from agent_engine.tool_gateway import ToolGateway
from services.mcp_service import MCPRegistry


class AppContext:
    """
    应用级服务上下文。

    职责：
    1. 按正确顺序初始化所有服务。
    2. 对外暴露统一访问接口。
    3. 管理持久化根目录、项目根目录、解释器发现等启动逻辑。
    """

    def __init__(
        self,
        config_path: str,
        writable_config_path: str,
        storage_dir: str,
        app_root: str = "",
    ):
        self.config_path = config_path
        self.writable_config_path = writable_config_path
        self.storage_dir = storage_dir
        self.app_root = app_root or self._default_app_root()

        os.makedirs(self.storage_dir, exist_ok=True)

        # ── 配置服务（最先初始化，其他服务依赖它）─────────────────
        self.config_service = ConfigService(
            config_path,
            writable_path=writable_config_path,
        )

        # ── 持久化服务 ──────────────────────────────────────────
        self.session_service = SessionService(
            os.path.join(self.storage_dir, "conversations.db")
        )

        # ── 项目服务（依赖 session + config）──────────────────────
        self.project_service = ProjectService(
            self.session_service,
            self.config_service,
        )

        # ── 上下文服务（依赖 project_service）─────────────────────
        self.context_service = ContextService(
            self.project_service,
            parent=None,
        )

        # ── 解释器服务（依赖项目根目录）───────────────────────────
        self._project_root = self.project_service.detect_current_project(self.app_root)
        self.context_service.set_project_root(self._project_root)
        self.interpreter_service = InterpreterService(
            self._project_root,
            self.config_service,
        )
        self.interpreter_service.discover()
        self.context_service.set_interpreter_service(self.interpreter_service)

        # ── 其他服务 ─────────────────────────────────────────────
        self.activity_service = ActivityService(
            os.path.join(self.storage_dir, "activities.json")
        )
        self.theme_service = ThemeService()
        self.mode_manager = ModeManager(config_path)
        self.llm_registry = LLMRegistry(config_path, writable_config_path)
        self.memory_manager = MemoryManager(
            self.config_service.get("memory", {}),
            storage_dir=self.storage_dir,
        )
        self.metrics_collector = MetricsCollector()

        # ── 工具网关与外部能力接入点 ─────────────────────────────
        self.tool_gateway = ToolGateway()
        self.mcp_registry = MCPRegistry()

        # ── v3 事件总线与任务服务 ────────────────────────────────
        self.message_bus = MessageBus(parent=self)
        self.message_bus.connect_dispatch()
        self.task_service = TaskService(
            capacity=TaskCapacity.from_config(self.config_service)
        )
        self.worker_manager = None  # 延迟注入，避免循环依赖

    # ═══════════════════════════════════════════════════════
    # 公共访问接口
    # ═══════════════════════════════════════════════════════
    def get_service(self, name: str):
        """通过名称获取服务实例"""
        return getattr(self, name, None)

    def config(self) -> ConfigService:
        return self.config_service

    def project_root(self) -> str:
        return self._project_root

    def set_project_root(self, path: str) -> str:
        """切换项目根目录，同步更新相关服务"""
        path = self.project_service.set_current_project(path)
        self._project_root = path
        self.context_service.set_project_root(path)
        self.interpreter_service.project_root = path
        self.interpreter_service.discover()
        self.context_service.set_interpreter_service(self.interpreter_service)
        return path

    # ═══════════════════════════════════════════════════════
    # 启动辅助
    # ═══════════════════════════════════════════════════════
    @staticmethod
    def _default_app_root() -> str:
        """默认应用根目录：开发时为项目根目录，打包时为 exe 所在目录"""
        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)
        # 开发时：services/app_context.py -> services/ -> 项目根目录
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @staticmethod
    def resolve_storage_dir(app_root: str = "") -> str:
        """统一持久化根目录：开发时项目根目录/storage，打包时 exe 同级/storage"""
        if getattr(sys, "frozen", False):
            return os.path.join(os.path.dirname(sys.executable), "storage")
        return os.path.join(app_root or AppContext._default_app_root(), "storage")
