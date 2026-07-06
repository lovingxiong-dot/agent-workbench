# V6 接口与信号契约

## 1. 分层契约

### 1.1 MainWindow 职责边界
MainWindow **只允许**做以下 5 件事：
1. 创建 `LeftPanel`、`ChatArea`、`RightPanel` 等 Widget。
2. 转发 UI 事件到 `UIController`。
3. 接收 `UIController` 的 UI 更新信号并调用对应 Widget 的公共接口。
4. 管理窗口行为（拖拽、resize、最大化、置顶）。
5. 注册全局快捷键。

**禁止**：直接调用 Runtime、Service、Worker、LLM、文件/网络/命令等任何业务逻辑。

### 1.2 UIController 职责
`UIController` 是 UI 层与业务层的唯一桥梁：
- 接收 `MainWindow` 发来的 UI 信号。
- 调用 `SessionManager`、`ConfigManager`、`AgentRuntime` 的方法。
- 将业务层事件转换为 UI 更新信号发回 `MainWindow`。
- 维护当前会话 ID、模式、模型等 UI 状态。

### 1.3 AgentRuntime 职责
`AgentRuntime` 是业务中枢：
- 接收 `UIController` 发送的任务请求（`ChatTask`、`AnalyzeTask` 等）。
- 通过 `Scheduler` 调度任务。
- 在 `RuntimeContext` 中维护任务上下文。
- 通过 `EventBus` 输出阶段事件、流式输出、工具执行、确认请求等。

## 2. UI 组件信号契约

### 2.1 LeftPanel 信号
```python
session_selected = Signal(str)          # 选中会话 ID
new_session_requested = Signal()        # 新建会话
session_action = Signal(str, str)       # action, sid  ("delete"/"rename"/"pin")
search_text_changed = Signal(str)       # 搜索文本
theme_toggled = Signal(str)             # "dark"/"light"
file_selected = Signal(str)             # 文件路径
tool_toggled = Signal(str, bool)        # 工具名, 启用状态
mcp_toggled = Signal(str, bool)         # MCP 名, 启用状态
skill_clicked = Signal(str)             # 技能名
automation_toggled = Signal(str, bool)  # 自动化名, 启用状态
```

### 2.2 ChatArea 信号
```python
send_msg = Signal(str)                  # 用户发送消息
stop_msg = Signal()                     # 停止生成
mode_changed = Signal(str)              # 模式切换
model_changed = Signal(str)             # 模型切换
export_requested = Signal()             # 导出会话
settings_requested = Signal()           # 打开设置
search_toggled = Signal()               # Ctrl+F 切换搜索条
more_clicked = Signal(QPoint)           # 更多按钮点击位置
toggle_right_panel = Signal()           # 切换右栏
```

### 2.3 RightPanel 信号
```python
open_file = Signal(str)                 # 打开文件
load_url = Signal(str)                  # 加载 URL
terminal_command = Signal(str)          # 终端执行命令
tab_closed = Signal(str)                # 关闭标签
```

### 2.4 HeaderBar 信号
```python
left_expand_toggled = Signal()
expand_toggled = Signal()
search_clicked = Signal()
more_clicked = Signal(QPoint)
double_clicked = Signal()  # 双击最大化/还原
```

### 2.5 InputArea 信号
```python
send_clicked = Signal()
stop_clicked = Signal()
mode_tag_clicked = Signal()
model_tag_clicked = Signal()
skill_btn_clicked = Signal()
```

## 3. UIController 输出信号
```python
# → MainWindow → LeftPanel
sign_update_sessions = Signal(list)      # Session 列表
sign_set_active_session = Signal(str)    # 设置激活会话
sign_theme_changed = Signal(str)         # 主题变化

# → MainWindow → ChatArea
sign_set_title = Signal(str, str)        # 标题, 副标题（项目路径）
sign_chat_user = Signal(str)             # 用户消息文本
sign_chat_ai = Signal(str, str)          # AI 消息文本, phase
sign_stream_chunk = Signal(str)          # 流式片段
sign_stream_end = Signal()               # 流式结束
sign_set_streaming = Signal(bool)        # 设置发送/停止按钮状态
sign_tool_executed = Signal(str, dict, str, int)  # 工具执行结果卡片
sign_confirm_required = Signal(str, str) # 工具名, 命令
sign_show_analyze_button = Signal(bool)  # 是否显示「帮我分析当前项目」按钮

# → MainWindow → RightPanel
sign_open_file = Signal(str)             # 打开文件到编辑器
sign_update_terminal = Signal(str)       # 追加终端日志
sign_switch_tab = Signal(str)            # 切换右栏标签
```

## 4. AgentRuntime 事件契约（通过 EventBus）
```python
@dataclass
class RuntimeEvent:
    type: str            # "user_message" / "ai_start" / "ai_chunk" / "ai_end" /
                         # "phase_start" / "phase_end" / "tool_call" / "tool_result" /
                         # "confirm_request" / "confirm_result" / "error" / "metric"
    payload: dict        # 事件载荷
    task_id: str         # 任务 ID
    timestamp: float     # 时间戳
```

## 5. 模块行数约束
- `base.py`：≤ 400 行
- 单个 UI 组件：≤ 300 行，超过则拆分
- `main_window.py`：≤ 250 行
- `ui_controller.py`：≤ 400 行
- `runtime.py`：≤ 400 行
- Engine 单文件：≤ 350 行

## 6. 测试契约
每个模块必须满足：
- 至少一个 import smoke 测试。
- UI 组件必须有属性/信号存在性测试。
- Runtime/Engine 必须有行为测试。
- 集成测试必须覆盖端到端 happy path。

## 7. 安全契约
- 禁止在 UI 组件中执行 `subprocess`、`open()`、网络请求、SQL 等。
- 所有外部调用必须通过 Runtime → Engine → Service。
- 工具执行必须经用户确认（除白名单安全工具外）。
- 用户输入必须做长度和类型校验。
