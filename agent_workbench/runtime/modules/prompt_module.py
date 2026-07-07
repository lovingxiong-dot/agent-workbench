"""agent_workbench/runtime/modules/prompt_module.py — Prompt 模块。

职责：
- Prompt 模板管理。
- PromptRenderer 切换与初始化。
- Prompt 热更新。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from agent_workbench.runtime.config_store import ConfigStore
from agent_workbench.runtime.metadata import (
    ActionMetadata,
    ModuleMetadata,
    PropertyMetadata,
    StatisticMetadata,
)
from agent_workbench.runtime.modules.base import BaseRuntimeModule
from agent_workbench.services.prompt_renderer import PromptRenderer
from agent_workbench.services.python_renderer import PythonRenderer

if TYPE_CHECKING:
    from agent_workbench.runtime.agent_runtime import AgentRuntime


class PromptModule(BaseRuntimeModule):
    """Prompt 能力模块。"""

    def __init__(self) -> None:
        self._runtime: "AgentRuntime | None" = None
        self._renderer: PromptRenderer = PythonRenderer()
        self._templates: Dict[str, Dict[str, Any]] = {}

    @property
    def namespace(self) -> str:
        return "prompt"

    @property
    def renderer(self) -> PromptRenderer:
        return self._renderer

    def initialize(self, runtime: "AgentRuntime") -> None:
        self._runtime = runtime

    def apply_config(self, store: ConfigStore) -> None:
        """热更新 Prompt 配置：切换 renderer、加载模板。"""
        renderer_name = store.get("prompt.renderer", "python")
        if renderer_name == "python":
            self._renderer = PythonRenderer()

        templates = store.get("prompt.templates", [])
        self._templates = {t["name"]: t for t in templates if "name" in t}

    def render(self, name: str, variables: Dict[str, Any]) -> str:
        """渲染指定模板。"""
        template = self._templates.get(name, {}).get("template", "")
        return self._renderer.render(template, variables)

    def list_templates(self) -> List[Dict[str, Any]]:
        """返回所有模板。"""
        return list(self._templates.values())

    def metadata(self) -> ModuleMetadata:
        """返回 Prompt Capability Metadata。"""
        templates = self.list_templates()
        return ModuleMetadata(
            id="prompt",
            type="prompt",
            name="Prompt",
            description="管理 Prompt 模板与渲染器。",
            icon="document-text",
            properties=[
                PropertyMetadata(
                    name="renderer",
                    label="Renderer",
                    type="select",
                    value="python",
                    options=["python"],
                ),
            ],
            statistics=[
                StatisticMetadata(name="templates_count", label="Templates", value=len(templates)),
            ],
            actions=[
                ActionMetadata(name="reload", label="Reload Templates", icon="refresh"),
            ],
        )
