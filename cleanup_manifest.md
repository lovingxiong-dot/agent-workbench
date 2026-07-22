# Pre-AISE Stabilization Cleanup Manifest

**执行时间**: 2026-07-20  
**执行分支**: v6-agent  
**目标**: 清除 Project Tree 中已无引用的历史资产，建立 AISE 接管前的安全边界

---

## 清理原则

1. Git History 已完整保存演进路线，不依赖工作区目录保留
2. 当前目录只保留 Active Development Context
3. 使用 `git mv` 保持 Git 可追踪性
4. 不影响 v6.14 当前运行链路

---

## 三层分类

| Layer | 说明 | 操作 |
|-------|------|------|
| A: Active Product | `agent_workbench/`, `packages/`, `tests/`, `docs/`, `scripts/` | 保留 |
| B: Active Dependency | `v6/` — Runtime Foundation Layer, 100+ imports | 保留 + 标记 migration_pending |
| C: Legacy Archive | 0 active references 的历史资产 | 移入 `_archive/` |

---

## 已归档 Legacy 代码

| 源路径 | 归档路径 | 类型 | 说明 |
|--------|---------|------|------|
| `v5/` | `_archive/v5/` | Legacy UI | Phase-Driven Workflow Engine, PySide6 UI (v5.x) |
| `agent_engine/` | `_archive/agent_engine/` | Legacy Engine | 旧版 Agent 编排引擎 (v3.x-v5.x) |
| `workers/` | `_archive/workers/` | Legacy Worker | 旧版 Worker 线程池 (v3.x-v5.x) |
| `services/` | `_archive/old_services/` | Legacy Service | 根级旧服务层 (v3.x-v5.x) |
| `tools/` | `_archive/old_tools/` | Legacy Tool | 旧工具函数 (v3.x-v5.x) |
| `core/` | `_archive/old_core/` | Legacy Core | 旧事件总线 (v3.x-v5.x) |

## 已归档旧版测试

| 源路径 | 归档路径 | 绑定架构 |
|--------|---------|---------|
| `tests/test_v5_smoke.py` | `_archive/legacy_tests/` | v5 |
| `tests/test_v5_chat_area.py` | `_archive/legacy_tests/` | v5 |
| `tests/test_v5_service.py` | `_archive/legacy_tests/` | v5 |
| `tests/test_v5_integration.py` | `_archive/legacy_tests/` | v5 |
| `tests/test_v5_adapter.py` | `_archive/legacy_tests/` | v5 |
| `tests/test_v5_controller.py` | `_archive/legacy_tests/` | v5 |
| `tests/test_agent_worker.py` | `_archive/legacy_tests/` | agent_engine, workers |
| `tests/test_agent_session_room.py` | `_archive/legacy_tests/` | agent_engine |
| `tests/test_agent_session_integration.py` | `_archive/legacy_tests/` | agent_engine |
| `tests/test_async_tools.py` | `_archive/legacy_tests/` | agent_engine |
| `tests/test_memory_manager.py` | `_archive/legacy_tests/` | agent_engine |
| `tests/test_orchestrator_phase.py` | `_archive/legacy_tests/` | agent_engine |
| `tests/test_tool_gateway.py` | `_archive/legacy_tests/` | agent_engine |
| `tests/test_phase_manager.py` | `_archive/legacy_tests/` | agent_engine |
| `tests/test_task_service_terminal.py` | `_archive/legacy_tests/` | workers |
| `tests/test_threading_baseline.py` | `_archive/legacy_tests/` | workers |
| `tests/integration_test_deepseek_metrics.py` | `_archive/legacy_tests/` | agent_engine |

## 已清理 Build Artifacts

| 路径 | 操作 | 说明 |
|------|------|------|
| `build/` | 删除 | PyInstaller 构建缓存，重建时自动生成 |
| `dist/AgentWorkbench/storage/` | 删除 | 运行时残留文件 |
| `assets/app.ico` | 删除 | 重复图标，保留 `agent_workbench/resources/app_icon.ico` |
| `assets/` | 删除 | 目录已空 |

## Active Dependency 标记

| 路径 | 角色 | 标记文件 |
|------|------|---------|
| `v6/` | Runtime Foundation Layer | `v6/.migration-status.json` |

```json
{
  "status": "active_dependency",
  "role": "runtime_foundation",
  "owner": "agent_workbench",
  "migration_target": "aos-runtime",
  "archive_allowed": false
}
```

## 保留的 Active Tests

- `tests/v6/` — v6 Runtime 测试
- `tests/ui/` — UI 测试
- `tests/runtime/` — Runtime 测试
- `tests/integration/` — 集成测试
- `tests/metadata/` — Metadata 测试
- `tests/package/` — Package 测试
- `tests/conversation/` — Conversation 测试
- `tests/feedback/` — Feedback 测试
- `tests/interaction/` — Interaction 测试
- `tests/test_agent_workbench.py` — 主测试
- `tests/test_manager.py` — Manager 测试
- `tests/conftest.py` — 测试配置

## 清理后目录结构

```
agent_workbench/
├── agent_workbench/          ← Active Product
├── v6/                       ← Active Runtime Dependency [migration_pending]
├── packages/                 ← Agent Packages
├── tests/                    ← 仅活跃测试
├── docs/                     ← 文档
├── scripts/                  ← 构建脚本
├── _archive/                 ← 历史归档（不被扫描）
│   ├── v5/
│   ├── agent_engine/
│   ├── workers/
│   ├── old_services/
│   ├── old_tools/
│   ├── old_core/
│   └── legacy_tests/
├── dist/AgentWorkbench/      ← 当前构建产物
├── PROJECT_BLUEPRINT.md
├── PROJECT_LINEAGE.md
├── CHANGELOG.md
└── README.md
```