"""
单元测试：双槽位等待队列 PendingQueue
"""
import sys
import threading
import time
import pytest
from PySide6.QtWidgets import QApplication

# QApplication singleton for tests
_app = QApplication.instance()
if _app is None:
    _app = QApplication(sys.argv)

from services.pending_queue import PendingQueue, PendingTask


@pytest.fixture
def queue():
    return PendingQueue()


@pytest.fixture
def make_task():
    def _make(task_id="t1", user_text="hello"):
        return PendingTask(task_id=task_id, user_text=user_text, mode="ask", context="test")
    return _make


class TestBasicOperations:
    def test_enqueue_first_slot(self, queue, make_task):
        task = make_task("t1")
        assert queue.enqueue(task) is True
        assert queue.length == 1
        assert queue.has_streaming is True
        assert queue.is_full is False
        assert queue.get_streaming_task() is task

    def test_enqueue_second_slot(self, queue, make_task):
        t1 = make_task("t1", "hello")
        t2 = make_task("t2", "world")
        queue.enqueue(t1)
        assert queue.enqueue(t2) is True
        assert queue.length == 2
        assert queue.has_streaming is True
        assert queue.is_full is True

    def test_enqueue_full_rejected(self, queue, make_task):
        t1 = make_task("t1")
        t2 = make_task("t2")
        t3 = make_task("t3")
        queue.enqueue(t1)
        queue.enqueue(t2)
        assert queue.enqueue(t3) is False
        assert queue.length == 2
        assert queue.is_full is True

    def test_cancel_streaming(self, queue, make_task):
        t1 = make_task("t1")
        t2 = make_task("t2")
        queue.enqueue(t1)
        queue.enqueue(t2)
        queue.cancel(0)  # cancel streaming (slot 0)
        assert queue.length == 1
        assert queue.has_streaming is True  # t2 moved to slot 0
        assert queue.get_streaming_task() is t2

    def test_cancel_pending(self, queue, make_task):
        t1 = make_task("t1")
        t2 = make_task("t2")
        queue.enqueue(t1)
        queue.enqueue(t2)
        queue.cancel(1)  # cancel pending (slot 1)
        assert queue.length == 1
        assert queue.has_streaming is True
        assert queue.get_streaming_task() is t1

    def test_cancel_all(self, queue, make_task):
        t1 = make_task("t1")
        t2 = make_task("t2")
        queue.enqueue(t1)
        queue.enqueue(t2)
        queue.cancel_all()
        assert queue.length == 0
        assert queue.has_streaming is False

    def test_mark_streaming_done_auto_dequeue(self, queue, make_task):
        t1 = make_task("t1")
        t2 = make_task("t2")
        queue.enqueue(t1)
        queue.enqueue(t2)
        queue.mark_streaming_done("t1")
        assert queue.length == 1
        assert queue.has_streaming is True
        assert queue.get_streaming_task() is t2
        assert t2.status == "streaming"

    def test_mark_streaming_done_empty_queue(self, queue, make_task):
        t1 = make_task("t1")
        queue.enqueue(t1)
        queue.mark_streaming_done("t1")
        assert queue.length == 0
        assert queue.has_streaming is False

    def test_dequeue(self, queue, make_task):
        t1 = make_task("t1")
        t2 = make_task("t2")
        queue.enqueue(t1)
        queue.enqueue(t2)
        # Manually set t2 as pending (not streaming) to test dequeue
        # Actually, in the actual queue, slot 1 is always pending
        result = queue.dequeue()
        assert result is t2  # t2 is in slot 1, which is pending
        assert queue.length == 1

    def test_clear(self, queue, make_task):
        t1 = make_task("t1")
        t2 = make_task("t2")
        queue.enqueue(t1)
        queue.enqueue(t2)
        queue.clear()
        assert queue.length == 0
        assert queue.has_streaming is False
        assert t1.status == "cancelled"
        assert t2.status == "cancelled"

    def test_get_pending_tasks(self, queue, make_task):
        t1 = make_task("t1")
        t2 = make_task("t2")
        queue.enqueue(t1)
        queue.enqueue(t2)
        pending = queue.get_pending_tasks()
        assert len(pending) == 1  # only slot 1 is pending
        assert pending[0] is t2


class TestPendingTask:
    def test_default_values(self):
        task = PendingTask(task_id="x", user_text="hi", mode="ask", context="")
        assert task.status == "pending"
        assert task.cancel_event.is_set() is False

    def test_cancel_event(self):
        task = PendingTask(task_id="x", user_text="hi", mode="ask", context="")
        task.cancel_event.set()
        assert task.cancel_event.is_set() is True


class TestThreadSafety:
    def test_concurrent_enqueue(self, queue, make_task):
        """并发入队不应产生竞态"""
        errors = []

        def enqueue_tasks():
            try:
                for i in range(50):
                    task = make_task(f"t-{threading.current_thread().name}-{i}")
                    queue.enqueue(task)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=enqueue_tasks) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors: {errors}"
        assert 0 <= queue.length <= 2  # max 2 slots