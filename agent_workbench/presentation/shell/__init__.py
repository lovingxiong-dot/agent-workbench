"""presentation/shell/ — Shell Protocol Layer.

Shell Protocol 是 Workbench OS 的 OS 级界面抽象。它定义 Navigation / Workspace /
Inspector / Command 四个核心区域的抽象模型和协议接口。

不包含任何具体 UI 组件名（LeftPanel/ChatArea/RightPanel）。
不 import PySide6，不 import Runtime，不创建 Widget。

目录结构（Phase 1-B）：
    protocol.py       — ShellProtocol(Protocol) + 抽象模型
    transformers/     — ViewModel → Shell Model 转换

目录结构（Phase 1-D 追加）：
    implementations/  — QtShell / WebShell / MobileShell
"""
