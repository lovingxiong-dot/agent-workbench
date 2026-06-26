import json
import os
import tempfile
import unittest

from agent_engine.memory_manager import MemoryManager


class TestMemoryManagerProfile(unittest.TestCase):
    """MemoryManager 用户画像初始化、迁移与合并逻辑测试。"""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="agent_workbench_memory_test_")
        self.defaults = {
            "schema_version": 1,
            "language": "zh-CN",
            "response_style": "detailed",
            "preferred_quant_source": "akshare",
            "default_python_env": "",
            "risk_tolerance": "medium",
            "frequent_tickers": [],
            "custom_terms": {},
        }
        self.config = {
            "short_term_db": os.path.join(self.tmp_dir, "short_term.db"),
            "user_profile": os.path.join(self.tmp_dir, "user_profile.json"),
            "vector_store": os.path.join(self.tmp_dir, "vector_store"),
            "user_profile_defaults": self.defaults,
        }

    def tearDown(self):
        # 清理测试生成的文件
        for name in ("short_term_db", "user_profile", "vector_store"):
            path = self.config[name]
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                os.rmdir(path)
        os.rmdir(self.tmp_dir)

    def test_init_creates_profile_with_defaults(self):
        """首次启动时，应使用 config defaults 初始化 user_profile.json。"""
        self.assertFalse(os.path.exists(self.config["user_profile"]))

        mgr = MemoryManager(self.config, storage_dir=self.tmp_dir)
        profile = mgr.load_user_profile()

        self.assertTrue(os.path.exists(self.config["user_profile"]))
        for key, expected in self.defaults.items():
            self.assertIn(key, profile)
            self.assertEqual(profile[key], expected)

    def test_safe_merge_fills_missing_keys(self):
        """已有画像文件缺少部分字段时，应仅补齐缺失 key，不覆盖已有值。"""
        existing = {
            "schema_version": 1,
            "language": "en-US",  # 用户已修改
            "custom_terms": {"foo": "bar"},  # 用户已有数据
        }
        with open(self.config["user_profile"], "w", encoding="utf-8") as f:
            json.dump(existing, f)

        mgr = MemoryManager(self.config, storage_dir=self.tmp_dir)
        profile = mgr.load_user_profile()

        # 已有值保留
        self.assertEqual(profile["language"], "en-US")
        self.assertEqual(profile["custom_terms"], {"foo": "bar"})
        # 缺失值补齐
        self.assertEqual(profile["response_style"], "detailed")
        self.assertEqual(profile["risk_tolerance"], "medium")
        self.assertEqual(profile["frequent_tickers"], [])
        # schema_version 保持正确
        self.assertEqual(profile["schema_version"], 1)

    def test_nested_dict_not_overwritten(self):
        """custom_terms 等嵌套 dict 中用户已有的内容，不应被 defaults 的空值覆盖。"""
        existing = {
            "schema_version": 1,
            "custom_terms": {
                "合约": "contract",
                "止盈": "take profit",
            },
        }
        with open(self.config["user_profile"], "w", encoding="utf-8") as f:
            json.dump(existing, f)

        mgr = MemoryManager(self.config, storage_dir=self.tmp_dir)
        profile = mgr.load_user_profile()

        self.assertEqual(
            profile["custom_terms"],
            {"合约": "contract", "止盈": "take profit"},
        )

    def test_migration_triggered_when_framework_version_newer(self):
        """当框架 schema_version 高于文件版本时，应触发迁移并补齐字段。"""
        # 模拟旧版本 profile：缺少 response_style、language 等字段
        old_profile = {
            "schema_version": 0,
            "preferred_quant_source": "yfinance",
            "risk_tolerance": "high",
        }
        with open(self.config["user_profile"], "w", encoding="utf-8") as f:
            json.dump(old_profile, f)

        mgr = MemoryManager(self.config, storage_dir=self.tmp_dir)
        profile = mgr.load_user_profile()

        # 迁移后版本号升级
        self.assertEqual(profile["schema_version"], 1)
        # 旧值保留
        self.assertEqual(profile["preferred_quant_source"], "yfinance")
        self.assertEqual(profile["risk_tolerance"], "high")
        # 新增字段补齐
        self.assertEqual(profile["language"], "zh-CN")
        self.assertEqual(profile["response_style"], "detailed")

    def test_update_user_profile_cannot_overwrite_schema_version(self):
        """外部更新不应允许覆盖 schema_version，避免破坏迁移锚点。"""
        mgr = MemoryManager(self.config, storage_dir=self.tmp_dir)
        mgr.update_user_profile({
            "schema_version": 99,
            "risk_tolerance": "low",
        })
        profile = mgr.load_user_profile()

        self.assertEqual(profile["schema_version"], 1)
        self.assertEqual(profile["risk_tolerance"], "low")


if __name__ == "__main__":
    unittest.main()
