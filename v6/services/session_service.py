"""v6/services/session_service.py — 会话业务服务。

对 SessionManager 的薄封装，为 UIController 提供符合左栏渲染契约的分组数据。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from v6.session_manager import SessionManager


class SessionService:
    """会话业务服务。"""

    def __init__(
        self,
        session_manager: SessionManager | None = None,
        data_dir: str | os.PathLike | None = None,
    ) -> None:
        self._sm = session_manager or SessionManager(data_dir=data_dir)

    @property
    def manager(self) -> SessionManager:
        return self._sm

    def load_groups(self) -> list[tuple[str, str, list[dict[str, Any]]]]:
        """加载按时间分组的会话列表。"""
        return self._sm.groups()

    def create(self, title: str) -> str:
        """创建会话并设为当前激活会话。"""
        sid = self._sm.create(title)
        self._sm.set_active(sid)
        return sid

    def delete(self, sid: str) -> None:
        """删除会话；若删除的是当前激活会话则清除激活状态。"""
        if self._sm.get_active() == sid:
            self._sm.set_active(None)
        self._sm.delete(sid)

    def rename(self, sid: str, title: str) -> None:
        """重命名会话。"""
        self._sm.rename(sid, title)

    def pin(self, sid: str) -> bool:
        """切换会话置顶状态。"""
        return self._sm.pin(sid)

    def set_active(self, sid: str) -> None:
        """设置当前激活会话。"""
        self._sm.set_active(sid)

    def get_active(self) -> str | None:
        """返回当前激活会话 ID。"""
        return self._sm.get_active()

    def search(self, text: str) -> list[tuple[str, str, list[dict[str, Any]]]]:
        """按标题/预览搜索会话，返回分组结构。"""
        needle = text.strip().lower()
        if not needle:
            return self.load_groups()

        def matches(s: dict[str, Any]) -> bool:
            return needle in s.get("title", "").lower() or needle in s.get(
                "preview", ""
            ).lower()

        result: list[tuple[str, str, list[dict[str, Any]]]] = []
        for gid, title, items in self._sm.groups():
            kept = [s for s in items if matches(s)]
            if kept:
                result.append((gid, title, kept))
        return result
