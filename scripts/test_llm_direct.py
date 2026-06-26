"""
直接测试当前配置的 LLM，绕过 Orchestrator/Agent/UI 全部代码。
用于判断： hangs 是 LLM 提供者问题，还是工作台代码问题。

用法：
    .\venv\Scripts\python.exe scripts\test_llm_direct.py
    .\venv\Scripts\python.exe scripts\test_llm_direct.py deepseek
"""
import asyncio
import sys
import time
from pathlib import Path

# 把项目根目录加入路径，确保能导入 agent_engine
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent_engine.llm_registry import LLMRegistry
from langchain_core.messages import HumanMessage, SystemMessage


async def test_provider(registry: LLMRegistry, provider_name: str, timeout: float = 30.0):
    providers = registry.list_providers()
    cfg = providers.get(provider_name)
    if not cfg:
        print(f"❌ provider '{provider_name}' 不存在")
        return False

    print(f"\n{'='*50}")
    print(f"测试 provider: {provider_name}")
    print(f"  model: {cfg.get('model')}")
    print(f"  base_url: {cfg.get('base_url')}")
    api_key = cfg.get('api_key', '')
    api_key_status = '未设置/not-needed'
    if api_key and api_key != 'not-needed':
        if api_key.startswith('${') and api_key.endswith('}'):
            api_key_status = f'环境变量占位符未解析: {api_key}'
        else:
            api_key_status = f'已设置 (长度 {len(api_key)})'
    print(f"  api_key: {api_key_status}")

    llm = registry.get_llm(provider_name)
    messages = [
        SystemMessage(content="你是一个 helpful AI assistant。"),
        HumanMessage(content="你好"),
    ]

    print(f"\n直接调用 llm.ainvoke(messages)，超时 {timeout} 秒...")
    start = time.time()
    try:
        response = await asyncio.wait_for(llm.ainvoke(messages), timeout=timeout)
        elapsed = time.time() - start
        print(f"✅ 成功！耗时 {elapsed:.2f} 秒")
        print(f"回复内容: {response.content[:200]}")
        if getattr(response, "usage_metadata", None):
            print(f"token 用量: {response.usage_metadata}")
        return True
    except asyncio.TimeoutError:
        elapsed = time.time() - start
        print(f"❌ 超时！{elapsed:.2f} 秒内无响应。")
        return False
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ 异常！耗时 {elapsed:.2f} 秒")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {e}")
        return False


async def main():
    config_path = ROOT / "config.yaml"
    registry = LLMRegistry(config_path=str(config_path))
    providers = registry.list_providers()
    print(f"已配置 providers: {list(providers.keys())}")

    target = sys.argv[1] if len(sys.argv) > 1 else None

    if target:
        await test_provider(registry, target)
    else:
        # 没有参数则逐个测试
        for name in providers.keys():
            await test_provider(registry, name)


if __name__ == "__main__":
    asyncio.run(main())
