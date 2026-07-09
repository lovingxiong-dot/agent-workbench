"""agent_workbench/package/executor.py — Package Action 执行器。

职责：
- 接收 PackageInfo 与 action_id，执行 Package 声明的动作。
- 优先调用 Package 目录下的 `starter_agent.py` 自定义执行逻辑。
- 无自定义逻辑时，使用内置默认实现更新运行时统计。
- 返回结构化结果，供 Controller / Runtime / UI 消费。

设计约束：
- 不依赖 Qt / UI。
- 不直接操作文件系统（统计更新保存在内存中的 PackageInfo 里）。
- 动态加载 Package 脚本时捕获所有异常，防止恶意/错误脚本破坏 Runtime。
"""
from __future__ import annotations

import importlib.util
import os
import time
from typing import Any

from agent_workbench.package.package_info import PackageInfo


class PackageExecutor:
    """Package Action 执行器。

    执行优先级：
    1. 若 package 目录存在 `starter_agent.py` 且定义了 `execute(...)` 函数，则调用该函数。
    2. 否则使用内置默认实现：递增 `execution_count` 统计。

    未来可通过 action_id 分发到具体 handler，或读取 package.runtime 配置
    调用外部脚本/服务。
    """

    def execute(self, package: PackageInfo, action_id: str) -> dict[str, Any]:
        """执行指定 Package 的 action 并更新运行时统计。"""
        if package is None or not action_id:
            return {"status": "failed", "error": "missing package or action_id"}

        custom_result = self._try_custom_execute(package, action_id)
        if custom_result is not None:
            return custom_result

        return self._default_execute(package, action_id)

    def _try_custom_execute(self, package: PackageInfo, action_id: str) -> dict[str, Any] | None:
        """尝试调用 package 目录下的 starter_agent.py 自定义执行逻辑。"""
        package_dir = package.manifest.package_dir
        if not package_dir:
            return None

        module_path = os.path.join(package_dir, "starter_agent.py")
        if not os.path.isfile(module_path):
            return None

        try:
            spec = importlib.util.spec_from_file_location(
                f"starter_agent_{package.manifest.id}", module_path
            )
            if spec is None or spec.loader is None:
                return None
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            execute_fn = getattr(module, "execute", None)
            if callable(execute_fn):
                return execute_fn(package.metadata, action_id, {})
        except Exception as exc:  # pragma: no cover - defensive boundary
            return {"status": "failed", "error": f"custom execute failed: {exc}"}
        return None

    def _default_execute(self, package: PackageInfo, action_id: str) -> dict[str, Any]:
        """内置默认执行逻辑：将 execution_count 统计值 +1。"""
        meta = package.metadata
        if not isinstance(meta, dict):
            meta = {}
            package.metadata = meta

        statistics = meta.get("statistics", [])
        if not isinstance(statistics, list):
            statistics = []

        stat_map = {stat.get("id", ""): stat for stat in statistics if isinstance(stat, dict)}
        execution_count_stat = stat_map.get("execution_count")
        if execution_count_stat is None:
            execution_count_stat = {
                "id": "execution_count",
                "name": "Executions",
                "value": 0,
                "unit": "times",
            }
            statistics.append(execution_count_stat)
            stat_map["execution_count"] = execution_count_stat

        try:
            execution_count_stat["value"] = int(execution_count_stat.get("value", 0)) + 1
        except (ValueError, TypeError):
            execution_count_stat["value"] = 1

        meta["statistics"] = statistics

        return {
            "status": "completed",
            "package_id": package.manifest.id,
            "action_id": action_id,
            "execution_count": execution_count_stat["value"],
            "timestamp": time.time(),
        }
