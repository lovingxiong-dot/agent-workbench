# 项目蓝图 (Project Blueprint)

> **AI 记忆锚点** - 新对话开始时，上传此文件或粘贴内容，AI 可立即恢复完整上下文

---

## 项目信息

| 属性 | 值 |
|------|-----|
| 项目名称 | _(待填写)_
| 创建日期 | 2026-06-24 |
| 项目路径 | E:\workbuddy\2026-06-24-21-38-49
| 远程仓库 | https://gitee.com/xyzturbo/xyz
| 默认分支 | main |

---

## 项目目标

_(在此描述项目的核心目标和愿景)_

---

## 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 编程语言 | _(待填写)_ | - |
| 框架/库 | _(待填写)_ | - |
| 运行环境 | _(待填写)_ | - |
| 包管理器 | _(待填写)_ | - |

---

## 目录结构

```
项目根目录/
├── .gitignore              # 项目忽略规则
├── CHANGELOG.md            # 变更日志（自动维护）
├── PROJECT_BLUEPRINT.md    # 本文件（AI 记忆锚点）
├── README.md               # 项目说明文档
└── src/                    # 源代码目录
```

---

## 快速启动

### 前置条件

- [ ] Git 已安装（当前版本: 2.x+）
- [ ] Node.js / Python 已安装（根据技术栈选择）
- [ ] SSH 密钥已配置（已完成）

### 启动步骤

```bash
# 1. 克隆仓库
git clone git@gitee.com:xyzturbo/xyz.git

# 2. 进入目录
cd xyz

# 3. 安装依赖（根据实际调整）
npm install  # 或 pip install -r requirements.txt

# 4. 启动项目
npm start   # 或 python main.py
```

---

## Git 工作流规范

### 分支策略

| 分支 | 用途 | 说明 |
|------|------|------|
| `main` | 主分支 | 生产代码，稳定版本 |
| `dev` | 开发分支 | 功能开发中 |
| `feature/*` | 功能分支 | 单个功能开发 |

### 提交格式

遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

```
<类型>(<范围>): <简短描述>

<可选的详细说明>
```

**类型标签：**

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(login): 添加用户登录页面` |
| `fix` | Bug 修复 | `fix(auth): 修复 token 过期问题` |
| `docs` | 文档变更 | `docs(readme): 更新安装说明` |
| `style` | 代码格式 | `style(lint): 修复缩进问题` |
| `refactor` | 重构 | `refactor(api): 简化请求处理逻辑` |
| `perf` | 性能优化 | `perf(db): 添加查询缓存` |
| `test` | 测试相关 | `test(unit): 添加用户模块单元测试` |
| `chore` | 构建工具 | `chore(deps): 更新依赖包版本` |

### 常用命令别名

```bash
git co      # checkout - 切换分支
git br      # branch - 查看/创建分支
git ci      # commit - 提交更改
git st      # status - 查看状态
git lg      # log --oneline --graph - 图形化日志
git diffc   # diff cached - 查看暂存区差异
git save    # 快速保存（自动时间戳）
git undo    # 撤销上次提交
```

### 「请存档」自动化流程

当你说「请存档」时，AI 会自动执行：

1. ✅ 更新 CHANGELOG.md（记录本轮改动）
2. ✅ git add <源码文件> + CHANGELOG.md
3. ✅ git commit -m "<自动生成摘要>"
4. ✅ git tag v<N>（版本号递增）
5. ✅ git push + git push --tags（如有远程）

---

## 当前状态与进度

### 已完成

- [x] 初始化 Git 仓库
- [x] 配置全局 Git 设置（身份、别名、SSH）
- [x] 配置远程仓库认证
- [x] 创建项目模板文件

### 进行中

- _(待更新)_

### 待办

- _(待更新)_

---

## 重要配置要点

### SSH 认证配置

- 密钥位置: `~/.ssh/id_ed25519`
- 公钥注释: lovingxiong@foxmail.com
- 已添加到 Gitee: 是/否
- 连接测试: `ssh -T git@gitee.com`

### 全局配置文件位置

| 文件 | 路径 |
|------|------|
| Git 全局配置 | `C:\Users\ThinkPad\.gitconfig` |
| 全局忽略规则 | `C:\Users\ThinkPad\.gitignore_global` |
| SSH 私钥 | `C:\Users\ThinkPad\.ssh\id_ed25519` |
| SSH 公钥 | `C:\Users\ThinkPad\.ssh\id_ed25519.pub` |
| SSH 配置 | `C:\Users\ThinkPad\.ssh\config` |

---

## 注意事项

1. **SSH 私钥安全**: 绝不将 `id_ed25519` 文件分享给任何人或提交到仓库
2. **定期备份**: 定期将重要配置和代码推送到 Gitee
3. **保持蓝图同步**: 大改动后及时更新本文件内容
4. **敏感信息**: 使用 `.env` 文件管理密钥/密码，确保已在 `.gitignore` 中排除

---

*最后更新: 2026-06-24*
