# Phase 3 Observation Buffer

> 轻量缓冲 — 非架构文档。Phase 3 完成后批量 Consolidation，不逐条更新 architecture-context.md。

## OBS Queue（Batch Review after Phase 3）

| ID | 标题 | 影响 | 等级 | 发现 Step |
|----|------|------|------|-----------|
| OBS-003 | Workspace Recovery Bypass — `_on_session_selected()` 绕过 Interaction Protocol | Medium | R2 | Step 3 |
| OBS-004 | MiniMax 未在 default.yaml 启用 — 配置选择，非能力缺失 | Low | R1 | Step 4 |
| OBS-005 | Config Resolution Consistency — `preflight_check()` 与 `OpenAIProvider._expand()` 展开路径不一致 | Low | R1 | Step 4-A |

## Debt Queue（D0=记录/D1=影响未来开发/D2=影响架构）

| ID | 标题 | 等级 | 发现 Step |
|----|------|------|-----------|
| DEBT-002 | Status Update Rendering Gap — `STATUS_UPDATE` handler 为 no-op | D1 | Step 3 |
| DEBT-003 | Provider UI 动态切换能力未覆盖验证 | D1 | Step 4 |

## 升级规则

- 仅当影响 Frozen Boundary / Runtime Contract / 长期 Architecture 时，才立即升级至 architecture-context.md
- 其余在 Phase 3 Consolidation 阶段批量处理