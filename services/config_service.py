import os
import yaml
from pathlib import Path


class ConfigService:
    """统一配置管理：优先读取 .env，回退 config.yaml"""

    def __init__(self, config_path="config.yaml", env_path=".env"):
        self.config_path = config_path
        self.env_path = env_path
        self.config = {}
        self.reload()

    def reload(self):
        # Load .env
        if os.path.exists(self.env_path):
            from dotenv import load_dotenv
            load_dotenv(self.env_path, override=True)
        # Load config.yaml
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        # Override API keys from .env
        for name, cfg in self.config.get("llm_providers", {}).items():
            env_key = f"{name.upper().replace('-', '_')}_API_KEY"
            if os.getenv(env_key):
                cfg["api_key"] = os.getenv(env_key)

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
