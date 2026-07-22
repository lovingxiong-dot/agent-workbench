# ADR-002 — Phase 2-C Presentation Architecture RFC

> **Status**: DRAFT — Phase 2-C.0 Contract Freeze
> **Date**: 2026-07-22
> **Supersedes**: ADR-001 (Shell Contract Freeze)
> **Scope**: Interaction Protocol Boundary + Presentation Runtime + Renderer Registry

---

## 1. 背景

### 1.1 当前架构状态

Phase 2-B.2 已完成 Architecture Declaration Sync，确立了以下架构：

```
CENTRE Runtime → Interaction Boundary → Presentation Renderer → v6/ui → Qt
```

### 1.2 当前代码中的三个架构债务

| # | 债务 | 位置 | 影响 |
|---|------|------|------|
| 1 | `InteractionEvent` 位于 `runtime/interaction/` 包内 | `event.py`, `renderer.py` | 它是 Runtime↔UI 通信协议，不应属于 Runtime 包 |
| 2 | `PresentationPipeline` 是静态方法集合 | `integration.py` | 无生命周期，无法支持多 Renderer |
| 3 | 非聊天命令通过 `RuntimeRequest(action_id=...)` 传递 | `v6_ui_application.py` | 缺少独立的 `InteractionCommand` 概念 |

### 1.3 目标

将当前"可工作的原型"升级为"正式协议化架构"：

```
Phase 2-B (当前):
  RuntimeRequest (含 action_id) → Runtime → InteractionEvent → Renderer → UI

Phase 2-C (目标):
  InteractionCommand → Runtime → InteractionEvent → PresentationRuntime → Renderer Registry → Concrete Renderer → UI
```

---

## 2. Interaction Protocol Boundary

### 2.1 协议包定位

当前 `InteractionEvent` 和 `UIEventRenderer` 位于 `runtime/interaction/`，但它们是 Runtime↔Presentation 的通信协议，类似 HTTP 不属于 nginx 也不属于浏览器。

**决策**：将 Interaction Protocol 从 Runtime 包中提取为独立协议包。

**目标路径**：

```
agent_workbench/
├── protocols/                    ← 新增：通信协议包
│   ├── __init__.py
│   ├── interaction/
│   │   ├── __init__.py
│   │   ├── command.py            ← 新增：InteractionCommand
│   │   ├── event.py              ← 迁移自 runtime/interaction/event.py
│   │   └── renderer.py           ← 迁移自 runtime/interaction/renderer.py
│   └── shell/
│       ├── __init__.py
│       ├── contract.py           ← 迁移自 presentation/shell/protocol.py
│       └── state.py              ← ShellContract 数据模型
│
├── runtime/
│   └── interaction/
│       ├── request.py            ← 保留：RuntimeRequest（Runtime 内部）
│       ├── layer.py              ← 保留：WorkbenchInteractionLayer
│       └── mapper.py             ← 保留：RuntimeEventMapper
│
└── presentation/
    └── shell/
        ├── integration.py        ← 重构：PresentationRuntime
        └── transformers/         ← 保留
```

### 2.2 协议职责表

| 协议类型 | 方向 | 包位置 | 作用 |
|---------|------|--------|------|
| `InteractionCommand` | UI → Runtime | `protocols/interaction/command.py` | 用户意图（聊天、停止、切换会话、打开工作区） |
| `RuntimeRequest` | Application → Runtime | `runtime/interaction/request.py` | 执行请求（内部） |
| `InteractionEvent` | Runtime → UI | `protocols/interaction/event.py` | 执行反馈 |
| `ShellContract` | State → Renderer | `protocols/shell/` | UI 状态同步 |

### 2.3 依赖方向（Migration 后）

```
v6/ui Widgets
    │
    │ Qt Signal
    ▼
InteractionCommand  (protocols/interaction/command.py)
    │
    ▼
RuntimeRequest  (runtime/interaction/request.py)
    │
    ▼
Runtime
    │
    ▼
InteractionEvent  (protocols/interaction/event.py)
    │
    ▼
PresentationRuntime  (presentation/shell/integration.py)
    │
    ▼
Renderer Registry
    │
    ▼
Concrete Renderer  (presentation/renderers/v6_ui/)
    │
    ▼
v6/ui Widgets
```

---

## 3. InteractionCommand 独立化

### 3.1 问题

当前代码中，非聊天命令通过 `RuntimeRequest(action_id=...)` 传递：

```python
# 当前：停止生成
RuntimeRequest(source=COMMAND_BAR, action_id="stop_generation")

# 当前：终端执行
RuntimeRequest(source=COMMAND_BAR, text=cmd, action_id="terminal_execute")
```

这导致：
- `action_id` 是字符串，无类型安全
- 命令语义分散在 `action_id` 和 `text` 之间
- Runtime 需要解析 `action_id` 来判断是否是非聊天命令

### 3.2 目标：InteractionCommand

```python
# protocols/interaction/command.py

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CommandType(str, Enum):
    """用户意图类型。"""
    CHAT_MESSAGE = "chat.message"       # 聊天消息
    GENERATION_CANCEL = "generation.cancel"  # 停止生成
    SESSION_CREATE = "session.create"   # 新建会话
    SESSION_SWITCH = "session.switch"   # 切换会话
    SESSION_DELETE = "session.delete"   # 删除会话
    WORKSPACE_OPEN = "workspace.open"   # 打开工作区
    TOOL_EXECUTE = "tool.execute"       # 执行工具
    TERMINAL_EXECUTE = "terminal.execute"  # 终端命令


@dataclass
class InteractionCommand:
    """UI 层用户意图。

    与 RuntimeRequest 的区别：
    - InteractionCommand 表达用户意图（UI 语言）
    - RuntimeRequest 表达执行请求（Runtime 语言）
    - Decision Layer 负责将 Command 翻译为 Request
    """
    type: CommandType
    payload: dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None
```

### 3.3 使用对比

```python
# 旧（Phase 2-B）：所有命令伪装成 RuntimeRequest
il.submit_request(RuntimeRequest(
    source=RuntimeRequestSource.COMMAND_BAR,
    action_id="stop_generation",
))

# 新（Phase 2-C）：明确的 InteractionCommand
il.submit_command(InteractionCommand(
    type=CommandType.GENERATION_CANCEL,
))

# 聊天消息
il.submit_command(InteractionCommand(
    type=CommandType.CHAT_MESSAGE,
    payload={"text": "hello"},
    session_id=self._controller.session_id,
))
```

### 3.4 InteractionLayer 新增方法

```python
class WorkbenchInteractionLayer:
    def submit_command(self, command: InteractionCommand) -> str:
        """接收 InteractionCommand，内部转换为 RuntimeRequest 后提交。"""
        request = self._command_to_request(command)
        return self.submit_request(request)

    def _command_to_request(self, command: InteractionCommand) -> RuntimeRequest:
        match command.type:
            case CommandType.CHAT_MESSAGE:
                return RuntimeRequest(
                    source=RuntimeRequestSource.GLOBAL_CHAT,
                    text=command.payload.get("text", ""),
                    session_id=command.session_id,
                )
            case CommandType.GENERATION_CANCEL:
                return RuntimeRequest(
                    source=RuntimeRequestSource.COMMAND_BAR,
                    action_id="stop_generation",
                )
            case CommandType.SESSION_CREATE:
                return RuntimeRequest(
                    source=RuntimeRequestSource.COMMAND_BAR,
                    action_id="create_session",
                )
            case CommandType.SESSION_SWITCH:
                return RuntimeRequest(
                    source=RuntimeRequestSource.COMMAND_BAR,
                    action_id="switch_session",
                    payload={"session_id": command.payload.get("session_id")},
                )
            case CommandType.SESSION_DELETE:
                return RuntimeRequest(
                    source=RuntimeRequestSource.COMMAND_BAR,
                    action_id="delete_session",
                    payload={"session_id": command.payload.get("session_id")},
                )
            case CommandType.TERMINAL_EXECUTE:
                return RuntimeRequest(
                    source=RuntimeRequestSource.COMMAND_BAR,
                    text=command.payload.get("cmd", ""),
                    action_id="terminal_execute",
                )
            case _:
                return RuntimeRequest(
                    source=RuntimeRequestSource.COMMAND_BAR,
                    payload=command.payload,
                )
```

---

## 4. PresentationPipeline 生命周期化

### 4.1 问题

当前 `PresentationPipeline` 是静态方法集合：

```python
class PresentationPipeline:
    @staticmethod
    def sessions_to_navigation_groups(raw_sessions): ...
    @staticmethod
    def messages_to_workspace_state(title, subtitle, raw_messages): ...
    @staticmethod
    def capabilities_to_navigation_items(raw_capabilities): ...
    @staticmethod
    def metadata_to_inspector_state(module_id, raw_properties): ...
```

使用方每次创建实例：

```python
pipeline = PresentationPipeline()
groups = pipeline.sessions_to_navigation_groups(raw_sessions)
```

### 4.2 目标：PresentationRuntime

```python
# presentation/shell/presentation_runtime.py（新增）

class PresentationRuntime:
    """Presentation 层运行时。

    职责：
    - 管理 Renderer 注册表
    - 分发 InteractionEvent 到注册的 Renderer
    - 编排 ShellContract 数据流（ViewModel → Shell Model → Renderer）
    - 生命周期管理

    不负责：
    - Runtime 执行（归属 agent_workbench/runtime/）
    - UI 创建（归属 application/）
    """

    def __init__(self) -> None:
        self._renderers: dict[str, UIEventRenderer] = {}
        self._shell_adapters: dict[str, ShellProtocol] = {}
        self._active_renderer: str | None = None
        self._transformers = PresentationPipeline()  # 保留现有转换逻辑

    # ── Renderer Registry ──

    def register_renderer(
        self, name: str, renderer: UIEventRenderer, shell: ShellProtocol
    ) -> None:
        """注册一个 Renderer。"""
        self._renderers[name] = renderer
        self._shell_adapters[name] = shell

    def set_active_renderer(self, name: str) -> None:
        """切换活跃 Renderer。"""
        if name not in self._renderers:
            raise ValueError(f"Renderer '{name}' not registered")
        self._active_renderer = name

    def get_active_renderer(self) -> UIEventRenderer | None:
        if self._active_renderer is None:
            return None
        return self._renderers[self._active_renderer]

    def get_active_shell(self) -> ShellProtocol | None:
        if self._active_renderer is None:
            return None
        return self._shell_adapters[self._active_renderer]

    # ── Event Dispatch ──

    def dispatch_event(self, event: InteractionEvent) -> None:
        """将 InteractionEvent 分发给活跃 Renderer。"""
        renderer = self.get_active_renderer()
        if renderer is not None:
            renderer.render(event)

    # ── Shell State Update ──

    def update_navigation(self, groups: list[NavigationGroup]) -> None:
        shell = self.get_active_shell()
        if shell is not None:
            shell.update_navigation(groups)

    def update_workspace(self, state: WorkspaceState) -> None:
        shell = self.get_active_shell()
        if shell is not None:
            shell.update_workspace(state)

    def update_inspector(self, state: InspectorState) -> None:
        shell = self.get_active_shell()
        if shell is not None:
            shell.update_inspector(state)

    # ── Data Pipeline（保留现有转换逻辑）──

    def sessions_to_navigation_groups(self, raw_sessions): ...
    def messages_to_workspace_state(self, title, subtitle, raw_messages): ...
    # ... 其余方法同现有 PresentationPipeline

    # ── Lifecycle ──

    def start(self) -> None:
        """启动 Presentation Runtime。"""
        pass

    def shutdown(self) -> None:
        """关闭 Presentation Runtime，释放所有 Renderer。"""
        self._renderers.clear()
        self._shell_adapters.clear()
        self._active_renderer = None
```

### 4.3 V6UIApplication 集成

```python
# 旧（Phase 2-B）：
self._event_renderer = V6UIEventRenderer(...)
self._shell_adapter = V6UIShellAdapter(...)
self._controller.interaction_layer.set_renderer(self._event_renderer)

# 新（Phase 2-C）：
self._presentation = PresentationRuntime()
self._presentation.register_renderer(
    "qt", V6UIEventRenderer(...), V6UIShellAdapter(...)
)
self._presentation.set_active_renderer("qt")
self._controller.interaction_layer.set_renderer(
    self._presentation.get_active_renderer()
)
```

---

## 5. Renderer Registry

### 5.1 设计

```python
# presentation/renderers/registry.py（新增）

class RendererRegistry:
    """Renderer 注册表。

    支持多 Renderer 并存：
    - Qt Renderer（Desktop）
    - Web Renderer
    - CLI Renderer
    - Mobile Renderer
    """

    def __init__(self) -> None:
        self._entries: dict[str, RendererEntry] = {}

    def register(
        self,
        name: str,
        event_renderer: UIEventRenderer,
        shell_adapter: ShellProtocol,
    ) -> None:
        self._entries[name] = RendererEntry(
            name=name,
            event_renderer=event_renderer,
            shell_adapter=shell_adapter,
        )

    def get(self, name: str) -> RendererEntry | None:
        return self._entries.get(name)

    def list(self) -> list[str]:
        return list(self._entries.keys())


@dataclass
class RendererEntry:
    name: str
    event_renderer: UIEventRenderer
    shell_adapter: ShellProtocol
```

---

## 6. Phase 2-C 执行步骤

### 2-C.0: Contract Freeze（本次）✅

- [x] ADR-002 创建
- [ ] 更新 PROJECT_BLUEPRINT.md
- [ ] 更新 architecture-boundaries.md
- [ ] Git commit + tag

### 2-C.1: Interaction Protocol Extraction

1. 创建 `protocols/interaction/` 包
2. 迁移 `InteractionEvent`、`InteractionEventType` 从 `runtime/interaction/event.py` → `protocols/interaction/event.py`
3. 迁移 `UIEventRenderer` 协议从 `runtime/interaction/renderer.py` → `protocols/interaction/renderer.py`
4. 新增 `InteractionCommand`、`CommandType` → `protocols/interaction/command.py`
5. 在 `runtime/interaction/event.py` 添加 re-export（兼容旧引用）
6. 更新所有 import 路径
7. 测试：所有现有测试通过，旧 import 路径不报 deprecation warning

### 2-C.2: PresentationRuntime

1. 创建 `presentation/shell/presentation_runtime.py`
2. 将 `PresentationPipeline` 静态方法迁移为 `PresentationRuntime` 实例方法
3. 新增 `register_renderer()` / `set_active_renderer()` / `dispatch_event()`
4. `V6UIApplication` 改用 `PresentationRuntime`
5. 测试：`PresentationRuntime` 单元测试

### 2-C.3: InteractionCommand 集成

1. `WorkbenchInteractionLayer` 新增 `submit_command()` 方法
2. `V6UIApplication._connect_signals()` 改用 `InteractionCommand`
3. 移除 `action_id` 字符串硬编码
4. 测试：`InteractionCommand` 序列化/反序列化测试

### 2-C.4: Renderer Registry

1. 创建 `presentation/renderers/registry.py`
2. `PresentationRuntime` 集成 `RendererRegistry`
3. 测试：多 Renderer 注册/切换测试

---

## 7. Frozen Zone 约束

Phase 2-C 执行期间，以下区域禁止修改：

| Zone | Files | Rule |
|------|-------|------|
| Runtime Kernel | 19 files | 不变 |
| v6/ui Foundation | 22 files | 不变 |
| Shell Contract | `presentation/shell/protocol.py` | 只迁移，不改语义 |
| Shell Transformers | `presentation/shell/transformers/` | 不变 |

允许修改：
- `runtime/interaction/event.py` — 添加 re-export（兼容旧路径）
- `runtime/interaction/renderer.py` — 添加 re-export
- `presentation/shell/integration.py` — 重构为 `PresentationRuntime`
- `application/v6_ui_application.py` — 适配新 API
- `presentation/renderers/v6_ui/` — 适配新 import 路径

---

## 8. 验证标准

### 8.1 迁移前

```
grep -r "from agent_workbench.runtime.interaction.event" → 所有引用点
grep -r "from agent_workbench.runtime.interaction.renderer" → 所有引用点
```

### 8.2 迁移后

```
grep -r "from agent_workbench.protocols.interaction" → 新路径已生效
grep -r "from agent_workbench.runtime.interaction.event" → 仅限 re-export 文件
```

### 8.3 架构验证

```
✓ protocols/interaction/ 零 Runtime Implementation import
✓ protocols/shell/ 零 Runtime import
✓ v6/ui 零 import 变更
✓ 所有现有测试通过
```

---

## 9. 版本历史

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-22 | 初始创建。Phase 2-C.0 Contract Freeze。 |