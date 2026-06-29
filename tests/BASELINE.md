# Test Baseline

## v3 Rewrite Start (2026-06-29)

Command: `.\venv\Scripts\python.exe -m pytest tests/ -q --tb=short`

Result: **177 passed, 9 failed**

### Known Failures at Baseline

| Test File | Failure Count | Reason |
|---|---|---|
| `tests/test_main_window_mode_agnostic_result.py` | 5 | `MainWindow` 缺少 `_session_mgr` 属性（绞杀者模式尚未完成） |
| `tests/test_session_orchestrator.py` | 4 | `SessionOrchestrator.create_runtime` 错误传入 `parent=self`，`SessionRuntime` 不接受该参数 |

### Notes

- 测试运行在项目虚拟环境 `venv` 中。
- 基线用于评估 v3 重构对现有测试的影响。
- 目标：重构完成后全部测试通过（包括新增测试）。
