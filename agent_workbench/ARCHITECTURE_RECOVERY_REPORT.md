# Workbench OS v6.13 — Architecture Recovery Report

> 生成日期：2026-07-21
> 生成者：AISE Agent（接替）
> 状态：Draft — 待审核
> 适用范围：v6.14 ~ v7.x 全部开发

---

## 1. 项目定位修正

### 1.1 历史名称 → 当前名称

| 历史名称 | 当前正确名称 | 定位变化 |
|---------|------------|---------|
| Agent Workbench | **Workbench OS** | 从"Agent 应用"升级为"Agent 操作系统" |
| v6/ui | **UI Shell（Qt 实现）** | 不再是项目核心，而是可替换的 UI 层 |
| Workbench UI | **Workbench OS Shell** | UI 是 Shell，不是本体 |

### 1.2 当前架构层级

```
Workbench OS
│
├── Runtime Kernel（冻结）     ← 不可因 UI 需求变更
├── Core Foundation（冻结）    ← Agent/Capability/Event/Registry/Lifecycle
├── Presentation Layer（新增）  ← ViewModel + Protocol + Adapter
├── UI Shell（纯UI，可替换）    ← Qt Shell（当前）/ Web Shell / Mobile Shell / CLI Shell
└── Adapter Ecosystem          ← Runtime → UI 的翻译层
```

### 1.3 v5→v6→v6.13 演进路线

```
v5（Agent Workbench）
  └── 单体应用：UI + Runtime 紧密耦合

v6 Runtime 重构
  └── 引入 Runtime 模块化（10+ RuntimeModule），
      建立 Request → Planning → Task → Capability → Engine → Provider 链路

v6.8 Core Foundation Freeze
  └── 核心对象模型冻结，ModuleRegistry 生命周期标准化

v6.9 Runtime Kernel Freeze
  └── 目标不是 UI 分离，而是冻结 Runtime 边界。
      AgentRuntime / CapabilityRegistry / DecisionManager / InteractionLayer 冻结。
      不允许新增 Runtime-level 模块；所有新能力通过 Capability Runtime Contract 接入。

v6.10+ Workbench Ecosystem
  └── Workbench 从 Runtime Owner 进化为 Runtime Client。
      Metadata Contract 长期冻结，Presentation Layer 建立。

v6.13 Architecture Stabilization
  └── 在已冻结 Runtime Kernel 基础上，建立 OS Shell 架构。
      Architecture Constitution 正式发布，五个核心原则冻结。
      UI Shell 定义为可替换层（shells/qt/ / shells/web/ / shells/mobile/ / shells/cli/）。
```

---

## 2. 冻结边界清单

### 2.1 Runtime Kernel 冻结模块

以下模块已冻结，**不可因 UI 需求变更**：

| 模块 | 位置 | 冻结内容 | 冻结依据 |
|------|------|---------|---------|
| **AgentRuntime** | `runtime/agent_runtime.py` | Agent 生命周期、PlannerLoop、DecisionManager | v6.9.6-foundation |
| **ModuleRegistry** | `runtime/module_registry.py` | 10+ RuntimeModule 注册、生命周期 | v6.8.0-alpha |
| **BaseRuntimeModule** | `runtime/modules/base.py` | `metadata()` 契约、initialize/apply_config/dispose 生命周期 | v6.8.0-alpha |
| **ConfigStore** | `runtime/config_store.py` | YAML 配置存储、热更新、Observer 模式 | v6.8.0-alpha |
| **CapabilityRouter** | `runtime/capability_router.py` | capability_id → engine_capability 解析 | v6.9.3-alpha |
| **CapabilityRegistry** | `runtime/capability/` | Capability Graph/Chain/Context/State | v6.9.6-alpha |
| **InteractionEvent** | `runtime/interaction/event.py` | UI 事件协议（屏蔽 RuntimeEventType） | v6.9.5-alpha |
| **InteractionLayer** | `runtime/interaction/layer.py` | Runtime → UI 事件映射 | v6.9.5-alpha |
| **DecisionManager** | `runtime/manager/decision_manager.py` | 路由、策略检查、能力选择 | v6.9.4-alpha |
| **ProviderRegistry** | `runtime/provider_registry.py` | Provider 注册与发现 | v6.9.6-foundation |

### 2.2 10个 RuntimeModule 冻结状态

| 模块 | namespace | 职责 | 冻结状态 |
|------|-----------|------|---------|
| `RuntimeModule` | `runtime` | Agent 生命周期、运行状态 | Frozen |
| `AgentModule` | `agent` | Agent 身份与配置 | Frozen |
| `ModelModule` | `model` | Provider/Model 选择 | Frozen |
| `PromptModule` | `prompt` | 系统提示词管理 | Frozen |
| `ToolModule` | `tool` | 工具注册与调用 | Frozen |
| `SkillModule` | `skill` | 技能注册与组合 | Frozen |
| `McpModule` | `mcp` | MCP 连接管理 | Frozen |
| `MemoryModule` | `memory` | 短期/长期记忆 | Frozen |
| `SessionModule` | `session` | 会话管理 | Frozen |
| `ProfileModule` | `profile` | Profile 导入导出 | Frozen |
| `TraceModule` | `trace` | 追踪与审计 | Frozen |
| `WorkflowModule` | `workflow` | 自动化工作流 | Frozen |
| `StrategyModule` | `strategy` | 决策策略 | Frozen |
| `ConfigModule` | `config` | 配置项管理 | Frozen |

### 2.3 Metadata 层冻结

| 模块 | 位置 | 冻结内容 |
|------|------|---------|
| **MetadataDefinition** | `metadata/model.py` | 跨层能力描述契约 |
| **MetadataAdapter** | `metadata/adapter.py` | 跨层适配器协议 |
| **ResourceMetadata** | `metadata/resource.py` | 资源元数据 |
| **MetadataTypes** | `metadata/types.py` | 类型定义 |

### 2.4 依赖方向（不可逆）

```
Agent → Skill → Capability → Engine → Provider → Tool
```

- Capability 不知道 Skill 的存在
- Engine 不知道 Agent 的存在
- **UI Shell 不知道 Runtime 的存在**（只消费 Presentation Contract）

---

## 3. Presentation Contract 定义

### 3.1 当前 ViewModel 清单

| ViewModel | 文件 | 使用者 | 状态 |
|-----------|------|--------|------|
| `AgentViewModel` | `presentation/view_models/agent.py` | Navigator Agent列表 | 已有 |
| `AgentRuntimeViewModel` | `presentation/view_models/agent.py` | StatusBar | 已有 |
| `ConversationViewModel` | `presentation/view_models/conversation.py` | ChatArea 消息列表 | 已有 |
| `CapabilityViewModel` | `presentation/view_models/capability.py` | Navigator 功能列表 | 已有 |
| `ToolViewModel` | `presentation/view_models/capability.py` | FunctionPage 工具列表 | 已有 |
| `MemoryViewModel` | `presentation/view_models/memory.py` | RightPanel 上下文面板 | 已有 |
| `SettingsViewModel` | `presentation/view_models/settings.py` | RightPanel 设置页 | 已有 |

### 3.2 缺失的 ViewModel

以下 UI 元素需要对应的 ViewModel，但当前不存在：

| 缺失 ViewModel | 对应 UI 元素 | 数据来源 |
|---------------|-------------|---------|
| `SessionViewModel` | LeftPanel 会话列表 | `SessionModule.metadata()` |
| `SessionGroupViewModel` | LeftPanel 会话分组 | `SessionModule` |
| `McpServerViewModel` | FunctionPage MCP 列表 | `McpModule.metadata()` |
| `SkillViewModel` | FunctionPage 技能列表 | `SkillModule.metadata()` |
| `AutomationViewModel` | FunctionPage 自动化列表 | `WorkflowModule.metadata()` |
| `TabViewModel` | RightPanel 标签 | 动态注册 |
| `FileViewModel` | RightPanel 最近文件 | 文件系统 |
| `TerminalViewModel` | RightPanel 终端 | 终端进程 |
| `EditorViewModel` | RightPanel 文件编辑器 | 文件系统 |
| `MessageViewModel` | ChatArea 消息流 | `InteractionEvent` |
| `ToolCallViewModel` | ChatArea 工具调用折叠 | `ToolModule` |
| `HeaderViewModel` | HeaderBar 信息 | `AgentRuntime` |
| `StatusItemViewModel` | StatusBar 状态项 | `AgentRuntime` |
| `WelcomeViewModel` | WelcomeWorkspace | `AgentRuntime` |
| `TraceEventViewModel` | TraceWorkspace | `TraceModule` |

### 3.3 建议新增 Protocol 层

当前 ViewModel 是纯数据（dataclass），缺少 Protocol 定义。建议新增：

```python
# presentation/protocols/agent_provider.py
class AgentProviderProtocol(Protocol):
    def list_agents() -> list[AgentViewModel]: ...
    def get_agent(agent_id: str) -> AgentViewModel | None: ...

# presentation/protocols/session_provider.py
class SessionProviderProtocol(Protocol):
    def list_sessions() -> list[SessionViewModel]: ...
    def create_session() -> SessionViewModel: ...
    def delete_session(session_id: str) -> None: ...

# presentation/protocols/capability_provider.py
class CapabilityProviderProtocol(Protocol):
    def list_tools() -> list[ToolViewModel]: ...
    def list_skills() -> list[SkillViewModel]: ...
    def list_mcp_servers() -> list[McpServerViewModel]: ...
```

Protocol 定义能力契约，ViewModel 承载数据。两者分离。

---

## 4. UI Shell 边界定义

### 4.1 UI Shell 是什么

> UI Shell 是 Workbench OS 的视觉外壳。它不包含任何业务逻辑，只负责：
> 1. 渲染 Presentation Contract 中的数据
> 2. 发出用户交互信号
> 3. 不导入任何 Runtime 模块

### 4.2 当前 UI Shell 实现

| 层 | 路径 | 设计来源 | 状态 |
|----|------|---------|------|
| **UI Design Source** | `origin/ui-template: experiments/ui_template.py` | 原始设计 | 纯净（2823行） |
| **Qt Shell 实现** | `v6/ui/`（未来迁移至 `shells/qt/`） | 从 ui-template 拆分 | 已被前 Agent 修改（31文件） |
| **Shell 组装层** | `agent_workbench/ui/workbench/workbench.py` | 新增 | 混合 v6/ui + OS 组件 |

### 4.3 UI Shell 与 Runtime 的边界

```
禁止：UI Shell 直接导入 Runtime 模块
允许：UI Shell 消费 Presentation Contract
允许：UI Shell 发出信号 → Workbench Shell 转发 → Controller → Runtime
```

### 4.4 当前架构偏离点

| 偏离 | 描述 | 严重程度 |
|------|------|---------|
| `v6/ui/` 文件被修改 | 31 文件，+1548/-883 行，混合了视觉修改 + 架构接口 | 高 |
| `workbench.py` 混合组装 | 同时使用 `v6/ui/`（纯UI）和 `agent_workbench/ui/workbench/`（OS级） | 高 |
| `navigator.py` 与 `left_panel.py` 设计不一致 | Navigator 是 QListWidget 设计，LeftPanel 是原始 SessionItem 设计 | 高 |
| `workbench_ui_controller.py` 959行 | 核心控制器被大幅重构，可能需要回退部分 | 中 |
| `v6/ui/` 组件直接使用 Demo 数据 | SessionItem、FunctionPage 等使用硬编码数据，未消费 Presentation Contract | 中 |

### 4.5 当前代码分类（Architecture Audit 基准）

前 Agent 修改的代码需要分类处理：

| 分类 | 判定标准 | 处理方式 |
|------|---------|---------|
| **A. 视觉变化** | 修改了颜色、字体、像素、间距、圆角 | 回滚到 ui-template 基准 |
| **B. 架构接口** | 新增了信号连接、数据注入方法、Presentation Contract 消费 | 保留 |
| **C. 临时代码** | 硬编码 Demo 数据、占位 pass | 删除 |
| **D. Runtime 侵入** | 在 v6/ui/ 中导入 Runtime 模块 | 删除 |

---

## 5. Configuration-Driven Workbench（核心原则）

> **Workbench OS 是配置驱动的，不是代码驱动的。所有扩展对象都应支持通过 UI 注册和配置，不需要修改源码。**

### 5.1 正确流程

```
UI → ConfigManager → Registry Reload → Capability Update → Agent Ready
```

### 5.2 反模式（禁止）

```
UI → 修改代码 → 重新编译 → 重新启动
```

### 5.3 配置链路

```
ConfigStore (YAML)
    │
    ▼
ConfigModule.apply_config()
    │
    ▼
ProviderRegistry / ToolRegistry / SkillRegistry / McpRegistry
    │
    ▼
RuntimeModule.apply_config() → 热更新
    │
    ▼
metadata() → Adapter → ViewModel → UI Shell 刷新
```

---

## 6. 三层数据流架构

### 6.1 正确数据流

```
┌─────────────────────────────────────────────────┐
│              Runtime Kernel（冻结）               │
│                                                   │
│  RuntimeModule.metadata() → MetadataDefinition    │
│  InteractionEvent → InteractionLayer              │
│                                                   │
│  Runtime 不知道 UI 的存在                          │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│           Presentation Layer（新增）              │
│                                                   │
│  MetadataAdapter.adapt() → PresentationModel      │
│  AgentAdapter / CapabilityAdapter / ...           │
│  AgentProviderProtocol / SessionProviderProtocol  │
│                                                   │
│  Presentation Layer 不知道 UI 的实现              │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│           UI Shell（纯UI，可替换）                 │
│                                                   │
│  Qt Shell: v6/ui/left_panel.py                   │
│            v6/ui/chat_area.py                    │
│            v6/ui/right_panel.py                  │
│                                                   │
│  消费 Presentation Contract，发出信号              │
│  不导入 Runtime 模块                              │
└─────────────────────────────────────────────────┘
```

### 6.2 错误数据流（当前 v6 部分路径）

```
v6/ui/left_panel.py
    └── 硬编码 Demo 数据（不经过 Presentation Layer）
    └── 可能直接导入 Runtime 概念（需 Audit 确认）

workbench.py
    └── 混合 v6/ui/ + agent_workbench/ui/workbench/
    └── 信号转发不完整
```

---

## 6. 后续迁移路线

### Phase 0：Architecture Recovery（当前）

**目标**：确认冻结边界，审计当前代码偏离。

**行动**：
1. 备份当前工作区（git stash），保护前 Agent 工作
2. 逐文件审计 `v6/ui/` 所有修改，分类为 A/B/C/D
3. 确认 `v6/ui/` 中是否有 Runtime 导入（D 类）
4. 输出 Architecture Audit Report

**产出**：`ARCHITECTURE_AUDIT.md`（每个 `v6/ui/` 文件的修改分类）

### Phase 1：Presentation Contract Freeze

**目标**：优先建立 Presentation Contract，再改 UI。

**行动**：
1. 新增缺失 ViewModel（Session/Mcp/Skill/Automation/Tab/Message 等）
2. 新增 Protocol 层（AgentProvider/SessionProvider/CapabilityProvider/MessageProvider/StatusProvider）
3. 升级目录结构：`presentation/protocols/` + `presentation/view_models/` + `presentation/adapters/` + `presentation/events/`
4. 冻结 Presentation Contract：后续 UI Shell 只消费此层

**产出**：`presentation/` 目录完整结构

### Phase 2：Qt Shell Recovery

**目标**：恢复 ui-template 视觉 100% 一致，只增加数据注入方法。

**行动**：
1. 回退 A 类修改（视觉变化）
2. 保留 B 类修改（架构接口）
3. 删除 C 类修改（Demo 数据）
4. 删除 D 类修改（Runtime 侵入）
5. 所有 UI 组件改为消费 Presentation Contract（`set_xxx(ViewModel)` / `load_xxx(ViewModel)`）
6. 验证视觉一致性（pixel/font/spacing/color/interaction）

**禁止**：
- 改颜色
- 改布局
- 改交互

**产出**：`v6/ui/` 文件更新为纯 UI Shell

### Phase 3：Runtime Adapter

**目标**：建立 Runtime → Adapter → ViewModel → UI Shell 完整链路。

**行动**：
1. 实现 MetadataAdapter → PresentationModel 的完整翻译
2. 实现 InteractionEvent → MessageViewModel 的完整翻译
3. 确保 Runtime 永远不知道 UI 的存在

**产出**：`presentation/adapters/` 完整实现

### Phase 4：Configuration OS

**目标**：实现 Provider/Model/Tool/MCP/Skill/Workflow/Memory 的 UI 配置管理。

**行动**：
1. UI 管理的 Provider 注册与切换
2. UI 管理的 Model 注册与切换
3. UI 管理的 Tool 启用/禁用
4. UI 管理的 MCP 连接
5. UI 管理的 Skill 安装
6. UI 管理的 Workflow 编排
7. UI 管理的 Memory 配置

**产出**：Configuration-driven Workbench 完整体验

---

## 7. 关键约束重申

### 7.1 不可违反的约束

1. **Runtime 不可因 UI 需求变更** — 冻结边界不可逾越
2. **UI Shell 不可导入 Runtime 模块** — 只消费 Presentation Contract
3. **依赖方向不可逆** — Agent → Skill → Capability → Engine → Provider → Tool
4. **三个注册体系不可合并** — AgentIdentityRegistry / PackageRegistry / DecisionManager
5. **Skill 不得进入 Runtime Kernel**

### 7.2 架构原则

- UI 变化 → UI Shell 变化 → 不影响 Runtime
- 新增 UI Shell（Web/Mobile/CLI）→ 实现同一 Presentation Contract → 不影响 Runtime
- 新增 Runtime 能力 → 通过 metadata() 暴露 → 不影响 UI Shell

---

## 8. 附录

### 8.1 关键文件索引

| 文件 | 用途 |
|------|------|
| `docs/v6/architecture-boundaries.md` | 架构边界定义（Frozen） |
| `v6/.migration-status.json` | v6 迁移状态 |
| `PROJECT_BLUEPRINT.md` | 项目蓝图 |
| `CHANGELOG.md` | 版本历史 |
| `PROJECT_LINEAGE.md` | 项目谱系 |
| `origin/ui-template:experiments/ui_template.py` | 纯 UI 设计源（2823行） |

### 8.2 当前 Git 状态

- 分支：`v6-agent`
- 未提交修改：31 文件，+1548/-883
- 基准分支：`origin/ui-template`

---

> 本报告是第一份 Architecture Recovery 输出。下一步：执行 Phase 0 Architecture Audit（逐文件分类 A/B/C/D）。