"""agent_workbench/application/ — Application Bootstrap Layer。

职责：
- Runtime 生命周期管理（启动/停止）
- UI 装配（创建 v6/ui 三栏组件）
- Renderer 绑定（连接事件渲染器 + 状态适配器到 Interaction Boundary）
- 初始状态加载（会话列表、Agent 列表、模型列表）

边界：
- Application 层是唯一合法的 Runtime 接触点
- 不拥有 UI 行为（UI 行为归 v6/ui 组件）
- 不拥有 Renderer 内部逻辑（Renderer 归 presentation/renderers/）
- 不导入 WorkbenchUIController
"""