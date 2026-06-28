"""
VerificationWorker — 本地验证后台 Worker

将 py_compile 语法检查和 unittest 单元测试移出主线程，
避免 Verify 阶段卡住 UI。
"""
import os
import shutil
import subprocess

from PySide6.QtCore import Signal

from workers.base_worker import BaseWorker


class VerificationWorker(BaseWorker):
    """
    在独立 QThread 中运行本地验证。
    信号：
      - result_ready(str): 验证详情文本
      - error_occurred(str, str): 错误码和详情
    """

    def __init__(self, project_root: str = "", python_path: str = "", task_timeout: float = 150.0):
        super().__init__(session_id="", task_timeout=task_timeout)
        self.project_root = project_root or ""
        self.python_path = python_path or shutil.which("python") or "python"

    async def _process(self):
        lines = []

        # 语法检查
        try:
            result = subprocess.run(
                [self.python_path, "-m", "py_compile", "main.py"],
                cwd=self.project_root or None,
                capture_output=True, text=True, timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode == 0:
                lines.append(f"✅ 语法检查通过 (main.py) — 使用 {self.python_path}")
            else:
                lines.append(f"❌ 语法检查失败: {result.stderr}")
        except Exception as e:
            lines.append(f"⚠️ 语法检查异常: {e}")

        # 单元测试
        try:
            result = subprocess.run(
                [self.python_path, "-m", "unittest", "discover", "-s", "tests", "-v"],
                cwd=self.project_root or None,
                capture_output=True, text=True, timeout=120,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode == 0:
                lines.append("✅ 单元测试通过")
            else:
                lines.append(f"❌ 单元测试失败: {result.stderr[:500]}")
        except Exception as e:
            lines.append(f"⚠️ 单元测试异常: {e}")

        self.result_ready.emit("\n".join(lines))
