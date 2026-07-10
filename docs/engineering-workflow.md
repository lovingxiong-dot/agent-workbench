# Engineering Workflow Contract

> 版本：v1.0
> 状态：Frozen
> 适用范围：Workbench OS 及所有未来项目

## 1. 概述

本文档冻结 AI 辅助软件工程的完整生命周期。所有 AI（Trae、ChatGPT、Claude、Gemini、Codex、Gateway 等）进入项目后，必须遵循本合约定义的流水线与 Skill 职责边界。

本合约的核心目标：

- **可替换性**：任何 AI 只是执行者，Git 仓库与项目知识才是永久资产。
- **一致性**：无论换什么 AI，工程流程不变。
- **可追溯性**：每个阶段都有明确输入、输出与校验标准。
- **安全性**：用户数据、配置、运行状态在升级过程中完整保留。

## 2. 五层架构

```
Product Layer
        │
        ▼
Engineering Workflow Layer
        │
        ▼
Repository Layer
        │
        ▼
Workspace Layer
        │
        ▼
Runtime Layer
```

### 2.1 Product Layer

- 产品目标、用户价值、体验标准。
- 由人类（Product Architect）定义与验收。
- 输出：Product Contract、Roadmap、Feedback。

### 2.2 Engineering Workflow Layer

- 把产品目标转化为可执行工程步骤。
- 由 AI 执行，人类监督。
- 包含五个标准 Skill：Archive、Mirror、Publish、Handoff、Sync Workspace。

### 2.3 Repository Layer

- 代码资产的唯一真相。
- Gitee 为 Primary，GitHub 为 Readonly Mirror。
- 所有版本、标签、分支、架构决策都保存在这里。

### 2.4 Workspace Layer

- 开发/运行环境。
- Local、Trae Cloud、未来 Workbench Cloud。
- 负责把 Repository 的某个版本安全部署为可运行状态。

### 2.5 Runtime Layer

- 真正运行的程序：Workbench.exe、Python 进程、数据库、配置。
- 由 Sync Workspace 启动与健康检查。

## 3. 完整生命周期

```
        ┌─────────────┐
        │    Idea     │ ← 人类提出产品构想
        └──────┬──────┘
               ▼
        ┌─────────────┐
        │ Architecture│ ← 人类定义架构与 Contract
        └──────┬──────┘
               ▼
        ┌─────────────┐
        │Implementation│ ← AI 编码、调试、测试
        └──────┬──────┘
               ▼
        ┌─────────────┐
        │   Testing   │ ← AI 运行测试，失败停止
        └──────┬──────┘
               ▼
        ┌─────────────┐
        │   Archive   │ ← AI 冻结版本，Push Gitee
        └──────┬──────┘
               ▼
        ┌─────────────┐
        │   Mirror    │ ← AI 同步 GitHub（Readonly Mirror）
        └──────┬──────┘
               ▼
        ┌─────────────┐
        │   Publish   │ ← AI 生成可发布产物
        └──────┬──────┘
               ▼
        ┌─────────────┐
        │   Handoff   │ ← AI 生成交接上下文（可选）
        └──────┬──────┘
               ▼
        ┌─────────────┐
        │ Sync Workspace│ ← AI 把环境升级到目标版本
        └──────┬──────┘
               ▼
        ┌─────────────┐
        │     Run     │ ← 用户运行产品
        └──────┬──────┘
               ▼
        ┌─────────────┐
        │   Feedback  │ ← 人类反馈，回到 Idea
        └─────────────┘
```

禁止跳步骤。每个步骤的输出是下一个步骤的输入。

## 4. 五大标准 Skill

| Skill | 触发词 | 输入 | 输出 | 职责边界 |
|-------|--------|------|------|----------|
| **gitops** | 新建项目 | 项目名、可选远程 | 项目骨架 | 初始化项目 |
| **Archive** | 存档 / 存档并push | 工作区变更 | Commit + Tag + Push Gitee | 版本冻结，不 Build |
| **Mirror** | 镜像 / Mirror | Gitee 最新状态 | GitHub 同步 + 校验 | 单向同步，不修改 Primary |
| **Publish** | 发布 / Publish | 已归档 Tag | Artifact + Release Notes | Release Pipeline，不部署 |
| **Handoff** | 移交 / 接替 | 当前上下文 | HANDOFF.md | 上下文交接，不打标签 |
| **Sync Workspace** | 同步 / Sync Workspace | 目标版本 | 运行中的 Workspace | 部署、升级、保留用户数据 |

## 5. Skill 调用关系

### 5.1 标准自动化链路

```
人类：「存档并push」
  │
  ▼
Archive
  │
  ├── Commit
  ├── Tag
  └── Push Gitee
       │
       ▼
  Trigger Mirror
       │
       ▼
Mirror
  │
  ├── Fetch origin
  ├── Fetch mirror
  ├── Compare SHA
  ├── Push branch
  ├── Push tag
  └── Verify
```

### 5.2 发布链路

```
人类：「发布」
  │
  ▼
Publish
  │
  ├── Verify Repository State
  ├── Build Artifact
  ├── Verify Artifact
  ├── Generate Release Notes
  ├── Update Artifact Manifest
  └── Output Publish Report
       │
       ▼
Sync Workspace（可选，由人类触发）
```

### 5.3 交接链路

```
人类：「移交」
  │
  ▼
Handoff
  │
  ├── 环境快照
  ├── 生成 HANDOFF.md
  │     ├── Mission
  │     ├── Progress
  │     ├── Blocker
  │     ├── Decision Log
  │     ├── Pending Questions
  │     ├── Key Files
  │     ├── Error Log
  │     ├── Environment Snapshot
  │     ├── Working State
  │     ├── Recent Conversation
  │     ├── Next Steps
  │     ├── Test Status
  │     └── Notes
  └── Commit HANDOFF.md
```

## 6. Repository Strategy

### 6.1 Single Source of Truth

- **Primary**: Gitee（`origin`）
- **Mirror**: GitHub（`mirror`）
- **Direction**: Gitee → GitHub，永远单向。
- **GitHub 角色**: Readonly Mirror，仅供 Cloud Agent Pull。

### 6.2 Mirror Policy

```yaml
Primary: Gitee
Mirror: GitHub
Direction: Primary -> Mirror
Force Push: Forbidden
Delete Branch: Forbidden
Delete Tag: Forbidden
Mirror Current Branch Only: True
Mirror Current Tag Only: True
Readonly Mirror: True
```

### 6.3 Cloud Agent 工作流

Cloud Agent 绝不 Push GitHub 再 Mirror 回 Gitee。正确路径：

```
Cloud Agent 开发
    │
    ▼
Push Gitee（Primary）
    │
    ▼
PR / Merge / Archive
    │
    ▼
Mirror → GitHub
    │
    ▼
其他 Cloud Agent Pull GitHub
```

## 7. Workspace State

Sync Workspace 维护 `.sync/` 目录：

```
.sync/
    workspace_state.json      # 当前环境状态
    sync_history.json         # 同步历史
    artifact_manifest.json    # 产物清单
```

### 7.1 workspace_state.json

```json
{
    "workspace": "Local",
    "branch": "v6-agent",
    "current_version": "v6.12.0-beta.13",
    "last_sync": "2026-07-10T08:31:00+08:00",
    "git_commit": "abcd1234",
    "git_tag": "v6.12.0-beta.13",
    "artifact_version": "v6.12.0-beta.13",
    "artifact_path": "dist/WorkbenchOS.exe",
    "database_version": 8,
    "config_version": 3
}
```

### 7.2 sync_history.json

记录每次同步的源版本、目标版本、时间、备份位置、结果。

### 7.3 artifact_manifest.json

记录产物版本、commit、构建时间、SHA256、路径。

## 8. Upgrade Plan

Sync Workspace 在执行任何升级前必须生成 Upgrade Plan：

```markdown
## Upgrade Plan

### Versions
- Repository: v6.12.0-beta.13
- Local: v6.12.0-beta.10
- Artifact: v6.12.0-beta.10
- Database: 7
- Config: 2

### Diff
- 需要升级 3 个版本
- 涉及模块：...

### Impact
- Database Migration: YES/NO
- Config Merge: YES/NO
- Artifact Rebuild: YES/NO
- Dependency Change: YES/NO
- Index Rebuild: YES/NO
- Estimated Time: N min

### Backup
- Location: .backup/YYYY-MM-DD-NNN/

### Risk
- 低 / 中 / 高

### Confirm
Continue? [Y/N]
```

## 9. 项目知识管理

所有长期知识保存在项目内，不依赖 IDE Memory：

```
.project/
    architecture/
    contracts/
    decisions/
    prompts/
    feedback/
    roadmap/
    standards/
```

所有 AI 进入项目第一步：读取 `.project/`。

## 10. 核心原则

1. **任何工具都是可替换的执行者**：Trae、ChatGPT、Claude、Gemini、Codex、Gateway 都可以接入同一套流程。
2. **Git 仓库和项目知识是永久资产**：更换 AI 或平台时无需迁移。
3. **Gitee 是唯一 Source of Truth**：GitHub 只是 Readonly Mirror。
4. **不跳过步骤**：Idea → Architecture → Implementation → Testing → Archive → Mirror → Publish → Handoff → Sync Workspace → Run → Feedback。
5. **保留用户数据**：Workspace 升级时，config、database、feedback 必须完整保留。
6. **先计划后执行**：Sync Workspace 必须生成 Upgrade Plan 并等待确认。
7. **交接必须完整**：Handoff 必须包含 Decision Log 和 Pending Questions。

## 11. 变更控制

本合约进入 Frozen 状态后：

- 允许新增字段、新增 Skill、新增说明。
- 禁止修改已冻结的流程顺序、Skill 职责边界、Repository Strategy。
- 如需修改，必须走架构评审，并更新版本号。

## 12. 相关文档

- `.project/decisions/ai-software-engineering-workflow.md` — 架构决策记录
- `docs/v6/product-contract.md` — Workbench OS 1.0 产品契约
- `PROJECT_BLUEPRINT.md` — 项目蓝图
- `CHANGELOG.md` — 版本历史
