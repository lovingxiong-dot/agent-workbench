"""v6/runtime/execution_registry.py — Orchestrator 内部 Execution 树注册表。

Phase 3.11-D v0.3 — Execution Graph Topology Owner。
设计文档：docs/v6/phase3-11-d-parent-child-execution-design.md
ADR-015 v0.3 — Parent-Child Execution Propagation（Decision #14: Execution Graph Ownership）。

核心原则：
- ExecutionRegistry 是 Execution topology 唯一所有者（Decision #14）。
- 不进入 RuntimeContext / RuntimeEvent / ExecutionMetadata。
- 不暴露到 Presentation Layer。
- 不是历史数据库（历史拓扑由 Trace / EventStore 承担）。
- children_ids 是 active topology references（cleanup 不强删）。
- 节点 cleanup 需满足 cleanup_safe predicate（terminal + descendants terminal + retention expired）。
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional


@dataclass
class ExecutionNode:
    """Orchestrator 内部 Execution 节点（v0.3: 含 cleanup lifecycle）。"""
    execution_id: str
    task_id: str
    parent_execution_id: Optional[str]
    children_ids: List[str] = field(default_factory=list)  # historical references
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    terminated_at: Optional[datetime] = None
    cleanup_eligible_at: Optional[datetime] = None  # v0.3: retention 过期时间


class ExecutionRegistry:
    """Orchestrator 内部的 Execution 树注册表。

    v0.3 关键变更：
    - active topology references（children_ids 保留历史引用）
    - cleanup safe predicate（三条件守卫）
    - cleanup_eligible_at = terminated_at + retention_seconds

    职责：
    - 记录每个 Execution 的 parent 关系
    - 提供 descendants 遍历（用于 cancel / deadline 传播）
    - 防止环路
    - 终态后延迟清理（默认 300s）
    - Orchestrator 销毁时全量清理

    线程安全：所有公共方法线程安全（内部 _lock 守卫）。
    """

    DEFAULT_RETENTION_SECONDS = 300.0

    def __init__(self, retention_seconds: float = DEFAULT_RETENTION_SECONDS) -> None:
        self._nodes: Dict[str, ExecutionNode] = {}
        self._cleanup_timers: Dict[str, threading.Timer] = {}
        self._retention_seconds = retention_seconds
        self._lock = threading.Lock()

    # ── Register ─────────────────────────────────────────

    def register(
        self,
        execution_id: str,
        task_id: str,
        parent_execution_id: Optional[str] = None,
    ) -> None:
        """注册 Execution 节点。

        Raises:
            ValueError: parent 形成环路或 execution_id 重复
        """
        with self._lock:
            if execution_id in self._nodes:
                raise ValueError(f"Duplicate execution_id: {execution_id}")

            # 环路检测
            if parent_execution_id is not None:
                current: Optional[str] = parent_execution_id
                while current is not None:
                    if current == execution_id:
                        raise ValueError(
                            f"Cycle detected: {execution_id} cannot be its own ancestor"
                        )
                    node = self._nodes.get(current)
                    if node is None:
                        break  # parent 尚未注册
                    current = node.parent_execution_id

            node = ExecutionNode(
                execution_id=execution_id,
                task_id=task_id,
                parent_execution_id=parent_execution_id,
            )
            self._nodes[execution_id] = node

            if parent_execution_id is not None:
                parent = self._nodes.get(parent_execution_id)
                if parent is not None:
                    parent.children_ids.append(execution_id)
                    # v0.3: 不再强一致；即使 parent 已被清理，children_ids 仍保留历史引用

    # ── Lifecycle Markers ────────────────────────────────

    def mark_terminated(self, execution_id: str) -> None:
        """标记节点为终态（记录 terminated_at + cleanup_eligible_at）。"""
        with self._lock:
            node = self._nodes.get(execution_id)
            if node is not None and node.terminated_at is None:
                now = datetime.now(timezone.utc)
                node.terminated_at = now
                node.cleanup_eligible_at = now + timedelta(seconds=self._retention_seconds)

    # ── Cleanup (v0.3: safe predicate) ──────────────────

    def schedule_cleanup(self, execution_id: str) -> None:
        """v0.3: 注册延迟清理（cleanup_eligible_at 后由 Timer 触发）。"""
        with self._lock:
            node = self._nodes.get(execution_id)
            if node is None or node.terminated_at is None:
                return

            # 取消已有 timer
            existing = self._cleanup_timers.pop(execution_id, None)
            if existing is not None:
                existing.cancel()

            def _cleanup() -> None:
                self.cleanup_due(datetime.now(timezone.utc))

            delay = max(
                0.0,
                (node.cleanup_eligible_at - datetime.now(timezone.utc)).total_seconds(),
            )
            timer = threading.Timer(delay, _cleanup)
            timer.daemon = True
            self._cleanup_timers[execution_id] = timer
            timer.start()

    def cleanup_due(self, now: datetime) -> int:
        """v0.3: 确定性清理触发器。

        遍历所有 cleanup_eligible_at ≤ now 的节点，按 _is_cleanup_safe 三条件清理。

        Args:
            now: 当前时间（测试可传 future time 模拟时间推进）

        Returns:
            实际清理的节点数
        """
        cleaned = 0
        with self._lock:
            # 收集候选节点（避免迭代中修改）
            candidates = [
                node
                for node in self._nodes.values()
                if node.cleanup_eligible_at is not None
                and now >= node.cleanup_eligible_at
            ]
            for node in candidates:
                if self._is_cleanup_safe(node, now):
                    self._remove_node(node.execution_id)
                    cleaned += 1
                # 不安全则跳过（下次 cleanup_due 再尝试）
        return cleaned

    def _is_cleanup_safe(self, node: ExecutionNode, now: datetime) -> bool:
        """v0.3: cleanup safe predicate（三条件）。

        节点 cleanup safe ⟺
        - node.terminated_at ≠ None
        - all_active_descendants.terminated
        - now ≥ cleanup_eligible_at
        """
        if node.terminated_at is None:
            return False
        if not self._all_active_descendants_terminal(node):
            return False
        if node.cleanup_eligible_at is None or now < node.cleanup_eligible_at:
            return False
        return True

    def _all_active_descendants_terminal(self, node: ExecutionNode) -> bool:
        """所有 active descendants 均已 terminal。"""
        for child_id in node.children_ids:
            child = self._nodes.get(child_id)
            if child is None:
                continue  # 已清理（active filter）
            if child.terminated_at is None:
                return False
            if not self._all_active_descendants_terminal(child):
                return False
        return True

    def _remove_node(self, execution_id: str) -> None:
        """v0.3: 仅从 _nodes 删除，不修改 parent.children_ids。

        parent.children_ids 保留为 historical topology references。

        注意：调用方必须持有 _lock（cleanup_due / schedule_cleanup）。
        不再次加锁以避免死锁。
        """
        self._nodes.pop(execution_id, None)
        # v0.3: 不修改 parent.children_ids

    def cleanup_all(self) -> None:
        """Orchestrator 销毁时全量清理。"""
        with self._lock:
            for timer in self._cleanup_timers.values():
                timer.cancel()
            self._cleanup_timers.clear()
            self._nodes.clear()

    # ── Query (v0.3: active filter) ──────────────────────

    def get(self, execution_id: str) -> Optional[ExecutionNode]:
        """获取 Execution 节点（active only）。"""
        with self._lock:
            return self._nodes.get(execution_id)

    def get_children(self, execution_id: str) -> List[ExecutionNode]:
        """返回直接子节点（active filter applied）。"""
        with self._lock:
            node = self._nodes.get(execution_id)
            if node is None:
                return []
            return [
                self._nodes[child_id]
                for child_id in node.children_ids
                if child_id in self._nodes
            ]

    def get_active_children(self, execution_id: str) -> List[ExecutionNode]:
        """v0.3: 返回 active children（active filter by _nodes presence）。"""
        return self.get_children(execution_id)

    def get_descendants(self, execution_id: str) -> List[ExecutionNode]:
        """返回所有后代（DFS 后序，active filter applied）。"""
        with self._lock:
            result: List[ExecutionNode] = []
            self._collect_active_descendants(execution_id, result)
            return result

    def _collect_active_descendants(
        self,
        execution_id: str,
        result: List[ExecutionNode],
    ) -> None:
        node = self._nodes.get(execution_id)
        if node is None:
            return
        for child_id in node.children_ids:
            child = self._nodes.get(child_id)
            if child is not None:
                result.append(child)
                self._collect_active_descendants(child_id, result)

    def get_active_descendants(self, execution_id: str) -> List[ExecutionNode]:
        """v0.3: 返回 active descendants（alias）。"""
        return self.get_descendants(execution_id)

    def get_root(self, execution_id: str) -> Optional[ExecutionNode]:
        """追溯到根 execution。"""
        with self._lock:
            current: Optional[ExecutionNode] = self._nodes.get(execution_id)
            if current is None:
                return None
            while current.parent_execution_id is not None:
                parent = self._nodes.get(current.parent_execution_id)
                if parent is None:
                    break
                current = parent
            return current

    def get_depth(self, execution_id: str) -> int:
        """返回到 root 的深度（root=0，清理后 ancestor 不可达时截断）。"""
        with self._lock:
            current = self._nodes.get(execution_id)
            if current is None:
                return -1
            depth = 0
            while current.parent_execution_id is not None:
                parent = self._nodes.get(current.parent_execution_id)
                if parent is None:
                    break  # v0.3: parent 已清理，截断
                current = parent
                depth += 1
            return depth

    def has_node(self, execution_id: str) -> bool:
        """判断 Execution 节点是否存在（active）。"""
        with self._lock:
            return execution_id in self._nodes