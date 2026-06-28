r"""
Craft 流程高保真冒烟脚本

不依赖 PySide6 UI，直接驱动 AgentSession + Orchestrator，
输出 Analyze → Confirm → Execute → Verify 全链路的详细状态日志。

用法：
    .\venv\Scripts\python.exe scripts\smoke_craft_flow.py
"""
import asyncio
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

# 把项目根目录加入路径，允许从 scripts/ 直接运行
sys_path_backup = None
if __name__ == "__main__":
    import sys
    sys_path_backup = list(sys.path)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from agent_engine.agent_session import AgentSession
from agent_engine.phase_manager import TaskItem
from tools.system import list_dir, read_file


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("craft_smoke")


def _fmt_msgs(msgs: List[Any]) -> str:
    if not msgs:
        return "(empty)"
    lines = []
    for i, m in enumerate(msgs):
        content = getattr(m, "content", "")
        preview = str(content)[:120].replace("\n", "\\n")
        lines.append(f"  [{i}] {type(m).__name__}: {preview!r}")
    return "\n".join(lines)


def log_state(label: str, session: AgentSession):
    orch = session.orchestrator
    logger.info("=" * 60)
    logger.info("STATE: %s", label)
    logger.info("  phase              = %s", orch._current_phase)
    logger.info("  workspace_context  = %s", orch.workspace_context)
    logger.info("  phase_messages len = %d", len(session.phase_messages))
    logger.debug("\n%s", _fmt_msgs(session.phase_messages))


def log_bound_tools(label: str, session: AgentSession, phase: str):
    orch = session.orchestrator
    bound_llm = orch.bind_tools_for_phase(phase)
    llm_mock = orch.llm
    if hasattr(llm_mock, "bind_tools") and llm_mock.bind_tools.called:
        call = llm_mock.bind_tools.call_args
        defs = call[0][0] if call and call[0] else []
        names = [d.get("function", {}).get("name", "?") for d in defs]
        logger.info("  [%s] bound tools = %s", label, names)
    else:
        logger.info("  [%s] bound tools = (none, raw LLM)", label)


async def main():
    project_root = os.getcwd()
    logger.info("PROJECT_ROOT = %s", project_root)

    tool_map = {
        "list_dir": list_dir,
        "read_file": read_file,
    }
    tool_definitions: List[Dict] = [
        {"type": "function", "function": {"name": "list_dir"}},
        {"type": "function", "function": {"name": "read_file"}},
    ]

    cpu_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="smoke_")
    session = AgentSession(
        llm=MagicMock(),
        tool_map=tool_map,
        tool_definitions=tool_definitions,
        mode="craft",
        project_root=project_root,
        system_prompt="You are a coding assistant.",
        cpu_executor=cpu_executor,
    )

    original_call_tool = session.orchestrator._call_tool

    async def logged_call_tool(name: str, args: Any) -> str:
        t0 = time.perf_counter()
        logger.info("  >> TOOL_CALL: %s(args=%r)", name, args)
        result = await original_call_tool(name, args)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.info("  << TOOL_RESULT: %s | len=%d | elapsed=%.2fms", name, len(str(result)), elapsed_ms)
        return result

    session.orchestrator._call_tool = logged_call_tool

    async def logged_arun(user_text: str, chat_history=None, callbacks=None):
        phase = session.orchestrator._current_phase
        chat_len = len(chat_history) if chat_history else 0
        logger.info("-" * 60)
        logger.info("ORCHESTRATOR.arun | phase=%s | chat_history_len=%d", phase, chat_len)
        logger.info("  user_text = %s", user_text[:200])
        log_bound_tools("bind_tools_for_phase", session, phase)

        t0 = time.perf_counter()
        if phase == "analyze":
            text = '[{"description": "列出项目根目录并读取 README.md"}]'
        elif phase == "execute":
            # 模拟真实工具调用链
            logger.info("  executing task list via tools...")
            dir_result = await logged_call_tool("list_dir", {"path": project_root})
            readme_path = os.path.join(project_root, "README.md")
            if os.path.isfile(readme_path):
                file_result = await logged_call_tool("read_file", {"path": readme_path})
            else:
                file_result = "README.md not found"
            text = (
                f"已完成任务：\n"
                f"- list_dir 返回 {len(str(dir_result))} 字符\n"
                f"- read_file 返回 {len(str(file_result))} 字符"
            )
        elif phase == "verify":
            text = "验证结果：任务已正确完成，目录结构和 README 内容均正常。"
        else:
            text = "未知 phase"
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.info("ORCHESTRATOR.arun returned | len=%d | elapsed=%.2fms", len(text), elapsed_ms)
        return text

    session.orchestrator.arun = logged_arun

    try:
        # ── Analyze ─────────────────────────────────────────────────
        log_state("BEFORE ANALYZE", session)
        tasks = await session.run_analyze("帮我看看项目结构并读一下 README", "workspace ctx")
        logger.info("PARSED TASKS = %s", [t.description for t in tasks])
        log_state("AFTER ANALYZE", session)

        # ── Execute ─────────────────────────────────────────────────
        result = await session.run_execute(tasks, "帮我看看项目结构并读一下 README", "execute ctx")
        logger.info("EXECUTE RESULT = %s", result[:200])
        log_state("AFTER EXECUTE", session)

        # ── Verify ──────────────────────────────────────────────────
        verify_result = await session.run_verify(
            [{"task": "列出目录并读 README", "result": result}],
            "本地验证：文件读取成功，无异常。",
            "verify ctx",
        )
        logger.info("VERIFY RESULT = %s", verify_result[:200])
        log_state("AFTER VERIFY", session)

        logger.info("=" * 60)
        logger.info("Craft 流程冒烟通过")
    finally:
        cpu_executor.shutdown(wait=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        if sys_path_backup is not None:
            import sys
            sys.path[:] = sys_path_backup
