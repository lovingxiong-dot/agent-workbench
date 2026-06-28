"""
MainWindow 会话隔离守卫测试

把场景 2（会话 A 发请求 → 不等完成切到会话 B → A 的回复不能出现在 B）
固化为单元测试，直接验证 _make_current_only_guard 的两个守卫条件：
1. Worker 实例未替换
2. 当前会话未切换

不依赖真实 LLM、Worker 线程和 UI 事件循环，用 MagicMock 模拟信号槽。
"""
import unittest
from unittest.mock import MagicMock

from ui.main_window import MainWindow


class FakeMainWindow:
    """模拟 MainWindow 的最小状态，仅保留守卫所需的两个属性。"""

    def __init__(self):
        self._worker = None
        self._current_session = ""


class TestSessionIsolationGuard(unittest.TestCase):
    """测试 _make_current_only_guard"""

    def test_signal_allowed_when_worker_and_session_match(self):
        """Worker 和当前会话都匹配时，信号应正常传递到槽函数。"""
        main = FakeMainWindow()
        worker = MagicMock()
        main._worker = worker
        main._current_session = "session-A"

        slot = MagicMock()
        guard = MainWindow._make_current_only_guard(worker, main, "session-A")
        wrapped = guard(slot)

        wrapped("chunk-data")
        slot.assert_called_once_with("chunk-data")

    def test_signal_dropped_when_session_switched(self):
        """用户切到会话 B 后，旧 Worker（绑定 session-A）的信号应被丢弃。"""
        main = FakeMainWindow()
        worker = MagicMock()
        main._worker = worker
        main._current_session = "session-B"  # 已切换到 B

        slot = MagicMock()
        guard = MainWindow._make_current_only_guard(worker, main, "session-A")
        wrapped = guard(slot)

        wrapped("chunk-data")
        slot.assert_not_called()

    def test_signal_dropped_when_worker_replaced(self):
        """新 Worker 已创建时，旧 Worker 的信号应被丢弃。"""
        main = FakeMainWindow()
        worker_old = MagicMock()
        worker_new = MagicMock()
        main._worker = worker_new
        main._current_session = "session-A"

        slot = MagicMock()
        guard = MainWindow._make_current_only_guard(worker_old, main, "session-A")
        wrapped = guard(slot)

        wrapped("chunk-data")
        slot.assert_not_called()

    def test_signal_allowed_again_when_switched_back(self):
        """切走再切回原会话，旧 Worker 信号应恢复传递。"""
        main = FakeMainWindow()
        worker = MagicMock()
        main._worker = worker
        main._current_session = "session-A"

        slot = MagicMock()
        guard = MainWindow._make_current_only_guard(worker, main, "session-A")
        wrapped = guard(slot)

        # 切走：信号被丢弃
        main._current_session = "session-B"
        wrapped("x")
        slot.assert_not_called()

        # 切回：信号恢复
        main._current_session = "session-A"
        wrapped("y")
        slot.assert_called_once_with("y")


if __name__ == "__main__":
    unittest.main()
