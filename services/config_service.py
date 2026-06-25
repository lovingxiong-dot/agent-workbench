import os
import re
import yaml


class ConfigService:
    """ConfigService: os.environ > .env file > config.yaml placeholders"""

    def __init__(self, config_path="config.yaml", env_path=".env"):
        self.config_path = config_path
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
        return self.config.get(key, default)
