"""v6/runtime/engines/prompt.py — PromptEngine：System Prompt 构建、模板渲染、画像注入。

设计来源：V4 agent_engine/engines/prompt_engine.py（提取核心逻辑）。

职责：读取 ctx.mode / ctx.phase / ctx.metadata 中 user_profile / workspace_context，
      写回 ctx.metadata["system_prompt"]。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from v6.runtime.engines.interfaces import IPromptEngine


_DEFAULT_PHASE_INSTRUCTIONS: Dict[str, str] = {
    "analyze": (
        "\n\n## Analysis Phase\n"
        "You are in the ANALYSIS phase. Your task is to:\n"
        "1. Understand the user's request thoroughly\n"
        "2. Break down complex problems into actionable sub-tasks\n"
        "3. Identify required tools, data sources, and dependencies\n"
        "4. Produce a structured task list for execution\n"
        "Do NOT execute tools yet. Focus on planning and analysis only."
    ),
    "verify": (
        "\n\n## Verification Phase\n"
        "You are in the VERIFICATION phase. Your task is to:\n"
        "1. Review execution results against the original requirements\n"
        "2. Check for correctness, completeness, and consistency\n"
        "3. Identify any issues, errors, or missing work\n"
        "4. Summarize findings and recommend next steps\n"
        "Do NOT execute new tools unless explicitly required for verification."
    ),
    "execute": "",
}


class PromptEngine(IPromptEngine):
    """Prompt 引擎：按层次组装 System Prompt。"""

    def __init__(
        self,
        base_prompts: Optional[Dict[str, str]] = None,
        phase_prompts: Optional[Dict[str, str]] = None,
        user_rules: Optional[List[str]] = None,
        app_version: str = "v6.x",
        model_name: str = "",
    ) -> None:
        self.base_prompts = base_prompts or {}
        self.phase_prompts = phase_prompts or {}
        self.user_rules = user_rules or []
        self.app_version = app_version or "v6.x"
        self.model_name = model_name or ""

    async def run(self, ctx: "RuntimeContext") -> "RuntimeContext":
        """构建 system prompt 并写回 ctx.metadata['system_prompt']。"""
        system_prompt = self.build_system_prompt(
            mode=ctx.mode,
            phase=ctx.phase or "execute",
            user_profile=ctx.metadata.get("user_profile"),
        )
        workspace_context = ctx.metadata.get("workspace_context", "")
        ctx.metadata["system_prompt"] = self.inject_context(
            system_prompt, workspace_context
        )
        return ctx

    def build_system_prompt(
        self,
        mode: str,
        phase: str = "execute",
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> str:
        """构建完整 system prompt。"""
        parts: List[str] = []

        base = self.base_prompts.get(mode, self.base_prompts.get("default", ""))
        if base:
            parts.append(base)

        phase_instruction = self.phase_prompts.get(phase) or _DEFAULT_PHASE_INSTRUCTIONS.get(
            phase, ""
        )
        if phase_instruction:
            parts.append(phase_instruction)

        if user_profile:
            profile_block = self._format_profile(user_profile)
            if profile_block:
                parts.append(f"\n\n## User Profile\n{profile_block}")

        return "\n".join(parts)

    def build_identity_block(self) -> str:
        """构建 AI 身份声明块。"""
        if self.model_name:
            return (
                f"You are AI Agent Workbench {self.app_version}, "
                f"powered by {self.model_name}."
            )
        return f"You are AI Agent Workbench {self.app_version}."

    def build_user_rules_block(self) -> str:
        """构建用户规则块（编号列表）。"""
        if not self.user_rules:
            return ""
        lines = ["## User Rules"]
        for i, rule in enumerate(self.user_rules, 1):
            lines.append(f"{i}. {rule}")
        return "\n".join(lines)

    def inject_context(self, base_prompt: str, workspace_context: str) -> str:
        """注入工作区上下文到 prompt。"""
        if not workspace_context:
            return base_prompt
        block = f"\n\n## Workspace Context\n{workspace_context}"
        return base_prompt + block

    @staticmethod
    def _format_profile(profile: Dict[str, Any]) -> str:
        """将用户画像字典格式化为文本。"""
        try:
            lines: List[str] = []
            for key, value in profile.items():
                if value is None:
                    continue
                label = key.replace("_", " ").title()
                lines.append(f"- {label}: {value}")
            return "\n".join(lines)
        except Exception:
            return str(profile)
