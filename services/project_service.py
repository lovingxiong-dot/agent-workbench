"""
ProjectService — 项目目录与会话关联管理

生产级设计目标：
- 每个对话会话可选关联一个项目目录（project_path）。
- 目录切换时自动加载该目录下的会话列表。
- 当前项目目录持久化到 config.yaml，启动自动恢复。
- 与 SessionService 解耦，仅负责目录维度的聚合与配置同步。
"""
import os
import sys
import hashlib
from datetime import datetime
from typing import List, Dict, Optional

from services.session_service import SessionService
from services.config_service import ConfigService


def _get_app_root() -> str:
    """返回应用根目录：打包时为 exe 同级目录，源码时为项目根目录。"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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

    def detect_current_project(self, fallback_path: str = "") -> str:
        """启动时自动检测当前用户最可能正在操作的目录。

        优先级：
        1. config 中持久化的 project_root（若目录仍存在）。
        2. SessionService 中最近有会话记录的目录。
        3. ActivityService 中最近一条 project_path 非空的活动目录。
        4. fallback_path（通常传应用根目录）。
        """
        # 1) config 持久化值
        configured = self.get_current_project()
        if configured and os.path.isdir(configured):
            return configured

        # 2) 最近有会话的目录
        try:
            projects = self.list_projects()
            if projects:
                latest = projects[0].get("path", "")
                if latest and os.path.isdir(latest):
                    return self.set_current_project(latest)
        except Exception:
            pass

        # 3) 最近活动记录中的 project_path
        try:
            from services.activity_service import ActivityService
            activity_storage_path = os.path.join(_get_app_root(), "storage", "activities.json")
            activity_service = ActivityService(activity_storage_path)
            for activity in activity_service.list_all():
                path = activity.get("project_path", "")
                if path and os.path.isdir(path):
                    return self.set_current_project(path)
        except Exception:
            pass

        # 4) 回退
        fallback = fallback_path or os.getcwd()
        return self.set_current_project(fallback)

    def list_recent_projects(self, limit: int = 10) -> List[Dict]:
        """返回最近项目列表，供 UI 下拉使用。

        来源合并：
        - config 中的 recent_projects（按顺序）。
        - 有会话记录的目录（按最近更新时间）。
        """
        recent = []
        seen = set()

        # config 中显式保存的最近项目
        cfg_recent = (
            self._config_service.get("ui", {})
            .get("explorer", {})
            .get("recent_projects", [])
        )
        for path in cfg_recent:
            path = self.normalize_path(path)
            if path and os.path.isdir(path) and path not in seen:
                seen.add(path)
                recent.append({"path": path, "source": "recent"})

        # 有会话记录的目录
        try:
            for item in self.list_projects():
                path = self.normalize_path(item.get("path", ""))
                if path and os.path.isdir(path) and path not in seen:
                    seen.add(path)
                    recent.append({"path": path, "source": "session", "updated_at": item.get("updated_at", "")})
        except Exception:
            pass

        return recent[:limit]

    def add_recent_project(self, path: str, max_count: int = 10):
        """把目录加入最近项目列表并持久化到 config.yaml"""
        path = self.normalize_path(path)
        if not path or not os.path.isdir(path):
            return
        ui_cfg = self._config_service.config.setdefault("ui", {})
        explorer_cfg = ui_cfg.setdefault("explorer", {})
        recent = explorer_cfg.get("recent_projects", [])
        # 去重并移到最前
        recent = [self.normalize_path(p) for p in recent if self.normalize_path(p) != path]
        recent.insert(0, path)
        explorer_cfg["recent_projects"] = recent[:max_count]
        self._config_service.save()
