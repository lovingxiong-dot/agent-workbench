"""
SelfContext — 代码层自识别上下文注入

每次请求时自动构建结构化自识别数据并注入 system prompt：
- 时间戳（datetime.now() 硬事实）
- 位置感知（项目根、会话ID、标题）
- 跨对话接替（Phase状态、任务清单、上次活动）
- 独立记忆（app_root/.memory/MEMORY.md + 最近日志）
"""

import os
import glob
import json
from datetime import datetime
from typing import Optional, Dict, Any, List


class SelfContext:
    """构建代码层自识别上下文，注入 prompt

    记忆定位规则：
    - 读取 app_root/.memory/ 下的 MEMORY.md 和每日日志
    - app_root 为项目根目录（agent_workbench/），由外部注入
    - 不再依赖 WorkBuddy 的 .workbuddy/memory/ 路径
    """

    _WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    # 默认截断长度
    DEFAULT_MEMORY_MAX_LEN = 3000
    DEFAULT_LOG_LINES = 3
    DEFAULT_LOG_DAYS = 3

    def __init__(
        self,
        context_service=None,
        task_service=None,
        config: Optional[Dict[str, Any]] = None,
        app_root: Optional[str] = None,
    ):
        self._context_service = context_service
        self._task_service = task_service
        self._config = config or {}
        if app_root is None:
            self._app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        else:
            self._app_root = app_root
        self._memory_cache: Optional[str] = None
        self._memory_cache_mtime: float = 0.0

    def build(self) -> str:
        """构建完整自识别上下文，追加到 workspace_context 之后"""
        parts = []

        # 时间戳
        ts = self._build_timestamp_context()
        if ts:
            parts.append(ts)

        # 位置
        pos = self._build_position_context()
        if pos:
            parts.append(pos)

        # 任务状态
        state = self._build_task_state_context()
        if state:
            parts.append(state)

        # 记忆
        mem = self._build_memory_context()
        if mem:
            parts.append(mem)

        return "\n\n".join(parts)

    def build_handoff(self, session_id: str) -> str:
        """构建跨对话接替上下文（切换会话时注入）"""
        if not self._task_service:
            return ""

        try:
            task = self._task_service.get_task_status(session_id)
        except Exception:
            return ""

        if not task:
            return ""

        # 无活跃任务且非终态 → 不显示接替上下文
        if not task.is_active and not task.is_terminal:
            return ""

        # 活跃但 phase 仍为 idle → PhaseManager 尚未推进，没有实际状态需要接替
        if task.is_active and task.phase == "idle":
            return ""

        parts = ["[会话接替上下文]"]
        if task.is_active:
            parts.append("🔄 此会话中有未完成的任务")
            parts.append(f"   当前阶段: {task.phase}")
            if hasattr(task.status, 'value'):
                if 'AWAITING_CONFIRM' in str(task.status):
                    parts.append("   等待确认的任务清单")
                    if task.task_list:
                        parts.append(f"   任务清单: {json.dumps(task.task_list, ensure_ascii=False)}")
        elif task.is_terminal:
            parts.append(f"✅ 上次任务已完成 (状态: {task.status.value if hasattr(task.status, 'value') else task.status})")
            parts.append(f"   完成时间: {task.updated_at}")

        if task.created_at:
            parts.append(f"   会话创建时间: {task.created_at}")
        if task.updated_at:
            parts.append(f"   上次活动: {task.updated_at}")

        return "\n".join(parts)

    def _build_timestamp_context(self) -> str:
        """时间戳注入：Agent 无需猜测当前时间"""
        now = datetime.now()
        tz_name = now.astimezone().tzname() or "Unknown"
        return (
            f"[当前时间]\n"
            f"本地时间: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"星期: {self._WEEKDAY_NAMES[now.weekday()]}\n"
            f"时区: {tz_name}"
        )

    def _build_position_context(self) -> str:
        """位置感知：当前项目根、会话标题"""
        parts = ["[当前位置]"]
        if self._context_service:
            root = self._context_service.get_project_root()
            if root:
                parts.append(f"项目目录: {root}")
            else:
                parts.append("当前在您的电脑上，未绑定特定项目目录（全局对话模式）")
        return "\n".join(parts)

    def _build_task_state_context(self) -> str:
        """任务状态感知：目前只在有活跃任务时输出"""
        if not self._task_service:
            return ""
        # 获取当前活跃任务概览
        try:
            active_count = self._task_service.get_active_count()
            queued_count = self._task_service.get_queued_count()
        except Exception:
            return ""

        if active_count == 0 and queued_count == 0:
            return ""

        parts = ["[系统任务状态]"]
        parts.append(f"活跃任务: {active_count}")
        parts.append(f"排队任务: {queued_count}")
        return "\n".join(parts)

    def _build_memory_context(self) -> str:
        """独立记忆注入：读取 app_root/.memory/ 下的项目记忆与每日日志"""
        app_root = self._app_root
        if not app_root:
            return ""

        memory_dir = os.path.join(app_root, ".memory")
        if not os.path.isdir(memory_dir):
            return ""

        # 缓存检查：如果目录 mtime 未变，返回缓存
        try:
            dir_mtime = os.path.getmtime(memory_dir)
        except OSError:
            return ""
        if self._memory_cache is not None and dir_mtime == self._memory_cache_mtime:
            return self._memory_cache

        context_parts = []
        max_len = self._config.get("memory_max_len", self.DEFAULT_MEMORY_MAX_LEN)

        # 读取 MEMORY.md（项目记忆）
        mem_file = os.path.join(memory_dir, "MEMORY.md")
        if os.path.exists(mem_file):
            try:
                with open(mem_file, "r", encoding="utf-8") as f:
                    content = f.read()[:max_len]
                    context_parts.append(f"[项目记忆 - 跨对话持久化]\n{content}")
            except Exception:
                pass

        # 读取 skills.md（技能协议，全量注入）
        skills_file = os.path.join(memory_dir, "skills.md")
        if os.path.exists(skills_file):
            try:
                with open(skills_file, "r", encoding="utf-8") as f:
                    skills_content = f.read()[:max_len]
                    context_parts.append(f"[内置技能协议]\n{skills_content}")
            except Exception:
                pass

        # 读取最近 N 天日志
        log_days = self._config.get("log_days", self.DEFAULT_LOG_DAYS)
        log_lines = self._config.get("log_lines", self.DEFAULT_LOG_LINES)
        try:
            log_files = sorted(
                glob.glob(os.path.join(memory_dir, "*.md")),
                key=os.path.getmtime,
                reverse=True,
            )
            for lf in log_files[:log_days]:
                basename = os.path.basename(lf).replace(".md", "")
                if basename in ("MEMORY", "skills"):  # 跳过已全量注入的文件
                    continue
                try:
                    with open(lf, "r", encoding="utf-8") as f:
                        first_n = "".join(f.readlines()[:log_lines])
                        context_parts.append(f"[{basename} 日志摘要]\n{first_n.strip()}")
                except Exception:
                    pass
        except Exception:
            pass

        result = "\n---\n".join(context_parts) if context_parts else ""
        self._memory_cache = result
        self._memory_cache_mtime = dir_mtime
        return result

    def invalidate_cache(self):
        """强制刷新记忆缓存"""
        self._memory_cache = None
        self._memory_cache_mtime = 0.0