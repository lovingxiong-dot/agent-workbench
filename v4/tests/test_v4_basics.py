"""
test_v4_basics.py — v4 单轨架构基础单元测试

覆盖：
- 会话创建与持久化
- 用户消息权威（DB 为准）
- 会话切换不重复
- 队列槽位满时拒绝

运行：python -m pytest tests/test_v4_basics.py -v
"""
import pytest
from PySide6.QtWidgets import QApplication

from v4.repository import SessionRepository
from v4.event_bus import MessageBus
from v4.orchestrator import SessionOrchestrator
from v4.events import SessionCreateEvent, SessionSwitchEvent, UserSendEvent


@pytest.fixture(scope="session")
def qt_app():
    """全局唯一 QApplication，避免 PySide6 重复构造，同时兼容 GUI 测试。"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def db_path(tmp_path):
    """每个测试独立的 SQLite 文件路径。"""
    return str(tmp_path / "v4_test.db")


@pytest.fixture
def repo(db_path):
    return SessionRepository(db_path=db_path)


@pytest.fixture
def bus(qt_app):
    b = MessageBus()
    b.connect_dispatch()
    return b


@pytest.fixture
def orchestrator(qt_app, repo, bus):
    return SessionOrchestrator(repository=repo, message_bus=bus)


class TestV4Basics:
    """v4 基础功能测试。"""

    def test_create_session(self, qt_app, repo, bus, orchestrator):
        """创建会话后，current_session_id 非空且 DB 中存在该会话。"""
        bus.process(SessionCreateEvent(
            title="测试会话",
            session_type="chat",
            project_path="",
            mode="ask",
            model="tool-agent",
        ))
        qt_app.processEvents()

        assert orchestrator.current_session_id is not None
        session = repo.get_session(orchestrator.current_session_id)
        assert session is not None
        assert session.title == "测试会话"

    def test_message_authority(self, qt_app, repo, bus, orchestrator):
        """用户发送消息后，DB messages 表应存在 1 条记录且内容正确。"""
        bus.process(SessionCreateEvent(
            title="消息测试",
            session_type="chat",
            project_path="",
            mode="ask",
            model="tool-agent",
        ))
        qt_app.processEvents()
        sid = orchestrator.current_session_id

        bus.process(UserSendEvent(
            session_id=sid,
            user_text="你好，v4",
            mode="ask",
        ))
        qt_app.processEvents()

        messages = repo.get_messages(sid)
        assert len(messages) == 1
        assert messages[0].role == "user"
        assert messages[0].content == "你好，v4"

    def test_switch_does_not_create_duplicate(self, qt_app, repo, bus, orchestrator):
        """创建两个会话并切换，current_session_id 正确且列表无重复。"""
        bus.process(SessionCreateEvent(
            title="会话 A",
            session_type="chat",
            project_path="",
            mode="ask",
            model="tool-agent",
        ))
        qt_app.processEvents()
        sid_a = orchestrator.current_session_id

        bus.process(SessionCreateEvent(
            title="会话 B",
            session_type="chat",
            project_path="",
            mode="ask",
            model="tool-agent",
        ))
        qt_app.processEvents()
        sid_b = orchestrator.current_session_id

        # 切换回 A
        bus.process(SessionSwitchEvent(new_session_id=sid_a))
        qt_app.processEvents()

        assert orchestrator.current_session_id == sid_a

        sessions = repo.list_sessions()
        session_ids = [s.session_id for s in sessions]
        assert len(session_ids) == len(set(session_ids))
        assert sid_a in session_ids
        assert sid_b in session_ids

    def test_queue_full(self, qt_app, repo, bus, orchestrator):
        """同一会话连续入队 3 个任务，第 3 个应被拒绝（返回 None）。"""
        bus.process(SessionCreateEvent(
            title="队列测试",
            session_type="chat",
            project_path="",
            mode="ask",
            model="tool-agent",
        ))
        qt_app.processEvents()
        sid = orchestrator.current_session_id
        rt = orchestrator.get_runtime(sid)

        task1 = rt.queue.enqueue("任务 1", "ask", "")
        task2 = rt.queue.enqueue("任务 2", "ask", "")
        task3 = rt.queue.enqueue("任务 3", "ask", "")

        assert task1 is not None
        assert task2 is not None
        assert task3 is None
        assert rt.queue.is_full
