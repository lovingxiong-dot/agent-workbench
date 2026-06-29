"""
Policy Engine — 配置管理、策略决策、A/B 测试

从 config.yaml 读取配置，提供 dot-path 查询接口。
闭环：MetricsEngine 数据 → PolicyEngine 评估 → 调整策略参数
"""
from typing import Any, Dict, Optional
from .interfaces import IPolicyEngine


class PolicyEngine(IPolicyEngine):
    """策略引擎：配置驱动、热加载、模型选择"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = config or {}
        self._mode_configs: Dict[str, Dict] = {}

    def get(self, path: str, default: Any = None) -> Any:
        """按点路径获取配置，如 'ai_engine.context.compression_threshold'"""
        keys = path.split(".")
        node = self._config
        for key in keys:
            if not isinstance(node, dict):
                return default
            node = node.get(key)
            if node is None:
                return default
        return node

    def get_for_mode(self, mode: str, key: str) -> Any:
        """获取 mode 级配置，优先 mode 覆盖，回退 defaults"""
        mode_cfg = self._mode_configs.get(mode, {})
        if key in mode_cfg:
            return mode_cfg[key]
        return self.get(f"agent.defaults.{key}")

    def select_model(self, query_features: Dict[str, Any]) -> str:
        """基于查询特征选模型 — 当前简化：返回配置中的默认模型"""
        return self.get("app.last_model", "deepseek-pro")

    def should_compress(self, session_metrics: Dict[str, Any]) -> bool:
        token_count = session_metrics.get("token_count", 0)
        threshold = session_metrics.get("max_tokens", 8192)
        return token_count > threshold * 0.85

    def reload(self) -> None:
        """热加载配置 — 占位，需对接文件监听机制"""
        pass

    def set_mode_config(self, mode: str, config: Dict) -> None:
        """运行时注入 mode 配置"""
        self._mode_configs[mode] = config

    def get_all(self) -> Dict:
        """返回完整配置快照"""
        return dict(self._config)
