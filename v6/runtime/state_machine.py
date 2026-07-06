"""v6/runtime/state_machine.py — Runtime 任务状态机。

设计来源：V6.5 Runtime Foundation Layer 阶段规划。

核心原则：
- 状态机只管理迁移规则，不保存任务状态。
- 所有状态使用 `RuntimeState` 枚举，禁止字符串硬编码。
- 非法迁移必须显式报错，为 Scheduler / Runtime 生命周期管理提供可预测接口。
"""
from __future__ import annotations

from typing import Dict, List, Set

from v6.runtime.enums import RuntimeState


class RuntimeStateTransitionError(ValueError):
    """非法 RuntimeState 迁移异常。"""

    def __init__(self, from_state: RuntimeState, to_state: RuntimeState) -> None:
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"Invalid RuntimeState transition: {from_state.value!r} -> {to_state.value!r}"
        )


class RuntimeStateMachine:
    """Runtime Task 生命周期状态机。

    维护状态之间的合法迁移关系，支持验证、查询、执行。
    """

    _transitions: Dict[RuntimeState, Set[RuntimeState]] = {
        RuntimeState.CREATED: {RuntimeState.QUEUED, RuntimeState.CANCELLED},
        RuntimeState.QUEUED: {RuntimeState.RUNNING, RuntimeState.CANCELLED},
        RuntimeState.RUNNING: {
            RuntimeState.WAITING,
            RuntimeState.PAUSED,
            RuntimeState.CANCELLED,
            RuntimeState.COMPLETED,
            RuntimeState.FAILED,
        },
        RuntimeState.WAITING: {
            RuntimeState.RUNNING,
            RuntimeState.CANCELLED,
            RuntimeState.FAILED,
        },
        RuntimeState.PAUSED: {RuntimeState.RUNNING, RuntimeState.CANCELLED},
        RuntimeState.FAILED: {RuntimeState.QUEUED},  # retry：重新回到队列
        RuntimeState.CANCELLED: set(),  # 终态
        RuntimeState.COMPLETED: set(),  # 终态
    }

    def can_transition(
        self,
        from_state: RuntimeState,
        to_state: RuntimeState,
    ) -> bool:
        """判断从 from_state 到 to_state 是否为合法迁移。"""
        if not isinstance(from_state, RuntimeState) or not isinstance(to_state, RuntimeState):
            return False
        return to_state in self._transitions.get(from_state, set())

    def transition(
        self,
        from_state: RuntimeState,
        to_state: RuntimeState,
    ) -> RuntimeState:
        """执行状态迁移；非法迁移抛出 RuntimeStateTransitionError。

        Returns:
            迁移后的目标状态（即 to_state）。
        """
        if not self.can_transition(from_state, to_state):
            raise RuntimeStateTransitionError(from_state, to_state)
        return to_state

    def valid_targets(self, from_state: RuntimeState) -> List[RuntimeState]:
        """返回从 from_state 可合法迁移到的所有目标状态。"""
        return list(self._transitions.get(from_state, set()))

    def is_terminal(self, state: RuntimeState) -> bool:
        """判断是否为终态（无合法出边）。"""
        return len(self._transitions.get(state, set())) == 0
