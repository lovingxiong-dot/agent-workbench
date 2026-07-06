# V6 路线图

## 总览
| 阶段 | 目标 | 版本标签 | 验收标准 |
| --- | --- | --- | --- |
| 0 | 骨架与规格 | v6.0.0-alpha | 目录完整、spec 就绪、所有模块可 import |
| 1 | 纯 UI 层 | v6.1.0-alpha | 三栏 UI 可独立显示，零业务逻辑 |
| 2 | Layout/UIController/MainWindow | v6.2.0-alpha | 窗口/分栏/折叠正常，MainWindow 无业务逻辑 |
| 3 | Session/Config Manager | v6.3.0-alpha | 会话持久化、配置验证通过 |
| 4 | AgentRuntime 骨架 | v6.4.0-alpha | 任务调度、事件总线可运行 |
| 5 | Engines | v6.5.0-alpha | 六大 Engine 独立并通过测试 |
| 6 | 业务服务与集成 | v6.6.0-alpha | 端到端 ChatTask 通过 |
| 7 | 打包与最终存档 | v6.7.0-alpha | exe 可启动、全量测试通过 |

## 当前阶段：阶段 0（v6.0.0-alpha）

### 任务清单
- [x] 创建 `v6/` 目录结构
- [x] 编写 `docs/v6/PROJECT_BLUEPRINT_v6.md`
- [x] 编写 `docs/v6/SPEC.md`
- [x] 编写 `docs/v6/ROADMAP.md`
- [x] 编写 `docs/v6/CHANGELOG_v6.md`
- [x] 创建空模块文件（`__init__.py` 等）
- [x] 编写最小 import smoke 测试
- [x] Review Agent 校验
- [ ] Git 存档 `v6.0.0-alpha`

### 下阶段预告：阶段 1（v6.1.0-alpha）
由 UI Agent 主导，实现完整纯 UI 层。
