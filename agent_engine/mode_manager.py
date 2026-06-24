import yaml


class ModeManager:
    """模式管理器：纯配置读取，不再做自动分类"""

    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    def get_mode_config(self, mode_name: str) -> dict:
        """获取指定手动模式的配置"""
        return self.config.get("manual_modes", {}).get(mode_name, {})

    def get_tool_names(self, mode_name: str) -> list:
        """获取指定模式下允许使用的工具列表"""
        return self.get_mode_config(mode_name).get("tools", [])
