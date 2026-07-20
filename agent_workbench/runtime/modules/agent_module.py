"""agent_workbench/runtime/modules/agent_module.py — Agent Identity 模块。

职责：
- 扫描 packages/ 目录，发现 Agent Identity 包。
- 管理 Active Agent 选择。
- 提供 system_prompt / provider / model 给运行时。
- 支持运行时切换 Agent（无需重启 Runtime）。

约束：
- 不进入 Runtime Kernel（Agent Identity 是应用层概念）。
- 不负责执行（只提供身份信息，不调用 LLM）。
- 不保存运行状态（只在切换时通知）。
"""
from __future__ import annotations

import yaml
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from agent_workbench.runtime.config_store import ConfigStore
from agent_workbench.runtime.modules.base import BaseRuntimeModule
from agent_workbench.runtime.metadata import (
    ModuleMetadata,
    PropertyMetadata,
    StatisticMetadata,
)

if TYPE_CHECKING:
    from agent_workbench.runtime.agent_runtime import AgentRuntime


class AgentIdentity:
    """Agent 身份描述。"""

    def __init__(self, data: Dict[str, Any]) -> None:
        self.id: str = data.get("id", "")
        self.name: str = data.get("name", "")
        self.version: str = data.get("version", "1.0.0")
        self.description: str = data.get("description", "")
        self.system_prompt: str = data.get("system_prompt", "")
        self.provider: str = data.get("provider", "echo")
        self.model: str = data.get("model", "echo-default")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "provider": self.provider,
            "model": self.model,
        }


class AgentModule(BaseRuntimeModule):
    """Agent Identity 模块。

    发现 packages/ 下的 agent manifest.yaml 文件，
    管理 Active Agent 选择，提供身份信息给运行时。
    """

    def __init__(self) -> None:
        self._runtime: "AgentRuntime | None" = None
        self._agents: Dict[str, AgentIdentity] = {}
        self._active_agent_id: str = "personal_agent"
        self._packages_dir: Path = Path(__file__).resolve().parents[3] / "packages"

    @property
    def namespace(self) -> str:
        return "agent"

    def initialize(self, runtime: "AgentRuntime") -> None:
        self._runtime = runtime
        self._discover_agents()

    def apply_config(self, store: ConfigStore) -> None:
        """从配置更新默认 Agent。"""
        default_agent = store.get("agent.default", "personal_agent")
        if default_agent in self._agents:
            self._active_agent_id = default_agent

    def _discover_agents(self) -> None:
        """扫描 packages/ 目录，发现 Agent Identity。"""
        if not self._packages_dir.exists():
            return
        for agent_dir in self._packages_dir.iterdir():
            if not agent_dir.is_dir():
                continue
            manifest = agent_dir / "manifest.yaml"
            if not manifest.exists():
                continue
            try:
                data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
                if isinstance(data, dict) and data.get("id"):
                    agent = AgentIdentity(data)
                    self._agents[agent.id] = agent
            except (yaml.YAMLError, OSError):
                continue

    def list_agents(self) -> List[Dict[str, Any]]:
        """返回所有已发现的 Agent 列表。"""
        return [a.to_dict() for a in self._agents.values()]

    def get_active_agent(self) -> AgentIdentity | None:
        """返回当前活跃的 Agent Identity。"""
        return self._agents.get(self._active_agent_id)

    def switch_agent(self, agent_id: str) -> bool:
        """切换到指定 Agent。

        Args:
            agent_id: Agent 标识（如 "personal_agent"、"coding_agent"）。

        Returns:
            True 如果切换成功。
        """
        if agent_id not in self._agents:
            return False
        old_id = self._active_agent_id
        self._active_agent_id = agent_id
        # 如果 Agent 指定了 provider/model，自动切换
        agent = self._agents[agent_id]
        if agent.provider and agent.provider != "echo":
            model_module = self._runtime.module_registry.get("model") if self._runtime else None
            if model_module is not None:
                model_module.switch_provider(agent.provider)
                if agent.model:
                    model_module.switch_model(agent.model)
        return True

    def get_system_prompt(self) -> str:
        """返回当前活跃 Agent 的 System Prompt。"""
        agent = self.get_active_agent()
        if agent:
            return agent.system_prompt
        return ""

    @property
    def active_agent_id(self) -> str:
        return self._active_agent_id

    def metadata(self) -> ModuleMetadata:
        """返回 Agent Identity Capability Metadata。"""
        agent_count = len(self._agents)
        return ModuleMetadata(
            id="agent",
            type="agent",
            name="Agent",
            description="Agent Identity 管理。",
            icon="user",
            properties=[
                PropertyMetadata(
                    name="active_agent",
                    label="Active Agent",
                    type="string",
                    value=self._active_agent_id,
                ),
            ],
            statistics=[
                StatisticMetadata(
                    name="agent_count",
                    label="Available Agents",
                    value=agent_count,
                    unit="agents",
                ),
            ],
        )