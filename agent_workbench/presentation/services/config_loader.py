"""presentation/services/config_loader.py — Workbench Local Config Loader。

v6.10.0-alpha local config support。

职责：
  - 合并 default.yaml + config.local.yaml (gitignored)
  - 提供 Runtime ConfigStore 可消费的合并数据
  - 不修改 Runtime ConfigStore / default.yaml

边界：
  - ConfigStore (Runtime frozen) 保留 single-YAML 行为
  - Workbench 通过 init_with_local_override() 在 Runtime 启动前合并
  - config.local.yaml 可包含真实 API Key（gitignored）

用法：
    merged_path = WorkbenchLocalConfigLoader.merge_to_temp(
        default_yaml=Path("agent_workbench/config/default.yaml"),
        local_yaml=Path("agent_workbench/config/config.local.yaml"),
    )
    controller = WorkbenchController(config_path=merged_path)
"""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class WorkbenchLocalConfigLoader:
    """Workbench local config 合并器（v6-agent 层）。"""

    DEFAULT_YAML_NAME = "default.yaml"
    LOCAL_YAML_NAME = "config.local.yaml"
    PROJECT_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"

    @classmethod
    def find_default_yaml(cls) -> Path:
        """定位默认 YAML。"""
        return cls.PROJECT_CONFIG_DIR / cls.DEFAULT_YAML_NAME

    @classmethod
    def find_local_yaml(cls) -> Optional[Path]:
        """定位 local YAML（不存在返回 None）。"""
        path = cls.PROJECT_CONFIG_DIR / cls.LOCAL_YAML_NAME
        return path if path.exists() else None

    @classmethod
    def merge(cls, default: Dict[str, Any], local: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并两个 dict（local 覆盖 default）。

        Args:
            default: default.yaml 内容。
            local: config.local.yaml 内容（更高优先级）。

        Returns:
            合并后的 dict。
        """
        result = cls._deep_copy(default)
        for key, value in local.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = cls.merge(result[key], value)
            else:
                result[key] = value
        return result

    @classmethod
    def merge_to_temp(
        cls,
        default_yaml: Optional[Path] = None,
        local_yaml: Optional[Path] = None,
    ) -> Path:
        """合并 default + local 到临时 YAML 文件，返回路径。

        Args:
            default_yaml: 默认配置路径（默认查找项目内 default.yaml）。
            local_yaml: local 配置路径（默认查找项目内 config.local.yaml）。

        Returns:
            临时合并 YAML 路径。
        """
        default_yaml = default_yaml or cls.find_default_yaml()
        local_yaml = local_yaml or cls.find_local_yaml()

        default_data: Dict[str, Any] = {}
        if default_yaml.exists():
            with default_yaml.open("r", encoding="utf-8") as fh:
                loaded = yaml.safe_load(fh)
                if isinstance(loaded, dict):
                    default_data = loaded

        if local_yaml is None or not local_yaml.exists():
            # 没有 local override，直接返回 default.yaml
            return default_yaml

        with local_yaml.open("r", encoding="utf-8") as fh:
            local_data = yaml.safe_load(fh) or {}
            if not isinstance(local_data, dict):
                local_data = {}

        merged = cls.merge(default_data, local_data)

        # 写入临时文件
        temp_dir = Path(tempfile.gettempdir()) / "agent_workbench_local"
        temp_dir.mkdir(parents=True, exist_ok=True)
        merged_path = temp_dir / f"merged_{os.getpid()}.yaml"
        with merged_path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(merged, fh, allow_unicode=True, sort_keys=False)

        return merged_path

    @staticmethod
    def _deep_copy(data: Any) -> Any:
        """深拷贝。"""
        if isinstance(data, dict):
            return {k: WorkbenchLocalConfigLoader._deep_copy(v) for k, v in data.items()}
        if isinstance(data, list):
            return [WorkbenchLocalConfigLoader._deep_copy(v) for v in data]
        return data