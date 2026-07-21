# Handoff Snapshot — Agent Workbench OS

> **会话 ID**: `6a5d8dfaa1d6da7f1e94d5f9`
> **前一会话**: `6a5c85036d28e0576cc4cd51`
> **移交类型**: SAVE
> **移交日期**: 2026-07-21
> **移交 Agent**: DeepSeek-V4-Pro @ Trae IDE
> **当前进度**: Agent Workbench OS — Constitution Sync + Presentation Contract Freeze

---

## 1. 项目状态

| 项目 | 值 |
|------|-----|
| 项目名称 | agent-workbench |
| 当前版本 | v6.14.0-alpha |
| 阶段 | Agent Workbench OS — 宪法同步完成，Presentation Contract 已冻结 |
| Runtime 基线 | v6.9.6-foundation（Frozen Zone 19 文件，禁止修改） |
| 活跃分支 | `v6-agent` |
| 末次提交 | `cc8d473` — feat(v6.14): Delivery — ControlBar |
| 工作区状态 | **117 文件 dirty**（含大量 _archive/ 迁移 + presentation/ 新建 + BLUEPRINT 重写） |

---

## 2. 本会话完成的核心工作

### 2.1 P0：PROJECT_BLUEPRINT.md 宪法同步

**从 "Agent IDE" 叙事升级为 "Agent Workbench OS" 叙事。**

| 位置 | 修正前 | 修正后 |
|------|--------|--------|
| 定位标题 | "Agent Workbench 定位" | "Agent Workbench OS 定位（v6.14+）" |
| 描述 | "Personal Agent Workbench / Agent IDE" | "AI Agent 操作系统，不是 IDE" |
| 架构第五条 | MainWindow→WorkbenchHost→Workbench（Navigator/Inspector） | Entry→UI Shell→Presentation→Runtime |
| 目录结构 | 无 presentation/ | 新增 presentation/view_models/ + adapters/ |

新增内容：
- **IS/IS NOT 声明**（不是 IDE、不是 Desktop App、不是 Demo）
- **核心对象模型表**（Agent/Conversation/Capability/Tool/Memory/Artifact/Context）
- **架构层级图**（Entry→Presentation→Runtime OS→Frozen Core）

### 2.2 P0：Presentation Layer 创建

新建 `agent_workbench/presentation/` 层，作为 Runtime 与 UI Shell 之间的唯一翻译层。

```
agent_workbench/presentation/
├── __init__.py
├── view_models/
│   ├── __init__.py
│   ├── agent.py          # AgentViewModel + AgentRuntimeViewModel
│   ├── conversation.py   # ConversationViewModel（替换 SessionViewModel）
│   ├── capability.py     # CapabilityViewModel + ToolViewModel
│   ├── memory.py         # MemoryViewModel（抽象模型，非 KV）
│   └── settings.py       # SettingsViewModel
└── adapters/
    ├── __init__.py
    ├── agent_adapter.py
    ├── conversation_adapter.py
    ├── capability_adapter.py
    ├── memory_adapter.py
    └── settings_adapter.py
```

### 2.3 ViewModel Contract 重新设计

| 变更 | 修正前 | 修正后 |
|------|--------|--------|
| Agent | 身份+配置混合 | **AgentViewModel**（身份：id/name/role/capability_ids）+ **AgentRuntimeViewModel**（配置：provider/model/temperature） |
| Session→Conversation | SessionViewModel | **ConversationViewModel**（UI 只看到 Conversation，内部 SessionRuntime 支撑） |
| Capability | 菜单项（id/name/icon/enabled） | **一级 Runtime 概念**（+input_schema/output_schema/provider/status/is_enabled） |
| Memory | KV 数据库（key/value） | **抽象模型**（content/memory_type/source/importance，支持 vector/graph/document） |

### 2.4 UI Shell 恢复

- [workbench.py](file:///e:/Development/workbench/agent_workbench/agent_workbench/ui/workbench/workbench.py)：移除 `LayoutManager` + `_central` 包装，改为直接 `QSplitter` + 三面板（匹配 ui-template 分支 MainWindow._setup_ui()）
- 布局参数：左 180-220px | 中 stretch | 右 400px

### 2.5 Bug 修复

- `'str' object has no attribute 'get'` — status_bar.set_runtime_status() 参数类型
- `font(10, mono=True) TypeError` — settings_panel.py
- `RightPanel.refresh_theme` AttributeError — 私有方法 `_refresh_theme`
- `LeftPanel._function_page` AttributeError

---

## 3. 架构保证（本会话建立）

```
Runtime OS  ──NEVER import by UI──►

        Presentation Adapter
        (getattr() 过渡模式)

        ViewModel Contract

        UI Shell (v6/ui/*.py + workbench.py)
```

---

## 4. 明确未完成（by design，不应急于做）

1. **Phase 4: UI 占位填充** — Agent/Skill/MCP/Settings/Provider 内容绑定。等待 Contract Review 完成后进行。
2. **Phase 3: Adapter 接入 Runtime** — 当前 `getattr()` 是过渡模式。等待 Runtime 类型稳定后替换为显式类型映射。
3. **UI 不修改** — 当前 EXE 已构建成功，UI Shell 结构已冻结。

---

## 5. Frozen Zone（19 文件，本会话未修改）

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

---

## 6. 关键文件索引

| 文件 | 作用 | 修改状态 |
|------|------|---------|
| [PROJECT_BLUEPRINT.md](file:///e:/Development/workbench/agent_workbench/PROJECT_BLUEPRINT.md) | 项目宪法（已升级为 Agent Workbench OS） | dirty |
| [.agent-entry.json](file:///e:/Development/workbench/agent_workbench/.agent-entry.json) | AISE Protocol Manifest | dirty |
| [agent_workbench/presentation/](file:///e:/Development/workbench/agent_workbench/agent_workbench/presentation/) | Presentation Layer（新建） | new |
| [agent_workbench/ui/workbench/workbench.py](file:///e:/Development/workbench/agent_workbench/agent_workbench/ui/workbench/workbench.py) | UI Shell 装配（已恢复 ui-template 模式） | dirty |
| [v6/layout_manager.py](file:///e:/Development/workbench/agent_workbench/v6/layout_manager.py) | 三栏布局（已恢复原始纯 UI 设计） | dirty |
| [docs/v6/architecture-boundaries.md](file:///e:/Development/workbench/agent_workbench/docs/v6/architecture-boundaries.md) | 架构边界文档 | clean |
| [.project/architecture/v6.13-freeze-report.md](file:///e:/Development/workbench/agent_workbench/.project/architecture/v6.13-freeze-report.md) | 冻结报告 | clean |

---

## 7. 接替指引

1. 读取 [.project/handoff/latest.md](file:///e:/Development/workbench/agent_workbench/.project/handoff/latest.md) + latest.json 获取完整上下文
2. 读取 [PROJECT_BLUEPRINT.md](file:///e:/Development/workbench/agent_workbench/PROJECT_BLUEPRINT.md) 了解新宪法（Agent Workbench OS，不是 IDE）
3. 读取 [docs/v6/architecture-boundaries.md](file:///e:/Development/workbench/agent_workbench/docs/v6/architecture-boundaries.md) 了解系统边界
4. **不要回退到 IDE 语义**（不使用 Navigator/Inspector/WorkspaceHost/CommandBar 概念）
5. 当前 Presentation Contract 已冻结，不要修改 ViewModel 结构
6. 下一步：Phase 4 UI 占位填充（通过 ViewModel 绑定，不直接引用 Runtime）
7. 运行 `git status --short` 确认工作区状态
8. 确认 Frozen Zone 19 文件未被修改

---

## 移交禁止事项

- Agent SHALL NOT 继续修复 Bug
- Agent SHALL NOT 打标签或修改版本号
- Agent SHALL NOT 要求用户提供额外信息
