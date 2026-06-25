from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QPlainTextEdit, QLineEdit, QScrollBar, QComboBox
from PySide6.QtGui import QFont
from PySide6.QtCore import Signal
from workers.terminal_worker import TerminalWorker


class TerminalWidget(QWidget):
    interpreter_changed = Signal(str)  # 发出解释器 type

    def __init__(self, parent=None, interpreter_service=None):
        super().__init__(parent)
        self.worker = None
        self._history = []
        self._history_index = -1
        self.interpreter_service = interpreter_service
        self._current_interpreter = None
        self._setup_ui()
        self._populate_interpreters()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        # === 顶部栏：标题 + 解释器选择 + 停止按钮 ===
        header = QHBoxLayout()
        title = QLabel("终端")
        title.setObjectName("panelHeader")
        header.addWidget(title)

        self.interpreter_combo = QComboBox()
        self.interpreter_combo.setToolTip("选择终端解释器")
        self.interpreter_combo.currentIndexChanged.connect(self._on_interpreter_selected)
        header.addWidget(self.interpreter_combo)

        header.addStretch()
        self.stop_btn = QPushButton("停止")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_command)
        header.addWidget(self.stop_btn)
        layout.addLayout(header)

        # === 输出区 ===
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Cascadia Code", 10))
        self.output.setObjectName("terminalOutput")
        layout.addWidget(self.output)

        # === 输入行 ===
        input_layout = QHBoxLayout()
        self.prompt = QLabel("$")
        self.prompt.setObjectName("terminalPrompt")
        input_layout.addWidget(self.prompt)
        self.input = QLineEdit()
        self.input.setPlaceholderText("输入命令并回车执行 (↑↓ 历史)...")
        self.input.returnPressed.connect(self._execute_command)
        layout.addLayout(input_layout)
        self.input.keyPressEvent = self._input_key_press

    def _populate_interpreters(self):
        """从 InterpreterService 填充下拉框"""
        if not self.interpreter_service:
            return
        self.interpreter_combo.blockSignals(True)
        self.interpreter_combo.clear()
        for interp in self.interpreter_service.list_all():
            self.interpreter_combo.addItem(interp.name, interp)
        # 选中当前
        current = self.interpreter_service.get_current()
        if current:
            for i in range(self.interpreter_combo.count()):
                if self.interpreter_combo.itemData(i).type == current.type:
                    self.interpreter_combo.setCurrentIndex(i)
                    self._update_prompt(current)
                    break
        self.interpreter_combo.blockSignals(False)

    def set_interpreter_service(self, service):
        """外部注入 InterpreterService 后刷新下拉框"""
        self.interpreter_service = service
        self._populate_interpreters()

    def _on_interpreter_selected(self, index):
        """用户手动切换解释器"""
        if index < 0 or not self.interpreter_service:
            return
        interp = self.interpreter_combo.itemData(index)
        if interp:
            self.interpreter_service.set_current(interp.type)
            self._update_prompt(interp)
            self.interpreter_changed.emit(interp.type)
            # 切换解释器时清空终端
            self.output.clear()

    def _update_prompt(self, interp):
        """更新提示符"""
        if self.interpreter_service:
            self.prompt.setText(self.interpreter_service.get_prompt_prefix())
        else:
            self.prompt.setText("$")

    def _input_key_press(self, event):
        from PySide6.QtCore import Qt as QtCore
        if event.key() == QtCore.Key_Up:
            if self._history_index < len(self._history) - 1:
                self._history_index += 1
                self.input.setText(self._history[self._history_index])
        elif event.key() == QtCore.Key_Down:
            if self._history_index > 0:
                self._history_index -= 1
                self.input.setText(self._history[self._history_index])
            elif self._history_index == 0:
                self._history_index = -1
                self.input.clear()
        else:
            QLineEdit.keyPressEvent(self.input, event)

    def _execute_command(self):
        command = self.input.text().strip()
        if not command:
            return
        self._history.insert(0, command)
        self._history_index = -1
        self.input.clear()
        prefix = self.prompt.text()
        self.output.appendPlainText(f"{prefix} {command}")
        self.stop_btn.setEnabled(True)
        shell_cmd = command
        if self.interpreter_service:
            interp = self.interpreter_service.get_current()
            if interp:
                shell_cmd = self.interpreter_service.get_shell_command(command)
        self.worker = TerminalWorker(shell_cmd)
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
