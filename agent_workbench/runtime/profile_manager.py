"""agent_workbench/runtime/profile_manager.py — Agent Workbench V6 Profile 管理。

职责：
- Profile 切换、导入、导出、合并。
- 不直接操作 YAML，而是通过 ConfigStore 读写当前配置。
- Profile 文件本身也是 YAML，便于 Git diff 和手动编辑。
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from agent_workbench.runtime.config_store import ConfigStore


class ProfileManager:
    """管理 Agent Workbench 的配置 Profile。"""

    def __init__(self, store: ConfigStore) -> None:
        self._store = store
        self._profiles_dir = self._store.config_path.parent.parent / "profiles"

    @property
    def current(self) -> str:
        """当前激活的 profile 名称。"""
        return self._store.get("profile.current", "default")

    def list_profiles(self) -> List[Dict[str, Any]]:
        """返回所有已注册 profile 的元信息列表。"""
        return self._store.get("profile.profiles", [])

    def switch(self, name: str) -> bool:
        """切换到指定 profile；不存在返回 False。"""
        profiles = {p["name"]: p for p in self.list_profiles() if "name" in p}
        if name not in profiles:
            return False

        profile_path = Path(profiles[name]["path"])
        if not profile_path.is_absolute():
            profile_path = self._profiles_dir / profile_path

        if not profile_path.exists():
            return False

        with profile_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}

        # 保留 profile 元信息，替换其余配置
        merged = copy.deepcopy(data)
        merged["profile"] = {
            "current": name,
            "profiles": self.list_profiles(),
        }
        self._store.replace(merged)
        return True

    def export_to(self, name: str, path: Optional[str | Path] = None) -> Path:
        """将当前配置导出为指定 profile 文件。"""
        if path is None:
            path = self._profiles_dir / f"{name}.yaml"
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = self._store.snapshot()
        # 导出时不包含 profile.current 指向自己的循环信息
        data["profile"] = {
            "current": name,
            "profiles": self.list_profiles(),
        }

        with path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False)

        self._register_profile(name, path)
        return path

    def import_from(self, path: str | Path) -> Optional[str]:
        """从外部 YAML 文件导入为新 profile；返回 profile 名称。"""
        path = Path(path)
        if not path.exists():
            return None

        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}

        name = data.get("agent", {}).get("name") or path.stem
        target_path = self._profiles_dir / f"{name}.yaml"
        target_path.parent.mkdir(parents=True, exist_ok=True)

        with target_path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False)

        self._register_profile(name, target_path)
        return name

    def merge(self, path: str | Path) -> bool:
        """将外部 YAML 文件合并到当前配置（不深覆盖 profile 元信息）。"""
        path = Path(path)
        if not path.exists():
            return False

        with path.open("r", encoding="utf-8") as fh:
            override = yaml.safe_load(fh) or {}

        current = self._store.snapshot()
        merged = self._deep_merge(copy.deepcopy(current), override)
        # 保留当前 profile 元信息
        merged["profile"] = current.get("profile", {})
        self._store.replace(merged)
        return True

    def _register_profile(self, name: str, path: str | Path) -> None:
        """将 profile 注册到当前配置列表。"""
        profiles = self.list_profiles()
        normalized_path = str(Path(path).resolve())

        for p in profiles:
            if p.get("name") == name:
                p["path"] = normalized_path
                self._store.set("profile.profiles", profiles)
                return

        profiles.append({"name": name, "path": normalized_path})
        self._store.set("profile.profiles", profiles)

    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并两个字典；override 优先。"""
        for key, value in override.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                ProfileManager._deep_merge(base[key], value)
            else:
                base[key] = copy.deepcopy(value)
        return base
