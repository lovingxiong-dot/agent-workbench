"""presentation/shell/transformers/ — ViewModel → Shell Model 数据转换。

纯数据转换，不创建 Widget，不 import PySide6，不 import Runtime。
职责：将 presentation/view_models/ 转换为 presentation/shell/protocol.py 定义的 Shell 抽象模型。
"""
