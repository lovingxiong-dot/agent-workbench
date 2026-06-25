"""
PhaseManager — 阶段驱动的工作流调度器

作为 Orchestrator 的上层调度器，负责把一次用户请求按 Mode 切分为不同的 Phase：
  Ask:    ANALYZE → ARCHIVE
  Plan:   ANALYZE → CONFIRM → ARCHIVE
  Craft:  ANALYZE → CONFIRM → EXECUTE → VERIFY → ARCHIVE

设计原则：
- 不直接调用 LLM / 工具，只通过信号通知 MainWindow 执行
- Phase 与 Mode 正交：Mode 决定权限，Phase 决定执行阶段
- Checkpoint 区分硬门控（必须满足）和软提示（可跳过）
- 状态异常时安全回退到 IDLE，不影响下一次对话
"""
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

from PySide6.QtCore import QObject, Signal


class Phase(str, Enum):
    IDLE = "idle"
    ANALYZE = "analyze"
    CONFIRM = "confirm"
    EXECUTE = "execute"
    VERIFY = "verify"
    ARCHIVE = "archive"


class CheckpointKind(str, Enum):
    HARD = "hard"
    SOFT = "soft"


@dataclass
class TaskItem:
    """任务清单中的单个任务"""
    id: str
    description: str
    done: bool = False
    result: str = ""

    def to_dict(self) -> dict:
        return {"id": self.id, "description": self.description, "done": self.done, "result": self.result}

    @classmethod
    def from_dict(cls, data: dict) -> "TaskItem":
        return cls(
            id=data.get("id", ""),
            description=data.get("description", ""),
            done=data.get("done", False),
            result=data.get("result", ""),
        )


@dataclass
class Checkpoint:
    """阶段检查点"""
    phase: Phase
    kind: CheckpointKind
    rule: Callable[["PhaseContext"], bool]
    message: str = ""
    skippable: bool = False


@dataclass
class PhaseContext:
    """一次工作流执行的完整上下文"""
    user_text: str = ""
    mode: str = "ask"
    task_list: List[TaskItem] = field(default_factory=list)
    user_confirmed: bool = False
    execution_results: List[dict] = field(default_factory=list)
    verification_passed: bool = False
    verification_details: str = ""

    def reset(self):
        self.user_text = ""
        self.mode = "ask"
        self.task_list.clear()
        self.user_confirmed = False
        self.execution_results.clear()
        self.verification_passed = False
        self.verification_details = ""


class PhaseManager(QObject):
    """
    阶段管理器。

    信号：
      - phase_changed(str, str): (phase_name, mode_name)
      - analyze_required(str, str, str): (user_text, mode, context)
      - confirm_required(list): TaskItem[] 等待用户确认
      - execute_required(list): TaskItem[] 等待执行
      - verify_required(list, str): (execution_results, mode)
      - archive_required(str): mode
      - flow_finished(bool, str): (success, message)
      - error_occurred(str, str): (code, detail)
    """

    phase_changed = Signal(str, str)
    analyze_required = Signal(str, str, str)
    confirm_required = Signal(list)
    execute_required = Signal(list)
    verify_required = Signal(list, str)
    archive_required = Signal(str)
    flow_finished = Signal(bool, str)
    error_occurred = Signal(str, str)

    # Mode → 阶段流
    PHASE_FLOW: Dict[str, List[Phase]] = {
        "ask": [Phase.ANALYZE, Phase.ARCHIVE],
        "plan": [Phase.ANALYZE, Phase.CONFIRM, Phase.ARCHIVE],
        "craft": [Phase.ANALYZE, Phase.CONFIRM, Phase.EXECUTE, Phase.VERIFY, Phase.ARCHIVE],
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._context = PhaseContext()
        self._current_phase: Phase = Phase.IDLE
        self._flow: List[Phase] = []
        self._flow_index: int = -1

    # ═══════════════════════════════════════════════════
    # 公共接口
    # ═══════════════════════════════════════════════════
    def start(self, user_text: str, mode: str, context: str = ""):
        """启动一次新的 phase-driven 工作流"""
        if self._current_phase != Phase.IDLE:
            self._emit_error("PHASE_BUSY", f"当前处于 {self._current_phase.value}，请先结束或重置")
            return
        if not user_text or not user_text.strip():
            self._emit_error("EMPTY_INPUT", "用户输入不能为空")
            return
        if mode not in self.PHASE_FLOW:
            self._emit_error("INVALID_MODE", f"不支持的模式: {mode}")
            return

        self._context.reset()
        self._context.user_text = user_text.strip()
        self._context.mode = mode
        self._flow = list(self.PHASE_FLOW[mode])
        self._flow_index = 0
        self._set_phase(self._flow[0])
        self.analyze_required.emit(user_text, mode, context)

    def reset(self):
        """强制重置到 IDLE"""
        self._context.reset()
        self._flow.clear()
        self._flow_index = -1
        self._set_phase(Phase.IDLE)

    def current_phase(self) -> str:
        return self._current_phase.value

    def current_context(self) -> PhaseContext:
        return self._context

    # ═══════════════════════════════════════════════════
    # 阶段推进（由 MainWindow 调用）
    # ═══════════════════════════════════════════════════
    def on_analyze_complete(self, task_list: List[TaskItem]):
        """分析阶段完成，传入解析出的任务清单"""
        if self._current_phase != Phase.ANALYZE:
            self._emit_error("PHASE_MISMATCH", f"期望 ANALYZE，当前是 {self._current_phase.value}")
            return
        self._context.task_list = list(task_list)
        self._advance()

    def on_user_confirm(self, confirmed: bool = True):
        """用户确认或取消当前任务清单"""
        if self._current_phase != Phase.CONFIRM:
            self._emit_error("PHASE_MISMATCH", f"期望 CONFIRM，当前是 {self._current_phase.value}")
            return
        if not confirmed:
            self.flow_finished.emit(False, "用户取消了任务执行")
            self.reset()
            return
        self._context.user_confirmed = True
        self._advance()

    def on_execute_complete(self, results: List[dict]):
        """执行阶段完成，传入各任务结果"""
        if self._current_phase != Phase.EXECUTE:
            self._emit_error("PHASE_MISMATCH", f"期望 EXECUTE，当前是 {self._current_phase.value}")
            return
        self._context.execution_results = list(results)
        self._advance()

    def on_verify_complete(self, passed: bool, details: str = ""):
        """验证阶段完成"""
        if self._current_phase != Phase.VERIFY:
            self._emit_error("PHASE_MISMATCH", f"期望 VERIFY，当前是 {self._current_phase.value}")
            return
        self._context.verification_passed = passed
        self._context.verification_details = details
        self._advance()

    def on_archive_complete(self, success: bool = True, message: str = ""):
        """存档阶段完成"""
        if self._current_phase != Phase.ARCHIVE:
            self._emit_error("PHASE_MISMATCH", f"期望 ARCHIVE，当前是 {self._current_phase.value}")
            return
        self.flow_finished.emit(success, message or "工作流完成")
        self.reset()

    # ═══════════════════════════════════════════════════
    # 解析工具：把 LLM 返回的文本解析为 TaskItem 列表
    # ═══════════════════════════════════════════════════
    @staticmethod
    def parse_task_list(text: str) -> List[TaskItem]:
        """
        支持两种格式：
        1. JSON 数组: [{"description": "..."}, ...]
        2. Markdown 列表: - [ ] task1\n- [ ] task2
        """
        import json
        import re

        text = (text or "").strip()
        if not text:
            return []

        # 尝试 JSON
        try:
            start = text.find("[")
            end = text.rfind("]")
            if start != -1 and end != -1 and end > start:
                data = json.loads(text[start:end + 1])
                if isinstance(data, list):
                    items = []
                    for i, entry in enumerate(data):
                        desc = entry if isinstance(entry, str) else entry.get("description", "")
                        if desc:
                            items.append(TaskItem(id=f"task-{i+1}", description=desc))
                    return items
        except Exception:
            pass

        # 回退 Markdown 列表
        items = []
        for i, line in enumerate(text.splitlines(), 1):
            line = line.strip()
            m = re.match(r"^[\-\*]\s*(?:\[[\s xX]\]\s*)?(.*)$", line)
            if m:
                desc = m.group(1).strip()
                if desc:
                    items.append(TaskItem(id=f"task-{i}", description=desc))
        return items

    # ═══════════════════════════════════════════════════
    # 内部方法
    # ═══════════════════════════════════════════════════
    def _set_phase(self, phase: Phase):
        self._current_phase = phase
        self.phase_changed.emit(phase.value, self._context.mode)

    def _advance(self):
        """进入下一个阶段"""
        # 软检查点：记录但不阻塞
        self._run_soft_checkpoints()

        self._flow_index += 1
        if self._flow_index >= len(self._flow):
            self.flow_finished.emit(True, "工作流完成")
            self.reset()
            return

        next_phase = self._flow[self._flow_index]

        # 硬检查点
        if not self._check_hard_checkpoint(next_phase):
            return

        self._set_phase(next_phase)
        self._emit_phase_signal(next_phase)

    def _emit_phase_signal(self, phase: Phase):
        if phase == Phase.CONFIRM:
            self.confirm_required.emit(self._context.task_list)
        elif phase == Phase.EXECUTE:
            self.execute_required.emit(self._context.task_list)
        elif phase == Phase.VERIFY:
            self.verify_required.emit(self._context.execution_results, self._context.mode)
        elif phase == Phase.ARCHIVE:
            # Archive 阶段不自动完成，由 MainWindow 执行可选存档后再调用 on_archive_complete
            self.archive_required.emit(self._context.mode)

    def _check_hard_checkpoint(self, phase: Phase) -> bool:
        """硬门控：不满足则停留在当前阶段并报错"""
        ctx = self._context
        if phase == Phase.CONFIRM and not ctx.task_list:
            self._emit_error("CHECKPOINT_HARD", "进入 CONFIRM 阶段前必须有 task list")
            return False
        if phase == Phase.EXECUTE and not ctx.user_confirmed:
            self._emit_error("CHECKPOINT_HARD", "进入 EXECUTE 阶段前必须用户确认")
            return False
        if phase == Phase.VERIFY and not ctx.execution_results:
            self._emit_error("CHECKPOINT_HARD", "进入 VERIFY 阶段前必须有执行结果")
            return False
        return True

    def _run_soft_checkpoints(self):
        """软提示：只发日志/信号，不阻塞"""
        ctx = self._context
        if self._current_phase == Phase.EXECUTE and ctx.task_list:
            # 执行前 soft checkpoint：空任务清单已在 hard 中拦截
            pass

    def _emit_error(self, code: str, detail: str):
        self.error_occurred.emit(code, detail)
        # 出错后安全回到 IDLE，避免卡住
        self.reset()
