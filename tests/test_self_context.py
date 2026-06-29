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
        sc = SelfContext(app_root="")
        result = sc._build_memory_context()
        assert result == ""

    def test_build_memory_no_dir(self):
        sc = SelfContext(app_root="/nonexistent")
        result = sc._build_memory_context()
        assert result == ""

    def test_build_memory_with_mem_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mem_dir = os.path.join(tmpdir, ".memory")
            os.makedirs(mem_dir, exist_ok=True)
            mem_file = os.path.join(mem_dir, "MEMORY.md")
            with open(mem_file, "w", encoding="utf-8") as f:
                f.write("This is test memory.")

            sc = SelfContext(app_root=tmpdir)
            result = sc._build_memory_context()
            assert "This is test memory" in result

    def test_cache_invalidation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mem_dir = os.path.join(tmpdir, ".memory")
            os.makedirs(mem_dir, exist_ok=True)
            mem_file = os.path.join(mem_dir, "MEMORY.md")
            with open(mem_file, "w", encoding="utf-8") as f:
                f.write("v1")

            sc = SelfContext(app_root=tmpdir)
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


class TestMemoryBoundary:
    """_build_memory_context 边界测试"""

    def test_memory_truncation_long_content(self):
        """记忆内容超过 memory_max_len 时应被截断"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mem_dir = os.path.join(tmpdir, ".memory")
            os.makedirs(mem_dir, exist_ok=True)
            mem_file = os.path.join(mem_dir, "MEMORY.md")
            long_text = "A" * 5000  # 超过默认 3000
            with open(mem_file, "w", encoding="utf-8") as f:
                f.write(long_text)

            sc = SelfContext(app_root=tmpdir)
            result = sc._build_memory_context()
            # 截断验证：5000 字符的完整内容不应出现在结果中
            assert "A" * 5000 not in result
            assert "[项目记忆 - 跨对话持久化]" in result

    def test_log_days_zero_no_logs(self):
        """log_days=0 时不读取任何日志文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mem_dir = os.path.join(tmpdir, ".memory")
            os.makedirs(mem_dir, exist_ok=True)
            log_file = os.path.join(mem_dir, "2026-06-28.md")
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("line1\nline2\nline3")

            sc = SelfContext(
                app_root=tmpdir,
                config={"log_days": 0, "log_lines": 3},
            )
            result = sc._build_memory_context()
            assert "line1" not in result  # 日志不应被读取

    def test_log_lines_zero_no_content(self):
        """log_lines=0 时日志文件读取 0 行"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mem_dir = os.path.join(tmpdir, ".memory")
            os.makedirs(mem_dir, exist_ok=True)
            with open(os.path.join(mem_dir, "MEMORY.md"), "w", encoding="utf-8") as f:
                f.write("mem")
            log_file = os.path.join(mem_dir, "2026-06-28.md")
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("line1\nline2\nline3")

            sc = SelfContext(
                app_root=tmpdir,
                config={"log_days": 3, "log_lines": 0},
            )
            result = sc._build_memory_context()
            assert "line1" not in result  # 0 行日志不应出现