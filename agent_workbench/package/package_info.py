"""agent_workbench/package/package_info.py — Package 运行时信息。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agent_workbench.package.manifest import PackageManifest


@dataclass
class PackageInfo:
    """已加载 Package 的运行时信息。"""

    manifest: PackageManifest
    loaded_at: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    capabilities: dict[str, Any] = field(default_factory=dict)
    view_schema: dict[str, Any] = field(default_factory=dict)
    runtime: dict[str, Any] = field(default_factory=dict)
