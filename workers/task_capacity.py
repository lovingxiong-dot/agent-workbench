"""
TaskCapacity — 运行时容量阈值

控制并发任务数、排队上限、工具调用数，防止资源耗尽。
配置从 config.yaml 读取，运行时可通过属性调整。
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class TaskCapacity:
    """运行时容量配置"""
    max_concurrent_tasks: int = 3       # 最大并发任务数
    max_queued_tasks: int = 5           # 最大排队任务数
    max_tools_per_task: int = 8         # 单任务最大工具调用数
    max_total_tools: int = 12           # 全局最大并发工具调用数
    cpu_cores_reserved: int = 1         # 保留给系统的 CPU 核心
    memory_threshold_mb: int = 512      # 低于此内存阈值拒绝新任务

    @property
    def total_capacity(self) -> int:
        return self.max_concurrent_tasks + self.max_queued_tasks

    @classmethod
    def from_config(cls, config_service) -> "TaskCapacity":
        """从 ConfigService 读取 task.capacity 配置段"""
        cfg = config_service.get("task", {}).get("capacity", {}) if config_service else {}
        if not cfg:
            return cls()
        return cls(
            max_concurrent_tasks=int(cfg.get("max_concurrent_tasks", 3)),
            max_queued_tasks=int(cfg.get("max_queued_tasks", 5)),
            max_tools_per_task=int(cfg.get("max_tools_per_task", 8)),
            max_total_tools=int(cfg.get("max_total_tools", 12)),
            cpu_cores_reserved=int(cfg.get("cpu_cores_reserved", 1)),
            memory_threshold_mb=int(cfg.get("memory_threshold_mb", 512)),
        )
