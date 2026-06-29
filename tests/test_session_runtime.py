"""
test_session_runtime.py — SessionRuntime 单元测试
"""
import pytest
from PySide6.QtCore import QCoreApplication

from services.session_runtime import SessionRuntime
from agent_engine.phase_manager import PhaseManager, TaskItem
from workers.session_task import SessionTask, TaskStatus


@pytest.fixture
def app():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


def test_runtime_initialization(app):
    rt = SessionRuntime(
        session_id="s1",
        project_path="/tmp",
        title="test",
        mode="ask",
        model="deepseek",
    )

    assert rt.session_id == "s1"
    assert rt.project_path == "/tmp"
    assert rt.mode == "ask"
    assert rt.worker is None
    assert rt.task is None
    assert not rt.is_active

    # 独立的业务对象已创建
    assert rt.pending_queue is not None
    assert rt.queue_manager is not None
    assert rt.phase_manager is not None
    assert isinstance(rt.phase_manager, PhaseManager)


def test_runtime_independent_phase_managers(app):
    rt1 = SessionRuntime(
        session_id="s1",
        project_path="/tmp",
        title="a",
        mode="ask",
        model="m1",
    )
    rt2 = SessionRuntime(
        session_id="s2",
        project_path="/tmp",
        title="b",
        mode="plan",
        model="m2",
    )

    # 两个 runtime 的 PhaseManager 应该是独立实例
    assert rt1.phase_manager is not rt2.phase_manager
    assert rt1.queue_manager is not rt2.queue_manager
    assert rt1.pending_queue is not rt2.pending_queue


def test_runtime_task_binding(app):
    rt = SessionRuntime(
        session_id="s1",
        project_path="/tmp",
        title="test",
        mode="ask",
        model="deepseek",
    )

    task = SessionTask(
        session_id="s1",
        mode="ask",
        user_input="hello",
    )
    rt.bind_task(task)

    assert rt.task is task
    assert rt.is_active

    task._set_status(TaskStatus.COMPLETED)
    assert not rt.is_active

    rt.clear_task()
    assert rt.task is None


def test_runtime_phase_state_snapshot(app):
    rt = SessionRuntime(
        session_id="s1",
        project_path="/tmp",
        title="test",
        mode="ask",
        model="deepseek",
    )

    rt.save_phase_state({"phase": "confirm", "task_list": ["t1"]})
    snapshot = rt.to_snapshot()

    assert snapshot["session_id"] == "s1"
    assert snapshot["phase_state"]["phase"] == "confirm"

    rt.clear_phase_state()
    assert rt.phase_state == {}


def test_runtime_worker_attach_detach(app):
    rt = SessionRuntime(
        session_id="s1",
        project_path="/tmp",
        title="test",
        mode="ask",
        model="deepseek",
    )

    class FakeWorker:
        pass

    worker = FakeWorker()
    rt.attach_worker(worker)
    assert rt.worker is worker

    rt.detach_worker()
    assert rt.worker is None
