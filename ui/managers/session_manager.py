"""
SessionManager — 会话生命周期管理器

职责：
- 会话 CRUD（创建、切换、删除、加载）
- 切换状态机：IDLE → SWITCHING → ACTIVE
- 全局会话自动清除 project_root
- SWITCHING 期间新请求排队（_pending_switch）
"""
import logging
from datetime import datetime
from enum import Enum, auto
from typing import Optional

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class SessionState(Enum):
    IDLE = auto()
    SWITCHING = auto()
    ACTIVE = auto()


class SessionManager(QObject):
    """会话生命周期管理器"""

    # 信号（单向：Manager → MainWindow）
    session_switched = Signal(str, str)  # old_id, new_id
    session_created = Signal(str, str)   # session_id, project_path
    session_deleted = Signal(str)        # session_id
    error_occurred = Signal(str, str)    # code, detail

    def __init__(
        self,
        session_service,
        project_service,
        context_service,
        memory_manager,
        conversation_list_widget,
        parent=None,
    ):
        super().__init__(parent)
        self._session_service = session_service
        self._project_service = project_service
        self._context_service = context_service
        self._memory_manager = memory_manager
        self._conversation_list = conversation_list_widget

        self._state = SessionState.IDLE
        self._current_session = ""
        self._sessions = {}  # session_id → {title, messages, project_path}
        self._pending_switch = None  # 排队切换请求
        self._switching = False     # 守卫标志（兼容旧代码）

    # ── 属性 ──────────────────────────────────────
    @property
    def current_session(self) -> str:
        return self._current_session

    @current_session.setter
    def current_session(self, value: str):
        if value != self._current_session:
            print(f"[DIAG-SESSION] current_session changed: {self._current_session} → {value}", flush=True)
        self._current_session = value

    @property
    def state(self) -> SessionState:
        return self._state

    @property
    def sessions(self) -> dict:
        return self._sessions

    @property
    def switching(self) -> bool:
        return self._switching

    @switching.setter
    def switching(self, value: bool):
        self._switching = value

    # ── 会话 CRUD ─────────────────────────────────
    def create_session(self, project_path: str = "", mode: str = "ask",
                   model: str = "tool-agent", title: str = "新对话") -> str:
        """创建新会话，返回 session_id"""
        print(f"[DIAG-SESSION] create_session: project_path={project_path}, title={title}", flush=True)
        old_state = self._state
        try:
            session_id = self._project_service.create_session(
                project_path=project_path, mode=mode, model=model, title=title,
            )
            self._sessions[session_id] = {
                "title": title, "messages": [], "project_path": project_path,
            }
            self._memory_manager.get_session_history(session_id)
            self._conversation_list.add_conversation(session_id, title, project_path=project_path)
            self._conversation_list.set_active_conversation(session_id)
            self._current_session = session_id
            self._state = SessionState.ACTIVE
            self.session_created.emit(session_id, project_path)
            logger.info("Session created: %s @ %s", session_id, project_path or "global")
            return session_id
        except Exception as e:
            self._state = old_state
            self.error_occurred.emit("CREATE_FAILED", str(e))
            logger.error("Session creation failed: %s", e)
            raise

    def switch_session(self, new_id: str) -> bool:
        """原子切换会话：状态机 + 异常回滚"""
        print(f"[DIAG-SESSION] switch_session called: current={self._current_session} → new={new_id}", flush=True)
        if new_id == self._current_session:
            return True

        if self._state == SessionState.SWITCHING:
            self._pending_switch = new_id
            logger.warning("Switch queued: %s (currently switching)", new_id)
            return False

        old_state = self._state
        old_session = self._current_session
        self._switching = True
        self._state = SessionState.SWITCHING

        try:
            self._current_session = new_id
            session = self._sessions.get(new_id, {
                "title": "未命名会话", "messages": [], "project_path": "",
            })
            msgs = self._session_service.get_messages(new_id)
            self._sessions[new_id] = {
                "title": session.get("title", "未命名会话"),
                "messages": msgs,
                "project_path": session.get("project_path", ""),
            }

            # 全局会话清除 project_root，项目会话设置
            session_project = session.get("project_path", "")
            if not session_project:
                self._context_service.set_project_root("")
            else:
                self._context_service.set_project_root(session_project)

            self._state = SessionState.ACTIVE
            self.session_switched.emit(old_session, new_id)
            logger.info("Session switched: %s → %s", old_session, new_id)
            return True
        except Exception as e:
            self._state = old_state
            self._current_session = old_session
            self.error_occurred.emit("SWITCH_FAILED", str(e))
            logger.error("Session switch failed: %s", e)
            return False
        finally:
            self._switching = False
            # 处理排队切换
            pending = self._pending_switch
            self._pending_switch = None
            if pending and pending != new_id:
                self.switch_session(pending)

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            self._conversation_list.remove_conversation(session_id)
            self._sessions.pop(session_id, None)
            self._memory_manager.store.pop(session_id, None)
            self._session_service.delete_conversation(session_id)
            if self._current_session == session_id:
                first = next(iter(self._sessions.keys()), "")
                if first:
                    self._current_session = first
            self.session_deleted.emit(session_id)
            logger.info("Session deleted: %s", session_id)
            return True
        except Exception as e:
            self.error_occurred.emit("DELETE_FAILED", str(e))
            logger.error("Session delete failed: %s", e)
            return False

    def load_project_sessions(self, project_path: str) -> tuple:
        """加载指定项目目录下的所有会话，返回 (project_sessions, global_sessions)"""
        global_sessions = self._project_service.list_sessions("")
        project_sessions = self._project_service.list_sessions(project_path)

        for conv in global_sessions:
            self._sessions[conv["id"]] = {
                "title": conv["title"], "messages": [], "project_path": "",
            }
            msgs = self._session_service.get_messages(conv["id"])
            self._sessions[conv["id"]]["messages"] = msgs
            self._conversation_list.add_conversation(
                conv["id"], conv["title"], project_path="",
            )

        for conv in project_sessions:
            self._sessions[conv["id"]] = {
                "title": conv["title"], "messages": [], "project_path": project_path,
            }
            msgs = self._session_service.get_messages(conv["id"])
            self._sessions[conv["id"]]["messages"] = msgs
            self._conversation_list.add_conversation(
                conv["id"], conv["title"], project_path=project_path,
            )

        logger.info("Loaded %d project + %d global sessions for %s",
                     len(project_sessions), len(global_sessions), project_path or "global")
        return project_sessions, global_sessions

    def get_session_data(self, session_id: str) -> dict:
        """获取会话数据"""
        return self._sessions.get(session_id, {
            "title": "未命名会话", "messages": [], "project_path": "",
        })

    def add_message(self, session_id: str, role: str, content: str):
        """添加消息到会话"""
        if session_id in self._sessions:
            self._sessions[session_id].setdefault("messages", []).append(
                {"role": role, "content": content}
            )

    def update_title(self, session_id: str, title: str):
        """更新会话标题（内存 + 持久化 + UI）"""
        if session_id in self._sessions:
            self._sessions[session_id]["title"] = title
        # UI 更新
        for lst in (self._conversation_list.project_list,
                     self._conversation_list.global_list):
            for i in range(lst.count()):
                item = lst.item(i)
                if item.data(Qt.UserRole) == session_id:
                    item.setText(title)
                    item.setToolTip(title)
                    return

    def find_empty_session(self, project_path: str) -> Optional[str]:
        """查找同 project_path 下的空对话（标题=新对话 且 消息数=0）"""
        for sid, data in self._sessions.items():
            if data.get("project_path") == project_path and data.get("title") == "新对话":
                if len(data.get("messages", [])) == 0:
                    return sid
        return None

    def clear(self):
        """清空所有会话（切换项目时调用）"""
        self._sessions.clear()
        self._current_session = ""
        self._conversation_list.clear_conversations()

    def reset(self):
        """强制重置到 IDLE"""
        self._state = SessionState.IDLE
        self._switching = False
        self._pending_switch = None