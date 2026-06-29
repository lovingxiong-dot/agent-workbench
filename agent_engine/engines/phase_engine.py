"""
Phase Engine — 阶段定义、流转、Checkpoint、插件扩展

从 PhaseManager 提取。默认定义：
  ask   → analyze → archive
  plan  → analyze → confirm → archive
  craft → analyze → confirm → execute → verify → archive
"""
from typing import Callable, Dict, List, Optional
from .interfaces import IPhaseEngine


class PhaseEngine(IPhaseEngine):
    """阶段引擎：Mode-Phase 矩阵管理"""

    _DEFAULTS = {
        "ask": ["analyze", "archive"],
        "plan": ["analyze", "confirm", "archive"],
        "craft": ["analyze", "confirm", "execute", "verify", "archive"],
    }

    def __init__(self, config: Optional[Dict] = None):
        self._definitions: Dict[str, List[str]] = dict(self._DEFAULTS)
        if config:
            for mode, phases in config.get("definitions", {}).items():
                self._definitions[mode] = phases
        self._plugins: Dict[str, List[Callable]] = {}

    def define(self, mode: str, phases: List[str]) -> None:
        self._definitions[mode] = list(phases)

    def next(self, mode: str, current_phase: str) -> Optional[str]:
        phases = self._definitions.get(mode, [])
        try:
            idx = phases.index(current_phase)
            return phases[idx + 1] if idx + 1 < len(phases) else None
        except ValueError:
            return None

    def add_plugin(self, phase_name: str, plugin: Callable) -> None:
        if phase_name not in self._plugins:
            self._plugins[phase_name] = []
        self._plugins[phase_name].append(plugin)

    def validate(self, phase: str, can_proceed: bool) -> bool:
        """硬 checkpoint：can_proceed 必须为 True 才能推进"""
        return can_proceed

    def enter(self, phase: str) -> None:
        """进入 Phase 时触发所有已注册插件"""
        for plugin in self._plugins.get(phase, []):
            try:
                plugin()
            except Exception:
                pass

    def is_terminal(self, mode: str, phase: str) -> bool:
        return self.next(mode, phase) is None
