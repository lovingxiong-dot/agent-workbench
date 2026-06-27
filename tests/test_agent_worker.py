"""
单元测试：AgentWorker 工具调用与停止逻辑（适配 v3.6+ Phase-Driven 架构）
运行：venv/Scripts/python -m pytest tests/test_agent_worker.py -v
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock

from workers.agent_worker import AgentWorker
from agent_engine.agent_session import AgentSession
from agent_engine.orchestrator import OrchestratorCancelledError
from langchain_core.messages import AIMessage, HumanMessage


class FakeLLM:
    def __init__(self, responses):
        """
        responses: list of (tool_calls, content) tuples
        - tool_calls: list of dict or None
        - content: str
        """
        self.model = "test-model"
        self._responses = list(responses)
        self._call_idx = 0
        self.final_invokes = 0

    def bind_tools(self, defs):
        return self

    async def ainvoke(self, messages):
        if self._call_idx >= len(self._responses):
            self.final_invokes += 1
            return AIMessage(content="fallback summary")

        tool_calls, content = self._responses[self._call_idx]
        self._call_idx += 1

        if tool_calls:
            return AIMessage(content=content or "", tool_calls=tool_calls)
        self.final_invokes += 1
        return AIMessage(content=content or "")


def _make_tool_map():
    m = MagicMock()
    m.run = MagicMock(side_effect=lambda args: f"Result for {args.get('url', args)}")
    return {"web_fetch": m}


# ── AgentSession 集成测试（工具调用循环）──────────────────────────────

def _make_session(llm, tool_map, max_tool_rounds=8):
    """创建 AgentSession 并注入 mock orchestrator"""
    session = AgentSession(
        llm=llm,
        tool_map=tool_map,
        tool_definitions=[{"type": "function", "function": {"name": "web_fetch"}}],
        mode="ask",
        project_root="",
        system_prompt="test",
        max_tool_rounds=max_tool_rounds,
        cpu_executor=ThreadPoolExecutor(max_workers=1),
    )
    return session


def test_multi_tool_single_final_response():
    """多工具调用时，最终总结 LLM 只应被调用一次"""
    llm = FakeLLM([
        ([
            {"name": "web_fetch", "args": {"url": "weather"}, "id": "tc1"},
            {"name": "web_fetch", "args": {"url": "gold"}, "id": "tc2"},
        ], ""),
        (None, "天气晴朗，黄金价格 500 元/克"),
    ])
    session = _make_session(llm, _make_tool_map())
    tasks, full_text = asyncio.run(
        session.run_analyze("查询天气和黄金价格", "context")
    )

    assert llm.final_invokes == 1, f"最终总结应只调用 1 次，实际 {llm.final_invokes} 次"
    assert "天气晴朗" in full_text and "500 元/克" in full_text


def test_multi_round_tool_calls():
    """模型连续多轮返回 tool_calls，应持续执行直到返回最终回复"""
    llm = FakeLLM([
        ([{"name": "web_fetch", "args": {"url": "a"}, "id": "tc1"}], ""),
        ([{"name": "web_fetch", "args": {"url": "b"}, "id": "tc2"}], ""),
        (None, "第三轮总结"),
    ])
    session = _make_session(llm, _make_tool_map())
    tasks, full_text = asyncio.run(
        session.run_analyze("多轮工具测试", "context")
    )

    assert llm.final_invokes == 1
    assert full_text == "第三轮总结"


def test_max_rounds_limit():
    """达到 max_tool_rounds 上限后，应返回原始工具结果"""
    llm = FakeLLM([
        ([{"name": "web_fetch", "args": {"url": "a"}, "id": "tc1"}], ""),
        ([{"name": "web_fetch", "args": {"url": "b"}, "id": "tc2"}], ""),
        ([{"name": "web_fetch", "args": {"url": "c"}, "id": "tc3"}], ""),
    ])
    session = _make_session(llm, _make_tool_map(), max_tool_rounds=2)
    tasks, full_text = asyncio.run(
        session.run_analyze("达到上限测试", "context")
    )

    assert llm.final_invokes == 0, "达到上限后不应再调用最终总结"
    assert "Result for a" in full_text
    assert "Result for b" in full_text


def test_stop_flag_interrupts_tool_chain():
    """stop_flag 设置后，应中断后续工具执行与最终总结"""
    import threading
    llm = FakeLLM([
        ([{"name": "web_fetch", "args": {"url": "a"}, "id": "tc1"}], ""),
        (None, "不应该返回"),
    ])
    tool_map = _make_tool_map()
    original_run = tool_map["web_fetch"].run

    cancel_event = threading.Event()

    def stopping_run(args):
        result = original_run(args)
        cancel_event.set()  # 模拟 stop 信号
        return result

    tool_map["web_fetch"].run = MagicMock(side_effect=stopping_run)

    session = _make_session(llm, tool_map)
    try:
        tasks, full_text = asyncio.run(
            session.run_analyze("stop test", "context", cancel_event=cancel_event)
        )
    except OrchestratorCancelledError:
        full_text = "[已取消]"

    assert tool_map["web_fetch"].run.call_count == 1, "停止后不应执行第二个工具"
    assert llm.final_invokes == 0, "停止后不应调用最终总结"


# ── AgentWorker 构造参数测试 ──────────────────────────────────────────

def test_max_tool_rounds_default():
    """未传入 max_tool_rounds 时应使用默认值 8"""
    worker = AgentWorker(
        mode_name="ask",
        current_llm=MagicMock(),
        current_tools=[],
        session_id="test-session",
    )
    assert worker.max_tool_rounds == 8, f"默认值应为 8，实际 {worker.max_tool_rounds}"


def test_max_tool_rounds_configurable():
    """传入的 max_tool_rounds 应被正确保存"""
    worker = AgentWorker(
        mode_name="craft",
        current_llm=MagicMock(),
        current_tools=[],
        session_id="test-session",
        max_tool_rounds=12,
    )
    assert worker.max_tool_rounds == 12


def test_invalid_max_tool_rounds_fallback():
    """传入非法值时应回退到默认值 8"""
    worker = AgentWorker(
        mode_name="ask",
        current_llm=MagicMock(),
        current_tools=[],
        session_id="test-session",
        max_tool_rounds=0,
    )
    assert worker.max_tool_rounds == 8


if __name__ == "__main__":
    test_multi_tool_single_final_response()
    test_multi_round_tool_calls()
    test_max_rounds_limit()
    test_max_tool_rounds_default()
    test_max_tool_rounds_configurable()
    test_invalid_max_tool_rounds_fallback()
    test_stop_flag_interrupts_tool_chain()
    print("所有测试通过")