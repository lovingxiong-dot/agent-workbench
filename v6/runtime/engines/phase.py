"""v6/runtime/engines/phase.py — PhaseEngine：阶段定义、流转、Checkpoint、插件扩展。

设计来源：V4 agent_engine/engines/phase_engine.py（提取核心逻辑）。

职责：读取 ctx.mode / ctx.phase，写回 ctx.phase。
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional

from v6.runtime.engines.interfaces import IPhaseEngine


class PhaseEngine(IPhaseEngine):
    """阶段引擎：Mode-Phase 矩阵管理。"""

    _DEFAULTS = {
        "ask": ["analyze", "archive"],
        "plan": ["analyze", "confirm", "archive"],
        "craft": ["analyze", "confirm", "execute", "verify", "archive"],
    }

    def __init__(self, config: Optional[Dict] = None) -> None:
        self._definitions: Dict[str, List[str]] = dict(self._DEFAULTS)
        if config:
            for mode, phases in config.get("definitions", {}).items():
                self._definitions[mode] = list(phases)
        self._plugins: Dict[str, List[Callable]] = {}

    async def run(self, ctx: "RuntimeContext") -> "RuntimeContext":
        """推进阶段：读取 ctx.mode / ctx.phase，写回 ctx.phase。"""
        mode = ctx.mode or "ask"
        current = ctx.phase or ""
        phases = self._definitions.get(mode, [])

        if not current and phases:
            ctx.phase = phases[0]
        else:
            next_phase = self.next(mode, current)
            if next_phase is not None:
                ctx.phase = next_phase

        self.enter(ctx.phase)
        return ctx

    def define(self, mode: str, phases: List[str]) -> None:
        """定义某个 Mode 的 Phase 流程。"""
        self._definitions[mode] = list(phases)

    def next(self, mode: str, current_phase: str) -> Optional[str]:
        """获取下一个 Phase。"""
        phases = self._definitions.get(mode, [])
        try:
            idx = phases.index(current_phase)
            return phases[idx + 1] if idx + 1 < len(phases) else None
        except ValueError:
            return None

    def add_plugin(self, phase_name: str, plugin: Callable) -> None:
        """注册 Phase 插件（扩展点）。"""
        if phase_name not in self._plugins:
            self._plugins[phase_name] = []
        self._plugins[phase_name].append(plugin)

    def validate(self, phase: str, can_proceed: bool) -> bool:
        """硬 checkpoint：can_proceed 必须为 True 才能推进。"""
        return can_proceed

    def enter(self, phase: str) -> None:
        """进入 Phase 时触发所有已注册插件。"""
        for plugin in self._plugins.get(phase, []):
            try:
                plugin()
            except Exception:
                pass

    def is_terminal(self, mode: str, phase: str) -> bool:
        """判断当前 Phase 是否为终止节点。"""
        return self.next(mode, phase) is None
