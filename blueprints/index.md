# 蓝图索引

本目录存放从 `.trae/documents/` 提炼后的设计蓝图（结果文档），按时间线和模块双维度组织。

> 原始设计讨论记录位于 `.trae/documents/`，属于 AI 工具的过程文档，仅供追溯参考。

---

## 按时间线

| 日期 | 蓝图 | 模块 | 状态 |
|---|---|---|---|
| 2026-06-26 | [工作空间上下文感知](./integration/workspace-context.md) | integration | ✅ 已完成 |
| 2026-06-27 | [多会话管理系统 v2](./session/v2-multi-session-design.md) | session | ✅ 已完成（被 v3 取代） |
| 2026-06-29 | [v3 事件总线架构重构](./session/v3-event-bus-architecture.md) | session | ✅ 已完成（当前架构） |

---

## 按模块

### session/（会话与核心架构）

| 蓝图 | 版本 | 摘要 |
|---|---|---|
| [v3 事件总线架构](./session/v3-event-bus-architecture.md) | v3.11.0 | 引入 MessageBus 作为唯一跨组件通信层，每会话独立 SessionRuntime 聚合根，SessionOrchestrator 统一协调 |
| [v2 多会话管理](./session/v2-multi-session-design.md) | v3.9.0 | 前后台分离 + 5 个 Manager，解决"切换会话 = 销毁 Worker"问题。后被 v3 事件总线取代 |

### integration/（集成与感知）

| 蓝图 | 版本 | 摘要 |
|---|---|---|
| [工作空间上下文感知](./integration/workspace-context.md) | v3.4 | ContextService 单一真相源，三条链路（收集 / 注入 / 解析）实现 Agent 感知工作目录与打开文件 |

---

## 蓝图文件标准

所有蓝图文件遵循统一结构：

1. **状态标记**：✅ 已完成 / 🔄 实施中 / 📋 待实施 / ❌ 已废弃
2. **问题背景**：描述要解决的问题和根因
3. **最终方案**：选定的设计决策和架构
4. **排除的替代方案**：被排除的方案及原因（Decision Log 核心价值）
5. **影响范围**：涉及的文件、新增/修改/删除
6. **关联蓝图**：前置 / 后继蓝图的交叉引用

## 源文档映射

| 蓝图 | 来源 |
|---|---|
| v3 事件总线架构 | `.trae/documents/v3-rewrite-plan.md` |
| v2 多会话管理 | `.trae/documents/multi-session-rewrite-v2.md` |
| 工作空间上下文 | `.trae/documents/workspace_context_design.md` |
