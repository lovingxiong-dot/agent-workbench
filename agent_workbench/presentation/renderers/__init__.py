"""presentation/renderers/ — UI Renderer Layer。

Renderer 是 Presentation Layer 与具体 UI 之间的桥接层。
每个 Renderer 实现一个特定 UI 技术栈（Qt / Web / CLI / Mobile）。

约束：
- Renderer 只能依赖 ShellContract 数据模型 + 目标 UI 组件
- Renderer 允许引用 Interaction Contract（runtime.interaction.event）
- Renderer 不能引用 Runtime Implementation（engine, executor, session, llm, tool）
- Renderer 不能 import PySide6（除非是 Qt 专用 Renderer）
- Renderer 不能修改 ShellContract 定义
"""