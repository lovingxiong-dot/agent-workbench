"""tests/v6/test_v6_agent.py — Agent Identity 切换验证。

覆盖：
- Agent 发现（扫描 packages/ 目录）
- Agent 切换
- System Prompt 获取
- 不存在的 Agent 切换失败
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import mock

import pytest
import yaml

from agent_workbench.runtime.modules.agent_module import AgentModule, AgentIdentity


@pytest.fixture
def agent_module():
    """创建 AgentModule，使用临时 packages 目录。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        packages_dir = Path(tmpdir) / "packages"
        packages_dir.mkdir()

        # 创建测试 Agent 包
        agents = {
            "personal_agent": {
                "id": "personal_agent",
                "name": "个人助手",
                "version": "1.0.0",
                "description": "通用个人助理",
                "system_prompt": "你是个人助手",
                "provider": "echo",
                "model": "echo-default",
            },
            "coding_agent": {
                "id": "coding_agent",
                "name": "编程助手",
                "version": "1.0.0",
                "description": "专业编程助手",
                "system_prompt": "你是编程助手",
                "provider": "echo",
                "model": "echo-default",
            },
        }
        for agent_id, data in agents.items():
            agent_dir = packages_dir / agent_id
            agent_dir.mkdir()
            manifest = agent_dir / "manifest.yaml"
            with open(manifest, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f)

        # 注入临时 packages 目录
        am = AgentModule()
        am._packages_dir = packages_dir
        am.initialize(mock.MagicMock())
        yield am


class TestAgentModule:
    """AgentModule 单元测试。"""

    def test_discover_agents(self, agent_module):
        """应发现 packages 目录下的 Agent 包。"""
        agents = agent_module.list_agents()
        assert len(agents) == 2
        ids = [a["id"] for a in agents]
        assert "personal_agent" in ids
        assert "coding_agent" in ids

    def test_default_active_agent(self, agent_module):
        """默认活跃 Agent 应为 personal_agent。"""
        assert agent_module.active_agent_id == "personal_agent"
        active = agent_module.get_active_agent()
        assert active is not None
        assert active.id == "personal_agent"
        assert active.name == "个人助手"

    def test_switch_agent(self, agent_module):
        """切换到 coding_agent。"""
        result = agent_module.switch_agent("coding_agent")
        assert result is True
        assert agent_module.active_agent_id == "coding_agent"

        active = agent_module.get_active_agent()
        assert active.name == "编程助手"

    def test_switch_to_nonexistent(self, agent_module):
        """切换到不存在的 Agent 应返回 False。"""
        result = agent_module.switch_agent("nonexistent")
        assert result is False
        assert agent_module.active_agent_id == "personal_agent"

    def test_get_system_prompt(self, agent_module):
        """应返回当前活跃 Agent 的 System Prompt。"""
        assert agent_module.get_system_prompt() == "你是个人助手"

        agent_module.switch_agent("coding_agent")
        assert agent_module.get_system_prompt() == "你是编程助手"

    def test_switch_back_and_forth(self, agent_module):
        """前后切换 Agent 应正确更新。"""
        agent_module.switch_agent("coding_agent")
        assert agent_module.get_system_prompt() == "你是编程助手"

        agent_module.switch_agent("personal_agent")
        assert agent_module.get_system_prompt() == "你是个人助手"

    def test_list_agents_returns_all(self, agent_module):
        """list_agents 应返回所有 Agent 的完整信息。"""
        agents = agent_module.list_agents()
        assert len(agents) == 2
        for a in agents:
            assert "id" in a
            assert "name" in a
            assert "description" in a
            assert "system_prompt" in a


class TestAgentIdentity:
    """AgentIdentity 数据类测试。"""

    def test_from_dict(self):
        """从 dict 创建 AgentIdentity。"""
        data = {
            "id": "test",
            "name": "测试",
            "system_prompt": "hello",
            "provider": "echo",
            "model": "echo-default",
        }
        agent = AgentIdentity(data)
        assert agent.id == "test"
        assert agent.name == "测试"
        assert agent.system_prompt == "hello"

    def test_to_dict(self):
        """to_dict 应返回完整字典。"""
        data = {
            "id": "test",
            "name": "测试",
            "system_prompt": "hello",
        }
        agent = AgentIdentity(data)
        d = agent.to_dict()
        assert d["id"] == "test"
        assert d["name"] == "测试"
        assert d["system_prompt"] == "hello"

    def test_defaults(self):
        """缺少字段时使用默认值。"""
        agent = AgentIdentity({"id": "minimal"})
        assert agent.id == "minimal"
        assert agent.name == ""
        assert agent.provider == "echo"
        assert agent.model == "echo-default"