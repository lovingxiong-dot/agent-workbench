from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt


class StatusIndicator(QWidget):
    """Status bar indicator showing model, token usage, and connection status"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        self.connection_dot = QLabel("●")
        self.connection_dot.setStyleSheet("color: #3FB950; font-size: 10px;")
        
        self.model_label = QLabel("tool-agent")
        self.model_label.setStyleSheet("color: #E6EDF3; font-size: 12px;")
        
        self.mode_label = QLabel("Ask")
        self.mode_label.setStyleSheet("color: #58A6FF; font-size: 11px; font-weight: bold;")
        
        self.token_label = QLabel("")
        self.token_label.setStyleSheet("color: #8B949E; font-size: 11px;")
        
        layout.addWidget(self.connection_dot)
        layout.addWidget(self.model_label)
        layout.addWidget(self.mode_label)
        layout.addStretch()
        layout.addWidget(self.token_label)
    
    def set_model(self, name):
        self.model_label.setText(name)
    
    def set_mode(self, mode):
        mode_colors = {"ask": "#3FB950", "plan": "#D29922", "craft": "#F85149"}
        color = mode_colors.get(mode, "#58A6FF")
        self.mode_label.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold;")
        self.mode_label.setText(mode.capitalize())
    
    def set_connected(self, connected=True):
        color = "#3FB950" if connected else "#F85149"
        self.connection_dot.setStyleSheet(f"color: {color}; font-size: 10px;")
        self.connection_dot.setToolTip("已连接" if connected else "已断开")
    
    def set_tokens(self, text):
        self.token_label.setText(text)
