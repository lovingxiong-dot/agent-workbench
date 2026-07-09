"""agent_workbench/runtime/config_store.py — Agent Workbench V6 统一配置存储。

设计原则：
- YAML 是唯一配置源（Source of Truth）。
- 内存 Runtime Cache 只用于运行时加速读取。
- 支持点分路径 get/set/delete。
- 按 namespace 发布变更通知，供 RuntimeModule 热更新。
- 配置属于资源文件，便于 Git diff 和 Profile 导入导出。
"""
from __future__ import annotations

import copy
import os
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml
from PySide6.QtCore import QObject, Signal


class _ConfigStoreSignals(QObject):
    """ConfigStore 的通用变更信号容器。"""

    changed = Signal(str, object)  # path, value


class ConfigStore:
    """Agent Workbench 统一配置存储。

    Args:
        config_path: YAML 配置文件路径；默认使用项目目录下的 config/default.yaml。
    """

    def __init__(self, config_path: str | os.PathLike | None = None) -> None:
        self._config_path = self._resolve_path(config_path)
        self._data: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._subscribers: Dict[str, List[Callable[[str, Any], None]]] = {}
        self._signals = _ConfigStoreSignals()
        self.changed = self._signals.changed
        self._load()

    @property
    def config_path(self) -> Path:
        """当前 YAML 配置文件路径。"""
        return self._config_path

    def get(self, path: str, default: Any = None) -> Any:
        """按点分路径读取配置，例如 'model.sampling.temperature'。"""
        if path == "":
            return self.snapshot()
        with self._lock:
            value: Any = self._data
            for key in path.split("."):
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            return copy.deepcopy(value)

    def set(self, path: str, value: Any, persist: bool = True) -> None:
        """按点分路径写入配置，可选立即持久化到 YAML。"""
        with self._lock:
            keys = path.split(".")
            target = self._data
            for key in keys[:-1]:
                if key not in target or not isinstance(target[key], dict):
                    target[key] = {}
                target = target[key]
            old_value = target.get(keys[-1])
            target[keys[-1]] = copy.deepcopy(value)

        namespace = keys[0]
        self._notify(namespace, path)

        if persist:
            self._save()

    def delete(self, path: str, persist: bool = True) -> bool:
        """按点分路径删除配置项；不存在返回 False。"""
        with self._lock:
            keys = path.split(".")
            target = self._data
            for key in keys[:-1]:
                if not isinstance(target, dict) or key not in target:
                    return False
                target = target[key]
            if not isinstance(target, dict) or keys[-1] not in target:
                return False
            del target[keys[-1]]

        namespace = keys[0]
        self._notify(namespace, path)

        if persist:
            self._save()
        return True

    def snapshot(self) -> Dict[str, Any]:
        """返回当前完整配置的深拷贝。"""
        with self._lock:
            return copy.deepcopy(self._data)

    def replace(self, data: Dict[str, Any], persist: bool = True) -> None:
        """整体替换配置（用于 Profile 切换）。"""
        with self._lock:
            self._data = copy.deepcopy(data)

        for namespace in list(self._subscribers.keys()):
            self._notify(namespace, namespace)

        if persist:
            self._save()

    def subscribe(self, namespace: str, callback: Callable[[str, Any], None]) -> None:
        """订阅某个 namespace 的变更通知。"""
        with self._lock:
            self._subscribers.setdefault(namespace, []).append(callback)

    def unsubscribe(self, namespace: str, callback: Callable[[str, Any], None]) -> None:
        """取消订阅。"""
        with self._lock:
            if namespace in self._subscribers:
                self._subscribers[namespace] = [
                    cb for cb in self._subscribers[namespace] if cb is not callback
                ]

    def namespaces(self) -> List[str]:
        """返回当前配置的所有顶层 namespace。"""
        with self._lock:
            return list(self._data.keys())

    def _load(self) -> None:
        """从 YAML 加载配置；文件不存在时初始化为空。"""
        if not self._config_path.exists():
            self._data = {}
            return

        with self._config_path.open("r", encoding="utf-8") as fh:
            loaded = yaml.safe_load(fh)
            self._data = loaded if isinstance(loaded, dict) else {}

    def _save(self) -> None:
        """持久化到 YAML。"""
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with self._config_path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(self.snapshot(), fh, allow_unicode=True, sort_keys=False)

    def _notify(self, namespace: str, path: str) -> None:
        """通知 namespace 订阅者，并发出通用 changed 信号。"""
        with self._lock:
            callbacks = list(self._subscribers.get(namespace, []))
        value = self.get(path)
        self._signals.changed.emit(path, value)
        for callback in callbacks:
            try:
                callback(path, value)
            except Exception:  # pragma: no cover - defensive
                pass

    @staticmethod
    def _resolve_path(config_path: str | os.PathLike | None) -> Path:
        if config_path is not None:
            return Path(config_path)

        # 默认：agent_workbench/config/default.yaml
        here = Path(__file__).resolve().parent.parent
        default = here / "config" / "default.yaml"
        return default
