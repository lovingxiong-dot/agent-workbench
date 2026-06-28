import copy
import os
import re
import yaml


class ConfigService:
    """ConfigService: os.environ > .env file > config.yaml placeholders"""

    def __init__(self, config_path="config.yaml", env_path=".env", writable_path=None):
        self.config_path = config_path
        self._writable_path = writable_path or config_path
        self.env_path = env_path
        self.config = {}
        self.reload()

    def reload(self):
        if os.path.exists(self.env_path):
            try:
                from dotenv import load_dotenv
                load_dotenv(self.env_path, override=False)
            except ImportError:
                pass

        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self._resolve_env_vars(self.config)

    def _resolve_env_vars(self, data, seen=None):
        if seen is None:
            seen = set()
        obj_id = id(data)
        if obj_id in seen:
            return
        seen.add(obj_id)

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and value.startswith("${"):
                    var_name = value.strip("${}")
                    resolved = os.environ.get(var_name, "")
                    if resolved:
                        data[key] = resolved
                elif isinstance(value, (dict, list)):
                    self._resolve_env_vars(value, seen)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, str) and item.startswith("${"):
                    var_name = item.strip("${}")
                    resolved = os.environ.get(var_name, "")
                    if resolved:
                        data[i] = resolved
                elif isinstance(item, (dict, list)):
                    self._resolve_env_vars(item, seen)

    def get_provider_config(self, name):
        return self.config.get("llm_providers", {}).get(name, {})

    def get_api_key(self, provider_name):
        provider = self.get_provider_config(provider_name)
        return provider.get("api_key", "")

    def get_base_url(self, provider_name):
        provider = self.get_provider_config(provider_name)
        return provider.get("base_url", "")

    def get_model(self, provider_name):
        provider = self.get_provider_config(provider_name)
        return provider.get("model", "")

    def get(self, key, default=None):
        """支持点号路径访问嵌套配置，例如 app.version"""
        if not isinstance(key, str) or "." not in key:
            return self.config.get(key, default)
        value = self.config
        for part in key.split("."):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        return value if value is not None else default

    def set(self, key: str, value):
        """支持点号路径写入嵌套配置，例如 terminal.preferred_interpreter"""
        if not isinstance(key, str) or "." not in key:
            self.config[key] = value
            return
        parts = key.split(".")
        d = self.config
        for p in parts[:-1]:
            if p not in d or not isinstance(d[p], dict):
                d[p] = {}
            d = d[p]
        d[parts[-1]] = value

    def get_mode_config(self, mode_name):
        """获取指定手动模式的完整配置（system_prompt、tools、current_model 等）"""
        return self.config.get("manual_modes", {}).get(mode_name, {})

    def get_agent_config(self, mode_name=None):
        """
        获取 agent 配置段。
        若指定 mode_name，返回 mode 级配置与 defaults 的合并结果（mode 优先）。
        """
        agent_cfg = self.config.get("agent", {})
        defaults = agent_cfg.get("defaults", {})
        if not mode_name:
            return defaults
        mode_cfg = agent_cfg.get(mode_name, {})
        merged = dict(defaults)
        merged.update(mode_cfg)
        return merged

    def get_max_tool_rounds(self, mode_name="ask"):
        """获取指定模式下 ReAct 工具调用的最大轮数"""
        return self.get_agent_config(mode_name).get("max_tool_rounds", 8)

    def get_task_timeout(self, mode_name="ask"):
        """获取指定模式下 Agent 任务总超时（秒）"""
        return self.get_agent_config(mode_name).get("task_timeout", 120.0)

    def get_llm_timeout(self, mode_name="ask"):
        """获取指定模式下单次 LLM 调用超时（秒）"""
        return self.get_agent_config(mode_name).get("llm_timeout", 90.0)

    def get_tool_timeout(self, mode_name="ask"):
        """获取指定模式下单轮工具执行超时（秒）"""
        return self.get_agent_config(mode_name).get("tool_timeout", 30.0)

    def save(self):
        """将当前配置写回文件；保存前把已解析的 API Key 还原为 ${...} 占位符，避免明文泄露。"""
        cfg = copy.deepcopy(self.config)
        for name, provider in cfg.get("llm_providers", {}).items():
            api_key = provider.get("api_key", "")
            env_key = f"{name.upper().replace('-', '_')}_API_KEY"
            env_value = os.environ.get(env_key, "")
            if env_value and api_key == env_value:
                provider["api_key"] = f"${{{env_key}}}"
        os.makedirs(os.path.dirname(self._writable_path) or ".", exist_ok=True)
        with open(self._writable_path, "w", encoding="utf-8") as f:
            yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
