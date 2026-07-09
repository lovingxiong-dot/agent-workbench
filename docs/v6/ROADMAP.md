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

| 梯队 | 优先级 | 内容 | 版本 |
|---|---|---|---|
| 第一梯队 | ⭐⭐⭐⭐⭐ | Workbench UI Framework、Configuration-Driven Loop | v6.10.0 ✅ |
| 第一梯队 | ⭐⭐⭐⭐⭐ | Metadata Contract、MetadataAdapter、UI 去硬编码 | v6.11.x |
| 第二梯队 | ⭐⭐⭐⭐ | Schema Foundation：Schema Model / Registry / Validator / Auto Dialog / Auto Inspector | v6.12.x |
| 第三梯队 | ⭐⭐⭐ | Runtime Executors：ProviderRuntime / ToolRuntime / SkillRuntime | v6.13.x 之前 |
| 第四梯队 | ⭐⭐⭐ | Real Provider Adapters：Claude / Gemini / OpenAI / Kimi / Qwen / DeepSeek | UI 成熟后 |
| 第五梯队 | ⭐⭐ | Resource Layer：System / Python Env / IDE / CLI / Agent CLI | v6.12.x 后 |
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

## v6.11.x：Metadata-driven Workbench

### Commit 3：Metadata Contract & Base Model

- [ ] 定义 `ModuleMetadata`、`PropertyMetadata`、`StatisticMetadata`、`ActionMetadata`
- [ ] 更新 `BaseRuntimeModule.metadata()` 返回严格类型化的 Metadata
- [ ] 非 GUI 测试覆盖

### Commit 4：MetadataAdapter & PresentationModel

- [ ] `ModuleMetadata → ModulePresentation`
- [ ] UI 只依赖 PresentationModel

### Commit 5-7：Runtime Module Metadata 补齐 + Navigator / Inspector / StatusBar 去硬编码

- [ ] Provider / MCP / Skill / Workflow / Prompt / Memory 返回统一 Metadata
- [ ] Navigator / Inspector / StatusBar 通过 PresentationModel 渲染

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
