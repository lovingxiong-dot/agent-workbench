"""packages/starter_agent/starter_agent.py — Starter Agent 执行逻辑。

约束：
- 不依赖 Qt 或任何 Workbench 内部实现。
- 只接收并返回基础 Python 数据结构（dict / list / str / int）。
- 可读写 package_info["metadata"]["statistics"] 以更新运行时统计。
- 异常由上层 PackageExecutor 捕获，不会破坏 Workbench Runtime。
"""
from __future__ import annotations

from typing import Any


def execute(package_info: dict[str, Any], action_id: str, context: dict[str, Any]) -> dict[str, Any]:
    """执行 Starter Agent action。

    Args:
        package_info: Package 的 metadata 字典（即 PackageInfo.metadata）。
        action_id: 被触发的 action 标识，例如 "execute"。
        context: 运行时上下文，当前版本为空字典，未来可传入 session_id、task_id 等。

    Returns:
        结构化执行结果，必须包含 "status" 字段。
    """
    if action_id != "execute":
        return {"status": "failed", "error": f"unsupported action: {action_id}"}

    if not isinstance(package_info, dict):
        return {"status": "failed", "error": "invalid package_info"}

    statistics = package_info.get("statistics", [])
    if not isinstance(statistics, list):
        statistics = []

    execution_count = 1
    for stat in statistics:
        if isinstance(stat, dict) and stat.get("id") == "execution_count":
            try:
                execution_count = int(stat.get("value", 0)) + 1
            except (ValueError, TypeError):
                execution_count = 1
            stat["value"] = execution_count
            break
    else:
        statistics.append({
            "id": "execution_count",
            "name": "Executions",
            "value": execution_count,
            "unit": "times",
        })

    package_info["statistics"] = statistics

    return {
        "status": "completed",
        "message": "Task executed successfully.",
        "action_id": action_id,
        "execution_count": execution_count,
    }
