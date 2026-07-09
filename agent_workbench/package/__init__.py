"""agent_workbench/package — Agent Package 发现与加载层。

设计约束：
- 本层不依赖 Qt。
- Package 通过 manifest.json 自描述，Loader 只负责扫描与解析契约。
- 具体 Renderer 属于 Workbench，Package 无权注册。
"""
from __future__ import annotations

from agent_workbench.package.exceptions import PackageValidationError
from agent_workbench.package.integration import PackageIntegration
from agent_workbench.package.loader import PackageLoader
from agent_workbench.package.manifest import PackageManifest
from agent_workbench.package.package_info import PackageInfo
from agent_workbench.package.registry import PackageRegistry


__all__ = [
    "PackageInfo",
    "PackageIntegration",
    "PackageLoader",
    "PackageManifest",
    "PackageRegistry",
    "PackageValidationError",
]
