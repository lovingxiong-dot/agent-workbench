# Architecture Decision: AI Software Engineering Workflow

## Status

Accepted — 2026-07-10
Frozen — 2026-07-10
Updated — 2026-07-10 (v1.1: GitHub as Single Source of Truth)

## Context

经过最近几轮 Workbench OS 开发，现有 AI 辅助流程已证明可以完成编码、调试、测试、文档、Git 和交接。但缺少一个统一的、跨项目的长期规范。本决策定义所有未来项目遵循的 AI 软件工程工作流。

本次更新的核心变化：

- **GitHub 成为唯一 Source of Truth（`origin`）。**
- **Gitee 退化为可选的 Release Mirror（`release`），不参与开发。**
- **所有 Skill 重构为 Repository Generic、Project Independent、Language Independent、Framework Independent。**
- **Mirror 从 Archive 子流程中解耦，仅在正式发布时由用户显式触发。**

## Decision

### 1. 角色划分

| 角色 | 负责人 |
|------|--------|
| Product Architect / System Architect | 人类用户 |
| Coder / Debugger / Tester / Documenter / Git / Build / Release | AI（Trae / ChatGPT / Claude / Codex / Cursor / Gateway 等） |

人类负责：

- 产品目标
- 架构设计
- Contract 定义
- 实际使用
- 提出反馈
- 验收结果

AI 负责完整软件工程生命周期。

### 2. 五层架构

整个体系分为五层，职责清晰解耦：

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

- **Product Layer**：产品目标、用户价值、体验标准。由人类定义与验收。
- **Engineering Workflow Layer**：把产品目标转化为可执行工程步骤。包含五个标准 Skill。
- **Repository Layer**：代码资产的唯一真相。**GitHub 为 Primary（`origin`），Gitee 为可选 Release Mirror（`release`）。**
- **Workspace Layer**：开发/运行环境（Local / Cloud）。负责把 Repository 版本安全部署为可运行状态。
- **Runtime Layer**：真正运行的程序（Application、Python、DB、Config）。

### 3. Repository Strategy

所有项目统一采用以下策略：

- **Primary Repository**: GitHub（唯一 Source of Truth）
- **Release Mirror**: Gitee（可选，仅在正式发布时同步）

原则：

- GitHub 为唯一开发仓库（Single Source of Truth）。
- Gitee 为可选 Release Mirror，不参与开发。
- 所有 Pull / Push / Archive / Handoff / Sync 基于 GitHub。
- 方向只在 Release 时单向：GitHub → Gitee。
- 所有 Tag、Commit、Branch 的开发历史以 GitHub 为准。
- Cloud Agent 开发完成后 Push origin（GitHub），经 PR / Merge / Archive 后，由 Publish（可选）+ Mirror 同步到 Gitee。
- 未来若增加 GitLab、Azure DevOps，统一作为可选 Release Mirror。

Mirror Policy：

```yaml
Primary: GitHub
Release Mirror: Gitee
Direction: GitHub -> Gitee
Force Push: Forbidden
Delete Branch: Forbidden
Delete Tag: Forbidden
Mirror Current Branch Only: True
Mirror Current Tag Only: True
Release Mirror: Optional
```

### 4. 完整生命周期

所有开发流程统一为：

```
Idea → Architecture → Implementation → Testing → Archive → Publish → Mirror → Handoff → Sync Workspace → Run → Feedback → Idea
```

禁止跳步骤。

- **Archive**：冻结版本，推送到 GitHub `origin`。
- **Publish**：从已归档版本生成可发布产物（Release Pipeline）。
- **Mirror**：可选，仅在正式发布时把 GitHub 同步到 Gitee Release Mirror。
- **Handoff**：生成交接上下文（可选，Cloud Workspace 必填）。
- **Sync Workspace**：把版本部署到本地/云端运行环境。

### 5. 五大标准 Skill

| Skill | 触发词 | 职责 | 输出 |
|-------|--------|------|------|
| gitops | 新建项目 | Git init + 项目骨架生成 + 可选远程关联（默认 origin→GitHub） | Project Report |
| Archive | 存档 / 存档并push | Version、CHANGELOG、PROJECT_BLUEPRINT、Git Commit、Git Tag、Push origin（GitHub） | Archive Report |
| Publish | 发布 / Publish | Release Pipeline：Build、生成 Release Notes、更新 Artifact Manifest | Publish Report |
| Handoff | 移交 / 接替 | 完整交接，包含 Version、Progress、Completed、Remaining、Known Issues、Risks、Environment、Next Step、Pending Questions、Git Status | Handoff Report |
| Sync Workspace | 同步 / Sync Workspace | 把工作环境安全升级到指定版本。Repository Sync → Analyze → Upgrade Plan → Backup → Upgrade → Launch → Acceptance。维护 `.sync/` 目录 | Sync Report |
| Mirror | 镜像 / Mirror | Release Mirror：GitHub → Gitee 单向同步（当前分支 + 当前 Tag） | Mirror Report |

### 6. Skill 调用关系

#### 6.1 标准自动化链路

```
Archive
  └── Commit
  └── Tag
  └── Push origin (GitHub)
```

Archive 不再自动触发 Mirror。

#### 6.2 发布链路

```
Publish
  ├── Verify Repository State
  ├── Build Artifact
  ├── Verify Artifact
  ├── Generate Release Notes
  ├── Update Artifact Manifest
  └── Output Publish Report
       │
       ▼
Mirror（可选，Release 时触发）
```

#### 6.3 交接链路

Handoff 必须包含：

- Mission
- Progress
- Blocker
- Decision Log
- Pending Questions（等待用户确认的问题）
- Key Files
- Error Log
- Environment Snapshot
- Working State
- Recent Conversation
- Next Steps
- Test Status
- Notes

### 7. Workspace State

Sync Workspace 维护 `.sync/` 目录：

```
.sync/
    workspace_state.json      # 当前环境状态
    sync_history.json         # 同步历史
    artifact_manifest.json    # 产物清单
```

AI 不再猜测当前同步状态，直接读取 `.sync/`。

### 8. Upgrade Plan

Sync Workspace 在执行升级前必须生成 Upgrade Plan，包含：

- 当前版本 vs 目标版本
- 影响面（Database Migration、Config Merge、Artifact Rebuild 等）
- 预计时间
- 备份位置
- 风险等级
- 用户确认（Continue? Y/N）

### 9. Cloud Workspace 定位

Cloud Workspace 不是仓库，只是 **Temporary Development Workspace**。

流程：

```
GitHub Clone → Coding → Testing → Archive → Push origin (GitHub) → Handoff → Terminate Session
```

Session 可以删除。真正的数据永远保存在 Git Repository。

任何时候：**Git Repository > Cloud Session**。

### 10. Workbench OS 定位

Workbench OS 不是 IDE，而是 **AI Product Operating System**。

用户每天只负责：

```
打开桌面快捷方式 → 体验 → 提出反馈 → 等待 AI 完成下一版本
```

用户不参与：编码、Debug、Git 操作、测试、Build。

### 11. Project Knowledge Management

不依赖 IDE Memory。所有长期知识统一保存在项目内：

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

保证更换 AI、IDE、云平台时项目知识全部保留。

### 12. Engineering Workflow Contract

完整工程生命周期与 Skill 职责边界已冻结于 `docs/engineering-workflow.md`。

本决策进入 Frozen 状态后：

- 允许新增字段、新增 Skill、新增说明。
- 禁止修改已冻结的流程顺序、Skill 职责边界、Repository Strategy。
- 如需修改，必须走架构评审，并更新版本号。

## Consequences

- 所有项目必须建立 `.project/` 目录。
- 所有 AI 交互以 GitHub 状态为基准，不以 Cloud Session 为基准。
- 发布流程必须包含 Archive → Publish → Mirror（可选）→ Handoff（Cloud 必填）→ Sync Workspace。
- 用户从 Developer 彻底转型为 Product Architect。
- 任何 AI 进入项目后，先读 `docs/engineering-workflow.md` 和 `.project/`。
- Skill 文档必须保持 Repository Generic，不得绑定具体项目、语言、框架。

## Related Decisions

- `docs/engineering-workflow.md` — Engineering Workflow Contract
- `.project/contracts/repository_contract.md` — Repository Contract
- `docs/v6/product-contract.md` — Workbench OS 1.0 Product Contract
