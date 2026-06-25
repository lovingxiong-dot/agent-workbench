from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QPlainTextEdit, QLineEdit, QScrollBar
from PySide6.QtGui import QFont
from workers.terminal_worker import TerminalWorker


class TerminalWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self._history = []
        self._history_index = -1
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
        self.input.setPlaceholderText("输入命令并回车执行 (↑↓ 历史)...")
        self.input.returnPressed.connect(self._execute_command)
        layout.addLayout(input_layout)
        # Key press event for history navigation
        self.input.keyPressEvent = self._input_key_press
        layout.addLayout(input_layout)

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
