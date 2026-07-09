"""agent_workbench/package/registry.py — Package 生命周期注册表。

职责：
- 提供 discover / load / unload / reload / list 生命周期接口。
- discover 阶段只扫描 manifest，不加载包内资源。
- load 阶段读取 manifest 指向的 metadata / capabilities / view_schema / runtime 文件。
- reload 接口先冻结，当前抛 NotImplementedError。

设计约束：
- 不依赖 Qt / Workbench / Runtime。
- Package 无权注册 Renderer。
"""
from __future__ import annotations

import json
import os
import time

from agent_workbench.package.exceptions import PackageValidationError
from agent_workbench.package.loader import PackageLoader
from agent_workbench.package.manifest import PackageManifest
from agent_workbench.package.package_info import PackageInfo


class PackageRegistry:
    """Package 生命周期注册表。"""

    def __init__(self, packages_dir: str | None = None) -> None:
        self._packages_dir = packages_dir
        self._packages: dict[str, PackageInfo] = {}

    def discover(self, packages_dir: str | None = None) -> list[PackageManifest]:
        """扫描 packages 目录并返回所有合法 manifest。"""
        target_dir = packages_dir or self._packages_dir
        if target_dir is None:
            raise PackageValidationError("packages_dir is required")
        return PackageLoader(target_dir).scan()

    def load(self, manifest: PackageManifest) -> PackageInfo:
        """加载单个 Package 并注册。"""
        info = PackageInfo(
            manifest=manifest,
            loaded_at=time.time(),
            metadata=self._load_json(manifest.package_dir, manifest.metadata),
            capabilities=self._load_json(manifest.package_dir, manifest.capabilities),
            view_schema=self._load_json(manifest.package_dir, manifest.view_schema),
            runtime=self._load_json(manifest.package_dir, manifest.runtime),
        )
        self._packages[manifest.id] = info
        return info

    def unload(self, package_id: str) -> None:
        """卸载指定 Package。"""
        self._packages.pop(package_id, None)

    def reload(self, package_id: str) -> PackageInfo:
        """重新加载 Package（接口先冻结）。"""
        raise NotImplementedError("PackageRegistry.reload() is not implemented yet")

    def list(self) -> list[PackageInfo]:
        """返回所有已加载 Package 信息。"""
        return list(self._packages.values())

    def get(self, package_id: str) -> PackageInfo | None:
        """按 ID 获取已加载 Package 信息。"""
        return self._packages.get(package_id)

    @staticmethod
    def _load_json(package_dir: str, filename: str) -> dict:
        """加载包内 JSON 文件；文件不存在或解析失败时返回空字典。"""
        path = os.path.join(package_dir, filename)
        if not os.path.isfile(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}
