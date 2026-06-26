"""
PersistenceService — UI 状态持久化服务

职责：
- 封装 mode / model / 会话等 UI 状态的持久化逻辑
- 提供可独立测试的接口，避免 MainWindow 直接操作 config dict
- 统一处理配置回退与校验
"""
from typing import Any, Dict, List, Optional, Tuple

from services.config_service import ConfigService


class PersistenceService:
    """UI 状态持久化服务"""

    def __init__(self, config_service: ConfigService):
        self._config = config_service

    # ═══════════════════════════════════════════════════
    # Mode / Model 持久化
    # ═══════════════════════════════════════════════════
    def save_mode(self, mode_name: str):
        """持久化当前模式到 app.last_mode"""
        self._config.set("app.last_mode", mode_name)
        self._config.save()

    def save_model(self, mode_name: str, model_name: str):
        """
        持久化当前模型：
        - manual_modes.<mode>.current_model
        - app.last_model
        """
        manual_cfg = self._config.config.setdefault("manual_modes", {})
        mode_cfg = manual_cfg.setdefault(mode_name, {})
        if not isinstance(mode_cfg, dict):
            mode_cfg = {}
            manual_cfg[mode_name] = mode_cfg
        mode_cfg["current_model"] = model_name
        self._config.set("app.last_model", model_name)
        self._config.save()

    def resolve_start_mode_model(
        self,
        available_modes: List[str],
        available_models: List[str],
        defaults: Tuple[str, str] = ("ask", "tool-agent"),
    ) -> Tuple[str, str]:
        """
        解析启动时应使用的 mode 和 model。
        若上次保存的值不在可用列表中，则回退到 defaults。
        """
        last_mode = self._config.get("app.last_mode", defaults[0])
        last_model = self._config.get("app.last_model", defaults[1])
        if last_mode not in available_modes:
            last_mode = defaults[0]
        if last_model not in available_models:
            last_model = available_models[0] if available_models else defaults[1]
        return last_mode, last_model

    def get_mode_model(self, mode_name: str) -> Optional[str]:
        """获取指定模式下最后一次选用的模型"""
        return self._config.get(f"manual_modes.{mode_name}.current_model")

    # ═══════════════════════════════════════════════════
    # 通用键值持久化
    # ═══════════════════════════════════════════════════
    def set(self, key: str, value: Any):
        self._config.set(key, value)

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def save(self):
        self._config.save()

    # ═══════════════════════════════════════════════════
    # 批量快照（用于会话状态保存）
    # ═══════════════════════════════════════════════════
    def snapshot_app_state(self, state: Dict[str, Any]):
        """保存应用级状态字典到 app.*"""
        app_cfg = self._config.config.setdefault("app", {})
        if not isinstance(app_cfg, dict):
            app_cfg = {}
            self._config.config["app"] = app_cfg
        app_cfg.update(state)
        self._config.save()
