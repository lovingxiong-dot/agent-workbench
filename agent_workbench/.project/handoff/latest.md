# CENTRE Handoff — Agent Workbench OS v6.14

> generated: 2026-07-22T12:00:00+08:00
> agent: AI-DeepSeek-V4-Pro
> schema_version: 3.1.0
> project: Agent Workbench OS (workbench/os)
> branch: v6-agent
> last_commit: (pending)
会话 ID：6a5ee38b172120d667423f31
---

## Mission

执行 Phase 2-B Architecture Declaration Sync — 将已确定的架构边界写入项目事实源（Project Truth），包括：

- **Phase 2-B**: Presentation Boundary Freeze（v6/ui Frozen Foundation + Renderer Layer）
- **Phase 2-B.1**: Renderer Boundary Cleanup（ChatArea Public API 修正 + 文档 Runtime import 描述修正）
- **Phase 2-B.2**: Architecture Declaration Sync（本次会话 — 全部文档同步）

## Progress

| Phase | 状态 | 说明 |
|-------|------|------|
| Phase 1-A | ✅ completed | v6/ui 去硬编码（bind_capabilities） |
| Phase 1-A.1 | ✅ completed | 命名修正：NavigationGroup, WorkspaceState, InspectorState |
| Phase 1-B | ✅ completed | Shell Protocol + Transformers 创建 |
| Phase 1-B.1 | ✅ completed | Shell Contract Freeze + 14 tests |
| Phase 2-B | ✅ completed | Presentation Boundary Freeze：v6/ui Frozen Foundation + Renderer Layer |
| Phase 2-B.1 | ✅ completed | Renderer Boundary Cleanup：ChatArea.add_capability_step() + 文档修正 |
| Phase 2-B.2 | ✅ completed | **Architecture Declaration Sync：9 文档同步 + 2 新增** |
| Phase 2-C | ⏳ pending | Presentation Runtime：InteractionCommand 独立化、Pipeline 生命周期化 |

## Architecture Status

```
CENTRE Runtime (FROZEN)
    │
    │ Interaction Contract
    ▼
Presentation Renderer (presentation/renderers/v6_ui/)
    │
    │ v6/ui Public API
    ▼
v6/ui Pure UI Foundation (FROZEN — 22 files)
    │
    ▼
Qt
```

**Dependency direction**: only downward. Never upward.

## Key Decisions (Phase 2-B)

| # | 决策 | 原因 |
|---|------|------|
| D4 | v6/ui 是 Pure UI Foundation，不是旧 v6-agent | 血统区分：v6-agent 是 UI→Controller→Runtime，v6/ui 是 Runtime-agnostic |
| D5 | Renderer 允许引用 Interaction Contract，禁止引用 Runtime Implementation | 精确边界：允许 event.py，禁止 engine/executor/session/llm/tool |
| D6 | Renderer 不得穿透 v6/ui 私有成员 | ChatArea 提供 Public API：reset_workspace(), add_capability_step() |
| D7 | Application 层使用 WorkbenchController，禁止 WorkbenchUIController | 防止 God Object 复辟 |
| D8 | v6/ui 只允许 UI Capability API，不允许 Runtime Concept API | 边界：append_user() 可以，update_agent() 不可以 |

## Architecture Declaration Sync (Phase 2-B.2)

### 已更新文档

| 文件 | 操作 | 说明 |
|------|------|------|
| PROJECT_BLUEPRINT.md | 更新 | 新增 Presentation Architecture 章节（Layer Ownership、v6/ui Positioning、Renderer Constraints、Dependency Direction、Artifact Lineage） |
| v6/UI_FOUNDATION.md | 升级 | 升级为正式 Frozen Foundation 文档（Origin、Responsibility、Forbidden Dependencies、Modification Policy、UI Capability vs Runtime Concept、Multi-Runtime Target） |
| docs/v6/architecture-boundaries.md | 更新 | 新增 §6 Presentation Boundary（核心边界图、各层职责、三项禁止事项、血统区分） |
| docs/ARCHITECTURE.md | 更新 | 新增 v6.14 架构状态章节、版本号更新 |
| docs/v6/SPEC.md | 更新 | 新增 §0 架构边界声明、版本号更新 |
| README.md | 更新 | 新增 Architecture Status 章节、For AI Agents 阅读顺序更新、版本号更新 |
| docs/v6/ROADMAP.md | 更新 | 新增 v6.14 Presentation Boundary 演进阶段 |
| .project/handoff/latest.md | 更新 | 本次 handoff 更新 |

### 新增文档

| 文件 | 说明 |
|------|------|
| ARCHITECTURE_BOUNDARY.md | Agent 施工规范（Layer Ownership、Frozen Zones、Modification Checklist、Before You Touch Anything） |
| .agent/architecture_rules.md | Agent 首次进入规则（快速参考卡片） |

## Frozen Zone Status

| Zone | Files | Status |
|------|-------|--------|
| Runtime Kernel | 19 files | FROZEN |
| v6/ui Foundation | 22 files | FROZEN |
| Shell Contract | 7 files | FROZEN |
| Metadata Contract | agent_workbench/metadata/ | FROZEN (additive only) |

## Next Phase

Phase 2-C：Presentation Runtime
- InteractionCommand 独立化
- PresentationPipeline → service lifecycle
- InteractionEvent 提升为 Protocol package
- Renderer Registry
| D4 | WorkspaceViewModel→WorkspaceState | 区分 shell 层与 view_models 层 |
| D5 | PresentationPipeline 在 integration.py | 编排全链路，不创建 Widget |
| D6 | Workbench 不 import v6/ui | Shell Adapter 做中间层 |

## Key Files

| 文件 | 类型 | 说明 |
|------|------|------|
| `v6/ui/function_page.py` | modified | 添加 bind_capabilities/clear_row/connect_row |
| `presentation/shell/protocol.py` | new | ShellProtocol(Protocol) + 6 模型 |
| `presentation/shell/transformers/session.py` | new | SessionVM → NavigationGroup |
| `presentation/shell/transformers/message.py` | new | MessageVM → WorkspaceState |
| `presentation/shell/transformers/capability.py` | new | CapabilityVM → NavigationItem |
| `presentation/shell/integration.py` | new | PresentationPipeline 编排 |
| `ui/workbench_ui_controller.py` | modified | +3 集成方法 |
| `tests/test_shell_protocol.py` | new | 14 tests |
| `tests/test_presentation_flow.py` | new | 8 tests |
| `docs/v6/shell-adapter-architecture.md` | new | Shell Adapter 设计文档 |
| `docs/v6/shell-integration-architecture-report.md` | new | 诊断报告 |

## Blocked / Failed Attempts

无阻塞项。所有阶段均按用户审核通过的顺序执行。之前踩过的坑已通过回退修复：
- ❌ 曾试图将 LeftPanel 嵌入 Workbench QSplitter（被用户纠正）
- ❌ 曾试图让 v6/ui 作为独立 Qt Window 运行（被用户纠正）
- ❌ 曾命名为 QtShellAdapter（改为 QtShell implements ShellProtocol）

## Test Status

- `test_shell_protocol.py`: 14/14 PASS
- `test_presentation_flow.py`: 10/10 PASS
- 无 GUI 测试（Phase 1-C 不含 UI Widget 创建）

## Environment

| 项目 | 值 |
|------|-----|
| Python | 3.10.11 |
| Branch | v6-agent |
| Last Commit | ebc426b (handoff) |
| Modified | workbench.py, workbench_ui_controller.py |
| Untracked | PROJ_BLUEPRINT, docs/, presentation/shell/, tests/, v6/ui/ (workspace shadow) |

## Next Steps (AI-Inferred)

1. **Phase 1-D**: 实现 `QtShell implements ShellProtocol` — 将 v6/ui 作为 Qt Shell 正式接入
   - 创建 `presentation/shell/implementations/qt_shell.py`
   - QtShell 内部映射：NavigationGroup→LeftPanel, WorkspaceState→ChatArea, InspectorState→RightPanel
   - 禁止：QtShell 调用 Widget 私有 API（`_scene`, `_models` 等）

2. **v6/ui ChatArea 公开接口**: 添加 `bind_workspace(state: WorkspaceState)` 方法替代私有 API 调用

3. **Workbench Shell 接入**: 完成 NavigatorHost 的 NavigationGroup 消费

4. **WorkbenchUIController 瘦身**: 长期避免控制器膨胀（当前 865+ 行）

## Critical Constraints for Next Agent

- ❌ 禁止修改 Runtime（Frozen Zone）
- ❌ 禁止修改 metadata() 接口
- ❌ 禁止将 v6/ui 作为 Workbench 子组件
- ❌ 禁止 Shell Protocol 暴露 UI 组件名（LeftPanel/ChatArea）
- ✅ 只允许修改 `presentation/shell/implementations/` 和 `v6/ui/`
- ✅ 所有数据流必须单向：Runtime → Presentation → Shell
