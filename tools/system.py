import os
import subprocess
import ctypes
from langchain.tools import tool


# 常见可直接启动的程序/命令白名单（无需捕获输出）
LAUNCH_COMMANDS = (
    "explorer", "notepad", "calc", "mspaint", "cmd", "powershell",
    "wt", "code", "chrome", "edge", "firefox",
)


def _is_launch_command(command: str) -> bool:
    """判断是否为启动程序/文件的命令"""
    cmd_lower = command.lower().strip()
    # 显式 start/open 开头的命令也视为启动
    if cmd_lower.startswith(("start ", "open ")):
        return True
    # 匹配白名单中的程序名
    for name in LAUNCH_COMMANDS:
        if cmd_lower == name or cmd_lower.startswith(name + " "):
            return True
    return False


@tool
def run_command(command: str) -> str:
    """以当前权限执行系统命令、启动程序或打开文件/文件夹"""
    try:
        command = command.strip()
        if not command:
            return "命令不能为空"

        # 处理 explorer 打开目录/文件的特例
        if command.lower().startswith("explorer "):
            path = command[9:].strip().strip('"')
            path = path or "."
            os.startfile(os.path.expandvars(path))
            return f"已打开: {path}"

        # 如果是启动类命令，用 Popen 非阻塞启动
        if _is_launch_command(command):
            # 对 windows 自带程序做特别处理，避免阻塞或找不到路径
            if " " not in command and command.lower() in ("notepad", "calc", "mspaint", "cmd"):
                subprocess.Popen(command, shell=True)
            else:
                subprocess.Popen(command, shell=True)
            return f"已启动: {command}"

        # 普通命令：捕获输出
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace"
        )
        output = (result.stdout + result.stderr).strip()
        return output if output else f"命令执行完成（退出码 {result.returncode}）"
    except Exception as e:
        return f"执行失败: {str(e)}"


@tool
def run_as_admin(command: str) -> str:
    """以管理员权限执行命令（会弹出 UAC 窗口等待用户确认）"""
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", f"/c {command}", None, 1)
        return "已发送管理员权限请求，请在 UAC 窗口确认。"
    except Exception as e:
        return f"提权失败: {str(e)}"
