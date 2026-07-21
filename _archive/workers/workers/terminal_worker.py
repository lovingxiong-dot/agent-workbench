import os
import subprocess
import shlex
from PySide6.QtCore import QThread, Signal


class TerminalWorker(QThread):
    output = Signal(str)
    finished_cmd = Signal(int)

    def __init__(self, command, cwd=None):
        """
        command: str 或 list。
        - str 时保持 shell=True 执行（兼容旧调用）。
        - list 时直接作为 argv 执行，shell=False，更安全。
        """
        super().__init__()
        self.command = command
        self.cwd = cwd or os.getcwd()
        self._process = None

    def run(self):
        try:
            if isinstance(self.command, list):
                cmd = list(self.command)
                shell = False
            else:
                cmd = str(self.command)
                shell = True

            self._process = subprocess.Popen(
                cmd,
                cwd=self.cwd,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            for line in iter(self._process.stdout.readline, ''):
                if line:
                    self.output.emit(line.rstrip('\n'))
            self._process.wait()
            self.finished_cmd.emit(self._process.returncode)
        except Exception as e:
            self.output.emit(f"[终端错误] {e}")
            self.finished_cmd.emit(-1)

    def stop(self):
        if self._process and self._process.poll() is None:
            self._process.terminate()
