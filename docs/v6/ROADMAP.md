# V6 路线图

## 产品定位

**Personal Agent Workbench / Agent IDE**

不是聊天机器人，而是一个可以不断安装能力、工具、Provider、Workflow 的 AI 工作台。

**核心原则**：Agent Workbench 是 V6 Runtime 的**官方产品化验证平台（Official Product Validation Platform）**。任何 Provider、Tool、Skill 只有能在 Workbench 中安装、运行、验证，才算完成。

**v6.10 目标**：打造一个今天能用的 **Autonomous Agent Workbench**。v6.10.0 已完成 Configuration-Driven Workbench Loop。

从 v6.11.x 起，项目重心从 **Runtime 演进** 转向 **Workbench 演进**。每一阶段回答：

> **Workbench 今天比昨天多支持一种什么类型的对象，而无需修改代码？**

## 演进路径

```text
Foundation Runtime          ← v6.9.6-foundation 已冻结
        ↓
Configuration-driven        ← v6.10.0：Provider/MCP/Skill/Workflow/Prompt/Memory
Workbench                       全部可通过 UI 注册，ConfigStore 驱动刷新
        ↓
Metadata-driven Workbench   ← v6.11.x：统一 Metadata 描述对象
        ↓
Schema-driven Workbench     ← v6.12.x：Schema 驱动 Dialog / Inspector / JSON Editor / Validator
        ↓
Plugin-driven Workbench     ← v6.13.x：零代码扩展
        ↓
Marketplace / Digital Identity / Gateway  ← 未来
```

阶段定义：

- **Metadata-driven**：所有对象都有统一的描述能力。Runtime 通过 `metadata()` 认识对象。
- **Schema-driven**：所有对象的配置都由 Schema 描述，Dialog / Inspector / Property Panel / JSON Editor / Import / Export / Validator 全部自动生成。
- **Plugin-driven**：放置一个 Plugin，Workbench 自动发现、读取 Metadata 与 Schema、生成 UI、注册 Runtime，完成零代码扩展。

## 时序原则

v6.11 起拆分为两条并行线：

- **A 线（架构线）**：Metadata → Schema → Resource → Plugin，确保平台可扩展。
- **B 线（产品线）**：单一真实 LLM 接入 → 对话体验打磨 → 真实任务执行验证，确保 Workbench 真正可用。

两条线互不阻塞。Commit 1（Metadata Contract 冻结）完成后，B 线立即启动。

| 梯队 | 优先级 | 内容 | 版本 |
|---|---|---|---|
| 第一梯队 | ⭐⭐⭐⭐⭐ | Workbench UI Framework、Configuration-Driven Loop | v6.10.0 ✅ |
| 第一梯队 | ⭐⭐⭐⭐⭐ | **A 线**：Metadata Contract、MetadataRegistry、MetadataAdapter | v6.11.x Commit 1 |
| 第一梯队 | ⭐⭐⭐⭐⭐ | **B 线**：单一真实 LLM 接入（OpenAIProvider）、Streaming 对话闭环 | v6.11.x Commit 2 |
| 第二梯队 | ⭐⭐⭐⭐⭐ | **B 线**：对话体验打磨（Cancel / Retry / Token 统计 / Context 管理 / UI 刷新） | v6.11.x |
| 第二梯队 | ⭐⭐⭐⭐ | **A 线**：Schema Foundation：Schema Model / Registry / Validator / Auto Dialog / Auto Inspector | v6.12.x |
| 第三梯队 | ⭐⭐⭐ | **A 线**：Runtime Executors：ProviderRuntime / ToolRuntime / SkillRuntime | v6.13.x 之前 |
| 第四梯队 | ⭐⭐⭐ | **B 线**：真实 Provider 扩展：Claude / Gemini / Kimi / Qwen / DeepSeek | 单一 LLM 跑通后 |
| 第五梯队 | ⭐⭐ | **A 线**：Resource Layer：System / Python Env / IDE / CLI / Agent CLI | v6.12.x 后 |
| 第六梯队 | ⭐⭐ | Workflow 体验闭环、Memory / Knowledge、MCP Client、Browser、Marketplace、Gateway | 更晚 |

## v6.10.0-alpha：Configuration-Driven Workbench Loop ✅

目标：打通完整配置闭环，让 Provider / MCP / Skill / Workflow / Prompt / Memory 全部可通过 Workbench UI 注册。

### Commit 1：Workbench UI Framework ✅

- [x] 固定 IDE 骨架：Workbench / Navigator / Workspace / Inspector / StatusBar / CommandBar
- [x] Workspace 管理器：创建、切换、销毁 Workspace
- [x] Workspace Registry：注册可用 Workspace 类型
- [x] Workspace Router：根据 Navigator 选择切换 Workspace
- [x] 所有 Workspace 初始为空实现，但布局、生命周期、事件全部固定

### Commit 2：Configuration-Driven Loop ✅

- [x] Provider / MCP / Skill / Workflow / Prompt / Memory 可通过 UI 注册
- [x] ConfigStore 持久化并发出通用 `changed(path, value)` 信号
- [x] Navigator / StatusBar / Inspector 自动刷新

## v6.11.x：Metadata-driven Workbench + 真实 LLM 产品验证

### A 线 Commit 1：Metadata Contract & Base Model

- [ ] 冻结 `agent_workbench/metadata/` 目录：`types.py`, `errors.py`, `model.py`, `registry.py`, `adapter.py`。
- [ ] 定义 `MetadataDefinition`、`MetadataProperty`、`MetadataAction`、`MetadataStatistics`。
- [ ] 实现 `MetadataRegistry`：`register()` / `get()` / `all()`。
- [ ] 实现 `MetadataAdapter` 骨架：`adapt(MetadataDefinition) -> ModulePresentation`。
- [ ] 更新 `BaseRuntimeModule.metadata()` 返回 `MetadataDefinition`。
- [ ] 非 GUI 测试覆盖。

### A 线 Commit 2：MetadataAdapter & PresentationModel

- [ ] `MetadataDefinition → ModulePresentation`
- [ ] UI 只依赖 PresentationModel

### A 线 Commit 3-5：Runtime Module Metadata 补齐 + Navigator / Inspector / StatusBar 去硬编码

- [ ] Provider / MCP / Skill / Workflow / Prompt / Memory 返回统一 Metadata
- [ ] Navigator / Inspector / StatusBar 通过 PresentationModel 渲染

### B 线 Commit 1：单一真实 LLM 接入

- [ ] 打通 `OpenAIProvider`：从 Workbench Provider 配置 → ConfigStore → ProviderRegistry → LLM 调用。
- [ ] 实现非流式对话：`User Input → Manager → Capability → Provider → LLM → Response → UI`。
- [ ] 非 GUI 集成测试覆盖一条完整对话链路。

### B 线 Commit 2：Streaming 与对话体验

- [ ] `OpenAIProvider` 支持 Streaming 输出。
- [ ] Workbench Chat Workspace 实时显示 Streaming Token。
- [ ] Trace 记录完整请求/响应/Token 统计。
- [ ] StatusBar 显示当前 Provider 与 Token 消耗。

### B 线 Commit 3：对话鲁棒性

- [ ] Cancel 中断、Retry 重试、Timeout 超时处理。
- [ ] Provider 切换时的 Context 保持与清理。
- [ ] 错误状态在 UI 中可视化。

## v6.12.x+ 预告：Resource Layer

当 Schema-driven UI 完成后，Workbench 将引入 **Resource Layer**，把系统环境、Python 虚拟环境、IDE、CLI、Agent CLI 建模为独立于 Capability 的配置对象：

```text
Digital Identity（AI）
        │
        ▼
Capability（我会什么）
        │
        ▼
Resource（我可以使用什么）
        │
        ▼
Provider（调用哪个模型）
        │
        ▼
Target（在哪个环境执行）
```

详见 [`resource-layer-spec.md`](./resource-layer-spec.md)。

## 现在不做的事

- Schema-driven UI（v6.12.x 再做）
- Runtime Executors（ProviderRuntime / ToolRuntime / SkillRuntime，Schema 之后）
- Resource Layer 实现（设计已完成，见 `resource-layer-spec.md`，Schema 之后落地）
- 新增 Runtime 类型：Knowledge / Persona / Browser / Plugin / Gateway / Digital Identity
- 真实 Provider 接入：Claude / Gemini / OpenAI / Kimi / Qwen / DeepSeek
- 复杂 Workflow DAG
