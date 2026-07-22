# Agent Workbench OS — Architecture Boundaries

> 版本：v6.13-frozen
> 状态：Frozen
> 生效日期：2026-07-19
> 适用范围：v6.14 ~ v7.x 全部开发
> 优先级：最高（高于 CHANGELOG、高于 Spec、高于 Task List）

---

## 1. 核心边界图

```
┌──────────────────────────────────────────────────┐
│                  Agent Layer                      │
│                                                   │
│  Identity（谁）  →  Decision（做什么）              │
│       │                    │                      │
│       ▼                    ▼                      │
│  Skill（组合能力）    Capability（原子能力）         │
│       │                    │                      │
│       └────────┬───────────┘                      │
│                │                                  │
│                ▼                                  │
│           Engine（执行实现）                        │
│                │                                  │
│                ▼                                  │
│           Provider（外部服务）                      │
│                │                                  │
│                ▼                                  │
│           Tool（外部动作）                          │
└──────────────────────────────────────────────────┘
```

### 1.1 各层职责

| 层 | 职责 | 类比（OS） | 示例 |
|----|------|-----------|------|
| **Agent** | 数字身份 + 目标 + 行为策略 | user profile / identity | Coding Agent, Research Agent |
| **Skill** | 可组合工作流能力 | application package | Code Review, Market Analysis |
| **Capability** | Runtime 原子能力 | syscall | file.read, tool.execute, llm.chat |
| **Engine** | 执行实现 | kernel module | PythonEngine, LLMEngine |
| **Provider** | 外部服务适配 | device driver | OpenAIProvider, MemoryProvider |
| **Tool** | 外部动作 | peripheral | GitHub API, Web Search |

### 1.2 依赖方向（单向，不可逆）

```
Agent → Skill → Capability → Engine → Provider → Tool
```

- Capability 不知道 Skill 的存在
- Engine 不知道 Agent 的存在
- Provider 不知道 Capability 的存在

**违反此依赖方向即视为架构污染。**

---

## 2. 三个注册体系（不可合并）

```
AgentIdentityRegistry          PackageRegistry               DecisionManager
       │                            │                             │
       │ 管"谁"                     │ 管"在哪"                    │ 管"做什么"
       │                            │                             │
  ┌────┴────┐                  ┌────┴────┐                   ┌────┴────┐
  │ Persona  │                  │ Skill   │                   │ Router   │
  │ Permission│                 │ Capability│                 │ Policy   │
  │ Policy   │                  │ Provider │                  │ Planning │
  │ Skill    │                  │ Tool    │                   │ Resolve  │
  │ Binding  │                  │ Package │                   │ Select   │
  └─────────┘                  └─────────┘                   └─────────┘
```

### 2.1 职责边界

| 注册中心 | 管理 | 不管理 |
|---------|------|--------|
| AgentIdentityRegistry | 身份、权限、策略、Skill 绑定 | 执行、状态、路由 |
| PackageRegistry | 包安装、版本、依赖、扫描 | 运行状态、会话数据 |
| DecisionManager | 路由、策略检查、能力选择 | 身份存储、包管理 |

### 2.2 类比

```
AgentIdentityRegistry = App Store + Docker Registry + HR System
PackageRegistry       = npm / pip / cargo
DecisionManager       = OS Scheduler + Security Policy
```

---

## 3. 四项禁止事项（永久生效）

### 禁止 1：Skill 不得进入 Runtime Kernel

```
禁止：  Runtime → SkillManager
正确：  Agent Layer → Skill Registry
```

Skill 是 Agent 的组合能力，不是 Runtime 的基础设施。Runtime Kernel 不感知 Skill 的存在。

---

### 禁止 2：Memory 不得进入 Capability

```
禁止：  Capability(memory.search)
正确：  Capability → MemoryProvider
```

Memory 是 Provider，不是 Capability。Capability 是原子操作，Memory 是存储后端。

---

### 禁止 3：AgentIdentityRegistry 不负责执行

```
禁止：  Agent.execute()
正确：  Identity → Decision → Capability → Engine
```

Registry 负责"谁"，Decision 负责"做什么"，Runtime 负责"怎么做"。

---

### 禁止 4：PackageRegistry 不保存运行状态

```
禁止：  Package.save_state()
正确：  Package = what it is, Runtime = what is happening
```

Package 是静态描述，Runtime 是动态执行。二者不可混淆。

---

## 4. 演进时间线

```
v6.9.6              v6.10-v6.12           v6.13                v7.0
Runtime Kernel      Workbench             Architecture          Agent
Freeze              Ecosystem             Freeze                Ecosystem
                                                                
"怎么运行"           "怎么接入"            "怎么组织"             "怎么扩展"
                                                                
Orchestrator        ConfigStore           Frozen Zone           Memory
RuntimeContext      ModuleRegistry        Boundary Rules        Knowledge
EventBus            InteractionLayer      Prohibitions          Workflow
Capability          Package System        Agent Identity Route  MCP
                    UI Protocol           Skill/Cap Split       Gateway
                    Metadata              Memory Provider       Marketplace
```

---

## 5. Frozen Zone 引用

详见 [v6.13 Architecture Freeze Report](../../.project/architecture/v6.13-freeze-report.md)。

### 5.1 冻结文件清单（19 个）

```
v6/runtime/orchestrator.py
v6/runtime/context.py
v6/runtime/event_bus.py
v6/runtime/runtime.py
v6/runtime/enums.py
v6/runtime/types.py
agent_workbench/runtime/capability/model.py
agent_workbench/runtime/capability/state.py
agent_workbench/runtime/capability/graph.py
agent_workbench/runtime/capability/chain.py
agent_workbench/runtime/interaction/request.py
agent_workbench/runtime/interaction/event.py
agent_workbench/runtime/interaction/renderer.py
agent_workbench/runtime/interaction/mapper.py
agent_workbench/runtime/interaction/layer.py
agent_workbench/runtime/config_store.py
agent_workbench/runtime/manager/decision_manager.py
agent_workbench/package/loader.py
agent_workbench/package/registry.py
```

### 5.2 Extension Point（5 个，允许新增）

- Module — 新增 Module，不改现有契约
- Capability — 新增能力注册，不改字段结构
- Engine — 新增 Engine，遵守 BaseEngine 协议
- Provider — 新增 Provider，不改流式接口
- Package — 新增 Agent Package，不改必填字段

---

## 6. Presentation Boundary（Phase 2-B.1 新增）

### 6.1 核心边界图

```
Runtime
    |
    v
Interaction Boundary
    |
    v
Presentation Renderer
    |
    v
v6/ui Pure UI Foundation
    |
    v
Qt
```

### 6.2 各层职责

| 层 | 职责 | 允许引用 | 禁止引用 |
|----|------|---------|---------|
| **Application** (`application/`) | 启动编排、依赖注入、生命周期 | `WorkbenchController`, `v6/ui`, `Renderer` | `WorkbenchUIController` |
| **Renderer** (`presentation/renderers/`) | 数据→UI 映射、事件→UI 方法 | `InteractionEvent`, `ShellContract`, `v6/ui` Public API | Runtime Implementation, v6/ui 私有成员 |
| **v6/ui Foundation** (`v6/ui/`) | 视觉系统、布局、交互组件 | `PySide6`, `Qt`, theme constants | 任何 `agent_workbench/` 包 |

### 6.3 依赖方向（单向，不可逆）

```
Runtime → Interaction Contract → Renderer → v6/ui → Qt
```

- Runtime 不知道 v6/ui 存在
- v6/ui 不引用任何 agent_workbench 包
- Renderer 允许引用 Interaction Contract（`runtime.interaction.event`），禁止引用 Runtime Implementation

**违反此依赖方向即视为架构污染。**

### 6.4 三项禁止事项（Presentation 专用）

#### 禁止 1：Renderer 不得穿透 v6/ui 私有成员

```
禁止：  self._chat._scene.clear_chat()
正确：  self._chat.reset_workspace()
```

#### 禁止 2：v6/ui 不得吸收 Runtime 概念

```
禁止：  ChatArea.update_agent()
禁止：  ChatArea.update_model()
禁止：  ChatArea.update_session()
正确：  ChatArea.append_user()          ← UI Capability
正确：  ChatArea.reset_workspace()      ← UI Capability
```

#### 禁止 3：不得将 v6/ui 混同于旧 v6-agent

```
禁止：  把 v6/ui 当成 v6-agent 的 UI 层
正确：  v6/ui 是独立 Pure UI Foundation，与 v6-agent 无关
```

### 6.5 血统区分

| 产物 | 定位 | 状态 |
|------|------|------|
| `v6/ui/` (22 files) | Pure UI Foundation | **ACTIVE** |
| `agent_workbench/ui/workbench/` (32 files) | 旧架构验证 UI | **PRESERVED** |
| `v6-agent` branch | 废弃的应用中心架构 | **ARCHIVED** |

旧架构：`UI → Controller → Agent Runtime → LLM`（应用中心）
新架构：`CENTRE Runtime → Interaction Boundary → Presentation Renderer → v6/ui → Qt`（Runtime-first, Presentation-agnostic）

---

## 8. Phase 2-C 预告（Contract Freeze）

Phase 2-C Presentation Architecture RFC 已冻结于 [.project/decisions/ADR-002-phase-2c-presentation-rfc.md](../../.project/decisions/ADR-002-phase-2c-presentation-rfc.md)。

核心变更：
1. **Interaction Protocol 独立包**：`protocols/interaction/`（`command.py` + `event.py` + `renderer.py`）
2. **InteractionCommand 独立化**：非聊天命令不再通过 `RuntimeRequest.action_id` 传递
3. **PresentationRuntime**：`PresentationPipeline` 从静态工具箱升级为生命周期服务
4. **Renderer Registry**：支持多 Renderer（Qt / Web / CLI / Mobile）并存

---

## 9. 版本历史

本文档进入 Frozen 状态后：

- 允许新增附录、说明、示例。
- 允许更新演进时间线。
- 禁止修改第 1-3 节的核心边界定义。
- 禁止修改四项禁止事项。
- 如需修改，必须走 Architecture Review，更新版本号，并同步更新 Frozen Zone 清单。

---

## 7. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v6.13-frozen | 2026-07-19 | 初始创建。从 v6.13-freeze-report rev3 提取核心边界定义、三项附录、四项禁止事项，升级为独立最高优先级边界文档。 |