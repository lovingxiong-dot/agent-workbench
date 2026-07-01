"""
test_v4_integration.py — v4 GUI 集成测试（适配最终版三栏 UI）

覆盖可自动化的手动验证清单：
1 创建 Chat 会话 — 列表出现新会话，可发送消息
2 创建 Work 会话 — 列表出现，带项目路径标记
3 发送消息 — 消息显示，DB 中有记录
4 切换会话 — UI 切换，消息加载
6 队列满 — 发送 3 条消息，第 3 条被拒绝
7 队列完成 — 任务完成后自动出队下一个
8 停止任务 — 点击停止，任务取消，状态恢复
9 置顶会话 — 置顶会话固定在最上方
10 重命名 — 同标题多会话，列表正常显示
12 环境感知 — Work 会话中 AI 知道项目目录
13 并发槽位 — 6 个任务同时启动，第 6 个排队
14 重启恢复 — 关闭重开，所有会话/消息/环境恢复

测试原则：
- 使用 QApplication + QTest 做无头/非阻塞 GUI 测试。
- 通过 StubWorkerManager 替代真实 WorkerManager，避免调用 LLM。
- 每个测试前删除 storage/conversations_v4.db，保证状态隔离。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from v4.main_window import MainWindow
from v4.worker_manager import WorkerManager
from v4.events import (
    SessionCreateEvent,
    SessionSwitchEvent,
    SessionPinEvent,
    SessionRenameEvent,
    WorkerResultEvent,
    PhaseCompleteEvent,
    WorkerDestroyEvent,
    WorkerCreatedEvent,
)

DB_PATH = "storage/conversations_v4.db"


class StubWorkerManager(WorkerManager):
    """WorkerManager 桩：不创建真实 AgentWorker，避免 LLM 调用。"""

    def __init__(self, message_bus, auto_complete=True, delay_ms=0):
        super().__init__(message_bus=message_bus, max_workers=WorkerManager.MAX_WORKERS)
        self.auto_complete = auto_complete
        self.delay_ms = delay_ms
        self.created_events = []

    def _create_worker(self, event):
        print(f"[DEBUG stub create] sid={event.session_id[-8:]} auto={self.auto_complete}", flush=True)
        worker_id = f"worker_{event.session_id[-8:]}"
        self._workers[event.session_id] = object()
        self.worker_count_changed.emit(self.active_count)
        self._bus.emit(WorkerCreatedEvent(session_id=event.session_id, worker_id=worker_id))
        self.created_events.append(event)

        if self.auto_complete:
            if self.delay_ms:
                QTimer.singleShot(self.delay_ms, lambda: self._complete(event, worker_id))
            else:
                self._complete(event, worker_id)

    def _complete(self, event, worker_id):
        print(f"[DEBUG stub complete] sid={event.session_id[-8:]}", flush=True)
        if event.session_id not in self._workers:
            return
        self._bus.emit(
            WorkerResultEvent(
                session_id=event.session_id,
                worker_id=worker_id,
                full_text=f"AI 回复：{event.session_id[-8:]}",
            )
        )
        self._bus.emit(
            PhaseCompleteEvent(
                session_id=event.session_id,
                success=True,
                message="done",
            )
        )
        self._bus.emit(
            WorkerDestroyEvent(
                session_id=event.session_id,
                worker_id=worker_id,
            )
        )


@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture(autouse=True)
def clean_db():
    """每个测试前清理默认 DB 文件，避免状态串扰。"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    activities = "storage/activities.json"
    if os.path.exists(activities):
        os.remove(activities)
    yield


class TestV4Integration:
    @pytest.fixture(autouse=True)
    def setup(self, qt_app):
        self.app = qt_app
        yield

    def _process_events(self, ms=50):
        """处理 Qt 事件队列，等待异步信号完成。"""
        self.app.processEvents()
        if ms:
            QTest.qWait(ms)

    def _create_window(self, auto_complete=True):
        """创建 MainWindow 并挂载 StubWorkerManager。"""
        window = MainWindow()

        # 解绑默认 WorkerManager，避免真实 V4Worker 干扰测试
        old_wm = window._worker_mgr
        window._bus.unsubscribe(old_wm._on_create)
        window._bus.unsubscribe(old_wm._on_destroy)

        stub = StubWorkerManager(window._bus, auto_complete=auto_complete)
        window._worker_mgr = stub
        window._stub_wm = stub
        window._orchestrator._worker_mgr = stub
        self._process_events()
        return window

    def _send_first_message(self, window, text="测试消息"):
        """在草稿窗口发送首条消息，返回创建后的 session_id。

        若窗口挂载了 auto_complete 的 StubWorkerManager，会额外等待 AI 消息
        写入 DB，避免 QueuedConnection 异步导致后续断言读到旧预览。
        """
        window.chat_area.input_field.setPlainText(text)
        window.chat_area.input_area.send_btn.click()
        self._process_events()
        sid = window._orchestrator.current_session_id
        assert sid is not None, "发送首条消息后应创建会话"

        stub = getattr(window, "_stub_wm", None)
        if stub and stub.auto_complete:
            for _ in range(20):
                if window._repo.get_last_message(sid, role="ai"):
                    break
                self._process_events(50)
            self._process_events()
        return sid

    # ── 列表遍历辅助（适配分组折叠新 UI）─────────────────────────────

    def _list_groups(self, window):
        """返回左栏所有 SessionGroupWidget。"""
        return list(window.conversation_list._iter_groups())

    def _list_all_items(self, window):
        """返回 [(session_id, SessionItemWidget)] 平铺列表（按 UI 顺序）。"""
        result = []
        for group in self._list_groups(window):
            for sid, item in group._items.items():
                result.append((sid, item))
        return result

    def _current_list_item(self, window):
        """返回当前激活的 SessionItemWidget（未找到返回 None）。"""
        for sid, item in self._list_all_items(window):
            if item.property("active") or item.styleSheet().find("border-left") != -1:
                return item
        # 备选：找当前会话对应的项
        current_sid = window._orchestrator.current_session_id
        if current_sid:
            for sid, item in self._list_all_items(window):
                if sid == current_sid:
                    return item
        return None

    # ------------------------------------------------------------------
    # 1. 创建 Chat 会话
    # ------------------------------------------------------------------
    def test_create_chat_session_and_send_message(self):
        window = self._create_window()
        assert len(window._repo.list_sessions()) == 0, "启动时列表应为空"

        # 点击新对话按钮不创建会话
        window.conversation_list.new_task_btn.click()
        self._process_events()
        assert len(window._repo.list_sessions()) == 0, "空点击不应新增会话"

        # 发送首条消息后才创建会话并出现在列表
        sid = self._send_first_message(window, "你好，v4")
        sessions = window._repo.list_sessions()
        assert len(sessions) == 1, (
            f"发送首条消息后应存在 1 个会话，实际 {len(sessions)}"
        )

        item = self._current_list_item(window)
        assert item is not None, "应存在当前会话对应的列表项"
        assert "新对话" in item.title_label.text(), "Chat 会话默认标题应为'新对话'"

        messages = window._repo.get_messages(sid)
        user_messages = [m for m in messages if m.role == "user"]
        assert len(user_messages) == 1, "DB 中应存在 1 条用户消息"
        assert user_messages[0].role == "user"
        assert user_messages[0].content == "你好，v4"

        html = window.chat_area.toHtml()
        assert "你好，v4" in html, "ChatView 应显示用户消息"

        window.close()
        window.deleteLater()
        self._process_events()

    # ------------------------------------------------------------------
    # 2. 创建 Work 会话 + 12. 环境感知
    # ------------------------------------------------------------------
    def test_create_work_session_with_project_path(self):
        window = self._create_window()
        test_path = r"C:\v4_test_project"

        # monkeypatch 项目路径获取逻辑
        window._get_project_path = lambda: test_path
        window.conversation_list.new_task_btn.click()
        self._process_events()

        # 点击 work 按钮后仍处于草稿状态，未创建会话
        assert window._orchestrator.current_session_id is None

        # 发送首条消息后创建 work 会话
        sid = self._send_first_message(window, "分析项目")
        session = window._repo.get_session(sid)
        assert session is not None
        assert session.session_type.value == "work", "应创建 work 类型会话"
        assert session.project_path == test_path, "Work 会话应记录项目路径"

        item = self._current_list_item(window)
        assert item is not None
        assert "新对话" in item.title_label.text(), "列表项应显示会话标题"
        assert "AI 回复：" in item.preview_label.text(), "列表项应显示最后消息预览"

        # 环境持久化
        env = window._repo.get_environment(sid)
        assert env.project_root == test_path, "environments 表应保存项目根目录"

        # 环境感知：Worker 创建请求应绑定项目目录
        assert window._stub_wm.created_events, "应产生 Worker 创建请求"
        last_event = window._stub_wm.created_events[-1]
        assert last_event.project_root == test_path, "Worker 创建请求应绑定项目目录"

        window.close()
        window.deleteLater()
        self._process_events()

    # ------------------------------------------------------------------
    # 3. 发送消息
    # ------------------------------------------------------------------
    def test_send_message_persists_and_renders(self):
        window = self._create_window()

        window.chat_area.input_field.setPlainText("测试消息")
        window.chat_area.input_area.send_btn.click()
        self._process_events()

        sid = window._orchestrator.current_session_id
        assert sid is not None, "发送首条消息后应创建会话"
        messages = window._repo.get_messages(sid)
        user_messages = [m for m in messages if m.role == "user"]
        assert len(user_messages) == 1
        assert user_messages[0].content == "测试消息"

        assert window.chat_area.input_field.toPlainText().strip() == "", "发送后输入框应清空"
        assert "测试消息" in window.chat_area.toHtml()

        window.close()
        window.deleteLater()
        self._process_events()

    # ------------------------------------------------------------------
    # 4. 切换会话
    # ------------------------------------------------------------------
    def test_switch_session_loads_messages(self):
        window = self._create_window()

        # 创建会话 A 并发送消息
        sid_a = self._send_first_message(window, "消息 A")

        # 点击新对话进入草稿状态，再发送消息创建会话 B
        window.conversation_list.new_task_btn.click()
        self._process_events()
        sid_b = self._send_first_message(window, "消息 B")

        assert sid_a != sid_b

        # 切换回 A
        window._bus.emit(SessionSwitchEvent(new_session_id=sid_a))
        self._process_events()

        assert window._orchestrator.current_session_id == sid_a
        html = window.chat_area.toHtml()
        assert "消息 A" in html, "切换回 A 应加载 A 的消息"
        assert "消息 B" not in html, "切换回 A 不应显示 B 的消息"

        # 列表当前选中项应同步
        current_item = self._current_list_item(window)
        assert current_item is not None
        assert current_item._session_id == sid_a

        window.close()
        window.deleteLater()
        self._process_events()

    # ------------------------------------------------------------------
    # 6. 队列满
    # ------------------------------------------------------------------
    def test_queue_full_rejects_third_message(self):
        window = self._create_window(auto_complete=False)

        # 发送首条消息创建会话
        sid = self._send_first_message(window, "任务 1")

        # 再发送一条，占满两个槽位
        window.chat_area.input_field.setPlainText("任务 2")
        window.chat_area.input_area.send_btn.click()
        self._process_events()

        rt = window._orchestrator.get_runtime(sid)
        assert rt.queue.is_full, "两个槽位应被占满"
        assert rt.queue.get_streaming_task().user_text == "任务 1"

        # 第 3 条直接通过事件发送，验证业务层即使队列满也会先持久化用户消息
        from v4.events import UserSendEvent
        window._bus.emit(UserSendEvent(session_id=sid, user_text="任务 3", mode="ask"))
        self._process_events()

        # DB 中 3 条用户消息均已写入
        messages = window._repo.get_messages(sid)
        assert len(messages) == 3, "即使第 3 条被拒绝，用户消息仍应写入 DB"

        # UI 显示队列已满提示
        html = window.chat_area.toHtml()
        assert "队列已满" in html, "应提示用户队列已满"

        # 发送按钮被禁用
        assert not window.chat_area.input_area.send_btn.isEnabled(), "队列满时发送按钮应禁用"

        window.close()
        window.deleteLater()
        self._process_events()

    # ------------------------------------------------------------------
    # 7. 队列完成
    # ------------------------------------------------------------------
    def test_queue_auto_dequeues_next_task(self):
        window = self._create_window(auto_complete=True)

        # 发送首条消息创建会话
        sid = self._send_first_message(window, "任务 A")

        window.chat_area.input_field.setPlainText("任务 B")
        window.chat_area.input_area.send_btn.click()
        self._process_events(300)

        rt = window._orchestrator.get_runtime(sid)
        assert rt.queue.is_empty, "两个任务完成后队列应为空"

        messages = window._repo.get_messages(sid)
        user_msgs = [m for m in messages if m.role == "user"]
        ai_msgs = [m for m in messages if m.role == "ai"]
        assert len(user_msgs) == 2
        assert len(ai_msgs) == 2, "每个任务应产生一条 AI 回复"

        window.close()
        window.deleteLater()
        self._process_events()

    # ------------------------------------------------------------------
    # 8. 停止任务
    # ------------------------------------------------------------------
    def test_stop_task_cancels_and_restores(self):
        window = self._create_window(auto_complete=False)

        # 发送首条消息创建会话并启动任务
        sid = self._send_first_message(window, "要停止的任务")

        rt = window._orchestrator.get_runtime(sid)
        assert rt.queue.has_streaming, "应存在正在运行的任务"

        window.chat_area.input_area.stop_btn.click()
        self._process_events()

        assert rt.queue.is_empty, "停止后队列应为空"
        state = window._repo.get_task_state(sid)
        assert state.phase.value == "cancelled", "任务状态应标记为 cancelled"

        window.close()
        window.deleteLater()
        self._process_events()

    # ------------------------------------------------------------------
    # 9. 置顶会话
    # ------------------------------------------------------------------
    def test_pin_session_keeps_on_top(self):
        window = self._create_window()

        # 创建两个会话
        sid_a = self._send_first_message(window, "会话 A")

        window.conversation_list.new_task_btn.click()
        self._process_events()
        sid_b = self._send_first_message(window, "会话 B")

        # 通过真实事件流置顶较早创建的 sid_a
        window._bus.emit(SessionPinEvent(session_id=sid_a, pinned=True))
        self._process_events()

        all_items = self._list_all_items(window)
        first_sid = all_items[0][0]
        assert first_sid == sid_a, "置顶会话应固定在最上方"
        assert "📌" in all_items[0][1].title_label.text(), "置顶项应显示置顶标记"

        # 取消置顶后，sid_b 应回到顶部（按 updated_at 排序）
        window._bus.emit(SessionPinEvent(session_id=sid_a, pinned=False))
        self._process_events()
        all_items = self._list_all_items(window)
        first_sid = all_items[0][0]
        assert first_sid == sid_b, "取消置顶后会话应恢复时间排序"

        window.close()
        window.deleteLater()
        self._process_events()

    # ------------------------------------------------------------------
    # 10. 重命名 / 同标题多会话
    # ------------------------------------------------------------------
    def test_same_title_sessions_display_distinctly(self):
        window = self._create_window()

        # 创建两个 Chat 会话
        sid_a = self._send_first_message(window, "会话 A")

        window.conversation_list.new_task_btn.click()
        self._process_events()
        sid_b = self._send_first_message(window, "会话 B")

        # 通过真实事件流把两个会话重命名为相同标题
        same_title = "同名测试会话"
        window._bus.emit(SessionRenameEvent(session_id=sid_a, new_title=same_title))
        self._process_events()
        window._bus.emit(SessionRenameEvent(session_id=sid_b, new_title=same_title))
        self._process_events()

        items = self._list_all_items(window)
        title_items = [item for _, item in items if same_title in item.title_label.text()]
        assert len(title_items) >= 2, "应存在至少两个同标题会话"

        sids = [sid for sid, _ in items]
        assert len(sids) == len(set(sids)), "每个列表项应有唯一 session_id"
        assert sid_a in sids and sid_b in sids

        # DB 中标题已更新
        assert window._repo.get_session(sid_a).title == same_title
        assert window._repo.get_session(sid_b).title == same_title

        window.close()
        window.deleteLater()
        self._process_events()

    # ------------------------------------------------------------------
    # 13. 并发槽位
    # ------------------------------------------------------------------
    def test_concurrent_slots_sixth_queues(self):
        window = self._create_window(auto_complete=False)

        # 创建 6 个不同会话：发送消息 → 点击新对话 → 发送消息 ...
        sids = []
        for i in range(6):
            sid = self._send_first_message(window, f"并发任务 {i}")
            sids.append(sid)
            if i < 5:
                window.conversation_list.new_task_btn.click()
                self._process_events()

        assert len(set(sids)) == 6, "应存在 6 个不同会话"

        # 切换到每个会话再发送一条消息，触发 6 个 Worker 创建请求
        for sid in sids:
            window._bus.emit(SessionSwitchEvent(new_session_id=sid))
            self._process_events()
            window.chat_area.input_field.setPlainText("并发任务")
            window.chat_area.input_area.send_btn.click()
            self._process_events()

        stub = window._stub_wm
        assert stub.active_count == 5, f"应有 5 个活跃 Worker，实际 {stub.active_count}"
        assert len(stub._pending) == 1, f"第 6 个 Worker 创建请求应排队，实际排队 {len(stub._pending)}"

        window.close()
        window.deleteLater()
        self._process_events()

    # ------------------------------------------------------------------
    # 14. 重启恢复
    # ------------------------------------------------------------------
    def test_restart_recovery(self):
        window = self._create_window()

        # 发送首条消息创建会话，等待 AI 回复写入
        sid = self._send_first_message(window, "持久化消息")
        self._process_events(300)

        sessions_before = window._repo.list_sessions()
        messages_before = window._repo.get_messages(sid)
        assert len(messages_before) >= 1

        window.close()
        window.deleteLater()
        self._process_events()

        # 重新打开 MainWindow，使用同一个 DB 文件
        window2 = MainWindow()
        window2._stub_wm = StubWorkerManager(window2._bus)
        self._process_events()

        sessions_after = window2._repo.list_sessions()
        assert len(sessions_after) == len(sessions_before), "重启后会话数量应一致"
        assert sid in [s.session_id for s in sessions_after], "重启后原会话应存在"

        # 切换回原会话并验证消息恢复
        window2._bus.emit(SessionSwitchEvent(new_session_id=sid))
        self._process_events()

        messages_after = window2._repo.get_messages(sid)
        assert len(messages_after) == len(messages_before), "重启后消息数量应一致"
        assert any("持久化消息" in m.content for m in messages_after)
        assert "持久化消息" in window2.chat_area.toHtml()

        window2.close()
        window2.deleteLater()
        self._process_events()
