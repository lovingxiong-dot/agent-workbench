# V6 路线图

## 产品定位

**Personal Agent Workbench / Agent IDE**

不是聊天机器人，而是一个可以不断安装能力、工具、Provider、Workflow 的 AI 工作台。

**核心原则**：Agent Workbench 是 V6 Runtime 的**官方产品化验证平台（Official Product Validation Platform）**。任何 Provider、Tool、Skill、Workflow 只有能在 Workbench 中安装、运行、验证，才算完成。

## 演进路径

```text
Foundation Runtime      ← v6.9.6-foundation 已冻结
        ↓
GUI Platform            ← v6.10.0 当前阶段
        ↓
Provider Framework      ← 先打通框架，哪怕只有一个 Provider
        ↓
Tool Runtime            ← Python / PowerShell / 系统工具等
        ↓
Skill Framework         ← Contract 优先，先不做具体 Skill
        ↓
Workflow                ← 基础串行任务流 A → B → C
        ↓
Memory / Knowledge      ← 基础抽象完成
        ↓
Agent Identity          ← 数字身份、Identity Database
        ↓
   （未来）
    Gateway             ← 最后才做，管理多个成熟 Agent
```

## 时序原则

| 梯队 | 优先级 | 内容 | 版本 |
|---|---|---|---|
| 第一梯队 | ⭐⭐⭐⭐⭐ | GUI Platform、Provider Framework、Tool Runtime、Skill Framework | v6.10.x |
| 第二梯队 | ⭐⭐⭐⭐ | Workflow、Memory / Knowledge | v6.11.x |
| 第三梯队 | ⭐⭐⭐ | MCP、Browser、External Service、Plugin Marketplace | v6.12.x |
| 第四梯队 | ⭐⭐ | Gateway、Distributed、Remote Runtime、Digital Identity | 未来 |

## v6.10.x 目标：Workbench Product

不是先做 OpenAI / Gemini / Claude，而是先把链路打通：

```text
GUI → Chat → Task → Capability → Tool → Provider
```

### 当前阶段：v6.10.0-alpha GUI Platform

- [ ] **GUI Platform**：Workbench UI 完整跑通、稳定、可交互
  - [ ] 主窗口可启动且不崩溃
  - [ ] 左侧面板显示会话列表
  - [ ] 中间聊天区可显示消息
  - [ ] 输入区可发送消息
  - [ ] 右侧工具/终端/文件面板可切换
  - [ ] 主题、模式、模型选择可持久化
- [ ] **Provider Framework**：打通 Provider Contract
  - [ ] 定义 `ProviderDefinition` / `ProviderContext` / `ProviderRegistry`
  - [ ] `ModelProvider` 接入 Registry
  - [ ] 配置中可指定默认 Provider
  - [ ] 至少一个 Provider 可跑通（EchoProvider 或真实 Provider）
- [ ] **Tool Runtime**：Tool 可注册、可执行、可观测
  - [ ] `ToolRegistry` 持久化配置
  - [ ] Tool 执行结果进入 `RuntimeContext`
  - [ ] 基础工具：read_file / write_file / bash / python
- [ ] **Skill Framework**：定义 Skill Contract
  - [ ] `SkillDefinition` / `SkillContext` / `SkillRuntime` / `SkillRegistry`
  - [ ] Skill 可注册、可发现
  - [ ] 先不做具体 Skill 实现

### v6.11.x 预告：Workflow / Memory / Knowledge

让 Agent 真正开始工作。

- Workflow 基础串行流
- Memory 上下文管理
- Knowledge 知识库接入

### v6.12.x 预告：MCP / Browser / External Service / Marketplace

扩展与外部世界的连接。

### 未来：Agent Identity / Gateway / Distributed / Remote Runtime

等 Single Agent Workbench 成熟后，再引入多 Agent 管理层。

---

## 现在不做的事

- **Digital Identity / Agent Identity**：只预留接口，不实现 Identity Database。
- **多 Provider 智能切换**：先支持一个 Provider，框架打通后再扩展。
- **复杂 Workflow DAG**：只做基础串行任务流。
- **MCP / Browser / External Service / Marketplace**：第三梯队，v6.12.x 再启动。
- **Gateway / Distributed / Remote Runtime**：第四梯队，未来再做。
