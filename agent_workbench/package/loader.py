"""agent_workbench/package/loader.py — Package 发现扫描器。

职责：
- 扫描 packages/ 目录，只读取包含 manifest.json 的子目录。
- 将 manifest.json 解析为 PackageManifest。
- 非法 manifest 不影响其他包的发现。

设计约束：
- 不依赖 Qt / Workbench / Runtime。
- 不加载包内其他资源（capabilities.json / view_schema.json / runtime.json 等）。
"""
from __future__ import annotations

import os

from agent_workbench.package.exceptions import PackageValidationError
from agent_workbench.package.manifest import PackageManifest


class PackageLoader:
    """Agent Package 发现扫描器。"""

    def __init__(self, packages_dir: str) -> None:
        self._packages_dir = packages_dir

    def scan(self) -> list[PackageManifest]:
        """扫描 packages 目录，返回所有合法 manifest 列表。

        仅当子目录包含 manifest.json 时才尝试解析；无 manifest 的目录直接忽略。
        非法 manifest 会被跳过并继续扫描其他目录（调用方可选择是否记录日志）。
        """
        manifests: list[PackageManifest] = []
        if not os.path.isdir(self._packages_dir):
            return manifests

        for entry in os.listdir(self._packages_dir):
            package_dir = os.path.join(self._packages_dir, entry)
            if not os.path.isdir(package_dir):
                continue

            manifest_path = os.path.join(package_dir, "manifest.json")
            if not os.path.isfile(manifest_path):
                continue

            try:
                manifest = PackageManifest.from_file(package_dir)
            except PackageValidationError:
                # 非法 manifest 不影响其他包；未来可接入日志。
                continue

            manifests.append(manifest)

        return manifests
