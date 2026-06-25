"""
解释器管理器：自动发现、手动选择、持久化当前终端解释器

支持的解释器类型：
- Python (venv): 项目虚拟环境
- Python (系统): 系统安装的 Python
- PowerShell: Windows PowerShell
- CMD: 命令提示符
- Git Bash: Git for Windows 附带的 Bash
"""

import os
import sys
import subprocess
import shutil
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Interpreter:
    """单个解释器的描述"""
    type: str          # "python", "powershell", "cmd", "git_bash"
    name: str          # 显示名，如 "Python (venv)"
    path: str          # 可执行文件完整路径
    version: str = ""  # 版本号
    args: List[str] = field(default_factory=list)  # 额外参数


class InterpreterService:
    """
    解释器发现与选择服务。

    用法:
        svc = InterpreterService(project_root="F:/Agent/agent_workbench")
        svc.discover()
        svc.set_current("python_venv")
        interp = svc.get_current()
    """

    CONFIG_KEY = "terminal"

    def __init__(self, project_root: str = "", config_service=None):
        self.project_root = os.path.abspath(project_root) if project_root else ""
        self.config_service = config_service
        self._interpreters: List[Interpreter] = []
        self._current: Optional[Interpreter] = None

    # ══════════════════════════════════════════════════════
    # 自动发现
    # ══════════════════════════════════════════════════════

    def discover(self) -> List[Interpreter]:
        """扫描系统中可用的解释器，优先项目 venv"""
        self._interpreters = []

        # 1. Python — 优先项目 venv
        if self.project_root:
            venv_python = os.path.join(self.project_root, "venv", "Scripts", "python.exe")
            if os.path.exists(venv_python):
                ver = self._get_python_version(venv_python)
                self._interpreters.append(Interpreter(
                    type="python", name=f"Python (venv) {ver}",
                    path=venv_python, version=ver
                ))

        # 2. Python — 系统安装
        for loc in self._find_system_pythons():
            ver = self._get_python_version(loc)
            self._interpreters.append(Interpreter(
                type="python", name=f"Python {ver}",
                path=loc, version=ver
            ))

        # 3. PowerShell
        for loc in ["powershell.exe", "pwsh.exe"]:
            path = shutil.which(loc)
            if path:
                ver = self._get_shell_version(path)
                label = "PowerShell" if "powershell" in loc else "PowerShell Core"
                self._interpreters.append(Interpreter(
                    type="powershell", name=f"{label} {ver}",
                    path=path, version=ver
                ))
                break

        # 4. CMD
        cmd_path = shutil.which("cmd.exe")
        if cmd_path:
            self._interpreters.append(Interpreter(
                type="cmd", name="CMD", path=cmd_path
            ))

        # 5. Git Bash
        bash_path = shutil.which("bash.exe")
        if bash_path and ("Git" in bash_path or "git" in bash_path.lower()):
            self._interpreters.append(Interpreter(
                type="git_bash", name="Git Bash", path=bash_path
            ))

        return self._interpreters

    def _find_system_pythons(self) -> List[str]:
        found = []
        venv_python = ""
        if self.project_root:
            venv_python = os.path.normpath(
                os.path.join(self.project_root, "venv", "Scripts", "python.exe")
            )
        candidates = [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python314\python.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python313\python.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python312\python.exe"),
            r"C:\Python314\python.exe",
            r"C:\Python313\python.exe",
            r"C:\Python312\python.exe",
        ]
        for c in candidates:
            c = os.path.normpath(c)
            if os.path.exists(c) and c != venv_python and c not in found:
                found.append(c)
        if not found:
            system_py = shutil.which("python")
            if system_py:
                system_py = os.path.normpath(system_py)
                if system_py != venv_python and system_py not in found:
                    found.append(system_py)
        return found

    def _get_python_version(self, python_path: str) -> str:
        try:
            result = subprocess.run(
                [python_path, "--version"],
                capture_output=True, text=True, timeout=5
            )
            ver = result.stdout.strip() or result.stderr.strip()
            if ver.startswith("Python "):
                return ver.split()[1]
            return ver
        except Exception:
            return ""

    def _get_shell_version(self, shell_path: str) -> str:
        try:
            if "powershell" in shell_path.lower():
                result = subprocess.run(
                    [shell_path, "-Command", "$PSVersionTable.PSVersion.ToString()"],
                    capture_output=True, text=True, timeout=10
                )
                return result.stdout.strip()
            if "pwsh" in shell_path.lower():
                result = subprocess.run(
                    [shell_path, "--version"],
                    capture_output=True, text=True, timeout=5
                )
                return result.stdout.strip()
        except Exception:
            pass
        return ""

    # ══════════════════════════════════════════════════════
    # 解释器列表与选择
    # ══════════════════════════════════════════════════════

    def list_all(self) -> List[Interpreter]:
        return self._interpreters

    def get_current(self) -> Optional[Interpreter]:
        return self._current

    def set_current(self, identifier: str) -> Optional[Interpreter]:
        identifier = identifier.lower().strip()
        for interp in self._interpreters:
            if interp.type == identifier:
                if identifier == "python":
                    venv_match = next(
                        (i for i in self._interpreters if i.type == "python" and "venv" in i.name.lower()),
                        None
                    )
                    if venv_match:
                        self._current = venv_match
                        self._save_preference()
                        return venv_match
                self._current = interp
                self._save_preference()
                return interp
        for interp in self._interpreters:
            if (identifier in interp.name.lower() or
                identifier in interp.path.lower()):
                self._current = interp
                self._save_preference()
                return interp
        if os.path.exists(identifier):
            interp = Interpreter(type="custom", name="Custom", path=identifier)
            self._current = interp
            self._save_preference()
            return interp
        return None

    def get_shell_command(self, user_command: str) -> List[str]:
        if not self._current:
            return ["cmd.exe", "/c", user_command]
        interp = self._current
        if interp.type == "python":
            return [interp.path, "-c", user_command]
        elif interp.type == "powershell":
            return [interp.path, "-Command", user_command]
        elif interp.type == "cmd":
            return [interp.path, "/c", user_command]
        elif interp.type == "git_bash":
            return [interp.path, "-c", user_command]
        else:
            return [interp.path, "/c", user_command]

    def get_prompt_prefix(self) -> str:
        if not self._current:
            return "$"
        t = self._current.type
        if t == "python":
            return ">>>"
        elif t == "powershell":
            return "PS>"
        elif t == "cmd":
            return ">"
        elif t == "git_bash":
            return "$"
        return "$"

    # ══════════════════════════════════════════════════════
    # 持久化
    # ══════════════════════════════════════════════════════

    def _save_preference(self):
        if self.config_service and self._current:
            try:
                self.config_service.set(
                    "terminal.preferred_interpreter",
                    {
                        "type": self._current.type,
                        "name": self._current.name,
                        "path": self._current.path,
                    }
                )
            except Exception:
                pass

    def load_preference(self) -> Optional[Interpreter]:
        if self.config_service:
            try:
                pref = self.config_service.get("terminal.preferred_interpreter")
                if pref and isinstance(pref, dict):
                    pref_type = pref.get("type", "")
                    pref_path = pref.get("path", "")
                    if pref_path and os.path.exists(pref_path):
                        return self.set_current(pref_type)
                    else:
                        return self.set_current(pref_type)
            except Exception:
                pass
        return None

    def get_context_string(self) -> str:
        if not self._interpreters:
            return "[当前终端环境]\n未发现解释器"
        current = self._current
        current_str = "无"
        if current:
            current_str = f"{current.name}\n路径: {current.path}"
        available = ", ".join(i.name for i in self._interpreters)
        return (
            f"[当前终端环境]\n"
            f"当前解释器: {current_str}\n"
            f"可用解释器: {available}"
        )
