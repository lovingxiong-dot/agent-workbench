"""agent_workbench/package/manifest.py — Package Manifest 定义与解析。

职责：
- 定义 PackageManifest 数据契约。
- 提供 from_dict / from_file 工厂方法。
- 校验必填字段与 schema_version。

设计约束：
- 不依赖 Qt / Workbench / Runtime。
- manifest.json 是 Package 唯一入口。
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from agent_workbench.package.exceptions import PackageValidationError


SUPPORTED_SCHEMA_VERSIONS = {"1.0"}


@dataclass
class PackageManifest:
    """Agent Package 的 manifest 契约。

    manifest.json 是 Package 唯一入口，Loader 只读取此文件决定是否继续加载。
    """

    id: str
    version: str
    schema_version: str
    package_dir: str
    metadata: str = "metadata.json"
    capabilities: str = "capabilities.json"
    view_schema: str = "view_schema.json"
    runtime: str = "runtime.json"

    @classmethod
    def from_file(cls, package_dir: str) -> "PackageManifest":
        """从 package_dir/manifest.json 解析 manifest。"""
        manifest_path = os.path.join(package_dir, "manifest.json")
        if not os.path.isfile(manifest_path):
            raise PackageValidationError(f"manifest.json not found in {package_dir}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as exc:
                raise PackageValidationError(f"invalid JSON in {manifest_path}: {exc}") from exc

        return cls.from_dict(data, package_dir)

    @classmethod
    def from_dict(cls, data: dict[str, Any], package_dir: str) -> "PackageManifest":
        """从字典构造并校验 manifest。"""
        if not isinstance(data, dict):
            raise PackageValidationError("manifest must be a JSON object")

        required = ("id", "version", "schema_version")
        missing = [key for key in required if key not in data or not data[key]]
        if missing:
            raise PackageValidationError(f"missing required fields: {', '.join(missing)}")

        schema_version = str(data["schema_version"])
        if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
            raise PackageValidationError(
                f"unsupported schema_version: {schema_version}; supported: {SUPPORTED_SCHEMA_VERSIONS}"
            )

        return cls(
            id=str(data["id"]),
            version=str(data["version"]),
            schema_version=schema_version,
            package_dir=package_dir,
            metadata=str(data.get("metadata", "metadata.json")),
            capabilities=str(data.get("capabilities", "capabilities.json")),
            view_schema=str(data.get("view_schema", "view_schema.json")),
            runtime=str(data.get("runtime", "runtime.json")),
        )
