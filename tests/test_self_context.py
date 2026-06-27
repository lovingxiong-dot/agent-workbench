"""
单元测试：自识别上下文 SelfContext
"""
import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch

from services.self_context import SelfContext


class TestSelfContext:
    def test_build_timestamp(self):
        sc = SelfContext()
        ts = sc._build_timestamp_context()
        assert "[当前时间]" in ts
        assert "本地时间:" in ts
        assert "星期:" in ts
        assert "时区:" in ts

    def test_build_position_no_context(self):
        sc = SelfContext()
        pos = sc._build_position_context()
        assert "[当前位置]" in pos

    def test_build_position_with_root(self):
        mock_cs = MagicMock()
        mock_cs.get_project_root.return_value = "/test/project"
        sc = SelfContext(context_service=mock_cs)
        pos = sc._build_position_context()
        assert "/test/project" in pos

    def test_build_task_state_no_tasks(self):
        mock_ts = MagicMock()
        mock_ts.get_active_count.return_value = 0
        mock_ts.get_queued_count.return_value = 0
        sc = SelfContext(task_service=mock_ts)
        state = sc._build_task_state_context()
        assert state == ""

    def test_build_task_state_with_tasks(self):
        mock_ts = MagicMock()
        mock_ts.get_active_count.return_value = 2
        mock_ts.get_queued_count.return_value = 1
        sc = SelfContext(task_service=mock_ts)
        state = sc._build_task_state_context()
        assert "活跃任务: 2" in state
        assert "排队任务: 1" in state

    def test_build_full_context(self):
        mock_cs = MagicMock()
        mock_cs.get_project_root.return_value = "/test/project"
        mock_ts = MagicMock()
        mock_ts.get_active_count.return_value = 1
        mock_ts.get_queued_count.return_value = 0
        sc = SelfContext(context_service=mock_cs, task_service=mock_ts)
        result = sc.build()
        assert "[当前时间]" in result
        assert "/test/project" in result
        assert "活跃任务: 1" in result

    def test_build_handoff_no_task(self):
        mock_ts = MagicMock()
        mock_ts.get_task_status.return_value = None
        sc = SelfContext(task_service=mock_ts)
        result = sc.build_handoff("session-1")
        assert result == ""

    def test_build_handoff_active_task(self):
        mock_task = MagicMock()
        mock_task.is_active = True
        mock_task.phase = "execute"
        mock_task.status = "RUNNING"
        mock_task.task_list = ["task1", "task2"]
        mock_ts = MagicMock()
        mock_ts.get_task_status.return_value = mock_task
        sc = SelfContext(task_service=mock_ts)
        result = sc.build_handoff("session-1")
        assert "未完成的任务" in result
        assert "execute" in result

    def test_build_handoff_terminal_task(self):
        mock_task = MagicMock()
        mock_task.is_active = False
        mock_task.is_terminal = True
        mock_task.status = MagicMock()
        mock_task.status.value = "COMPLETED"
        mock_task.updated_at = "2026-06-28 12:00"
        mock_ts = MagicMock()
        mock_ts.get_task_status.return_value = mock_task
        sc = SelfContext(task_service=mock_ts)
        result = sc.build_handoff("session-1")
        assert "已完成" in result

    def test_build_memory_no_root(self):
        sc = SelfContext()
        result = sc._build_memory_context()
        assert result == ""

    def test_build_memory_no_dir(self):
        mock_cs = MagicMock()
        mock_cs.get_project_root.return_value = "/nonexistent"
        sc = SelfContext(context_service=mock_cs)
        result = sc._build_memory_context()
        assert result == ""

    def test_build_memory_with_mem_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mem_dir = os.path.join(tmpdir, ".workbuddy", "memory")
            os.makedirs(mem_dir, exist_ok=True)
            mem_file = os.path.join(mem_dir, "MEMORY.md")
            with open(mem_file, "w", encoding="utf-8") as f:
                f.write("This is test memory.")

            mock_cs = MagicMock()
            mock_cs.get_project_root.return_value = tmpdir
            sc = SelfContext(context_service=mock_cs)
            result = sc._build_memory_context()
            assert "This is test memory" in result

    def test_cache_invalidation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mem_dir = os.path.join(tmpdir, ".workbuddy", "memory")
            os.makedirs(mem_dir, exist_ok=True)
            mem_file = os.path.join(mem_dir, "MEMORY.md")
            with open(mem_file, "w", encoding="utf-8") as f:
                f.write("v1")

            mock_cs = MagicMock()
            mock_cs.get_project_root.return_value = tmpdir
            sc = SelfContext(context_service=mock_cs)
            result1 = sc._build_memory_context()
            assert "v1" in result1

            # Update file
            with open(mem_file, "w", encoding="utf-8") as f:
                f.write("v2")

            # Cache should still be stale
            result2 = sc._build_memory_context()
            assert "v1" in result2  # cached

            # Invalidate and re-read
            sc.invalidate_cache()
            result3 = sc._build_memory_context()
            assert "v2" in result3

    def test_build_task_state_exception_handling(self):
        mock_ts = MagicMock()
        mock_ts.get_active_count.side_effect = Exception("db error")
        sc = SelfContext(task_service=mock_ts)
        state = sc._build_task_state_context()
        assert state == ""

    def test_build_handoff_exception_handling(self):
        mock_ts = MagicMock()
        mock_ts.get_task_status.side_effect = Exception("db error")
        sc = SelfContext(task_service=mock_ts)
        result = sc.build_handoff("session-1")
        assert result == ""