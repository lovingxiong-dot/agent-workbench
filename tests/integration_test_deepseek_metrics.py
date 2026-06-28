"""
DeepSeek 集成测试：验证真实 API 返回 usage_metadata，
并验证 MetricsCollector + AgentWorker 链路能正确提取和转发指标。
"""
import asyncio
import os
import shutil
import sys
import tempfile
import unittest

# 把项目根目录加入路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage

from agent_engine.llm_registry import LLMRegistry
from services.metrics_collector import MetricsCollector


def _load_env_key(name: str) -> str:
    """轻量 .env 读取，避免依赖 python-dotenv"""
    if os.environ.get(name):
        return os.environ.get(name)
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(name + "="):
                    return line.split("=", 1)[1].strip().strip('"')
    return ""


class DeepSeekMetricsIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api_key = _load_env_key("DEEPSEEK_API_KEY")
        if not cls.api_key:
            raise unittest.SkipTest("DEEPSEEK_API_KEY not set")

    def test_deepseek_returns_usage_metadata(self):
        """直接调用 DeepSeek 模型，确认返回 AIMessage 包含 usage_metadata"""
        # 使用临时配置文件，避免污染用户配置
        tmp_dir = tempfile.mkdtemp()
        tmp_config = os.path.join(tmp_dir, "config.yaml")
        shutil.copy("config.yaml", tmp_config)
        try:
            registry = LLMRegistry(tmp_config, writable_path=tmp_config)
            # 临时注入 deepseek provider
            registry.add_provider("deepseek-test", {
                "base_url": "https://api.deepseek.com/v1",
                "api_key": self.api_key,
                "model": "deepseek-chat",
            })
            llm = registry.get_llm("deepseek-test")

            messages = [HumanMessage(content="Say hi in one word.")]
            response = asyncio.run(llm.ainvoke(messages))

            self.assertTrue(hasattr(response, "content"))
            usage = getattr(response, "usage_metadata", None)
            self.assertIsNotNone(usage, "response 没有 usage_metadata")
            self.assertIn("input_tokens", usage)
            self.assertIn("output_tokens", usage)
            self.assertGreater(usage["input_tokens"] + usage["output_tokens"], 0)

            print(f"\n[DeepSeek usage] input={usage['input_tokens']} output={usage['output_tokens']}")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_metrics_collector_with_usage(self):
        """模拟从 response 提取 usage 后，MetricsCollector 能产出正确格式"""
        collector = MetricsCollector()
        collector.start_turn()
        usage = {"input_tokens": 12, "output_tokens": 5}
        metrics = collector.finish_turn(usage["input_tokens"], usage["output_tokens"])

        self.assertEqual(metrics.total_tokens, 17)
        self.assertEqual(metrics.format_brief(), "17tok/0ms")
        self.assertIn("Tokens=12+5=17", metrics.format_detail())


if __name__ == "__main__":
    unittest.main()
