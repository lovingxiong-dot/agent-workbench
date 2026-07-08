# V6 路线图

## 产品定位

**Personal Agent Workbench / Agent IDE**

不是一个聊天机器人，而是一个可以不断安装能力、工具、Provider、Workflow 的 AI 工作台。

## 演进路径

```text
Foundation Runtime      ← v6.9.6-foundation 已冻结
        ↓
Agent Workbench         ← v6.10.x 当前阶段
        ↓
Provider Ecosystem
        ↓
Tool Ecosystem
        ↓
Skill Ecosystem
        ↓
Workflow Ecosystem
        ↓
Knowledge & Memory
        ↓
Digital Identity
        ↓
   （未来）
    Gateway             ← 最后才做
```

## 优先级梯队

| 梯队 | 优先级 | 内容 | 预计版本 |
|---|---|---|---|
| 第一梯队 | ⭐⭐⭐⭐⭐ | GUI、Provider、Tool Runtime、Skill Registry | v6.10.x |
| 第二梯队 | ⭐⭐⭐⭐ | Workflow、Memory、Knowledge | v6.11.x |
| 第三梯队 | ⭐⭐⭐ | MCP、Browser、External Service、Plugin Marketplace | v6.12.x |
| 第四梯队 | ⭐⭐ | Gateway、Distributed、Remote Runtime | 未来 |

## 当前阶段：v6.10.0-alpha Agent Workbench Ecosystem Bootstrap

### 任务清单
- [ ] GUI：Workbench UI 完整跑通、稳定、可交互
- [ ] Provider：接入第一个真实 LLM Provider
- [ ] Tool Runtime：Tool 可注册、可执行、可观测
- [ ] Skill Registry：Skill 能力包的注册、发现、加载机制

### 下阶段预告：v6.11.x
Workflow / Memory / Knowledge 让 Agent 真正开始工作。
