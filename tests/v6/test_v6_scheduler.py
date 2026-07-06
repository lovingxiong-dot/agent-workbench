"""tests/v6/test_v6_scheduler.py — Scheduler 单元测试。"""
from __future__ import annotations

import threading
import time

import pytest

from v6.runtime.scheduler import Scheduler
from v6.runtime.task import ChatTask, Task


def wait_for(event: threading.Event, timeout: float = 2.0) -> bool:
    return event.wait(timeout=timeout)


def test_submit_and_execute():
    executed = []
    done = threading.Event()

    def executor(task: Task) -> None:
        executed.append(task.task_id)
        done.set()

    scheduler = Scheduler(executor=executor)
    scheduler.start()
    try:
        task = ChatTask(text="hello")
        task_id = scheduler.submit(task)
        assert task_id == task.task_id
        assert wait_for(done)
        assert executed == [task_id]
    finally:
        scheduler.stop()


def test_cancel_before_execution():
    executed = []

    def executor(task: Task) -> None:
        executed.append(task.task_id)

    scheduler = Scheduler(executor=executor)
    scheduler.start()
    try:
        task = ChatTask(text="hello")
        task_id = scheduler.submit(task)
        assert scheduler.cancel(task_id) is True
        time.sleep(0.1)
        assert task_id not in executed
        assert scheduler.cancel(task_id) is False
    finally:
        scheduler.stop()


def test_sequential_execution_order():
    executed = []
    lock = threading.Lock()
    done = threading.Event()
    count = 5

    def executor(task: Task) -> None:
        with lock:
            executed.append(task.payload.get("index"))
            if len(executed) >= count:
                done.set()
        time.sleep(0.01)

    scheduler = Scheduler(concurrency=1, executor=executor)
    scheduler.start()
    try:
        for i in range(count):
            task = ChatTask(text=f"msg-{i}")
            task.payload["index"] = i
            scheduler.submit(task)
        assert wait_for(done)
        assert executed == list(range(count))
    finally:
        scheduler.stop()


def test_concurrency_limit():
    running = threading.Semaphore(0)
    max_running = [0]
    lock = threading.Lock()
    barrier = threading.Barrier(3)

    def executor(task: Task) -> None:
        with lock:
            current = running._value + 1
            max_running[0] = max(max_running[0], current)
        running.acquire()
        barrier.wait()

    scheduler = Scheduler(concurrency=2, executor=executor)
    scheduler.start()
    try:
        for _ in range(3):
            scheduler.submit(ChatTask(text="block"))
        # 给调度器时间启动任务
        time.sleep(0.1)
        with lock:
            assert max_running[0] <= 2
        for _ in range(3):
            running.release()
        time.sleep(0.2)
    finally:
        scheduler.stop()


def test_submit_when_not_running():
    scheduler = Scheduler()
    task = ChatTask(text="hello")
    task_id = scheduler.submit(task)
    assert task_id == task.task_id
    assert scheduler.cancel(task_id) is True
