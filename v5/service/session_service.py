"""v5 会话服务包装层：仅依赖根目录共享 services.session_service，零 v4 依赖。"""
import json
import os
import sqlite3
import uuid
from dataclasses import dataclass
from typing import List, Optional

from services.session_service import SessionService as _RootSessionService
from services.session_service import _get_app_root


@dataclass
class Session:
    """V5 会话视图对象，保持与旧 v5 Controller 的字段兼容。"""

    session_id: str
    title: str
    session_type: str = "chat"
    mode: str = "ask"
    model: str = "tool-agent"
    project_path: str = ""
    pinned: bool = False
    created_at: str = ""
    updated_at: str = ""
    preview: str = ""


class SessionService:
    """封装根目录通用 SessionService，对外提供 V5 所需 CRUD。

    说明：根目录 services/session_service 只维护 conversations/messages 通用表，
    不感知 session_type / pinned 等 V5 业务字段。这些字段由本层在
    storage/v5_session_meta.json 中独立维护，不改动共享底层表结构。
    """

    def __init__(self, db_path: Optional[str] = None, meta_path: Optional[str] = None):
        if db_path is not None:
            self._svc = _RootSessionService(db_path=db_path)
        else:
            self._svc = _RootSessionService()
        self._meta_path = meta_path or self._default_meta_path()
        self._meta: dict = self._load_meta()

    def _default_meta_path(self) -> str:
        return os.path.join(_get_app_root(), "storage", "v5_session_meta.json")

    def _load_meta(self) -> dict:
        if os.path.exists(self._meta_path):
            try:
                with open(self._meta_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_meta(self):
        os.makedirs(os.path.dirname(self._meta_path) or ".", exist_ok=True)
        with open(self._meta_path, "w", encoding="utf-8") as f:
            json.dump(self._meta, f, ensure_ascii=False, indent=2)

    def _ensure_meta(self, session_id: str) -> dict:
        return self._meta.setdefault(session_id, {"session_type": "chat", "pinned": False})

    def _conv_to_session(self, conv: dict) -> Session:
        sid = conv.get("id", "")
        meta = self._ensure_meta(sid)
        messages = self._svc.get_messages(sid)
        preview = ""
        if messages:
            last = messages[-1]
            content = last.get("content", "") if isinstance(last, dict) else getattr(last, "content", "")
            preview = (content or "")[:120]
        return Session(
            session_id=sid,
            title=conv.get("title") or "新会话",
            session_type=meta.get("session_type", "chat"),
            mode=conv.get("mode") or "ask",
            model=conv.get("model") or "tool-agent",
            project_path=conv.get("project_path") or "",
            pinned=bool(meta.get("pinned", False)),
            created_at=conv.get("created_at", ""),
            updated_at=conv.get("created_at", ""),
            preview=preview,
        )

    def create_session(
        self,
        session_type: str = "chat",
        mode: str = "ask",
        model: str = "tool-agent",
        project_path: str = "",
        title: str = "",
    ) -> str:
        sid = uuid.uuid4().hex
        display_title = title or ("新项目" if session_type == "work" else "新会话")
        self._svc.create_conversation(sid, display_title, mode, model, project_path)
        meta = self._ensure_meta(sid)
        meta["session_type"] = session_type
        meta["pinned"] = False
        self._save_meta()
        return sid

    def get_session(self, session_id: str) -> Optional[Session]:
        for conv in self._svc.list_conversations():
            if conv.get("id") == session_id:
                return self._conv_to_session(conv)
        return None

    def list_sessions(self) -> List[Session]:
        return [self._conv_to_session(c) for c in self._svc.list_conversations()]

    def delete_session(self, session_id: str) -> bool:
        try:
            self._svc.delete_conversation(session_id)
        except Exception:
            return False
        self._meta.pop(session_id, None)
        self._save_meta()
        return True

    def rename_session(self, session_id: str, new_title: str) -> bool:
        """仅更新标题，保留 created_at / updated_at。"""
        try:
            with sqlite3.connect(self._svc.db_path) as conn:
                conn.execute(
                    "UPDATE conversations SET title=? WHERE id=?",
                    (new_title, session_id),
                )
                conn.commit()
        except Exception:
            return False
        return True

    def pin_session(self, session_id: str, pinned: bool = True) -> bool:
        meta = self._ensure_meta(session_id)
        meta["pinned"] = bool(pinned)
        self._save_meta()
        return True

    def add_message(self, session_id: str, role: str, content: str) -> bool:
        try:
            self._svc.add_message(session_id, role, content)
            return True
        except Exception:
            return False

    def list_messages(self, session_id: str) -> List[dict]:
        return self._svc.get_messages(session_id)
