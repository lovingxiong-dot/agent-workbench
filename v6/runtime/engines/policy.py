"""v6/runtime/engines/policy.py — PolicyEngine：配置管理、策略决策、A/B 测试。

设计来源：V4 agent_engine/engines/policy_engine.py（提取核心逻辑）。

职责：读取 ctx.metadata 中 policy_query / query_features / session_metrics，
      写回 ctx.metadata["policy_result"] / ctx.metadata["next_action"]。
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from v6.runtime.engines.interfaces import IPolicyEngine


class PolicyEngine(IPolicyEngine):
    """策略引擎：配置驱动、热加载、模型选择。"""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self._config = config or {}
        self._mode_configs: Dict[str, Dict] = {}

    async def run(self, ctx: "RuntimeContext") -> "RuntimeContext":
        """执行策略查询，结果写回 ctx.metadata。"""
        query = ctx.metadata.get("policy_query")
        if isinstance(query, str):
            ctx.metadata["policy_result"] = self.get(query)

        features = ctx.metadata.get("query_features", {})
        if isinstance(features, dict):
            ctx.metadata["selected_model"] = self.select_model(features)

        session_metrics = ctx.metadata.get("session_metrics", {})
        if isinstance(session_metrics, dict):
            ctx.metadata["should_compress"] = self.should_compress(session_metrics)

        ctx.metadata["next_action"] = ctx.metadata.get("next_action", "continue")
        return ctx

    def get(self, path: str, default: Any = None) -> Any:
        """按点路径获取配置值，如 'ai_engine.context.compression_threshold'。"""
        keys = path.split(".")
        node: Any = self._config
        for key in keys:
            if not isinstance(node, dict):
                return default
            node = node.get(key)
            if node is None:
                return default
        return node

    def get_for_mode(self, mode: str, key: str) -> Any:
        """获取 mode 级配置，优先 mode 覆盖，回退 defaults。"""
        mode_cfg = self._mode_configs.get(mode, {})
        if key in mode_cfg:
            return mode_cfg[key]
        return self.get(f"agent.defaults.{key}")

    def select_model(self, query_features: Dict[str, Any]) -> str:
        """基于查询特征选模型 — 当前简化：返回配置中的默认模型。"""
        return self.get("app.last_model", "deepseek-pro")

    def should_compress(self, session_metrics: Dict[str, Any]) -> bool:
        """基于会话指标决定是否触发压缩。"""
        token_count = session_metrics.get("token_count", 0)
        threshold = session_metrics.get("max_tokens", 8192)
        return token_count > threshold * 0.85

    def reload(self) -> None:
        """热加载配置 — 占位，需对接文件监听机制。"""
        pass

    def set_mode_config(self, mode: str, config: Dict) -> None:
        """运行时注入 mode 配置。"""
        self._mode_configs[mode] = config

    def get_all(self) -> Dict:
        """返回完整配置快照。"""
        return dict(self._config)
