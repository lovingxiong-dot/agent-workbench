# V6 路线图

## 产品定位

**Personal Agent Workbench / Agent IDE**

不是聊天机器人，而是一个可以不断安装能力、工具、Provider、Workflow 的 AI 工作台。

**核心原则**：Agent Workbench 是 V6 Runtime 的**官方产品化验证平台（Official Product Validation Platform）**。任何 Provider、Tool、Skill 只有能在 Workbench 中安装、运行、验证，才算完成。

**v6.10 目标**：打造一个今天能用的 **Autonomous Agent Workbench**。每一阶段回答：

> **Agent 今天比昨天多会了一件什么事情？**

## 演进路径

```text
Foundation Runtime      ← v6.9.6-foundation 已冻结
        ↓
Workbench UI Framework  ← v6.10.0：固定 IDE 骨架
        ↓
Presentation Layer      ← v6.10.0：Service → Presentation → UI
        ↓
Chat Workspace          ← v6.10.0：Agent 能聊天
        ↓
Skill Registry          ← v6.10.x：Agent 能安装能力
        ↓
Tool Runtime            ← v6.10.x：Agent 能执行工具
        ↓
Provider Framework      ← v6.10.x：Agent 能调用 LLM
        ↓
（未来再看）
```

## 时序原则

| 梯队 | 优先级 | 内容 | 版本 |
|---|---|---|---|
| 第一梯队 | ⭐⭐⭐⭐⭐ | Workbench UI Framework、Presentation Layer、Chat Workspace | v6.10.0 |
| 第二梯队 | ⭐⭐⭐⭐ | Skill Registry、Tool Runtime、Provider Framework | v6.10.x |
| 第三梯队 | ⭐⭐⭐ | Workflow、Memory / Knowledge | v6.11.x |
| 第四梯队 | ⭐⭐ | MCP、Browser、External Service、Marketplace、Gateway | 未来 |

## v6.10.0-alpha：Workbench UI Framework + Chat Workspace

目标：先固定 IDE 骨架，再往里面塞功能。不做聊天客户端，做 Agent IDE。

### Commit 1：Workbench UI Framework

- [ ] 固定 IDE 骨架：Workbench / Navigator / Workspace / Inspector / StatusBar / CommandBar
- [ ] Workspace 管理器：创建、切换、销毁 Workspace
- [ ] Workspace Registry：注册可用 Workspace 类型
- [ ] Workspace Router：根据 Navigator 选择切换 Workspace
- [ ] 所有 Workspace 初始为空实现，但布局、生命周期、事件全部固定

### Commit 2：Presentation Layer

- [ ] 建立 `Service → PresentationModel → UI` 翻译层
- [ ] `SessionPresentation`
- [ ] `ToolPresentation`
- [ ] `SkillPresentation`
- [ ] `ProviderPresentation`

### Commit 3：Chat Workspace

- [ ] 左侧会话列表
- [ ] 中间聊天区
- [ ] 输入区
- [ ] 消息通过 Runtime 链路跑通
- [ ] Agent 能聊天

## v6.10.x 后续：Skill / Tool / Provider

### Commit 4：Skill Registry

- [ ] `SkillDefinition` / `SkillContext` / `SkillRuntime` / `SkillRegistry`
- [ ] Skill 可注册、可发现
- [ ] 先不做具体 Skill 实现

### Commit 5：Tool Runtime

- [ ] Tool 可注册、可执行、可观测
- [ ] 基础工具：read_file / write_file / bash / python
- [ ] Tool 执行结果进入 RuntimeContext

### Commit 6：Provider Framework

- [ ] `ProviderDefinition` / `ProviderRegistry` / `ProviderConfig` / `ProviderSelector`
- [ ] 先支持一个 Provider（EchoProvider 或一个真实 LLM）
- [ ] Provider 调用结果进入 RuntimeContext

## v6.11.x 预告

- Workflow 基础串行流
- Memory 上下文管理
- Knowledge 知识库接入

## 现在不做的事

- 复杂 Workflow DAG
- Memory / Knowledge（放 v6.11.x）
- MCP / Browser / External Service / Marketplace
- Gateway / Distributed / Remote Runtime / Digital Identity
