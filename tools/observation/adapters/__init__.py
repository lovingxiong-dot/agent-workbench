"""tools/observation/adapters/ — Frozen Input Adapters。

约束：
- 允许 import: v6.runtime.* 作为数据类型（read-only）
- 禁止 import: Orchestrator / EngineManager / PlannerLoop / CapabilityRouter
- 禁止修改 EventBus / Registry 状态
- 禁止启动 Runtime Worker 线程
"""
