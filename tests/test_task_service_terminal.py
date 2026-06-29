"""
test_task_service_terminal.py — TaskService 终端状态保护测试

验证：
- 任务到达 COMPLETED / FAILED 后不会被 complete_task / fail_task / cancel_task 覆盖。
- terminal 状态的任务不再响应 _on_phase_change 的状态变更。
"""
import pytest
from PySide6.QtCore import QCoreApplication

from services.task_service import TaskService
from workers.session_task import SessionTask, TaskStatus


@pytest.fixture
def app():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


@pytest.fixture
def service(app):
    return TaskService()


def test_complete_task_sets_completed(service):
    service.submit_task("s1", "ask", "hello")
    service.complete_task("s1", True)

    task = service.get_task_status("s1")
    assert task.status == TaskStatus.COMPLETED


def test_fail_task_sets_failed(service):
    service.submit_task("s1", "ask", "hello")
    service.fail_task("s1", "出错了")

    task = service.get_task_status("s1")
    assert task.status == TaskStatus.FAILED
    assert task.last_error == "出错了"


def test_completed_task_not_overwritten_by_complete(service):
    service.submit_task("s1", "ask", "hello")
    service.complete_task("s1", True)
    service.complete_task("s1", False, "试图覆盖")

    task = service.get_task_status("s1")
    assert task.status == TaskStatus.COMPLETED
    assert task.last_error == ""


def test_completed_task_not_overwritten_by_fail(service):
    service.submit_task("s1", "ask", "hello")
    service.complete_task("s1", True)
    service.fail_task("s1", "试图覆盖")

    task = service.get_task_status("s1")
    assert task.status == TaskStatus.COMPLETED


def test_failed_task_not_overwritten_by_cancel(service):
    service.submit_task("s1", "ask", "hello")
    service.fail_task("s1", "original error")
    service.cancel_task("s1")

    task = service.get_task_status("s1")
    assert task.status == TaskStatus.FAILED
    assert "original error" in task.last_error


def test_phase_change_ignored_when_terminal(service):
    service.submit_task("s1", "ask", "hello")
    service.complete_task("s1", True)

    # 模拟旧 Worker 滞后回调
    service._on_phase_change("s1", "executing", "滞后回调")

    task = service.get_task_status("s1")
    assert task.status == TaskStatus.COMPLETED


def test_task_status_property_read_only():
    task = SessionTask(session_id="s1", mode="ask", user_input="hello")
    assert task.status == TaskStatus.QUEUED

    # 内部方法可以修改
    task._set_status(TaskStatus.ANALYZING)
    assert task.status == TaskStatus.ANALYZING

    # property 无 setter，直接赋值应抛出 AttributeError
    with pytest.raises(AttributeError):
        task.status = TaskStatus.COMPLETED
