#!/usr/bin/env python3
"""
AI Agent 工作台 · 手动模式专业版 (PySide6)
模式：Ask（问答） / Plan（规划） / Act（执行）
所有模式均拥有完整工具权限，敏感操作二次确认。
"""

import os
import sys
import json
import yaml
import asyncio
import subprocess
import threading
from datetime import datetime
from pathlib import Path

from markdown import markdown

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QListWidget, QSplitter,
    QStatusBar, QFrame, QStyleFactory, QListWidgetItem, QScrollBar,
    QTreeView, QFileSystemModel, QPlainTextEdit, QStackedWidget,
    QToolButton, QSizePolicy, QMenu, QInputDialog, QMessageBox,
    QAbstractItemView, QHeaderView, QButtonGroup
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer, QSize, QDir
from PySide6.QtGui import QFont, QColor, QPalette, QIcon, QTextCursor, QAction

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from agent_engine import ModeManager, LLMRegistry, MemoryManager
from tools.system import run_command, run_as_admin
from tools.quant import fetch_stock_data, run_backtest
from tools.mt5 import mt5_get_price, mt5_place_order


# ═══════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════
def resource_path(relative_path):
    """获取资源绝对路径，兼容开发环境和 PyInstaller 打包"""
    if getattr(sys, 'frozen', False):
        base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


def md_to_html(text):
    """Markdown 转 HTML（支持代码块、表格、换行）"""
    html = markdown(
        text,
        extensions=['fenced_code', 'tables', 'nl2br'],
        extension_configs={'fenced_code': {}}
    )
    return html


# ═══════════════════════════════════════════════════════
# 全局配置
# ═══════════════════════════════════════════════════════
with open(resource_path("config.yaml"), "r", encoding="utf-8") as f:
    global_config = yaml.safe_load(f)

mode_manager = ModeManager(resource_path("config.yaml"))
llm_registry = LLMRegistry(resource_path("config.yaml"))
memory_manager = MemoryManager(global_config["memory"])

TOOL_MAP = {
    "run_command": run_command,
    "run_as_admin": run_as_admin,
    "fetch_stock_data": fetch_stock_data,
    "run_backtest": run_backtest,
    "mt5_get_price": mt5_get_price,
    "mt5_place_order": mt5_place_order,
}

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "以当前权限执行系统命令、启动程序或打开文件/文件夹",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string", "description": "要执行的命令"}},
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_as_admin",
            "description": "以管理员权限执行命令（会弹出 UAC 窗口等待用户确认）",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string", "description": "要执行的命令"}},
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_stock_data",
            "description": "获取股票历史数据",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "股票代码"},
                    "start_date": {"type": "string", "description": "开始日期，如 2024-01-01"},
                    "end_date": {"type": "string", "description": "结束日期，如 2024-12-31"}
                },
                "required": ["ticker"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_backtest",
            "description": "运行量化策略回测",
            "parameters": {
                "type": "object",
                "properties": {"strategy_code": {"type": "string", "description": "策略代码"}},
                "required": ["strategy_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mt5_get_price",
            "description": "获取 MT5 实时报价",
            "parameters": {
                "type": "object",
                "properties": {"symbol": {"type": "string", "description": "交易品种，如 EURUSD"}},
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mt5_place_order",
            "description": "MT5 下单",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "交易品种"},
                    "volume": {"type": "number", "description": "手数"},
                    "order_type": {"type": "string", "description": "订单类型，如 buy/sell"}
                },
                "required": ["symbol", "volume", "order_type"]
            }
        }
    },
]

DANGEROUS_KEYWORDS = [
    "del ", "delete", "rm -", "rd /s", "rmdir /s", "format ",
    "mkfs", "shutdown", "reg delete", "reg add", "diskpart",
]


# ═══════════════════════════════════════════════════════
# Agent 后台工作线程（手动模式版，移除自动分类）
# ═══════════════════════════════════════════════════════
class AgentWorker(QThread):
    result_ready = Signal(str)
    log_message = Signal(str)
    task_created = Signal(str, str)   # task_id, description
    task_finished = Signal(str, str)  # task_id, result
    confirm_required = Signal(str, str)  # tool_name, command

    def __init__(self, user_text, mode_name, current_llm, current_tools, session_id):
        super().__init__()
        self.user_text = user_text
        self.mode_name = mode_name
        self.current_llm = current_llm
        self.current_tools = current_tools
        self.session_id = session_id
        self.confirm_event = threading.Event()
        self.confirm_result = False

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._process())
        finally:
            loop.close()

    async def _process(self):
        mode_config = global_config["manual_modes"].get(self.mode_name, {})
        system_prompt = mode_config.get("system_prompt", "你是全能 AI 助手。")

        history = memory_manager.get_session_history(self.session_id)
        system_msg = SystemMessage(content=system_prompt)
        messages = [system_msg] + history.messages + [HumanMessage(content=self.user_text)]

        try:
            allowed_defs = [d for d in TOOL_DEFINITIONS if d["function"]["name"] in self.current_tools]
            llm_with_tools = self.current_llm.bind_tools(allowed_defs) if allowed_defs else self.current_llm
            response = await llm_with_tools.ainvoke(messages)

            if hasattr(response, "tool_calls") and response.tool_calls:
                self.log_message.emit(f"🔧 调用工具: {[tc['name'] for tc in response.tool_calls]}")
                for tc in response.tool_calls:
                    tool_name = tc["name"]
                    tool_args = tc["args"]
                    task_id = f"{tool_name}_{datetime.now().strftime('%H%M%S')}"
                    self.task_created.emit(task_id, f"执行工具 {tool_name}")
                    result = await asyncio.to_thread(self._sync_call_tool, tool_name, tool_args)
                    self.task_finished.emit(task_id, str(result)[:200])
                    messages.append(AIMessage(content=f"工具 {tool_name} 结果: {result}"))
                    self.log_message.emit(f"✅ {tool_name} 返回: {str(result)[:100]}")
                final_response = await self.current_llm.ainvoke(messages)
                reply = final_response.content
            else:
                reply = response.content

            history.add_message(HumanMessage(content=self.user_text))
            history.add_message(AIMessage(content=reply))
            self.result_ready.emit(reply)

        except Exception as ex:
            self.result_ready.emit(f"❌ 错误: {str(ex)}")
            self.log_message.emit(f"❌ 错误: {ex}")

    def _sync_call_tool(self, name, args):
        tool_func = TOOL_MAP.get(name)
        if not tool_func:
            return f"工具 {name} 不存在"
        try:
            if isinstance(args, str):
                args = json.loads(args)

            # 敏感操作二次确认
            if name in ("run_command", "run_as_admin"):
                command = args.get("command", "") if isinstance(args, dict) else str(args)
                if self._is_dangerous(command):
                    self.confirm_required.emit(name, command)
                    self.confirm_event.wait()
                    if not self.confirm_result:
                        return "用户取消了敏感操作"

            return tool_func.run(args)
        except Exception as e:
            return f"工具执行失败: {str(e)}"

    def _is_dangerous(self, command: str) -> bool:
        cmd_lower = command.lower()
        return any(kw in cmd_lower for kw in DANGEROUS_KEYWORDS)


# ═══════════════════════════════════════════════════════
# 终端后台线程
# ═══════════════════════════════════════════════════════
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


# ═══════════════════════════════════════════════════════
# 自定义侧边栏按钮
# ═══════════════════════════════════════════════════════
class SidebarButton(QToolButton):
    def __init__(self, text, tooltip, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setToolTip(tooltip)
        self.setCheckable(True)
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setFixedSize(44, 44)
        self.setCursor(Qt.PointingHandCursor)


# ═══════════════════════════════════════════════════════
# 资源管理器面板
# ═══════════════════════════════════════════════════════
class FileTreeWidget(QWidget):
    file_selected = Signal(str)

    def __init__(self, root_path, parent=None):
        super().__init__(parent)
        self.root_path = root_path
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        header = QLabel("资源管理器")
        header.setObjectName("panelHeader")
        layout.addWidget(header)

        self.model = QFileSystemModel()
        self.model.setRootPath(self.root_path)
        self.model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot | QDir.Files)

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.root_path))
        self.tree.setHeaderHidden(True)
        self.tree.setColumnWidth(0, 220)
        self.tree.hideColumn(1)
        self.tree.hideColumn(2)
        self.tree.hideColumn(3)
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree.clicked.connect(self._on_file_clicked)
        layout.addWidget(self.tree)

    def _on_file_clicked(self, index):
        path = self.model.filePath(index)
        self.file_selected.emit(path)


# ═══════════════════════════════════════════════════════
# 对话列表面板
# ═══════════════════════════════════════════════════════
class ConversationListWidget(QWidget):
    new_conversation = Signal()
    conversation_selected = Signal(str)
    conversation_deleted = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        header = QLabel("对话")
        header.setObjectName("panelHeader")
        layout.addWidget(header)

        self.new_btn = QPushButton("+ 新对话")
        self.new_btn.setObjectName("newChatBtn")
        self.new_btn.setCursor(Qt.PointingHandCursor)
        self.new_btn.clicked.connect(self.new_conversation.emit)
        layout.addWidget(self.new_btn)

        self.list = QListWidget()
        self.list.setObjectName("conversationList")
        self.list.itemClicked.connect(self._on_item_clicked)
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self.list)

    def add_conversation(self, session_id, title, active=False):
        item = QListWidgetItem(title)
        item.setData(Qt.UserRole, session_id)
        item.setToolTip(title)
        self.list.addItem(item)
        if active:
            self.list.setCurrentItem(item)
            self._style_active_item(item)

    def set_active(self, session_id):
        for i in range(self.list.count()):
            item = self.list.item(i)
            if item.data(Qt.UserRole) == session_id:
                self.list.setCurrentItem(item)
                self._style_active_item(item)
                return

    def _style_active_item(self, item):
        item.setForeground(QColor("#58A6FF"))

    def _on_item_clicked(self, item):
        session_id = item.data(Qt.UserRole)
        self.conversation_selected.emit(session_id)

    def _on_context_menu(self, pos):
        item = self.list.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        rename = QAction("重命名", self)
        delete = QAction("删除", self)
        rename.triggered.connect(lambda: self._rename_item(item))
        delete.triggered.connect(lambda: self.conversation_deleted.emit(item.data(Qt.UserRole)))
        menu.addAction(rename)
        menu.addAction(delete)
        menu.exec(self.list.mapToGlobal(pos))

    def _rename_item(self, item):
        text, ok = QInputDialog.getText(self, "重命名对话", "名称:", text=item.text())
        if ok and text.strip():
            item.setText(text.strip())

    def remove_conversation(self, session_id):
        for i in range(self.list.count()):
            item = self.list.item(i)
            if item.data(Qt.UserRole) == session_id:
                self.list.takeItem(i)
                return


# ═══════════════════════════════════════════════════════
# 任务列表面板
# ═══════════════════════════════════════════════════════
class TaskListWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tasks = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        header = QLabel("任务")
        header.setObjectName("panelHeader")
        layout.addWidget(header)

        top = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("添加新任务...")
        self.add_btn = QPushButton("+")
        self.add_btn.setFixedWidth(32)
        self.add_btn.clicked.connect(self._add_task_from_input)
        self.input.returnPressed.connect(self._add_task_from_input)
        top.addWidget(self.input)
        top.addWidget(self.add_btn)
        layout.addLayout(top)

        self.list = QListWidget()
        self.list.setObjectName("taskList")
        self.list.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.list)

        self.clear_btn = QPushButton("清除已完成")
        self.clear_btn.clicked.connect(self._clear_completed)
        layout.addWidget(self.clear_btn)

    def _add_task_from_input(self):
        text = self.input.text().strip()
        if text:
            self.add_task(text)
            self.input.clear()

    def add_task(self, text, task_id=None, status="pending"):
        if task_id is None:
            task_id = f"task_{datetime.now().strftime('%H%M%S%f')[:-3]}"
        item = QListWidgetItem(text)
        item.setData(Qt.UserRole, task_id)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Checked if status == "done" else Qt.Unchecked)
        self.list.addItem(item)
        self._tasks[task_id] = item
        return task_id

    def finish_task(self, task_id, result=""):
        item = self._tasks.get(task_id)
        if item:
            item.setCheckState(Qt.Checked)
            if result:
                item.setText(f"{item.text()}  ✅ {result}")

    def _on_item_changed(self, item):
        task_id = item.data(Qt.UserRole)
        self._tasks[task_id] = item

    def _clear_completed(self):
        for i in range(self.list.count() - 1, -1, -1):
            item = self.list.item(i)
            if item.checkState() == Qt.Checked:
                task_id = item.data(Qt.UserRole)
                self._tasks.pop(task_id, None)
                self.list.takeItem(i)


# ═══════════════════════════════════════════════════════
# 终端控制台面板
# ═══════════════════════════════════════════════════════
class TerminalWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        header = QHBoxLayout()
        title = QLabel("终端")
        title.setObjectName("panelHeader")
        header.addWidget(title)
        header.addStretch()
        self.stop_btn = QPushButton("停止")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_command)
        header.addWidget(self.stop_btn)
        layout.addLayout(header)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Cascadia Code", 10))
        self.output.setObjectName("terminalOutput")
        layout.addWidget(self.output)

        input_layout = QHBoxLayout()
        self.prompt = QLabel("$")
        self.prompt.setObjectName("terminalPrompt")
        input_layout.addWidget(self.prompt)
        self.input = QLineEdit()
        self.input.setPlaceholderText("输入命令并回车执行...")
        self.input.returnPressed.connect(self._execute_command)
        input_layout.addWidget(self.input)
        layout.addLayout(input_layout)

    def _execute_command(self):
        command = self.input.text().strip()
        if not command:
            return
        self.input.clear()
        self.output.appendPlainText(f"$ {command}")
        self.stop_btn.setEnabled(True)

        self.worker = TerminalWorker(command)
        self.worker.output.connect(self._append_output)
        self.worker.finished_cmd.connect(self._command_finished)
        self.worker.start()

    def _append_output(self, text):
        self.output.appendPlainText(text)
        scrollbar = self.output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _command_finished(self, code):
        self.output.appendPlainText(f"[退出码 {code}]")
        self.stop_btn.setEnabled(False)
        self.worker = None

    def _stop_command(self):
        if self.worker:
            self.worker.stop()
            self.output.appendPlainText("[已终止]")
            self.stop_btn.setEnabled(False)

    def append_system(self, text):
        self.output.appendPlainText(text)


# ═══════════════════════════════════════════════════════
# 聊天视图
# ═══════════════════════════════════════════════════════
class ChatView(QWidget):
    send_clicked = Signal(str)
    mode_clicked = Signal(str)  # ask / plan / act

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部工具栏
        self.toolbar = QHBoxLayout()
        self.toolbar.setContentsMargins(12, 8, 12, 8)
        self.toolbar.setSpacing(12)

        self.mode_indicator = QLabel("●")
        self.mode_indicator.setStyleSheet("color: #3FB950; font-size: 12px;")
        self.mode_label = QLabel("Ask")
        self.mode_label.setObjectName("modeLabel")

        self.model_label = QLabel("tool-agent")
        self.model_label.setObjectName("modelLabel")

        self.session_label = QLabel("默认会话")
        self.session_label.setObjectName("sessionLabel")

        self.toolbar.addWidget(self.mode_indicator)
        self.toolbar.addWidget(self.mode_label)
        self.toolbar.addSpacing(12)

        # ★ 手动模式切换按钮组
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.btn_ask = QPushButton("Ask")
        self.btn_plan = QPushButton("Plan")
        self.btn_act = QPushButton("Act")
        for idx, (btn, name) in enumerate([(self.btn_ask, "ask"), (self.btn_plan, "plan"), (self.btn_act, "act")]):
            btn.setCheckable(True)
            btn.setProperty("mode", name)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #21262D; color: #E6EDF3; border: 1px solid #30363D;
                    padding: 4px 16px; border-radius: 8px; font-weight: bold;
                }
                QPushButton:checked {
                    background-color: #388BFD26; border: 1px solid #58A6FF; color: #58A6FF;
                }
                QPushButton:hover { background-color: #30363D; }
            """)
            btn.clicked.connect(lambda checked, n=name: self.mode_clicked.emit(n))
            self.mode_group.addButton(btn)
            self.toolbar.addWidget(btn)
        self.btn_ask.setChecked(True)

        self.toolbar.addStretch()
        self.toolbar.addWidget(self.model_label)
        self.toolbar.addWidget(self.session_label)
        layout.addLayout(self.toolbar)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("toolbarSeparator")
        layout.addWidget(sep)

        # 聊天显示区
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setFont(QFont("Segoe UI", 12))
        self.chat_area.setObjectName("chatArea")
        layout.addWidget(self.chat_area)

        # 输入区
        input_widget = QWidget()
        input_widget.setObjectName("inputWidget")
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(12, 12, 12, 12)
        input_layout.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入指令，Enter 发送...")
        self.input_field.returnPressed.connect(self._send)

        self.send_btn = QPushButton("发送")
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.setFixedWidth(80)
        self.send_btn.clicked.connect(self._send)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        layout.addWidget(input_widget)

    def _send(self):
        text = self.input_field.text().strip()
        if text:
            self.input_field.clear()
            self.send_clicked.emit(text)

    def append_user(self, text):
        self._append_message("user", text)

    def append_ai(self, text):
        self._append_message("ai", text)

    def append_system(self, text):
        self._append_message("system", text)

    def _append_message(self, role, text):
        if role == "user":
            html = self._build_bubble("right", "#1F6FEB", "#FFFFFF", text)
        elif role == "ai":
            html = self._build_bubble("left", "#21262D", "#E6EDF3", text)
        else:
            html = f"<div style='color:#8B949E;font-size:12px;text-align:center;margin:8px 0;'>{text}</div>"

        self.chat_area.moveCursor(QTextCursor.End)
        self.chat_area.insertHtml(html)
        self.chat_area.moveCursor(QTextCursor.End)

    def _build_bubble(self, align, bg, color, text):
        if align == "right":
            margin = "margin: 8px 16px 8px 80px;"
            align_style = "text-align: right;"
        else:
            margin = "margin: 8px 80px 8px 16px;"
            align_style = "text-align: left;"

        html_content = md_to_html(text)
        bubble = f"""
        <div style='{margin}{align_style}'>
            <div style='display:inline-block;background:{bg};color:{color};padding:10px 14px;border-radius:12px;
                        max-width:85%;font-family:"Segoe UI";font-size:13px;line-height:1.5;text-align:left;'>
                {html_content}
            </div>
        </div>
        """
        return bubble

    def set_header(self, mode, model, session):
        self.mode_label.setText(mode.capitalize())
        self.model_label.setText(model)
        self.session_label.setText(session)

    def set_mode(self, mode_name):
        self.btn_ask.setChecked(mode_name == "ask")
        self.btn_plan.setChecked(mode_name == "plan")
        self.btn_act.setChecked(mode_name == "act")
        self.mode_label.setText(mode_name.capitalize())

    def clear(self):
        self.chat_area.clear()


# ═══════════════════════════════════════════════════════
# 主窗口
# ═══════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Agent 工作台 · 手动模式")
        self.resize(1600, 950)

        self._current_session = "default"
        self._sessions = {"default": {"title": "默认会话", "messages": []}}
        self._current_mode = "ask"
        self._current_llm = None
        self._current_tools = []
        self._current_model_name = "tool-agent"

        self._apply_dark_theme()
        self._setup_ui()
        self._init_mode("ask")
        self._init_default_session()

    def _apply_dark_theme(self):
        app = QApplication.instance()
        app.setStyle(QStyleFactory.create("Fusion"))

        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor("#0D1117"))
        dark_palette.setColor(QPalette.WindowText, QColor("#E6EDF3"))
        dark_palette.setColor(QPalette.Base, QColor("#161B22"))
        dark_palette.setColor(QPalette.AlternateBase, QColor("#1C2128"))
        dark_palette.setColor(QPalette.ToolTipBase, QColor("#21262D"))
        dark_palette.setColor(QPalette.ToolTipText, QColor("#E6EDF3"))
        dark_palette.setColor(QPalette.Text, QColor("#E6EDF3"))
        dark_palette.setColor(QPalette.Button, QColor("#21262D"))
        dark_palette.setColor(QPalette.ButtonText, QColor("#E6EDF3"))
        dark_palette.setColor(QPalette.BrightText, QColor("#FF5555"))
        dark_palette.setColor(QPalette.Link, QColor("#58A6FF"))
        dark_palette.setColor(QPalette.Highlight, QColor("#58A6FF"))
        dark_palette.setColor(QPalette.HighlightedText, QColor("#0D1117"))
        app.setPalette(dark_palette)

        app.setStyleSheet("""
            QMainWindow { background-color: #0D1117; }
            QToolTip { background-color: #21262D; color: #E6EDF3; border: 1px solid #30363D; }

            /* 侧边栏 */
            #sidebar { background-color: #010409; border-right: 1px solid #30363D; }
            QToolButton#sidebarBtn {
                background-color: transparent;
                color: #8B949E;
                border: none;
                border-radius: 6px;
                font-size: 18px;
                margin: 4px;
            }
            QToolButton#sidebarBtn:hover { background-color: #21262D; color: #E6EDF3; }
            QToolButton#sidebarBtn:checked { background-color: #1C2128; color: #58A6FF; }

            /* 左侧面板 */
            #leftPanel { background-color: #0D1117; border-right: 1px solid #30363D; }
            #panelHeader {
                color: #E6EDF3;
                font-size: 12px;
                font-weight: bold;
                padding: 10px 12px;
                text-transform: uppercase;
            }

            /* 按钮 */
            QPushButton {
                background-color: #238636;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #2EA043; }
            QPushButton:pressed { background-color: #196C2E; }
            QPushButton:disabled { background-color: #30363D; color: #8B949E; }
            QPushButton#newChatBtn { background-color: #1F6FEB; }
            QPushButton#newChatBtn:hover { background-color: #388BFD; }
            QPushButton#sendBtn { font-weight: bold; }

            /* 输入框 */
            QLineEdit {
                background-color: #161B22;
                color: #E6EDF3;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus { border: 1px solid #58A6FF; }

            /* 列表 */
            QListWidget {
                background-color: transparent;
                border: none;
                color: #E6EDF3;
                font-size: 13px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-radius: 4px;
                margin: 2px 6px;
            }
            QListWidget::item:hover { background-color: #21262D; }
            QListWidget::item:selected { background-color: #1F6FEB33; color: #58A6FF; }
            QListWidget::item:selected:!active { background-color: #1F6FEB33; }

            /* 树形 */
            QTreeView {
                background-color: transparent;
                border: none;
                color: #E6EDF3;
                font-size: 13px;
                outline: none;
            }
            QTreeView::item { padding: 4px; }
            QTreeView::item:selected { background-color: #1F6FEB33; color: #58A6FF; }
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings { image: none; }
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings { image: none; }

            /* 聊天区 */
            QTextEdit#chatArea {
                background-color: #0D1117;
                border: none;
                padding: 8px;
            }
            QTextEdit#chatArea QScrollBar:vertical {
                background: #0D1117; width: 8px; margin: 0;
            }
            QTextEdit#chatArea QScrollBar::handle:vertical {
                background: #30363D; border-radius: 4px; min-height: 20px;
            }

            /* 输入区 */
            QWidget#inputWidget {
                background-color: #161B22;
                border-top: 1px solid #30363D;
            }
            QLabel#modeLabel { color: #E6EDF3; font-weight: bold; font-size: 13px; }
            QLabel#modelLabel {
                background-color: #21262D; color: #58A6FF;
                border-radius: 10px; padding: 2px 10px; font-size: 11px;
            }
            QLabel#sessionLabel { color: #8B949E; font-size: 12px; }
            QFrame#toolbarSeparator { color: #30363D; max-height: 1px; }

            /* 终端 */
            QPlainTextEdit#terminalOutput {
                background-color: #010409;
                color: #E6EDF3;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px;
            }
            QLabel#terminalPrompt { color: #3FB950; font-family: "Cascadia Code"; font-size: 12px; }

            /* 滚动条通用 */
            QScrollBar:vertical { background: #0D1117; width: 8px; margin: 0; }
            QScrollBar::handle:vertical { background: #30363D; border-radius: 4px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }

            /* 代码块 */
            pre {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 10px;
                margin: 8px 0;
                overflow-x: auto;
            }
            code {
                font-family: "Cascadia Code", Consolas, monospace;
                font-size: 12px;
                color: #E6EDF3;
            }
            table {
                border-collapse: collapse;
                margin: 8px 0;
            }
            th, td {
                border: 1px solid #30363D;
                padding: 6px 10px;
            }
            th { background-color: #161B22; }
        """)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左侧图标栏
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(52)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(4, 12, 4, 12)
        sidebar_layout.setSpacing(8)

        self.explorer_btn = self._create_sidebar_btn("📁", "资源管理器", "explorer")
        self.chat_btn = self._create_sidebar_btn("💬", "对话", "chat")
        self.terminal_btn = self._create_sidebar_btn("🖥", "终端", "terminal")
        self.tasks_btn = self._create_sidebar_btn("📝", "任务", "tasks")

        sidebar_layout.addWidget(self.explorer_btn)
        sidebar_layout.addWidget(self.chat_btn)
        sidebar_layout.addWidget(self.terminal_btn)
        sidebar_layout.addWidget(self.tasks_btn)
        sidebar_layout.addStretch()

        main_layout.addWidget(self.sidebar)

        # 左侧面板（可切换）
        self.left_panel = QWidget()
        self.left_panel.setObjectName("leftPanel")
        self.left_panel.setFixedWidth(260)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 8, 0, 8)
        left_layout.setSpacing(0)

        self.left_stack = QStackedWidget()
        self.file_tree = FileTreeWidget(os.path.dirname(os.path.abspath(__file__)))
        self.file_tree.file_selected.connect(self._on_file_selected)

        self.conversation_list = ConversationListWidget()
        self.conversation_list.new_conversation.connect(self._new_conversation)
        self.conversation_list.conversation_selected.connect(self._switch_conversation)
        self.conversation_list.conversation_deleted.connect(self._delete_conversation)

        self.task_list = TaskListWidget()

        self.left_stack.addWidget(self.file_tree)
        self.left_stack.addWidget(self.conversation_list)
        self.left_stack.addWidget(self.task_list)
        left_layout.addWidget(self.left_stack)
        main_layout.addWidget(self.left_panel)

        # 中央 + 底部终端
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        self.center_splitter = QSplitter(Qt.Vertical)
        self.chat_view = ChatView()
        self.chat_view.send_clicked.connect(self._send_message)
        self.chat_view.mode_clicked.connect(self._on_mode_clicked)

        self.terminal = TerminalWidget()

        self.center_splitter.addWidget(self.chat_view)
        self.center_splitter.addWidget(self.terminal)
        self.center_splitter.setSizes([650, 250])
        center_layout.addWidget(self.center_splitter)

        main_layout.addWidget(center_container, 1)

        # 右侧日志面板
        self.right_panel = QWidget()
        self.right_panel.setObjectName("leftPanel")
        self.right_panel.setFixedWidth(280)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(0, 8, 0, 8)
        right_layout.setSpacing(4)

        log_header = QLabel("Agent 日志")
        log_header.setObjectName("panelHeader")
        right_layout.addWidget(log_header)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont("Cascadia Code", 9))
        self.log_area.setObjectName("chatArea")
        right_layout.addWidget(self.log_area)
        main_layout.addWidget(self.right_panel)

        # 状态栏
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("background-color: #161B22; border-top: 1px solid #30363D; color: #8B949E;")
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)
        self.setStatusBar(self.status_bar)

        # 默认选中对话
        self.chat_btn.setChecked(True)
        self.left_stack.setCurrentIndex(1)

    def _create_sidebar_btn(self, icon_text, tooltip, name):
        btn = SidebarButton(icon_text, tooltip)
        btn.setObjectName("sidebarBtn")
        btn.setProperty("view", name)
        btn.clicked.connect(self._on_sidebar_clicked)
        return btn

    def _on_sidebar_clicked(self):
        sender = self.sender()
        view = sender.property("view")

        for btn in [self.explorer_btn, self.chat_btn, self.terminal_btn, self.tasks_btn]:
            if btn != sender:
                btn.setChecked(False)
        sender.setChecked(True)

        if view == "explorer":
            self.left_stack.setCurrentIndex(0)
        elif view == "chat":
            self.left_stack.setCurrentIndex(1)
        elif view == "tasks":
            self.left_stack.setCurrentIndex(2)
        elif view == "terminal":
            self.left_stack.setCurrentIndex(1)
            self.terminal.input.setFocus()

    def _init_mode(self, mode_name):
        """根据模式名加载 LLM 和工具（所有模式拥有相同工具权限）"""
        mode_config = global_config["manual_modes"].get(mode_name)
        if not mode_config:
            return
        self._current_mode = mode_name
        llm_name = mode_config.get("default_llm", "tool-agent")
        self._current_llm = llm_registry.get_llm(llm_name)
        self._current_tools = mode_config.get("tools", list(TOOL_MAP.keys()))
        provider = global_config["llm_providers"].get(llm_name, {})
        self._current_model_name = provider.get("model", llm_name)
        if hasattr(self, 'chat_view'):
            self.chat_view.set_mode(mode_name)
            self.chat_view.set_header(
                mode_name,
                self._current_model_name,
                self._sessions[self._current_session]["title"]
            )
        self._log_message(f"🔄 切换模式: {mode_name} / {self._current_model_name}")

    def _on_mode_clicked(self, mode_name):
        self._init_mode(mode_name)

    def _init_default_session(self):
        self.conversation_list.add_conversation("default", "默认会话", active=True)
        self.chat_view.set_header(
            self._current_mode,
            self._current_model_name,
            self._sessions["default"]["title"]
        )
        self.chat_view.append_system(f"欢迎使用 AI Agent 工作台。当前模式：{self._current_mode.capitalize()}。")

    def _new_conversation(self):
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        title = f"新对话 {len(self._sessions)}"
        self._sessions[session_id] = {"title": title, "messages": []}
        memory_manager.get_session_history(session_id)
        self.conversation_list.add_conversation(session_id, title, active=True)
        self._current_session = session_id
        self.chat_view.clear()
        self.chat_view.set_header(
            self._current_mode,
            self._current_model_name,
            title
        )
        self.status_label.setText(f"新建会话: {title}")

    def _switch_conversation(self, session_id):
        self._current_session = session_id
        session = self._sessions[session_id]
        self.chat_view.clear()
        self.chat_view.set_header(
            self._current_mode,
            self._current_model_name,
            session["title"]
        )
        for msg in session["messages"]:
            self._render_stored_message(msg)
        self.status_label.setText(f"切换会话: {session['title']}")

    def _render_stored_message(self, msg):
        if msg["role"] == "user":
            self.chat_view.append_user(msg["content"])
        elif msg["role"] == "ai":
            self.chat_view.append_ai(msg["content"])
        else:
            self.chat_view.append_system(msg["content"])

    def _delete_conversation(self, session_id):
        if session_id == "default" and len(self._sessions) == 1:
            QMessageBox.information(self, "提示", "不能删除唯一的默认会话")
            return
        self.conversation_list.remove_conversation(session_id)
        self._sessions.pop(session_id, None)
        memory_manager.store.pop(session_id, None)

        if self._current_session == session_id:
            first = next(iter(self._sessions.keys()), "default")
            self._switch_conversation(first)

    def _on_file_selected(self, path):
        self.status_label.setText(f"选中文件: {path}")
        self.log_area.append(f"📁 资源管理器: {path}")

    def _send_message(self, user_text):
        self._sessions[self._current_session]["messages"].append({"role": "user", "content": user_text})
        self.chat_view.append_user(user_text)

        session = self._sessions[self._current_session]
        if len(session["messages"]) == 1:
            title = user_text[:16] + "..." if len(user_text) > 16 else user_text
            session["title"] = title
            self._update_conversation_title(self._current_session, title)
            self.chat_view.set_header(
                self._current_mode,
                self._current_model_name,
                title
            )

        self.chat_view.append_system("AI 思考中...")
        self.status_label.setText("AI 思考中...")

        self.worker = AgentWorker(
            user_text,
            self._current_mode,
            self._current_llm,
            self._current_tools,
            self._current_session
        )
        self.worker.result_ready.connect(self._show_reply)
        self.worker.log_message.connect(self._log_message)
        self.worker.task_created.connect(self._add_task)
        self.worker.task_finished.connect(self._finish_task)
        self.worker.confirm_required.connect(self._on_confirm_required)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def _update_conversation_title(self, session_id, title):
        for i in range(self.conversation_list.list.count()):
            item = self.conversation_list.list.item(i)
            if item.data(Qt.UserRole) == session_id:
                item.setText(title)
                item.setToolTip(title)
                return

    @Slot(str)
    def _show_reply(self, text):
        cursor = self.chat_view.chat_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()

        self.chat_view.append_ai(text)
        self._sessions[self._current_session]["messages"].append({"role": "ai", "content": text})
        self.status_label.setText("就绪")

    @Slot(str)
    def _log_message(self, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {text}")

    @Slot(str, str)
    def _add_task(self, task_id, description):
        self.task_list.add_task(description, task_id)
        self.status_label.setText(f"任务创建: {description}")

    @Slot(str, str)
    def _finish_task(self, task_id, result):
        self.task_list.finish_task(task_id, result)

    @Slot(str, str)
    def _on_confirm_required(self, tool_name, command):
        reply = QMessageBox.warning(
            self,
            "敏感操作确认",
            f"工具 <b>{tool_name}</b> 即将执行以下命令：\n\n{command}\n\n是否继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        self.worker.confirm_result = (reply == QMessageBox.Yes)
        self.worker.confirm_event.set()
        if not self.worker.confirm_result:
            self._log_message(f"⛔ 用户取消了敏感操作: {command}")

    def closeEvent(self, event):
        if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
            self.worker.wait(1000)
        event.accept()


# ═══════════════════════════════════════════════════════
# 启动入口
# ═══════════════════════════════════════════════════════
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
