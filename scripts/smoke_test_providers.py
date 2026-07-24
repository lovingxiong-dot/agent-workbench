"""scripts/smoke_test_providers.py — Provider LLM 冒烟测试。

v6.10.0-alpha 打包前冒烟测试。

测试：
  1. minimax-M3 (OpenAI 兼容) — 真实 API 调用
  2. deepseek-v4-pro (火山引擎 Coding Plan) — 真实 API 调用

输出：
  - 测试结果打印到 stdout
  - 不修改任何持久化状态
  - 不写日志文件

使用：
  python scripts/smoke_test_providers.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# 确保 project root 在 path 中
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 加载 merged config
from agent_workbench.presentation.services.config_loader import WorkbenchLocalConfigLoader

merged_path = WorkbenchLocalConfigLoader.merge_to_temp()
os.environ["WORKBENCH_CONFIG"] = str(merged_path)

import yaml

with merged_path.open("r", encoding="utf-8") as fh:
    config = yaml.safe_load(fh)

PROVIDERS = config.get("model", {}).get("providers", [])


def smoke_test_provider(provider_config: dict, test_prompt: str = "用一句话介绍你自己。") -> dict:
    """冒烟测试单个 Provider。

    Args:
        provider_config: model.providers 配置项。
        test_prompt: 测试 prompt。

    Returns:
        dict: {success, response, latency_ms, error}
    """
    import openai

    api_key = provider_config.get("api_key", "")
    base_url = provider_config.get("base_url", "")
    model = provider_config.get("model", "")
    use_custom = provider_config.get("use_custom_protocol", False)
    name = provider_config.get("name", "unknown")

    if not api_key:
        return {"success": False, "error": "missing api_key", "name": name}

    print(f"\n{'=' * 60}")
    print(f"Testing Provider: {name}")
    print(f"  Model:     {model}")
    print(f"  Base URL:  {base_url}")
    print(f"  Custom:    {use_custom}")
    print(f"  Prompt:    {test_prompt}")
    print(f"{'-' * 60}")

    start = time.time()
    try:
        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": test_prompt},
            ],
            temperature=0.7,
            max_tokens=256,
            timeout=30,
        )
        latency_ms = int((time.time() - start) * 1000)
        content = response.choices[0].message.content or ""
        print(f"  Latency:   {latency_ms} ms")
        print(f"  Response:  {content[:200]}")
        return {
            "success": True,
            "name": name,
            "model": model,
            "response": content,
            "latency_ms": latency_ms,
        }
    except Exception as exc:
        latency_ms = int((time.time() - start) * 1000)
        print(f"  FAILED:    {exc}")
        return {
            "success": False,
            "name": name,
            "model": model,
            "error": str(exc),
            "latency_ms": latency_ms,
        }


def main() -> int:
    print("=" * 60)
    print("v6.10.0-alpha Provider Smoke Test")
    print(f"Config: {merged_path}")
    print(f"Providers: {len(PROVIDERS)}")
    print("=" * 60)

    if not PROVIDERS:
        print("ERROR: No providers configured in config.local.yaml")
        return 1

    results = []
    for provider in PROVIDERS:
        if not provider.get("enabled", True):
            print(f"\nSkipping {provider.get('name')} (disabled)")
            continue
        result = smoke_test_provider(provider)
        results.append(result)

    print(f"\n{'=' * 60}")
    print("Smoke Test Summary")
    print(f"{'=' * 60}")
    success_count = sum(1 for r in results if r["success"])
    print(f"Passed: {success_count}/{len(results)}")
    for r in results:
        status = "✅ PASS" if r["success"] else "❌ FAIL"
        latency = f"{r.get('latency_ms', 0)} ms"
        print(f"  {status}  {r['name']:20s}  {latency}")
        if not r["success"]:
            print(f"           Error: {r.get('error', 'unknown')}")

    return 0 if success_count == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())