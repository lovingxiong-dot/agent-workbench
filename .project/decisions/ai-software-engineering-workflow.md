# Architecture Decision: AI Software Engineering Workflow

## Status

Accepted — 2026-07-10

## Context

经过最近几轮 Workbench OS 开发，现有 AI 辅助流程已证明可以完成编码、调试、测试、文档、Git 和交接。但缺少一个统一的、跨项目的长期规范。本决策定义所有未来项目遵循的 AI 软件工程工作流。

## Decision

### 1. 角色划分

| 角色 | 负责人 |
|------|--------|
| Product Architect / System Architect | 人类用户 |
| Coder / Debugger / Tester / Documenter / Git / Build / Release | AI（Trae / ChatGPT / Claude / Codex / Gateway 等） |

人类负责：
- 产品目标
- 架构设计
- Contract 定义
- 实际使用
- 提出反馈
- 验收结果

AI 负责完整软件工程生命周期。

### 2. Repository Strategy

所有项目统一采用双仓库：

- **Primary Repository**: Gitee（唯一 Source of Truth）
- **Mirror Repository**: GitHub（服务于 Cloud Agent / Trae Cloud）

原则：
- Gitee 为唯一主仓库（Single Source of Truth）。
- GitHub 为镜像仓库，仅服务于 Cloud Agent / Trae Cloud。
- 用户不直接维护 GitHub，Mirror 由 AI 自动完成。
- 所有 Tag、Commit、Branch 同步。
- AI 完成任务后：Commit → Push Gitee → Mirror → GitHub → Verify Commit SHA 一致。
- 未来若增加 GitLab、Azure DevOps，统一作为 Mirror。

Mirror 是独立的基础设施 Skill，与 Archive、Sync Workspace 解耦：

- **Archive**：冻结版本并推送到 Gitee。
- **Mirror**：把 Gitee 同步到 GitHub。
- **Sync Workspace**：把 Repository 版本部署到 Local / Cloud 工作环境。

### 3. Layered Model

整个体系分为三层，职责清晰解耦：

```
Repository Layer（代码资产）
        │
        ├── Gitee（Primary / Single Source of Truth）
        └── GitHub（Mirror / Cloud Agent）
                 │
                 ▼
Workspace Layer（开发环境）
        │
        ├── Local
        ├── Trae Cloud
        └── 未来 Workbench Cloud
                 │
                 ▼
Product Layer（交付产物）
        │
        └── Workbench OS.exe
```

- **Repository Layer**：只由 Git 管理，Mirror Skill 负责 Gitee ↔ GitHub 一致性。
- **Workspace Layer**：由 Sync Workspace Skill 管理，负责 Config / Database / Runtime / Artifact / Launch。
- **Product Layer**：由 Publish / Acceptance 管理（后期），生成可运行的产品并验收。

### 4. Cloud Workspace 定位

Cloud Workspace 不是仓库，只是 **Temporary Development Workspace**。

流程：

```
Git Clone → Coding → Testing → Commit → Push → 结束
```

Session 可以删除。真正的数据永远保存在 Git Repository。

任何时候：**Git Repository > Cloud Session**。

### 4. Release Pipeline

所有开发流程统一为：

```
Idea → Architecture → Implementation → Testing → Archive → Mirror → Handoff → Sync Workspace → Experience → Feedback
```

禁止跳步骤。

- **Archive**：冻结版本，推送到 Gitee。
- **Mirror**：把版本同步到 GitHub Mirror。
- **Handoff**：生成交接上下文。
- **Sync Workspace**：把版本部署到本地/云端运行环境。

Publish / Acceptance 作为后期 Skill，在当前阶段不强制纳入主线。

### 5. Standard Skills

所有 AI 默认拥有的工程技能：

| Skill | 触发词 | 职责 | 输出 |
|-------|--------|------|------|
| gitops | 新建项目 | Git init + 项目骨架生成 + 可选远程关联 | Project Report |
| Archive | 存档 / 存档并push | Version、CHANGELOG、PROJECT_BLUEPRINT、Handoff、Docs、Git Commit、Git Tag | Archive Report |
| Mirror | 镜像 / Mirror | Gitee → GitHub 仓库镜像同步与一致性校验（当前分支 + 当前 Tag） | Mirror Report |
| Handoff | 移交 / 接替 | 完整交接，包含 Version、Progress、Completed、Remaining、Known Issues、Risks、Environment、Next Step、Git Status | Handoff Report |
| Sync Workspace | 同步 / Sync Workspace | 把工作环境安全升级到指定版本。双层：Repository Sync（Git/Branch/Tag）→ Workspace Backup → Workspace Upgrade（Replace/Config Merge/DB Migration/Artifact）→ Launch → Acceptance。维护 `.sync/workspace_state.json`，执行前生成 Upgrade Plan | Sync Report |

未来扩展：

- **Publish**：Build / PyInstaller / Release（后期）。
- **Acceptance**：GUI 自动验收 / 截图 / Smoke Test（后期）。

### 6. Workbench OS 定位

Workbench OS 不是 IDE，而是 **AI Product Operating System**。

用户每天只负责：

```
打开桌面快捷方式 → 体验 → 提出反馈 → 等待 AI 完成下一版本
```

用户不参与：编码、Debug、Git 操作、测试、Build。

### 7. Project Knowledge Management

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

### 8. Core Design Principle

> 任何工具（Trae、ChatGPT、Claude、Codex、Gateway）都是可替换的执行者；Git 仓库和项目知识才是永久资产。整个架构必须保证更换任何 AI 或平台时，无需迁移项目资产，只需更换执行者即可继续开发。

## Consequences

- 所有项目必须建立 `.project/` 目录。
- 所有 AI 交互以 Git 状态为基准，不以 Cloud Session 为基准。
- 发布流程必须包含 Archive → Mirror → Handoff → Sync Workspace 四阶段。
- 用户从 Developer 彻底转型为 Product Architect。

## Related Decisions

- `docs/v6/product-contract.md` — Workbench OS 1.0 Product Contract
