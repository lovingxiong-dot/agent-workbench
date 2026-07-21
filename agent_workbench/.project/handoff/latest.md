# CENTRE Handoff — Agent Workbench OS v6.14

> generated: 2026-07-21T13:14:00+08:00
> agent: AI-DeepSeek-V4-Pro
> schema_version: 3.1.0
> project: Agent Workbench OS (workbench/os)
> branch: v6-agent
> last_commit: ebc426b

---

## Mission

执行 v6.14 Shell Integration — 将纯 UI（v6/ui）从"旧 UI"重新定位为 Workbench OS 的 Qt Shell Reference Implementation，通过 Presentation Boundary 实现 Runtime → Shell Contract → UI Shell 的单向数据流。

核心任务：
- **Phase 1-A**: v6/ui 去硬编码（bind_capabilities）
- **Phase 1-A.1**: Shell 命名修正（NavigationState→NavigationGroup, WorkspaceViewModel→WorkspaceState）
- **Phase 1-B**: Shell Protocol + Transformers 创建
- **Phase 1-B.1**: Shell Contract Freeze（命名、Boundary 注释、测试）
- **Phase 1-C**: Presentation Pipeline 集成（PresentationPipeline + WorkbenchUIController 接入）

## Progress

| Phase | 状态 | 说明 |
|-------|------|------|
| Phase 1-A | ✅ completed | function_page.py: bind_capabilities + _clear_rows + _connect_row |
| Phase 1-A.1 | ✅ completed | 命名修正：NavigationGroup, WorkspaceState, InspectorState |
| Phase 1-B | ✅ completed | protocol.py + 3 transformers (session/message/capability) |
| Phase 1-B.1 | ✅ completed | Shell Contract Freeze + 14 tests |
| Phase 1-C | ✅ completed | PresentationPipeline + 3 集成方法 + 10 tests |
| Phase 1-D | ⏳ pending | QtShell implements ShellProtocol（未开始） |

## Architecture Status

```
Runtime Kernel (FROZEN)
    │
    ▼
Presentation Boundary
├── adapters/        (Runtime → ViewModel, 已有)
├── view_models/     (数据契约, 已有 6 个)
├── shell/           (新增)
│   ├── protocol.py  (ShellProtocol(Protocol) + 6 OS 抽象模型)
│   ├── transformers/ (ViewModel → Shell Model)
│   └── integration.py (PresentationPipeline)
    │
    ▼
Shell Implementation
├── ui/workbench/    (OS Host Shell, 已有)
└── v6/ui/           (Qt Shell, Phase 1-D 待接入)
```

## Decision Log

| # | 决策 | 原因 |
|---|------|------|
| D1 | v6/ui 不嵌入 Workbench | 防止"四套 UI 概念混合"，保持 Shell 边界 |
| D2 | ShellProtocol 使用 typing.Protocol | Structural Typing，不强绑继承 |
| D3 | NavigationState→NavigationGroup | 结构模型非运行时状态 |
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
