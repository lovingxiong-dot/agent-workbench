from PySide6.QtWidgets import QToolButton, QWidget, QVBoxLayout, QLabel, QTreeView, QFileSystemModel
from PySide6.QtCore import Qt, QDir, Signal
from PySide6.QtWidgets import QAbstractItemView


class SidebarButton(QToolButton):
    def __init__(self, text, tooltip, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setToolTip(tooltip)
        self.setCheckable(True)
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setFixedSize(44, 44)
        self.setCursor(Qt.PointingHandCursor)


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
        header = QLabel("\u8d44\u6e90\u7ba1\u7406\u5668")
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
