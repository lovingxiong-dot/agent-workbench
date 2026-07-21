"""
PythonResolver — 自动解析项目应使用的 Python 解释器

为 AI 工具执行提供"正确的 Python"，优先级：
1. 当前 InterpreterService 中选中的 Python（如果是 venv）
2. project_root/venv/Scripts/python.exe
3. project_root/.venv/Scripts/python.exe
4. 用户画像中记录的 default_python_env
5. shutil.which("python")
"""
import os
import shutil
from typing import Optional


VENV_RELATIVE_PATHS = [
    ("venv", "Scripts", "python.exe"),
    (".venv", "Scripts", "python.exe"),
]


def resolve_project_python(
    project_root: str = "",
    interpreter_service=None,
    user_profile: dict = None,
) -> Optional[str]:
    """
    返回项目应使用的 Python 可执行文件完整路径。
    若无法找到项目 venv，则回退到系统 python。
    """
    project_root = project_root or ""

    # 1. 当前 InterpreterService 中选中的 Python
    if interpreter_service is not None:
        current = interpreter_service.get_current()
        if current and current.type == "python" and os.path.exists(current.path):
            return current.path

    # 2. project_root 下的 venv / .venv
    if project_root and os.path.isdir(project_root):
        for parts in VENV_RELATIVE_PATHS:
            candidate = os.path.normpath(os.path.join(project_root, *parts))
            if os.path.exists(candidate):
                return candidate

    # 3. 用户画像中记录的默认 Python 环境
    if user_profile:
        default_env = user_profile.get("default_python_env", "")
        if default_env and os.path.exists(default_env):
            return default_env

    # 4. 系统 PATH 中的 python
    system_python = shutil.which("python")
    if system_python:
        return system_python

    return None


def resolve_python_command(
    command: str,
    project_root: str = "",
    interpreter_service=None,
    user_profile: dict = None,
) -> str:
    """
    若 command 以 python/python.exe/py 开头，自动替换为项目 venv Python 路径。
    返回重写后的命令字符串。
    """
    if not command:
        return command
    import re
    pattern = re.compile(r'^(python\.exe|python|py)\b', re.IGNORECASE)
    if not pattern.match(command.strip()):
        return command
    venv_python = resolve_project_python(project_root, interpreter_service, user_profile)
    if not venv_python:
        return command
    # 对含空格路径加双引号
    python_display = f'"{venv_python}"' if ' ' in venv_python else venv_python
    return pattern.sub(python_display, command.strip(), count=1)
