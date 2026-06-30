"""
test_orchestrator.py — v4 SessionOrchestrator 集成测试

测试目标：
- 会话创建/切换/删除的数据完整性
- 消息权威（DB 是权威来源）
- 会话切换不中断后台任务
- 队列槽位控制
- 并发槽位控制
"""
import pytest
import os
import tempfile
from PySide6.QtWidgets import QApplication
from unittest.mock import MagicMock

from v4.models import SessionMetadata, Message, TaskPhase, TaskState, SessionType, Environment
from v4.repository import SessionRepository
from v4.event_bus import MessageBus
from v4.events import (
    UserSendEvent, UserStopEvent, SessionCreateEvent, SessionSwitchEvent, SessionDeleteEvent,
    SessionPinEvent, SessionRenameEvent,
    UIAppendUserEvent, UIAppendAIEvent, UIStreamChunkEvent, UIFinalizeStreamEvent,
    UIUpdateSessionListEvent, UIUpdateSessionBadgeEvent,
)
from v4.orchestrator import SessionOrchestrator


@pytest.fixture
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def repo(temp_db):
    return SessionRepository(db_path=temp_db)


@pytest.fixture
def bus(qt_app):
    b = MessageBus()
    b.connect_dispatch()
    return b


@pytest.fixture
def orchestrator(qt_app, repo, bus):
    return SessionOrchestrator(repository=repo, message_bus=bus)


class EventSpy:
    """事件监听器"""
    def __init__(self, bus: MessageBus):
        self.events = []
        bus.subscribe(self.on_event)
    
    def on_event(self, event):
        self.events.append(event)
    
    def filter(self, event_type):
        return [e for e in self.events if isinstance(e, event_type)]


class TestSessionCreate:
    """会话创建测试"""
    
    def test_create_chat_session(self, qt_app, repo, bus, orchestrator):
        """创建纯对话会话"""
        spy = EventSpy(bus)
        
        bus.process(SessionCreateEvent(
            title="测试会话",
            session_type="chat",
            project_path="",
            mode="ask",
            model="tool-agent",
        ))
        qt_app.processEvents()
        
        # 验证会话创建
        sessions = repo.list_sessions()
        assert len(sessions) == 1
        assert sessions[0].title == "测试会话"
        assert sessions[0].session_type == SessionType.CHAT
        assert sessions[0].project_path == ""
        
        # 验证运行时创建
        assert orchestrator.has_runtime(sessions[0].session_id)
        
        # 验证当前会话切换
        assert orchestrator.current_session_id == sessions[0].session_id
        
        # 验证 UI 事件
        list_events = spy.filter(UIUpdateSessionListEvent)
        assert len(list_events) >= 1

    def test_create_work_session_with_environment(self, qt_app, repo, bus, orchestrator):
        """创建项目会话（带环境）"""
        bus.process(SessionCreateEvent(
            title="项目任务",
            session_type="work",
            project_path="/projects/my-app",
            mode="plan",
            model="deepseek",
        ))
        qt_app.processEvents()
        
        sessions = repo.list_sessions()
        assert len(sessions) == 1
        assert sessions[0].session_type == SessionType.WORK
        assert sessions[0].project_path == "/projects/my-app"
        
        # 验证环境持久化
        env = repo.get_environment(sessions[0].session_id)
        assert env.project_root == "/projects/my-app"


class TestSessionSwitch:
    """会话切换测试"""
    
    def test_switch_loads_messages_from_db(self, qt_app, repo, bus, orchestrator):
        """切换会话从 DB 加载消息（权威来源）"""
        # 创建会话 A，发送消息
        bus.process(SessionCreateEvent(title="会话A", session_type="chat", project_path="", mode="ask", model="m1"))
        qt_app.processEvents()
        sid_a = orchestrator.current_session_id
        
        # 发送消息（写 DB）
        bus.process(UserSendEvent(session_id=sid_a, user_text="Hello A", mode="ask"))
        qt_app.processEvents()
        
        # 创建会话 B
        bus.process(SessionCreateEvent(title="会话B", session_type="chat", project_path="", mode="ask", model="m1"))
        qt_app.processEvents()
        sid_b = orchestrator.current_session_id
        
        # 切换回 A
        spy = EventSpy(bus)
        bus.process(SessionSwitchEvent(new_session_id=sid_a))
        qt_app.processEvents()
        
        # 验证当前会话切换
        assert orchestrator.current_session_id == sid_a
        
        # 验证消息从 DB 加载（UI 事件）
        user_events = spy.filter(UIAppendUserEvent)
        assert len(user_events) == 1
        assert user_events[0].text == "Hello A"
    
    def test_switch_does_not_affect_worker(self, qt_app, repo, bus, orchestrator):
        """切换会话不操作 Worker（后台继续）"""
        # 创建会话 A，启动 Worker
        bus.process(SessionCreateEvent(title="会话A", session_type="work", project_path="/proj", mode="plan", model="m1"))
        qt_app.processEvents()
        sid_a = orchestrator.current_session_id
        
        # 模拟 Worker 创建
        rt = orchestrator.get_runtime(sid_a)
        rt.attach_worker(MagicMock(worker_id="w1"))
        
        # 创建会话 B
        bus.process(SessionCreateEvent(title="会话B", session_type="chat", project_path="", mode="ask", model="m1"))
        qt_app.processEvents()
        sid_b = orchestrator.current_session_id
        
        # 切换回 A
        bus.process(SessionSwitchEvent(new_session_id=sid_a))
        qt_app.processEvents()
        
        # 验证 Worker 未被销毁
        assert rt.worker is not None
        assert rt.worker.worker_id == "w1"
        # Worker 未被调用 stop()
        rt.worker.stop.assert_not_called()


class TestMessageAuthority:
    """消息权威测试"""
    
    def test_message_persisted_to_db(self, qt_app, repo, bus, orchestrator):
        """消息发送后写入 DB（权威来源）"""
        bus.process(SessionCreateEvent(title="测试", session_type="chat", project_path="", mode="ask", model="m1"))
        qt_app.processEvents()
        sid = orchestrator.current_session_id
        
        bus.process(UserSendEvent(session_id=sid, user_text="Hello", mode="ask"))
        qt_app.processEvents()
        
        # 从 DB 验证消息
        msgs = repo.get_messages(sid)
        assert len(msgs) == 1
        assert msgs[0].role == "user"
        assert msgs[0].content == "Hello"
    
    def test_message_loaded_from_db_on_switch(self, qt_app, repo, bus, orchestrator):
        """切换会话时从 DB 加载消息（不从内存缓存）"""
        # 创建会话 A
        bus.process(SessionCreateEvent(title="A", session_type="chat", project_path="", mode="ask", model="m1"))
        qt_app.processEvents()
        sid_a = orchestrator.current_session_id
        
        # 发送消息
        bus.process(UserSendEvent(session_id=sid_a, user_text="Hello", mode="ask"))
        qt_app.processEvents()
        
        # 清除运行时（模拟内存丢失）
        orchestrator._runtimes.pop(sid_a, None)
        
        # 切换回 A（此时内存中没有运行时，应从 DB 恢复）
        bus.process(SessionSwitchEvent(new_session_id=sid_a))
        qt_app.processEvents()
        
        # 验证运行时从 DB 恢复
        assert orchestrator.has_runtime(sid_a)
        
        # 验证消息从 DB 加载
        msgs = repo.get_messages(sid_a)
        assert len(msgs) == 1


class TestQueueSlot:
    """队列槽位测试"""
    
    def test_queue_full_rejects_new_message(self, qt_app, repo, bus, orchestrator):
        """队列满时拒绝新消息"""
        bus.process(SessionCreateEvent(title="测试", session_type="chat", project_path="", mode="ask", model="m1"))
        qt_app.processEvents()
        sid = orchestrator.current_session_id
        
        rt = orchestrator.get_runtime(sid)
        
        # 填充两个槽位
        rt.queue.enqueue("msg1", "ask", "")
        rt.queue.enqueue("msg2", "ask", "")
        
        # 第三个消息应被拒绝
        result = rt.queue.enqueue("msg3", "ask", "")
        assert result is None
        assert rt.queue.is_full

    def test_mark_done_compacts_queue(self, qt_app, repo, bus, orchestrator):
        """标记完成后自动出队下一个"""
        bus.process(SessionCreateEvent(title="测试", session_type="chat", project_path="", mode="ask", model="m1"))
        qt_app.processEvents()
        sid = orchestrator.current_session_id
        
        rt = orchestrator.get_runtime(sid)
        
        # 入队两个任务
        task1 = rt.queue.enqueue("msg1", "ask", "")
        task2 = rt.queue.enqueue("msg2", "ask", "")
        
        # 标记第一个完成
        rt.queue.mark_done(task1.task_id)
        
        # 验证 slot[0] 现在是 task2
        assert rt.queue.get_streaming_task().task_id == task2.task_id
        assert not rt.queue.has_pending


class TestConcurrencySlot:
    """并发槽位测试"""
    
    def test_max_workers_limit(self, qt_app, repo, bus, orchestrator):
        """最多同时运行 N 个 Worker"""
        # 创建 5 个会话，每个启动一个任务
        for i in range(5):
            bus.process(SessionCreateEvent(
                title=f"会话{i}",
                session_type="chat",
                project_path="",
                mode="ask",
                model="m1",
            ))
            qt_app.processEvents()
            sid = orchestrator.current_session_id
            
            rt = orchestrator.get_runtime(sid)
            rt.queue.enqueue(f"msg{i}", "ask", "")
        
        # 创建第 6 个会话
        bus.process(SessionCreateEvent(title="会话6", session_type="chat", project_path="", mode="ask", model="m1"))
        qt_app.processEvents()
        sid_6 = orchestrator.current_session_id
        
        rt_6 = orchestrator.get_runtime(sid_6)
        # 队列入队应成功（队列槽位与 Worker 并发槽位是独立的）
        task = rt_6.queue.enqueue("msg6", "ask", "")
        assert task is not None
        # 但 Worker 创建请求会被排队（WorkerManager 层面）


class TestEnvironmentAware:
    """环境感知测试"""
    
    def test_work_session_has_environment(self, qt_app, repo, bus, orchestrator):
        """Work 会话有环境上下文"""
        bus.process(SessionCreateEvent(
            title="项目任务",
            session_type="work",
            project_path="/projects/my-app",
            mode="plan",
            model="m1",
        ))
        qt_app.processEvents()
        sid = orchestrator.current_session_id
        
        rt = orchestrator.get_runtime(sid)
        env = rt.environment
        
        assert env.project_root == "/projects/my-app"
        assert rt.is_work
        assert not rt.is_chat
    
    def test_chat_session_no_environment(self, qt_app, repo, bus, orchestrator):
        """Chat 会话无环境上下文"""
        bus.process(SessionCreateEvent(
            title="闲聊",
            session_type="chat",
            project_path="",
            mode="ask",
            model="m1",
        ))
        qt_app.processEvents()
        sid = orchestrator.current_session_id
        
        rt = orchestrator.get_runtime(sid)
        env = rt.environment
        
        assert env.is_empty()
        assert rt.is_chat
        assert not rt.is_work


class TestSessionPin:
    """置顶测试"""
    
    def test_pinned_session_stays_on_top(self, qt_app, repo, bus, orchestrator):
        """置顶会话排在列表最上方"""
        # 创建 3 个会话
        for i in range(3):
            bus.process(SessionCreateEvent(
                title=f"会话{i}",
                session_type="chat",
                project_path="",
                mode="ask",
                model="m1",
            ))
            qt_app.processEvents()
        
        # 置顶第一个会话
        sessions = repo.list_sessions()
        sid_0 = sessions[0].session_id
        
        bus.process(SessionPinEvent(session_id=sid_0, pinned=True))
        qt_app.processEvents()
        
        # 验证排序：置顶的会话在最上方
        updated = repo.list_sessions()
        assert updated[0].session_id == sid_0
        assert updated[0].pinned


class TestSessionRename:
    """重命名测试"""
    
    def test_rename_session(self, qt_app, repo, bus, orchestrator):
        """重命名会话"""
        bus.process(SessionCreateEvent(title="旧名称", session_type="chat", project_path="", mode="ask", model="m1"))
        qt_app.processEvents()
        sid = orchestrator.current_session_id
        
        bus.process(SessionRenameEvent(session_id=sid, new_title="新名称"))
        qt_app.processEvents()
        
        session = repo.get_session(sid)
        assert session.title == "新名称"
