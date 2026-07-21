"""
ActivityService — 结构化活动记录服务

将系统运行中的关键事件（打开文件、切换项目、新建对话、工具调用等）
以中文标题 + 详情形式持久化，供 UI 活动面板展示。
"""
import os
import json
import sys
import uuid
from datetime import datetime
from typing import List, Dict, Optional


def _get_app_root() -> str:
    """返回应用根目录：打包时为 exe 同级目录，源码时为项目根目录。"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ActivityService:
    """活动记录服务，基于 JSON 文件持久化"""

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.join(_get_app_root(), "storage", "activities.json")
        self._activities: List[Dict] = []
        self._load()

    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self._activities = json.load(f)
            except Exception:
                self._activities = []

    def _save(self):
        os.makedirs(os.path.dirname(self.storage_path) or ".", exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self._activities, f, ensure_ascii=False, indent=2)

    def add(
        self,
        title: str,
        category: str = "系统",
        project_path: str = "",
        summary: str = "",
        detail: str = "",
    ) -> Dict:
        """添加一条活动记录"""
        activity = {
            "id": str(uuid.uuid4())[:8],
            "title": title,
            "category": category,
            "project_path": project_path or "",
            "timestamp": datetime.now().isoformat(),
            "summary": summary or title,
            "detail": detail or title,
        }
        self._activities.insert(0, activity)
        self._trim()
        self._save()
        return activity

    def _trim(self, max_count: int = 200):
        if len(self._activities) > max_count:
            self._activities = self._activities[:max_count]

    def list_all(self) -> List[Dict]:
        return list(self._activities)

    def list_by_project(self, project_path: str) -> List[Dict]:
        """返回指定项目的活动 + 全局活动"""
        path = project_path or ""
        return [a for a in self._activities if a.get("project_path", "") == path or a.get("project_path", "") == ""]

    def clear(self):
        self._activities = []
        self._save()
