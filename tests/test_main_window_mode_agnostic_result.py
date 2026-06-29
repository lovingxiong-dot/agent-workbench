"""
MainWindow Mode-agnostic AI 回复落盘测试

验证 result_ready → _on_result(session_id, text) 统一入口：
- 全模式 AI 回复按显式 session_id 写入数据库
- 当前房间内容同步显示到 UI
- 非当前房间只持久化、不显示
"""
import unittest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


class TestMainWindowModeAgnosticResult(unittest.TestCase):
    """测试 _on_result 统一落盘入口"""

    @classmethod
    def setUpClass(cls):
        # PySide6 需要 QApplication 实例
        cls.app = QApplication.instance() or QApplication([])

    def _make_main(self):
        """构造一个最小化的 MainWindow 实例用于单元测试。"""
        with patch.object(MainWindow, "__init__", lambda self: None):
            main = MainWindow.__new__(MainWindow)
        # v3.11+ SessionManager 代理属性需要 _session_mgr 存在
        main._session_mgr = MagicMock()
        sessions = {
            "session-A": {"title": "会话A", "messages": []},
            "session-B": {"title": "会话B", "messages": []},
        }

        def _add_message(sid, role, text):
            sessions[sid]["messages"].append({"role": role, "content": text})

        main._session_mgr.add_message = _add_message
        main._session_mgr.current_session = "session-A"
        main._session_mgr.sessions = sessions
        main._current_session = "session-A"
        main.session_service = MagicMock()
        main.memory_manager = MagicMock()
        main.chat_view = MagicMock()
        main.status_indicator = MagicMock()
        main._chunks_received = False
        main._pending_metrics = None
        main._current_phase = "idle"
        main._phase_manager = MagicMock()
        main._pending_queue = MagicMock()  # v3.10: 双槽位队列
        main._worker = None
        main._workers = {}
        main.worker_pool = MagicMock()
        main.task_service = MagicMock()
        return main

    def test_on_result_persists_to_current_session(self):
        """_on_result 把 AI 回复写入当前 session 的 DB 和内存缓存"""
        main = self._make_main()
        main._on_result("session-A", "AI 回复内容")

        main.session_service.add_message.assert_called_once_with("session-A", "ai", "AI 回复内容")
        self.assertEqual(len(main._sessions["session-A"]["messages"]), 1)
        self.assertEqual(main._sessions["session-A"]["messages"][0]["role"], "ai")
        main.memory_manager.get_session_history.assert_called_once_with("session-A")

    def test_on_result_appends_to_current_chat_view(self):
        """当前 session 的回复会显示到 chat_view"""
        main = self._make_main()
        main._on_result("session-A", "AI 回复内容")

        main.chat_view.finalize_stream.assert_called_once()
        main.chat_view.append_ai.assert_called_once_with("AI 回复内容")

    def test_on_result_does_not_render_when_session_not_current(self):
        """非当前 session 的回复只落盘、不渲染"""
        main = self._make_main()
        main._on_result("session-B", "B 的回复")

        main.session_service.add_message.assert_called_once_with("session-B", "ai", "B 的回复")
        self.assertEqual(len(main._sessions["session-B"]["messages"]), 1)
        main.chat_view.append_ai.assert_not_called()

    def test_on_result_skips_empty_text(self):
        """空文本不应写入"""
        main = self._make_main()
        main._on_result("session-A", "   ")

        main.session_service.add_message.assert_not_called()

    def test_on_result_avoids_duplicate_render_in_streaming_mode(self):
        """流式模式下 _on_result 不重复追加气泡"""
        main = self._make_main()
        main._chunks_received = True
        main._on_result("session-A", "AI 回复内容")

        main.chat_view.finalize_stream.assert_called_once()
        main.chat_view.append_ai.assert_not_called()
        self.assertFalse(main._chunks_received)


if __name__ == "__main__":
    unittest.main()
