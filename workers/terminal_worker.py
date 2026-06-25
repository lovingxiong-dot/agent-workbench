import os
import subprocess
from PySide6.QtCore import QThread, Signal


class TerminalWorker(QThread):
    output = Signal(str)
    finished_cmd = Signal(int)

    def __init__(self, command, cwd=None):
        super().__init__()
        self.command = command
        self.cwd = cwd or os.getcwd()
        self._process = None

    def run(self):
        try:
            self._process = subprocess.Popen(
                self.command,
                cwd=self.cwd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace'
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
