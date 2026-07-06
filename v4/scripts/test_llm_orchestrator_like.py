"""
模拟 Orchestrator 的实际调用路径：绑定工具 + system prompt + workspace context。
用于判断工具绑定或 prompt 是否导致 hang。
"""
import asyncio
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent_engine.llm_registry import LLMRegistry
from agent_engine.orchestrator import AgentOrchestrator
from langchain_core.messages import HumanMessage


async def main():
    config_path = ROOT / "config" / "config.yaml"
    registry = LLMRegistry(config_path=str(config_path))

    provider_name = sys.argv[1] if len(sys.argv) > 1 else "deepseek"
    print(f"测试 provider: {provider_name}")

    llm = registry.get_llm(provider_name)

    # 模拟 Ask 模式下 Analyze 阶段的真实配置
    tool_definitions = [
        {"type": "function", "function": {"name": "read_file", "description": "读取文件", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
        {"type": "function", "function": {"name": "list_dir", "description": "列出目录", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": []}}},
        {"type": "function", "function": {"name": "web_fetch", "description": "抓取网页", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    ]

    orch = AgentOrchestrator(
        llm=llm,
        tool_map={},
        tool_definitions=tool_definitions,
        system_prompt="你是 AI Agent Workbench 的分析专家。",
        workspace_context="当前项目根目录: F:\\Agent\\agent_workbench",
        app_version="v3.7.3",
        llm_timeout=30.0,
    )
    orch.set_phase("analyze", "ask", "当前项目根目录: F:\\Agent\\agent_workbench")

    print("\nPhase: analyze, Mode: ask")
    print("绑定工具后调用 LLM，超时 30 秒...")
    start = time.time()
    try:
        text = await asyncio.wait_for(
            orch.arun("你好", chat_history=[], cancel_event=None),
            timeout=35.0,
        )
        elapsed = time.time() - start
        print(f"✅ 成功！耗时 {elapsed:.2f} 秒")
        print(f"回复: {text[:300]}")
    except asyncio.TimeoutError:
        elapsed = time.time() - start
        print(f"❌ 超时！{elapsed:.2f} 秒")
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ 异常！耗时 {elapsed:.2f} 秒")
        print(f"错误: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
