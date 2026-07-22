# V6 路线图

> **当前版本**: v6.14.0-alpha — Presentation Boundary Freeze
> **v6/ui 状态**: Frozen Foundation，详见 [v6/UI_FOUNDATION.md](../../v6/UI_FOUNDATION.md)

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
Metadata-driven Workbench   ← v6.11.0-alpha.2：Metadata Cross-layer Contract 已冻结
        ↓
真实 LLM 对话闭环         ← v6.11.0-beta.x：B 线优先，让 Workbench 真正可用
        ↓
Schema-driven Workbench     ← v6.12.x：Schema 驱动 Dialog / Inspector / JSON Editor / Validator
        ↓
Presentation Boundary Freeze ← v6.14.0-alpha Phase 2-B.1：v6/ui Frozen Foundation + Renderer Layer
        ↓
Presentation Runtime         ← v6.14.x Phase 2-C：InteractionCommand 独立化、PresentationPipeline 生命周期化
        ↓
Plugin-driven Workbench     ← v6.13.x：零代码扩展
        ↓
Marketplace / Digital Identity / Gateway  ← 未来
```

阶段定义：

- **Metadata-driven**：所有对象都有统一的描述能力。Runtime 通过 `metadata()` 认识对象。
- **真实 LLM 对话闭环**：Workbench 第一条真实链路跑通，普通聊天也能调用 LLM，建立产品价值。
- **Schema-driven**：所有对象的配置都由 Schema 描述，Dialog / Inspector / Property Panel / JSON Editor / Import / Export / Validator 全部自动生成。
- **Plugin-driven**：放置一个 Plugin，Workbench 自动发现、读取 Metadata 与 Schema、生成 UI、注册 Runtime，完成零代码扩展。

## 时序原则：B 线优先，A 线冻结式推进

v6.11 起拆分为两条并行线：

- **B 线（产品线）**：单一真实 LLM 接入 → 对话体验打磨 → 真实任务执行验证，确保 Workbench 真正可用。本阶段**优先**。
- **A 线（架构线）**：Metadata → Schema → Resource → Plugin，确保平台可扩展。Commit 1（Metadata Contract）已冻结，后续 A 线任务**冻结式推进**，不阻塞 B 线。

| 梯队 | 优先级 | 内容 | 版本 |
|---|---|---|---|
| 第一梯队 | ⭐⭐⭐⭐⭐ | Workbench UI Framework、Configuration-Driven Loop | v6.10.0 ✅ |
| 第一梯队 | ⭐⭐⭐⭐⭐ | **A 线 Commit 1**：Metadata Contract、MetadataRegistry、MetadataAdapter | v6.11.0-alpha.2 ✅（已冻结） |
| 第一梯队 | ⭐⭐⭐⭐⭐ | **B 线 Commit 1**：单一真实 LLM 接入（OpenAIProvider）、非流式对话闭环 | v6.11.0-beta.1 |
| 第二梯队 | ⭐⭐⭐⭐⭐ | **B 线 Commit 2**：Streaming 对话体验（实时 Token / Trace / StatusBar） | v6.11.0-beta.2 |
| 第二梯队 | ⭐⭐⭐⭐⭐ | **B 线 Commit 3**：对话鲁棒性（Cancel / Retry / Timeout / Provider 切换） | v6.11.x |
| 第三梯队 | ⭐⭐⭐⭐ | **A 线 Commit 2+**：MetadataAdapter、Runtime Module Metadata、Workbench UI 去硬编码 | v6.11.x / v6.12.x（冻结推进） |
| 第四梯队 | ⭐⭐⭐⭐ | **A 线**：Schema Foundation：Schema Model / Registry / Validator / Auto Dialog / Auto Inspector | v6.12.x |
| 第五梯队 | ⭐⭐⭐ | **A 线**：Runtime Executors：ProviderRuntime / ToolRuntime / SkillRuntime | v6.13.x 之前 |
| 第六梯队 | ⭐⭐⭐ | **B 线**：真实 Provider 扩展：Claude / Gemini / Kimi / Qwen / DeepSeek | 单一 LLM 跑通后 |
| 第七梯队 | ⭐⭐ | **A 线**：Resource Layer：System / Python Env / IDE / CLI / Agent CLI | v6.12.x 后 |
| 第八梯队 | ⭐⭐ | Workflow 体验闭环、Memory / Knowledge、MCP Client、Browser、Marketplace、Gateway | 更晚 |

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

## v6.11.x：真实 LLM 对话闭环（B 线优先）

### B 线 Commit 1：单一真实 LLM 接入（v6.11.0-beta.1）

目标：打通第一条真实链路，让 Workbench 从架构进入产品阶段。

```text
User
   ↓
Workbench UI
   ↓
Manager AI
   ↓
Capability
   ↓
OpenAI Provider
   ↓
LLM
   ↓
Response
   ↓
UI
```

- [x] 普通聊天请求由 Manager AI 路由到 `chat` Capability，不再跳过 Runtime。
- [x] `OpenAIProvider` 从 ConfigStore 读取 `api_key`、`base_url`、`model` 并调用真实 LLM。
- [x] `ModelModule` 根据 `model.providers` 配置注册 OpenAI Provider，支持切换 active provider。
- [x] 非 GUI 集成测试覆盖一条完整对话链路（使用 mock HTTP 验证请求/响应格式，api_key 不回传）。

### B 线 Commit 2：Streaming 与对话体验（v6.11.0-beta.2）

- [ ] `OpenAIProvider` 支持 Streaming 输出。
- [ ] Workbench Chat Workspace 实时显示 Streaming Token。
- [ ] Trace 记录完整请求/响应/Token 统计。
- [ ] StatusBar 显示当前 Provider 与 Token 消耗。

### B 线 Commit 3：对话鲁棒性

- [ ] Cancel 中断、Retry 重试、Timeout 超时处理。
- [ ] Provider 切换时的 Context 保持与清理。
- [ ] 错误状态在 UI 中可视化。

## A 线：Metadata / Schema / Resource（冻结式推进）

A 线负责基础设施，已冻结部分不再变更；未完成任务仅在 B 线不阻塞的前提下继续。

### A 线 Commit 1：Metadata Contract & Base Model ✅（已冻结）

- [x] 冻结 `agent_workbench/metadata/` 目录：`types.py`, `errors.py`, `model.py`, `registry.py`, `adapter.py`。
- [x] 定义 `MetadataDefinition`、`MetadataProperty`、`MetadataAction`、`MetadataStatistics`。
- [x] 实现 `MetadataRegistry`：`register()` / `get()` / `all()`。
- [x] 实现 `MetadataAdapter` 骨架：`adapt(MetadataDefinition) -> ModulePresentation`。
- [x] 更新 `BaseRuntimeModule.metadata()` 返回 `MetadataDefinition`。
- [x] 非 GUI 测试覆盖。

### A 线 Commit 2+：MetadataAdapter & PresentationModel & UI 去硬编码

- [ ] `MetadataDefinition → ModulePresentation`。
- [ ] Navigator / Inspector / StatusBar 全部通过 `PresentationModel` 渲染。
- [ ] 新增 Runtime Module 类型后，Workbench UI 自动展示，无需修改 Navigator/Inspector/StatusBar。

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
- 多 Provider 接入：Claude / Gemini / Kimi / Qwen / DeepSeek（OpenAI 跑通后再接）
- 复杂 Workflow DAG
