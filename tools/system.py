"""
系统工具：命令执行 / 文件操作 / 网络 / 剪贴板 / 通知 / 进程管理
"""
import os
import subprocess
import ctypes
from langchain.tools import tool


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


@tool
def run_command(command: str) -> str:
    """以当前权限执行系统命令、启动程序或打开文件/文件夹"""
    try:
        command = command.strip()
        if not command:
            return "命令不能为空"
        if command.lower().startswith("explorer "):
            path = command[9:].strip().strip('"')
            path = path or "."
            os.startfile(os.path.expandvars(path))
            return f"\u5df2\u6253\u5f00: {path}"
        if _is_launch_command(command):
            subprocess.Popen(command, shell=True)
            return f"\u5df2\u542f\u52a8: {command}"
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=30, encoding="utf-8", errors="replace"
        )
        output = (result.stdout + result.stderr).strip()
        return output if output else f"\u547d\u4ee4\u6267\u884c\u5b8c\u6210\uff08\u9000\u51fa\u7801 {result.returncode}\uff09"
    except Exception as e:
        return f"\u6267\u884c\u5931\u8d25: {str(e)}"


@tool
def run_as_admin(command: str) -> str:
    """以管理员权限执行命令（会弹出 UAC 窗口等待用户确认）"""
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", f"/c {command}", None, 1)
        return "\u5df2\u53d1\u9001\u7ba1\u7406\u5458\u6743\u9650\u8bf7\u6c42\uff0c\u8bf7\u5728 UAC \u7a97\u53e3\u786e\u8ba4\u3002"
    except Exception as e:
        return f"\u63d0\u6743\u5931\u8d25: {str(e)}"


# ═══════════════════════════════════════════════════════
# 文件操作
# ═══════════════════════════════════════════════════════

@tool
def read_file(path: str, encoding: str = "utf-8") -> str:
    """读取文件内容（文本文件），返回前5000字符"""
    try:
        path = os.path.expandvars(path.strip())
        if not os.path.exists(path):
            return f"\u6587\u4ef6\u4e0d\u5b58\u5728: {path}"
        if os.path.isdir(path):
            return f"\u8def\u5f84\u662f\u76ee\u5f55\u800c\u975e\u6587\u4ef6: {path}\n\u8bf7\u4f7f\u7528 list_dir \u67e5\u770b\u76ee\u5f55\u5185\u5bb9"
        with open(path, "r", encoding=encoding, errors="replace") as f:
            content = f.read(5000)
        if len(content) == 5000:
            content += f"\n\n[... \u5df2\u622a\u65ad\uff0c\u6587\u4ef6\u592a\u957f]"
        size = os.path.getsize(path)
        return f"\u6587\u4ef6: {path} ({size} bytes)\n{'-'*40}\n{content}"
    except Exception as e:
        return f"\u8bfb\u53d6\u5931\u8d25: {str(e)}"


@tool
def write_file(path: str, content: str, encoding: str = "utf-8") -> str:
    """写入内容到文件（覆盖模式）"""
    try:
        path = os.path.expandvars(path.strip())
        if not path:
            return "\u8def\u5f84\u4e0d\u80fd\u4e3a\u7a7a"
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding=encoding) as f:
            f.write(content)
        size = os.path.getsize(path)
        return f"\u5df2\u5199\u5165: {path} ({size} bytes)"
    except Exception as e:
        return f"\u5199\u5165\u5931\u8d25: {str(e)}"


@tool
def list_dir(path: str = ".") -> str:
    """列出目录内容（文件和子目录）"""
    try:
        path = os.path.expandvars(path.strip()) or "."
        if not os.path.exists(path):
            return f"\u76ee\u5f55\u4e0d\u5b58\u5728: {path}"
        if not os.path.isdir(path):
            return f"\u4e0d\u662f\u76ee\u5f55: {path}"
        entries = sorted(os.listdir(path))
        if not entries:
            return f"\u76ee\u5f55\u4e3a\u7a7a: {path}"
        lines = []
        for name in entries:
            full = os.path.join(path, name)
            tag = "[DIR]" if os.path.isdir(full) else "[FILE]"
            try:
                size = os.path.getsize(full) if os.path.isfile(full) else 0
                lines.append(f"  {tag}  {name}  ({size} bytes)" if tag == "[FILE]" else f"  {tag}  {name}")
            except OSError:
                lines.append(f"  {tag}  {name}")
        return f"\u76ee\u5f55: {os.path.abspath(path)}\n{'-'*40}\n" + "\n".join(lines)
    except Exception as e:
        return f"\u5217\u51fa\u5931\u8d25: {str(e)}"


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


@tool
def web_fetch(url: str) -> str:
    """抓取网页内容，返回文本摘要（前2000字符）"""
    try:
        import urllib.request
        import urllib.error

        url = url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        req = urllib.request.Request(url, headers={"User-Agent": "AI-Agent-Workbench/2.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read()

        # Try to decode
        for enc in ["utf-8", "gbk", "gb2312", "latin-1"]:
            try:
                text = raw.decode(enc, errors="replace")
                break
            except Exception:
                continue

        # Strip HTML tags for plain text. Prefer BeautifulSoup; fallback to regex.
        text = _html_to_text(text)

        if len(text) > 2000:
            text = text[:2000] + f"\n\n[... 已截断，原始长度 {len(text)} 字符]"

        return f"\u7f51\u9875: {url}\n{'-'*40}\n{text}"

    except urllib.error.HTTPError as e:
        return f"HTTP \u9519\u8bef {e.code}: {url}"
    except urllib.error.URLError as e:
        return f"\u7f51\u7edc\u9519\u8bef: {str(e.reason)[:200]}"
    except Exception as e:
        return f"\u6293\u53d6\u5931\u8d25: {str(e)[:200]}"


# ═══════════════════════════════════════════════════════
# 剪贴板
# ═══════════════════════════════════════════════════════

@tool
def clipboard_read() -> str:
    """读取 Windows 剪贴板文本内容"""
    try:
        import subprocess
        result = subprocess.run(
            ["powershell", "-Command", "Get-Clipboard"],
            capture_output=True, text=True, timeout=5
        )
        text = result.stdout.strip()
        return text if text else "\u526a\u8d34\u677f\u4e3a\u7a7a\u6216\u65e0\u6587\u5b57\u5185\u5bb9"
    except Exception as e:
        return f"\u8bfb\u53d6\u526a\u8d34\u677f\u5931\u8d25: {str(e)}"


@tool
def clipboard_write(text: str) -> str:
    """将文本写入 Windows 剪贴板"""
    try:
        import subprocess
        proc = subprocess.Popen(
            ["powershell", "-Command", "Set-Clipboard -Value $input"],
            stdin=subprocess.PIPE, text=True
        )
        proc.communicate(input=text, timeout=5)
        return f"\u5df2\u5199\u5165\u526a\u8d34\u677f ({len(text)} \u5b57\u7b26)"
    except Exception as e:
        return f"\u5199\u5165\u526a\u8d34\u677f\u5931\u8d25: {str(e)}"


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
        return f"\u5df2\u53d1\u9001\u901a\u77e5: {title}"
    except ImportError:
        # Fallback using PowerShell
        try:
            subprocess.run(
                ["powershell", "-Command",
                 f"New-BurntToastNotification -Text '{title}', '{message}'"],
                capture_output=True, timeout=5
            )
            return f"\u5df2\u53d1\u9001\u901a\u77e5: {title}"
        except Exception:
            return "\u901a\u77e5\u53d1\u9001\u5931\u8d25: \u8bf7\u5b89\u88c5 pip install winotify"
    except Exception as e:
        return f"\u901a\u77e5\u5931\u8d25: {str(e)}"


# ═══════════════════════════════════════════════════════
# 进程管理
# ═══════════════════════════════════════════════════════

@tool
def list_processes() -> str:
    """列出当前运行的主要进程（按内存使用排序，前15个）"""
    try:
        import subprocess
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-Process | Sort-Object WS -Descending | Select-Object -First 15 | "
             "ForEach-Object { '{0,-30} PID:{1,6}  RAM:{2,10:N0}KB' -f $_.ProcessName, $_.Id, ($_.WS/1KB) }"],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout.strip()
        return f"\u8fdb\u7a0b\u5217\u8868 (\u6309\u5185\u5b58\u6392\u5e8f):\n{output}" if output else "\u65e0\u6cd5\u83b7\u53d6\u8fdb\u7a0b\u5217\u8868"
    except Exception as e:
        return f"\u83b7\u53d6\u8fdb\u7a0b\u5217\u8868\u5931\u8d25: {str(e)}"


@tool
def kill_process(name: str) -> str:
    """按名称终止进程（需确认，模糊匹配）"""
    try:
        import subprocess
        name = name.strip()
        if not name:
            return "\u8fdb\u7a0b\u540d\u4e0d\u80fd\u4e3a\u7a7a"
        result = subprocess.run(
            ["taskkill", "/f", "/im", f"{name}.exe" if not name.endswith(".exe") else name],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() or result.stderr.strip() or f"\u5df2\u7ec8\u6b62: {name}"
    except Exception as e:
        return f"\u7ec8\u6b62\u5931\u8d25: {str(e)}"
