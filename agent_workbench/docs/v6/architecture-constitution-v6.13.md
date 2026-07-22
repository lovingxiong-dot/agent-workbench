# Workbench OS — Architecture Constitution v6.13 Revision

> 版本：v6.13-frozen
> 状态：Frozen — 所有后续开发必须遵守
> 生效日期：2026-07-21
> 适用范围：v6.14 ~ v7.x 全部开发
> 优先级：最高（高于 CHANGELOG、高于 Spec、高于 Task List）
> 前置文档：`docs/v6/architecture-boundaries.md`（边界定义，本 Constitution 的引用基础）

---

## Preamble

本 Constitution 是 Workbench OS 的架构宪法。它定义了五个不可违反的核心原则，所有代码、设计、重构和功能扩展都必须遵守。

违反本 Constitution 的代码不得合并。违反本 Constitution 的架构决策视为无效。

---

## Principle 1: Workbench OS Identity

> **Workbench OS 是一个 AI Agent 操作系统。Desktop UI（PySide6）是第一个参考 Shell 实现，不是产品本质。**

### 1.1 架构层级

```
Workbench OS
│
├── Runtime Kernel（冻结）        ← 不可因 UI 需求变更
├── Core Foundation（冻结）       ← Agent/Capability/Event/Registry/Lifecycle
├── Presentation Layer（新增）     ← Protocol + ViewModel + Adapter
├── UI Shell（纯UI，可替换）       ← shells/qt/（当前）/ shells/web/ / shells/mobile/ / shells/cli/
└── Adapter Ecosystem             ← Runtime → UI 的翻译层
```

### 1.2 Workbench OS IS

- 一个可替换 UI Shell 的 Agent 操作系统
- Runtime Kernel 之上的 Presentation + Entry Layer
- Agent / Conversation / Capability / Memory / Tool / Artifact / Context 的统一编排平台
- 所有新能力（Provider、Skill、MCP、Workflow）的集成验证平台与产品化门槛

### 1.3 Workbench OS IS NOT

- 不是 IDE（不是代码编辑器、不是项目管理器）
- 不是 Desktop App（Desktop 只是一个 Shell 实现，不是产品本质）
- 不是 Demo 或原型
- 不是 "Agent Workbench GUI"（这是 v5 的历史定位，v6 已废弃）

### 1.4 命名约束

| 废弃名称 | 正确名称 | 原因 |
|---------|---------|------|
| Agent Workbench | Workbench OS | v5→v6 架构跃迁 |
| v6/ui | shells/qt | v6/ui 是历史目录，Qt 是第一个 Shell 实现 |
| Workbench UI | Workbench OS Shell | UI 是 Shell，不是本体 |
| Agent Workbench GUI | Workbench OS Desktop Shell | Desktop 只是入口 |

---

## Principle 2: Runtime Kernel Freeze

> **Runtime Kernel 已冻结。任何 UI 需求不得导致 Runtime 变更。**

### 2.1 冻结清单

以下模块已冻结，不可因 UI 需求新增、修改或删除：

| 模块 | 路径 | 冻结日期 |
|------|------|---------|
| `AgentRuntime` | `agent_workbench/runtime/agent_runtime.py` | v6.9.6-foundation |
| `ModuleRegistry` | `agent_workbench/runtime/module_registry.py` | v6.9.6-foundation |
| `BaseRuntimeModule` | `agent_workbench/runtime/modules/base.py` | v6.9.6-foundation |
| `ConfigStore` | `agent_workbench/runtime/config_store.py` | v6.9.6-foundation |
| `CapabilityRouter` | `agent_workbench/runtime/capability_router.py` | v6.9.6-foundation |
| `CapabilityRegistry` | `agent_workbench/runtime/capability/` | v6.9.6-foundation |
| `InteractionEvent` | `agent_workbench/runtime/interaction/event.py` | v6.9.5-alpha |
| `InteractionLayer` | `agent_workbench/runtime/interaction/layer.py` | v6.9.5-alpha |
| `DecisionManager` | `agent_workbench/runtime/manager/decision_manager.py` | v6.9.4-alpha |
| `ProviderRegistry` | `agent_workbench/runtime/provider_registry.py` | v6.9.6-foundation |
| `MetadataDefinition` | `agent_workbench/metadata/model.py` | v6.11.0-beta.4 |
| `MetadataAdapter` | `agent_workbench/metadata/adapter.py` | v6.11.0-beta.4 |

14 个 RuntimeModule 全部冻结：

| 模块 | namespace | 冻结 |
|------|-----------|------|
| `RuntimeModule` | `runtime` | Frozen |
| `AgentModule` | `agent` | Frozen |
| `ModelModule` | `model` | Frozen |
| `PromptModule` | `prompt` | Frozen |
| `ToolModule` | `tool` | Frozen |
| `SkillModule` | `skill` | Frozen |
| `McpModule` | `mcp` | Frozen |
| `MemoryModule` | `memory` | Frozen |
| `SessionModule` | `session` | Frozen |
| `ProfileModule` | `profile` | Frozen |
| `TraceModule` | `trace` | Frozen |
| `WorkflowModule` | `workflow` | Frozen |
| `StrategyModule` | `strategy` | Frozen |
| `ConfigModule` | `config` | Frozen |

### 2.2 冻结规则

1. **不允许新增 Runtime-level 模块。** 所有新能力通过 Capability Runtime Contract 接入。
2. **不允许 RuntimeModule 新增 UI 相关方法。** metadata() 是唯一对外暴露的接口。
3. **不允许为 UI 需求修改 Runtime 内部逻辑。** 包括但不限于：新增信号、修改数据结构、添加 UI 回调。

### 2.3 正确 vs 错误

```
错误：UI需要显示xxx → Runtime新增xxx Module
正确：Runtime.metadata() → Adapter → ViewModel → UI Shell
```

### 2.4 依赖方向（不可逆）

```
Agent → Skill → Capability → Engine → Provider → Tool
```

- Capability 不知道 Skill 的存在
- Engine 不知道 Agent 的存在
- Runtime 不知道 UI 的存在
- UI Shell 不知道 Runtime 的存在（只消费 Presentation Contract）

---

## Principle 3: Presentation Contract

> **Presentation Layer 是 Runtime 与 UI Shell 之间的唯一翻译层。它包含三层：Protocol（能力契约）、ViewModel（数据结构）、Adapter（翻译逻辑）。**

### 3.1 三层结构

```
Runtime
   │
   │ metadata() / InteractionEvent
   ▼
Presentation Protocol     ← 能力契约（Protocol，定义"能做什么"）
   │
   ▼
Presentation ViewModel    ← 数据结构（dataclass，承载"是什么"）
   │
   ▼
Presentation Adapter      ← 翻译逻辑（Metadata → ViewModel）
   │
   ▼
UI Shell                  ← 消费 ViewModel，发出信号
```

### 3.2 目录结构

```
agent_workbench/presentation/
├── protocols/              # 能力契约（Protocol）
│   ├── agent_provider.py
│   ├── session_provider.py
│   ├── capability_provider.py
│   ├── message_provider.py
│   └── status_provider.py
├── view_models/            # 数据结构（dataclass）
│   ├── agent.py
│   ├── conversation.py
│   ├── capability.py
│   ├── session.py
│   ├── message.py
│   ├── memory.py
│   ├── settings.py
│   └── tab.py
├── adapters/               # 翻译逻辑
│   ├── agent_adapter.py
│   ├── conversation_adapter.py
│   ├── capability_adapter.py
│   ├── session_adapter.py
│   ├── message_adapter.py
│   ├── memory_adapter.py
│   └── settings_adapter.py
└── events/                 # UI 事件定义
    └── ui_events.py
```

### 3.3 Protocol 示例

```python
# presentation/protocols/agent_provider.py
from typing import Protocol, runtime_checkable
from agent_workbench.presentation.view_models.agent import AgentViewModel

@runtime_checkable
class AgentProviderProtocol(Protocol):
    """Agent 能力契约。UI Shell 消费此 Protocol，不直接访问 Runtime。"""
    def list_agents(self) -> list[AgentViewModel]: ...
    def get_agent(self, agent_id: str) -> AgentViewModel | None: ...
    def activate_agent(self, agent_id: str) -> None: ...
    def update_agent_config(self, agent_id: str, config: dict) -> None: ...
```

### 3.4 关键约束

1. **Protocol 定义能力，ViewModel 承载数据。** 两者不可合并。
2. **UI Shell 只消费 Protocol + ViewModel。** 不 import Runtime 模块。
3. **Adapter 是唯一翻译点。** Runtime → ViewModel 的转换只在 Adapter 中发生。
4. **Presentation Layer 不知道 UI 的实现。** 同一个 ViewModel 可被 Qt / Web / CLI 三种 Shell 消费。

---

## Principle 4: UI Shell Boundary

> **UI Shell 是 Workbench OS 的视觉外壳。它不包含任何业务逻辑，不导入任何 Runtime 模块，只消费 Presentation Contract。**

### 4.1 UI Shell 职责

| 可以 | 不可以 |
|------|--------|
| 渲染 ViewModel 数据 | 导入 Runtime 模块 |
| 发出用户交互信号 | 直接调用 Runtime API |
| 管理自己的布局和样式 | 包含业务逻辑 |
| 消费 Presentation Protocol | 直接构造 RuntimeDecision |

### 4.2 Shell 目录结构

```
workbench_os/
├── runtime/            ← Runtime Kernel（冻结）
├── core/               ← Core Foundation（冻结）
├── presentation/       ← Presentation Layer
└── shells/             ← UI Shell 实现
    ├── qt/             ← 当前 Qt Shell（从 v6/ui/ 迁移）
    ├── web/            ← 未来 Web Shell
    ├── mobile/         ← 未来 Mobile Shell
    └── cli/            ← 未来 CLI Shell
```

### 4.3 视觉源

`origin/ui-template:experiments/ui_template.py`（2823行）是 UI Shell 的**视觉源**。

它不是 Runtime 的一部分，不是架构核心，而是**第一个 Qt Shell 实现的视觉设计参考**。

所有 Qt Shell 实现必须保持与 ui-template 的视觉一致性：
- pixel（像素精度）
- font（字体族、大小、权重）
- spacing（间距、边距、内边距）
- color（颜色调色板、透明度）
- interaction（hover、click、focus 行为）

### 4.4 Qt Shell 实现约束

1. **视觉不动**：不修改 ui-template 定义的任何视觉属性
2. **只加数据注入**：只新增 `set_xxx(ViewModel)` / `load_xxx(ViewModel)` 方法
3. **不导入 Runtime**：不在 Shell 代码中 import 任何 Runtime 模块
4. **信号向上**：用户交互通过 Qt Signal 向上传递，由 Workbench Shell 组装层转发

---

## Principle 5: Configuration-Driven Workbench

> **Workbench OS 是配置驱动的，不是代码驱动的。所有扩展对象（Provider、Model、MCP、Skill、Tool、Workflow、Prompt、Memory）都应支持通过 UI 注册和配置，不需要修改源码。**

### 5.1 正确流程

```
UI → ConfigManager → Registry Reload → Capability Update → Agent Ready
```

### 5.2 反模式（禁止）

```
UI → 修改代码 → 重新编译 → 重新启动
```

### 5.3 具体示例

| 操作 | 正确方式 | 错误方式 |
|------|---------|---------|
| 新增 OpenAI 兼容模型 | Settings → AI Models → + | 修改 Python 代码新增 OpenAI 类 |
| 接入 MCP Server | Settings → MCP → + | 修改 Runtime 代码新增 MCP 连接 |
| 新增 Python 技能 | Skills → +，选择脚本 | 修改 SkillModule 代码 |
| 切换 Provider | ControlBar 下拉选择 | 修改 config.yaml 后重启 |
| 禁用某个工具 | Settings → Tools → 开关 | 注释掉代码 |

### 5.4 配置链路

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

### 5.5 关键约束

1. **任何 Provider**，只有能安装到 Workbench 并跑通，才算完成。
2. **任何 Tool**，只有能在 Workbench 中注册、执行、观测，才算完成。
3. **任何 Skill**，只有能在 Workbench 中安装、发现、调用，才算完成。
4. **任何 Workflow**，只有能在 Workbench 中编排、运行、调试，才算完成。
5. **任何 Memory / Knowledge / Agent Identity**，只有能在 Workbench 中验证体验，才算完成。

---

## 6. Architecture Decision Records

### ADR-001: Presentation Layer 升级（v6.13）

**决策**：Presentation Layer 从 "ViewModel-only" 升级为 "Protocol + ViewModel + Adapter" 三层结构。

**原因**：ViewModel 是纯数据，无法定义"如何获取、如何刷新、如何响应事件"。Protocol 定义能力契约，ViewModel 承载数据，两者分离。

**影响**：
- 新增 `presentation/protocols/` 目录
- 现有 ViewModel 不变
- 新增 Protocol 作为 UI Shell 的消费接口

### ADR-002: UI Shell 目录从 v6/ui 迁移到 shells/qt（v6.13）

**决策**：`v6/ui/` 是历史目录，未来应迁移到 `shells/qt/`。当前阶段保持兼容，过渡期完成后迁移。

**原因**：`v6/ui` 暗示 "v6 版本的 UI"，但 Workbench OS 的未来 Shell 不止 Qt 一种。`shells/qt` 明确表达"Qt 是第一个 Shell 实现"。

**影响**：当前不立即迁移，在 Phase 2（Pure UI Migration）中渐进迁移。

### ADR-003: Configuration-Driven 原则正式写入 Constitution（v6.13）

**决策**：Configuration-Driven 从"最佳实践"升级为"架构宪法原则"。

**原因**：Workbench OS 的核心差异化在于"不需要改代码就能扩展"。这是区别于普通 AI 客户端的关键特征。

**影响**：所有新增功能必须先通过 ConfigStore 注册，再通过 Registry 发现，最后通过 UI 呈现。

---

## 7. 违规判定

以下行为视为违反本 Constitution：

1. 在 UI Shell 代码中 import Runtime 模块
2. 为 UI 需求修改 RuntimeModule 内部逻辑
3. 在 ViewModel 中定义业务逻辑（ViewModel 必须是纯数据 dataclass）
4. 绕过 Presentation Layer 直接连接 Runtime 与 UI
5. 新增功能需要修改源码（而非通过 ConfigStore 注册）
6. 修改 ui-template 定义的视觉属性（颜色、字体、像素、间距、圆角）

---

## 8. 修正历史

| 版本 | 日期 | 修正内容 |
|------|------|---------|
| v6.9.6-foundation | 2026-07-09 | Runtime Kernel Freeze |
| v6.11.0-beta.4 | 2026-07-15 | Metadata Contract 长期冻结 |
| v6.13-frozen | 2026-07-21 | Architecture Constitution 正式发布：五个核心原则 + 三个 ADR |

---

> 本 Constitution 是 Workbench OS 的最高架构文档。任何与本 Constitution 冲突的 Spec、Task、PR 均视为无效。修改本 Constitution 必须通过 Architecture Review。