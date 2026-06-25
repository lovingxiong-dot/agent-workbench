"""
单元测试：AgentWorker 工具调用与停止逻辑
运行：venv/Scripts/python -m pytest tests/test_agent_worker.py -v
或直接：venv/Scripts/python tests/test_agent_worker.py
"""
import asyncio
import sys
from unittest.mock import MagicMock

sys.path.insert(0, r"F:\Agent\agent_workbench")

from workers.agent_worker import AgentWorker, TOOL_DEFINITIONS
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage


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
            # 默认：没有更多 tool_calls，返回空总结
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


from workers.base_worker import WorkerCancelledError


def _run_worker(worker):
    chunks = []
    replies = []
    worker.chunk_ready.connect(lambda c: chunks.append(c))
    worker.result_ready.connect(lambda r: replies.append(r))
    try:
        asyncio.run(worker._process())
    except WorkerCancelledError:
        pass
    return chunks, replies


def test_multi_tool_single_final_response():
    """多工具调用时，最终总结 LLM 只应被调用一次"""
    llm = FakeLLM([
        ([
            {"name": "web_fetch", "args": {"url": "weather"}, "id": "tc1"},
            {"name": "web_fetch", "args": {"url": "gold"}, "id": "tc2"},
        ], ""),
        (None, "天气晴朗，黄金价格 500 元/克"),
    ])
    worker = AgentWorker(
        user_text="查询天气和黄金价格",
        mode_name="ask",
        current_llm=llm,
        current_tools=["web_fetch"],
        session_id="test-session",
        tool_map=_make_tool_map(),
        tool_definitions=TOOL_DEFINITIONS,
        chat_history=[],
    )
    chunks, replies = _run_worker(worker)

    assert llm.final_invokes == 1, f"最终总结应只调用 1 次，实际 {llm.final_invokes} 次"
    assert len(replies) == 1, f"应只收到 1 个 result_ready，实际 {len(replies)} 个"
    assert "天气晴朗" in replies[0] and "500 元/克" in replies[0]
    assert len(chunks) > 0, "流式输出应产生 chunk"


def test_multi_round_tool_calls():
    """模型连续多轮返回 tool_calls，应持续执行直到返回最终回复"""
    llm = FakeLLM([
        ([{"name": "web_fetch", "args": {"url": "a"}, "id": "tc1"}], ""),
        ([{"name": "web_fetch", "args": {"url": "b"}, "id": "tc2"}], ""),
        (None, "第三轮总结"),
    ])
    worker = AgentWorker(
        user_text="多轮工具测试",
        mode_name="ask",
        current_llm=llm,
        current_tools=["web_fetch"],
        session_id="test-session",
        tool_map=_make_tool_map(),
        tool_definitions=TOOL_DEFINITIONS,
        chat_history=[],
    )
    chunks, replies = _run_worker(worker)

    assert llm.final_invokes == 1
    assert len(replies) == 1
    assert replies[0] == "第三轮总结"


def test_max_rounds_limit():
    """达到 max_tool_rounds 上限后，应返回原始工具结果"""
    llm = FakeLLM([
        ([{"name": "web_fetch", "args": {"url": "a"}, "id": "tc1"}], ""),
        ([{"name": "web_fetch", "args": {"url": "b"}, "id": "tc2"}], ""),
        ([{"name": "web_fetch", "args": {"url": "c"}, "id": "tc3"}], ""),
    ])
    worker = AgentWorker(
        user_text="达到上限测试",
        mode_name="ask",
        current_llm=llm,
        current_tools=["web_fetch"],
        session_id="test-session",
        tool_map=_make_tool_map(),
        tool_definitions=TOOL_DEFINITIONS,
        chat_history=[],
        max_tool_rounds=2,
    )
    chunks, replies = _run_worker(worker)

    assert llm.final_invokes == 0, "达到上限后不应再调用最终总结"
    assert len(replies) == 1
    assert "Result for a" in replies[0]
    assert "Result for b" in replies[0]


def test_max_tool_rounds_default():
    """未传入 max_tool_rounds 时应使用默认值 8"""
    worker = AgentWorker(
        user_text="test",
        mode_name="ask",
        current_llm=MagicMock(),
        current_tools=[],
        session_id="test-session",
    )
    assert worker.max_tool_rounds == 8, f"默认值应为 8，实际 {worker.max_tool_rounds}"


def test_max_tool_rounds_configurable():
    """传入的 max_tool_rounds 应被正确保存"""
    worker = AgentWorker(
        user_text="test",
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
        user_text="test",
        mode_name="ask",
        current_llm=MagicMock(),
        current_tools=[],
        session_id="test-session",
        max_tool_rounds=0,
    )
    assert worker.max_tool_rounds == 8


def test_stop_flag_interrupts_tool_chain():
    """stop_flag 设置后，应中断后续工具执行与最终总结"""
    llm = FakeLLM([
        ([{"name": "web_fetch", "args": {"url": "a"}, "id": "tc1"}], ""),
        (None, "不应该返回"),
    ])
    tool_map = _make_tool_map()
    original_run = tool_map["web_fetch"].run

    def stopping_run(args):
        result = original_run(args)
        worker.stop()
        return result

    tool_map["web_fetch"].run = MagicMock(side_effect=stopping_run)

    worker = AgentWorker(
        user_text="test",
        mode_name="ask",
        current_llm=llm,
        current_tools=["web_fetch"],
        session_id="test-session",
        tool_map=tool_map,
        tool_definitions=TOOL_DEFINITIONS,
        chat_history=[],
    )
    chunks, replies = _run_worker(worker)

    assert tool_map["web_fetch"].run.call_count == 1, "停止后不应执行第二个工具"
    assert llm.final_invokes == 0, "停止后不应调用最终总结"
    assert len(replies) <= 1, "停止后最多收到一个取消标记"
    if replies:
        assert "取消" in replies[0] or "取消" in replies[0], replies[0]


def test_user_message_not_duplicated_in_messages():
    """AgentWorker 不应在内部再次追加 HumanMessage"""
    llm = FakeLLM([(None, "hello")])
    history = [HumanMessage(content="用户问题")]
    worker = AgentWorker(
        user_text="用户问题",
        mode_name="ask",
        current_llm=llm,
        current_tools=[],
        session_id="test-session",
        tool_map={},
        tool_definitions=[],
        chat_history=history,
    )
    _run_worker(worker)
    assert len(worker.chat_history) == 1


if __name__ == "__main__":
    test_multi_tool_single_final_response()
    test_multi_round_tool_calls()
    test_max_rounds_limit()
    test_max_tool_rounds_default()
    test_max_tool_rounds_configurable()
    test_invalid_max_tool_rounds_fallback()
    test_stop_flag_interrupts_tool_chain()
    test_user_message_not_duplicated_in_messages()
    print("✅ 所有测试通过")
