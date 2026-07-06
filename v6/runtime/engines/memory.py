"""v6/runtime/engines/memory.py — MemoryEngine：三层记忆管理、检索、画像。

设计来源：V4 agent_engine/engines/memory_engine.py（提取核心逻辑）。

职责：读取 ctx.session_id / ctx.messages，写回 ctx.memory / ctx.metadata['memory_context']。
"""
from __future__ import annotations

import glob
import os
from typing import Any, Dict, List, Optional

from v6.runtime.engines.interfaces import IMemoryEngine
from v6.runtime.types import ChatMessage


class MemoryEngine(IMemoryEngine):
    """记忆引擎：上下文存储 + 画像管理 + 项目记忆注入。"""

    DEFAULT_MEMORY_MAX_LEN = 3000
    DEFAULT_LOG_DAYS = 3
    DEFAULT_LOG_LINES = 3

    def __init__(
        self,
        app_root: str = "",
        config: Optional[Dict[str, Any]] = None,
        policy_engine=None,
    ) -> None:
        self._app_root = app_root
        self._config = config or {}
        self._policy = policy_engine
        self._store: Dict[str, List[ChatMessage]] = {}
        self._profile: Dict[str, Any] = {}
        self._cache: Optional[str] = None
        self._cache_mtime: float = 0.0

    async def run(self, ctx: "RuntimeContext") -> "RuntimeContext":
        """存储当前消息、检索记忆、构建记忆上下文块。"""
        if ctx.session_id and ctx.messages:
            self.store(ctx.session_id, list(ctx.messages))

        query = ctx.metadata.get("memory_query", "")
        top_k = ctx.metadata.get("memory_top_k", 5)
        retrieved = self.retrieve(ctx.session_id or "", query, top_k=top_k)
        ctx.memory["retrieved"] = [m.__dict__ for m in retrieved]

        ctx.metadata["memory_context"] = self.build_context_block()
        ctx.memory["profile"] = self.get_profile()
        return ctx

    def store(self, session_id: str, messages: List[ChatMessage]) -> None:
        """存储会话记忆。"""
        if session_id not in self._store:
            self._store[session_id] = []
        self._store[session_id].extend(messages)

    def retrieve(self, session_id: str, query: str = "", top_k: int = 5) -> List[ChatMessage]:
        """检索相关记忆（当前简化：返回最近 top_k 条）。"""
        msgs = self._store.get(session_id, [])
        return msgs[-top_k:] if msgs else []

    def get_profile(self) -> Dict[str, Any]:
        """获取用户画像。"""
        return dict(self._profile)

    def update_profile(self, updates: Dict[str, Any]) -> None:
        """更新用户画像。"""
        self._profile.update(updates)

    def build_context_block(self) -> str:
        """构建项目记忆上下文块，用于注入 system prompt。"""
        mem_dir = os.path.join(self._app_root, ".memory") if self._app_root else ""
        if not mem_dir or not os.path.isdir(mem_dir):
            return ""

        try:
            dir_mtime = os.path.getmtime(mem_dir)
        except OSError:
            return ""

        if self._cache is not None and dir_mtime == self._cache_mtime:
            return self._cache

        parts: List[str] = []
        max_len = self._config.get("memory_max_len", self.DEFAULT_MEMORY_MAX_LEN)

        mem_file = os.path.join(mem_dir, "MEMORY.md")
        if os.path.exists(mem_file):
            try:
                with open(mem_file, "r", encoding="utf-8") as f:
                    parts.append(f"[项目记忆 - 跨对话持久化]\n{f.read()[:max_len]}")
            except Exception:
                pass

        log_days = self._config.get("log_days", self.DEFAULT_LOG_DAYS)
        log_lines = self._config.get("log_lines", self.DEFAULT_LOG_LINES)
        try:
            log_files = sorted(
                glob.glob(os.path.join(mem_dir, "*.md")),
                key=os.path.getmtime,
                reverse=True,
            )
            for lf in log_files[:log_days]:
                basename = os.path.basename(lf).replace(".md", "")
                if basename == "MEMORY":
                    continue
                try:
                    with open(lf, "r", encoding="utf-8") as f:
                        first_n = "".join(f.readlines()[:log_lines])
                        parts.append(f"[{basename} 日志摘要]\n{first_n.strip()}")
                except Exception:
                    pass
        except Exception:
            pass

        result = "\n---\n".join(parts) if parts else ""
        self._cache = result
        self._cache_mtime = dir_mtime
        return result

    def invalidate_cache(self) -> None:
        """使项目记忆缓存失效。"""
        self._cache = None
        self._cache_mtime = 0.0
