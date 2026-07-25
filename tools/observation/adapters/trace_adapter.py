"""tools/observation/adapters/trace_adapter.py — RuntimeTrace Adapter。

RuntimeTrace 是 ctx.trace，用于存储 task lifecycle trace。
Adapter 仅消费 steps，不修改 trace。
"""
from __future__ import annotations

from typing import List, Optional

from v6.runtime.trace import RuntimeTrace, TraceStep


def collect_trace_steps(
    trace: RuntimeTrace,
    execution_id: Optional[str] = None,
) -> List[TraceStep]:
    """收集 trace 中的 step 列表（可选 execution_id 过滤）。

    注意：RuntimeTrace.steps() 返回迭代器；Adapter 转 list 提供多次消费能力。
    """
    if trace is None:
        return []
    if execution_id is None:
        return list(trace.steps())
    # phase 字段用于过滤（execution_id 不在 TraceStep schema 内）
    return [
        step for step in trace.steps()
        if getattr(step, "node", None) == execution_id
    ]
