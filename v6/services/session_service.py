"""v6/services/session_service.py — 会话业务服务。

对 SessionManager 的薄封装，为 UIController / Runtime 提供符合 Runtime Interface Principle 的接口。

设计来源：docs/v6/SPEC.md 第 8.12 节。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from v6.runtime.context import RuntimeContext
from v6.session_manager import SessionManager


class SessionService:
    """会话业务服务。

    公共方法统一接收 RuntimeContext，方法名保留语义。
    """

    def __init__(
        self,
        session_manager: SessionManager | None = None,
        data_dir: str | os.PathLike | None = None,
    ) -> None:
        self._sm = session_manager or SessionManager(data_dir=data_dir)

    @property
    def manager(self) -> SessionManager:
        return self._sm

    def load(self, ctx: RuntimeContext) -> None:
        """将会话列表加载到 RuntimeContext.metadata['session_groups']。"""
        ctx.metadata["session_groups"] = self._sm.groups()

    def create(self, ctx: RuntimeContext) -> None:
        """创建新会话，写回 ctx.session_id 与 ctx.metadata['session_title']。"""
        title = ctx.metadata.get("session_title", "新会话")
        summary = ctx.metadata.get("session_summary", "")
        icon = ctx.metadata.get("session_icon", "")
        workspace_id = ctx.metadata.get("session_workspace_id", "")
        sid = self._sm.create(title, summary=summary, icon=icon, workspace_id=workspace_id)
        self._sm.set_active(sid)
        ctx.session_id = sid
        ctx.metadata["session_title"] = title

    def delete(self, ctx: RuntimeContext) -> None:
        """删除 ctx.session_id 指定的会话。"""
        sid = ctx.session_id
        if sid is None:
            return
        if self._sm.get_active() == sid:
            self._sm.set_active(None)
        self._sm.delete(sid)

    def rename(self, ctx: RuntimeContext) -> None:
        """重命名 ctx.session_id 指定的会话；新标题从 ctx.metadata['session_title'] 读取。"""
        sid = ctx.session_id
        title = ctx.metadata.get("session_title", "重命名会话")
        if sid:
            self._sm.rename(sid, title)

    def pin(self, ctx: RuntimeContext) -> bool:
        """切换 ctx.session_id 的置顶状态，返回新置顶状态。"""
        sid = ctx.session_id
        if sid:
            return self._sm.pin(sid)
        return False

    def update_metadata(self, ctx: RuntimeContext) -> None:
        """更新 ctx.session_id 指定会话的元数据字段。"""
        sid = ctx.session_id
        if sid is None:
            return
        self._sm.update_metadata(
            sid,
            title=ctx.metadata.get("session_title"),
            summary=ctx.metadata.get("session_summary"),
            icon=ctx.metadata.get("session_icon"),
            workspace_id=ctx.metadata.get("session_workspace_id"),
            last_activity=ctx.metadata.get("session_last_activity"),
        )

    def set_active(self, ctx: RuntimeContext) -> None:
        """将 ctx.session_id 设为激活会话。"""
        sid = ctx.session_id
        if sid:
            self._sm.set_active(sid)

    def get_active(self, ctx: RuntimeContext) -> None:
        """将当前激活会话 ID 写回 ctx.session_id。"""
        ctx.session_id = self._sm.get_active()

    def search(self, ctx: RuntimeContext) -> None:
        """按 ctx.metadata['search_text'] 搜索会话，结果写回 ctx.metadata['session_groups']。"""
        needle = str(ctx.metadata.get("search_text", "")).strip().lower()
        if not needle:
            self.load(ctx)
            return

        def matches(s: dict[str, Any]) -> bool:
            return needle in s.get("title", "").lower() or needle in s.get(
                "preview", ""
            ).lower()

        result: list[tuple[str, str, list[dict[str, Any]]]] = []
        for gid, title, items in self._sm.groups():
            kept = [s for s in items if matches(s)]
            if kept:
                result.append((gid, title, kept))
        ctx.metadata["session_groups"] = result
