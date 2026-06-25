"""
ProjectService — 项目目录与会话关联管理

生产级设计目标：
- 每个对话会话可选关联一个项目目录（project_path）。
- 目录切换时自动加载该目录下的会话列表。
- 当前项目目录持久化到 config.yaml，启动自动恢复。
- 与 SessionService 解耦，仅负责目录维度的聚合与配置同步。
"""
import os
import hashlib
from datetime import datetime
from typing import List, Dict, Optional

from services.session_service import SessionService
from services.config_service import ConfigService


class ProjectService:
    """项目目录上下文服务"""

    CONFIG_KEY_PATH = "ui.explorer.project_root"

    def __init__(self, session_service: SessionService, config_service: ConfigService):
        self._session_service = session_service
        self._config_service = config_service
        # 确保数据库 schema 支持 project_path
        self._session_service._ensure_project_path_column()

    @staticmethod
    def normalize_path(path: str) -> str:
        """规范化路径：展开环境变量、取绝对路径、统一分隔符"""
        if not path:
            return ""
        try:
            return os.path.normpath(os.path.abspath(os.path.expandvars(path)))
        except Exception:
            return path

    def get_current_project(self) -> str:
        """从配置读取当前项目目录"""
        raw = self._config_service.get("ui", {}).get("explorer", {}).get("project_root", "")
        return self.normalize_path(raw) if raw else ""

    def set_current_project(self, path: str) -> str:
        """设置当前项目目录并持久化到 config.yaml"""
        path = self.normalize_path(path)
        ui_cfg = self._config_service.config.setdefault("ui", {})
        explorer_cfg = ui_cfg.setdefault("explorer", {})
        explorer_cfg["project_root"] = path
        self._config_service.save()
        return path

    def list_projects(self) -> List[Dict]:
        """返回所有有会话记录的目录，按最近更新时间降序"""
        return self._session_service.list_projects()

    def list_sessions(self, project_path: str) -> List[Dict]:
        """返回指定目录下的所有会话，按更新时间降序"""
        return self._session_service.list_conversations(project_path=project_path)

    def create_session(
        self,
        project_path: str = "",
        mode: str = "ask",
        model: str = "tool-agent",
        title: str = "新对话",
    ) -> str:
        """在当前项目目录下创建新会话，返回 session_id"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._session_service.create_conversation(
            session_id, title, mode=mode, model=model, project_path=project_path
        )
        return session_id

    def get_session_project(self, session_id: str) -> str:
        """查询会话所属目录"""
        return self._session_service.get_conversation_project_path(session_id)

    def has_sessions(self, project_path: str) -> bool:
        """指定目录下是否已有会话"""
        return len(self.list_sessions(project_path)) > 0
