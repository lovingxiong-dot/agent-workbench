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

## 6. 变更控制

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