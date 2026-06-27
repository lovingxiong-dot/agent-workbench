"""
系统工具：命令执行 / 文件操作 / 网络 / 剪贴板 / 通知 / 进程管理
支持原生异步执行（arun），同步入口（@tool）保留兼容。
"""
import asyncio
import os
import sys
import subprocess
import ctypes
from typing import Optional
from langchain.tools import tool

from services.path_resolver import resolve_path
from services.python_resolver import resolve_project_python, resolve_python_command

# 模块级项目根目录，由 AgentWorker 在每次任务前设置
_project_root = ""


def set_project_root(path: str):
    """设置当前任务的项目根目录，供文件工具解析相对路径"""
    global _project_root
    _project_root = os.path.normpath(os.path.abspath(os.path.expandvars(path))) if path else ""


def _subprocess_kwargs(timeout: float = None, extra: dict = None) -> dict:
    """构建跨平台的 subprocess 参数：Windows 下隐藏控制台窗口"""
    kwargs = {}
    if timeout is not None:
        kwargs["timeout"] = timeout
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    if extra:
        kwargs.update(extra)
    return kwargs


# ═══════════════════════════════════════════════════════
# 命令执行
# ═══════════════════════════════════════════════════════

LAUNCH_COMMANDS = (
    "explorer", "notepad", "calc", "mspaint", "cmd", "powershell",
    "wt", "code", "chrome", "edge", "firefox",
)


def _is_launch_command(command: str) -> bool:
    cmd_lower = command.lower().strip()
    if cmd_lower.startswith(("start ", "open ")):
        return True
    for name in LAUNCH_COMMANDS:
        if cmd_lower == name or cmd_lower.startswith(name + " "):
            return True
    return False


async def arun_command(args: dict) -> str:
    """以当前权限执行系统命令（异步原生）"""
    command = args.get("command", "").strip() if isinstance(args, dict) else str(args).strip()
    if not command:
        return "命令不能为空"

    if command.lower().startswith("explorer "):
        path = command[9:].strip().strip('"')
        path = path or "."
        # os.startfile 是同步 Win32 API，但执行极快，直接调用
        os.startfile(os.path.expandvars(path))
        return f"已打开: {path}"

    if _is_launch_command(command):
        # 启动类命令不等待进程结束，直接 Popen
        subprocess.Popen(command, shell=True, **_subprocess_kwargs())
        return f"已启动: {command}"

    # AI 调用 python 命令时自动使用项目 venv
    command = resolve_python_command(command, project_root=_project_root)

    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return "命令执行超过 30 秒，已中断"

    output = (stdout.decode("utf-8", errors="replace") +
              stderr.decode("utf-8", errors="replace")).strip()
    return output if output else f"命令执行完成（退出码 {proc.returncode}）"


@tool
def run_command(command: str) -> str:
    """以当前权限执行系统命令、启动程序或打开文件/文件夹"""
    try:
        return asyncio.run(arun_command({"command": command}))
    except Exception as e:
        return f"执行失败: {str(e)}"


# arun 入口统一在 tools/__init__.py 的 ARUN_MAP 中注册


@tool
def run_as_admin(command: str) -> str:
    """以管理员权限执行命令（会弹出 UAC 窗口等待用户确认）"""
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", f"/c {command}", None, 1)
        return "已发送管理员权限请求，请在 UAC 窗口确认。"
    except Exception as e:
        return f"提权失败: {str(e)}"

# run_as_admin 保持同步，不附加 arun


# ═══════════════════════════════════════════════════════
# 文件操作
# ═══════════════════════════════════════════════════════

async def arun_read_file(args: dict) -> str:
    """异步读取文件内容（文本文件），返回前5000字符"""
    path = args.get("path", "") if isinstance(args, dict) else str(args)
    encoding = args.get("encoding", "utf-8") if isinstance(args, dict) else "utf-8"
    path = resolve_path(path, _project_root)
    if not os.path.exists(path):
        return f"文件不存在: {path}"
    if os.path.isdir(path):
        return f"路径是目录而非文件: {path}\n请使用 list_dir 查看目录内容"

    try:
        import aiofiles
        async with aiofiles.open(path, "r", encoding=encoding, errors="replace") as f:
            content = await f.read(5000)
    except ImportError:
        # 兜底：同步读取（理论上 aiofiles 已安装）
        with open(path, "r", encoding=encoding, errors="replace") as f:
            content = f.read(5000)

    if len(content) == 5000:
        content += f"\n\n[... 已截断，文件太长]"
    size = os.path.getsize(path)
    return f"文件: {path} ({size} bytes)\n{'-'*40}\n{content}"


@tool
def read_file(path: str, encoding: str = "utf-8") -> str:
    """读取文件内容（文本文件），返回前5000字符"""
    try:
        return asyncio.run(arun_read_file({"path": path, "encoding": encoding}))
    except Exception as e:
        return f"读取失败: {str(e)}"


# arun 入口统一在 tools/__init__.py 的 ARUN_MAP 中注册


async def arun_write_file(args: dict) -> str:
    """异步写入内容到文件（覆盖模式）"""
    path = args.get("path", "") if isinstance(args, dict) else ""
    content = args.get("content", "") if isinstance(args, dict) else ""
    encoding = args.get("encoding", "utf-8") if isinstance(args, dict) else "utf-8"
    path = resolve_path(path, _project_root)
    if not path:
        return "路径不能为空"
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    try:
        import aiofiles
        async with aiofiles.open(path, "w", encoding=encoding, errors="replace") as f:
            await f.write(content)
    except ImportError:
        with open(path, "w", encoding=encoding, errors="replace") as f:
            f.write(content)

    size = os.path.getsize(path)
    return f"已写入: {path} ({size} bytes)"


@tool
def write_file(path: str, content: str, encoding: str = "utf-8") -> str:
    """写入内容到文件（覆盖模式）"""
    try:
        return asyncio.run(arun_write_file({"path": path, "content": content, "encoding": encoding}))
    except Exception as e:
        return f"写入失败: {str(e)}"


# arun 入口统一在 tools/__init__.py 的 ARUN_MAP 中注册


async def arun_list_dir(args: dict) -> str:
    """异步列出目录内容"""
    path = args.get("path", ".") if isinstance(args, dict) else str(args) if args else "."
    path = resolve_path(path, _project_root)
    if not os.path.exists(path):
        return f"目录不存在: {path}"
    if not os.path.isdir(path):
        return f"不是目录: {path}"

    try:
        import aiofiles.os
        entries = sorted(await aiofiles.os.listdir(path))
    except ImportError:
        entries = sorted(os.listdir(path))

    if not entries:
        return f"目录为空: {path}"
    lines = []
    for name in entries:
        full = os.path.join(path, name)
        tag = "[DIR]" if os.path.isdir(full) else "[FILE]"
        try:
            size = os.path.getsize(full) if os.path.isfile(full) else 0
            lines.append(f"  {tag}  {name}  ({size} bytes)" if tag == "[FILE]" else f"  {tag}  {name}")
        except OSError:
            lines.append(f"  {tag}  {name}")
    return f"目录: {os.path.abspath(path)}\n{'-'*40}\n" + "\n".join(lines)


@tool
def list_dir(path: str = ".") -> str:
    """列出目录内容（文件和子目录）"""
    try:
        return asyncio.run(arun_list_dir({"path": path}))
    except Exception as e:
        return f"列出失败: {str(e)}"


# arun 入口统一在 tools/__init__.py 的 ARUN_MAP 中注册


# ═══════════════════════════════════════════════════════
# 网络
# ═══════════════════════════════════════════════════════


def _html_to_text(html: str) -> str:
    """将 HTML 转为可读纯文本。优先使用 BeautifulSoup，未安装则回退正则。"""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        # 移除脚本、样式、导航、页脚等噪音节点
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()
        # 优先取正文区域
        main = soup.find("main") or soup.find("article") or soup.find("body") or soup
        text = main.get_text(separator="\n", strip=True)
    except Exception:
        import re
        text = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

    # 压缩空行
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


async def arun_web_fetch(args: dict) -> str:
    """异步抓取网页内容，返回文本摘要"""
    url = args.get("url", "") if isinstance(args, dict) else str(args)
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        import aiohttp
        import ssl as _ssl
        _ssl_error = None
        for _verify_ssl in (True, False):
            try:
                connector = aiohttp.TCPConnector(ssl=False if not _verify_ssl else True)
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=10),
                    connector=connector,
                ) as session:
                    async with session.get(url, headers={"User-Agent": "AI-Agent-Workbench/3.8"}) as resp:
                        raw = await resp.read()
                        content_type = resp.headers.get("Content-Type", "")
                        break
            except aiohttp.ClientConnectorCertificateError as e:
                _ssl_error = e
                continue  # 降级为不验证证书重试
        else:
            raise _ssl_error
    except ImportError:
        # 兜底同步 urllib
        import urllib.request
        import urllib.error
        req = urllib.request.Request(url, headers={"User-Agent": "AI-Agent-Workbench/3.8"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            content_type = resp.headers.get("Content-Type", "")

    # 尝试解码
    text = ""
    for enc in ["utf-8", "gbk", "gb2312", "latin-1"]:
        try:
            text = raw.decode(enc, errors="replace")
            break
        except Exception:
            continue

    text = _html_to_text(text)
    if len(text) > 2000:
        text = text[:2000] + f"\n\n[... 已截断，原始长度 {len(text)} 字符]"

    return f"网页: {url}\n{'-'*40}\n{text}"


@tool
def web_fetch(url: str) -> str:
    """抓取网页内容，返回文本摘要（前2000字符）"""
    try:
        return asyncio.run(arun_web_fetch({"url": url}))
    except Exception as e:
        return f"抓取失败: {str(e)[:200]}"


# arun 入口统一在 tools/__init__.py 的 ARUN_MAP 中注册


# ═══════════════════════════════════════════════════════
# 剪贴板
# ═══════════════════════════════════════════════════════

async def arun_clipboard_read(args: dict = None) -> str:
    """异步读取 Windows 剪贴板文本内容"""
    proc = await asyncio.create_subprocess_exec(
        "powershell", "-Command", "Get-Clipboard",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return "读取剪贴板超时"
    text = stdout.decode("utf-8", errors="replace").strip()
    return text if text else "剪贴板为空或无文字内容"


@tool
def clipboard_read() -> str:
    """读取 Windows 剪贴板文本内容"""
    try:
        return asyncio.run(arun_clipboard_read({}))
    except Exception as e:
        return f"读取剪贴板失败: {str(e)}"


# arun 入口统一在 tools/__init__.py 的 ARUN_MAP 中注册


async def arun_clipboard_write(args: dict) -> str:
    """异步将文本写入 Windows 剪贴板"""
    text = args.get("text", "") if isinstance(args, dict) else str(args)
    proc = await asyncio.create_subprocess_exec(
        "powershell", "-Command", "Set-Clipboard -Value $input",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=text.encode("utf-8")),
            timeout=5
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return "写入剪贴板超时"
    return f"已写入剪贴板 ({len(text)} 字符)"


@tool
def clipboard_write(text: str) -> str:
    """将文本写入 Windows 剪贴板"""
    try:
        return asyncio.run(arun_clipboard_write({"text": text}))
    except Exception as e:
        return f"写入剪贴板失败: {str(e)}"


# arun 入口统一在 tools/__init__.py 的 ARUN_MAP 中注册


# ═══════════════════════════════════════════════════════
# 通知
# ═══════════════════════════════════════════════════════

@tool
def send_notification(title: str, message: str = "") -> str:
    """发送 Windows 桌面通知（气球提示）"""
    try:
        from winotify import Notification
        notif = Notification(
            app_id="AI Agent Workbench",
            title=title,
            msg=message or title,
            duration="short"
        )
        notif.show()
        return f"已发送通知: {title}"
    except ImportError:
        # Fallback using PowerShell
        try:
            subprocess.run(
                ["powershell", "-Command",
                 f"New-BurntToastNotification -Text '{title}', '{message}'"],
                capture_output=True,
                **_subprocess_kwargs(timeout=5)
            )
            return f"已发送通知: {title}"
        except Exception:
            return "通知发送失败: 请安装 pip install winotify"
    except Exception as e:
        return f"通知失败: {str(e)}"

# send_notification 保持同步，不附加 arun


# ═══════════════════════════════════════════════════════
# 进程管理
# ═══════════════════════════════════════════════════════

async def arun_list_processes(args: dict = None) -> str:
    """异步列出当前运行的主要进程"""
    proc = await asyncio.create_subprocess_exec(
        "powershell", "-Command",
        "Get-Process | Sort-Object WS -Descending | Select-Object -First 15 | "
        "ForEach-Object { '{0,-30} PID:{1,6}  RAM:{2,10:N0}KB' -f $_.ProcessName, $_.Id, ($_.WS/1KB) }",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return "获取进程列表超时"
    output = stdout.decode("utf-8", errors="replace").strip()
    return f"进程列表 (按内存排序):\n{output}" if output else "无法获取进程列表"


@tool
def list_processes() -> str:
    """列出当前运行的主要进程（按内存使用排序，前15个）"""
    try:
        return asyncio.run(arun_list_processes({}))
    except Exception as e:
        return f"获取进程列表失败: {str(e)}"


# arun 入口统一在 tools/__init__.py 的 ARUN_MAP 中注册


async def arun_kill_process(args: dict) -> str:
    """异步按名称终止进程"""
    name = args.get("name", "").strip() if isinstance(args, dict) else str(args).strip()
    if not name:
        return "进程名不能为空"
    proc = await asyncio.create_subprocess_exec(
        "taskkill", "/f", "/im",
        f"{name}.exe" if not name.endswith(".exe") else name,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return "终止进程超时"
    output = (stdout.decode("utf-8", errors="replace") +
              stderr.decode("utf-8", errors="replace")).strip()
    return output or f"已终止: {name}"


@tool
def kill_process(name: str) -> str:
    """按名称终止进程（需确认，模糊匹配）"""
    try:
        return asyncio.run(arun_kill_process({"name": name}))
    except Exception as e:
        return f"终止失败: {str(e)}"


# arun 入口统一在 tools/__init__.py 的 ARUN_MAP 中注册


# ══════════════════════════════════════════════════════
# 解释器专用工具
# ══════════════════════════════════════════════════════

async def arun_run_python(args: dict) -> str:
    """异步使用项目 venv 或系统 Python 执行代码片段"""
    code = args.get("code", "") if isinstance(args, dict) else str(args)
    import shutil
    python_path = resolve_project_python(_project_root) or (shutil.which("python") or "python")
    proc = await asyncio.create_subprocess_exec(
        python_path, "-c", code,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return "Python 执行超过 30 秒，已中断"
    output = (stdout.decode("utf-8", errors="replace") +
              stderr.decode("utf-8", errors="replace")).strip()
    return output if output else f"Python 执行完成（退出码 {proc.returncode}）"


@tool
def run_python(code: str) -> str:
    """使用项目 venv 或系统 Python 解释器执行代码片段，返回输出结果"""
    try:
        return asyncio.run(arun_run_python({"code": code}))
    except Exception as e:
        return f"Python 执行失败: {str(e)}"


# arun 入口统一在 tools/__init__.py 的 ARUN_MAP 中注册


async def arun_run_powershell(args: dict) -> str:
    """异步使用 PowerShell 执行命令"""
    command = args.get("command", "") if isinstance(args, dict) else str(args)
    proc = await asyncio.create_subprocess_exec(
        "powershell.exe", "-Command", command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return "PowerShell 执行超过 30 秒，已中断"
    output = (stdout.decode("utf-8", errors="replace") +
              stderr.decode("utf-8", errors="replace")).strip()
    return output if output else f"PowerShell 执行完成（退出码 {proc.returncode}）"


@tool
def run_powershell(command: str) -> str:
    """使用 PowerShell 执行命令，返回输出结果"""
    try:
        return asyncio.run(arun_run_powershell({"command": command}))
    except Exception as e:
        return f"PowerShell 执行失败: {str(e)}"


# arun 入口统一在 tools/__init__.py 的 ARUN_MAP 中注册


async def arun_run_bash(command: str) -> str:
    """异步使用 Git Bash 执行命令"""
    import shutil
    bash_path = shutil.which("bash.exe")
    if not bash_path:
        return "未找到 Git Bash (bash.exe)"
    proc = await asyncio.create_subprocess_exec(
        bash_path, "-c", command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return "Bash 执行超过 30 秒，已中断"
    output = (stdout.decode("utf-8", errors="replace") +
              stderr.decode("utf-8", errors="replace")).strip()
    return output if output else f"Bash 执行完成（退出码 {proc.returncode}）"


@tool
def run_bash(command: str) -> str:
    """使用 Git Bash 执行命令，返回输出结果"""
    try:
        return asyncio.run(arun_run_bash(command))
    except Exception as e:
        return f"Bash 执行失败: {str(e)}"


# arun 入口统一在 tools/__init__.py 的 ARUN_MAP 中注册
