"""presentation/renderers/v6_ui/ — v6/ui Pure UI Foundation Renderer。

将 v6/ui Presentation Foundation 接入 Runtime 数据流。

组件：
- event_renderer.py: V6UIEventRenderer — InteractionEvent → v6/ui 组件公共 API
- shell_adapter.py: V6UIShellAdapter — ShellContract → v6/ui 组件公共 API

约束：
- 允许引用 Interaction Contract（runtime.interaction.event）
- 不引用 Runtime Implementation（engine, executor, session, llm, tool）
- 不 import WorkbenchUIController
- 不修改 v6/ui 布局/视觉设计
- 只调用 v6/ui 公共 API，不穿透私有成员
"""