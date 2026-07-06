"""v6/runtime/engine_manager.py — Engine 注册与获取管理器。

设计来源：Runtime Kernel 演进方向。

目的：
- 不让 Runtime 直接 new Engine，统一通过注册或工厂获取。
- 为后续多 Engine、动态替换、Mock 测试、分布式执行预留扩展点。
- 当前阶段内部可返回单例或简单占位实现，保持接口稳定。

使用方式：
    manager = EngineManager()
    manager.register("inference", inference_engine)
    engine = manager.get("inference")
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Protocol


class Engine(Protocol):
    """Engine 最小协议：接收 RuntimeContext 并修改自己负责的字段。"""

    def run(self, ctx: Any) -> None:
        ...


class EngineManager:
    """Engine 注册表。"""

    def __init__(self) -> None:
        self._engines: Dict[str, Engine] = {}

    def register(self, name: str, engine: Engine) -> None:
        """注册一个 Engine 实例。"""
        self._engines[name] = engine

    def get(self, name: str) -> Optional[Engine]:
        """获取指定 Engine；未注册返回 None。"""
        return self._engines.get(name)

    def has(self, name: str) -> bool:
        """判断 Engine 是否已注册。"""
        return name in self._engines

    def names(self) -> list[str]:
        """返回所有已注册 Engine 名称。"""
        return list(self._engines.keys())

    def unregister(self, name: str) -> bool:
        """注销指定 Engine；成功返回 True。"""
        if name in self._engines:
            del self._engines[name]
            return True
        return False

    def clear(self) -> None:
        """清空所有注册。"""
        self._engines.clear()
