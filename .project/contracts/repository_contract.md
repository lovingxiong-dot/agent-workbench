# Repository Contract

> 版本：v1.0
> 状态：Frozen
> 适用范围：所有项目

## 1. 总则

本合约定义所有项目必须遵守的 Git 仓库基础设施标准。目标是在任何 AI、任何平台、任何项目之间建立统一的 Repository 认知，避免多源冲突与数据丢失。

## 2. Single Source of Truth

- **GitHub 是所有项目的唯一开发源（Single Source of Truth）。**
- `origin` 必须指向 GitHub。
- 所有开发行为（Pull / Push / Archive / Handoff / Sync Workspace）基于 GitHub。

## 3. Release Mirror

- Gitee 定位为可选的 **Release Mirror**，不参与开发。
- 可选远程名称为 `release`，指向 Gitee。
- Mirror 方向永远单向：**GitHub → Gitee**。
- 仅同步当前分支与当前 Tag。
- 禁止使用 `--force`、`--mirror`、`--all`。
- 禁止删除 Mirror 上的分支或标签。

## 4. Workspace 类型

- **Local**：用户本地机器，长期保存用户数据、配置、数据库。
- **Cloud**：Trae Cloud / 其他 Cloud Agent 临时环境，不保存长期资产。

## 5. Cloud Workspace 约束

Cloud Workspace 只是 Execution Workspace：

```
GitHub Clone → Development → Testing → Archive → Push origin → Handoff → Destroy Session
```

Cloud Session 删除前必须：

- Commit
- Push origin（GitHub）
- 生成 HANDOFF.md

禁止 Cloud Workspace 保存唯一数据。

## 6. Local Workspace 约束

Local Workspace 通过 Sync Workspace 升级：

```
Sync Workspace → Launch → Application
```

用户不打开 IDE，只使用最终应用。

## 7. Remote 配置示例

```
origin   git@github.com:<org>/<repo>.git (fetch)
origin   git@github.com:<org>/<repo>.git (push)
release  git@gitee.com:<org>/<repo>.git (fetch)
release  git@gitee.com:<org>/<repo>.git (push)
```

## 8. 禁止行为

- 禁止把 Gitee 当开发源。
- 禁止 Gitee → GitHub 反向同步。
- 禁止 Cloud Agent 直接 Push Gitee。
- 禁止修改 `origin` 指向非 GitHub 地址。
- 禁止在 Archive 中自动触发 Mirror。

## 9. 变更控制

本合约进入 Frozen 状态后：

- 允许新增说明或可选远程。
- 禁止修改 Single Source of Truth 为 GitHub 的核心约定。
- 如需修改，必须走架构评审，并更新版本号。
