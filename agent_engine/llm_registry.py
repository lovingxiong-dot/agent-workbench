import os
import yaml
from langchain_openai import ChatOpenAI


class LLMRegistry:
    """LLM 注册表：管理多个提供商，支持运行时增删改查并持久化到 yaml"""

    def __init__(self, config_path: str = "config.yaml", writable_path: str = None):
        self._writable_path = writable_path or config_path
        read_path = self._writable_path if os.path.exists(self._writable_path) else config_path
        with open(read_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        self._instances = {}

    # ── 查询 ──────────────────────────────────────
    def list_providers(self) -> dict:
        """返回所有提供商 {name: {base_url, model, api_key}}"""
        return self.config.get("llm_providers", {})

    def get_provider_config(self, name: str) -> dict:
        """获取单个提供商配置"""
        return self.config.get("llm_providers", {}).get(name, {})

    def get_llm(self, provider_name: str = "local-qwen"):
        if provider_name in self._instances:
            return self._instances[provider_name]

        cfg = self.config["llm_providers"].get(provider_name)
        if not cfg:
            raise ValueError(f"Unknown LLM provider: {provider_name}")

        llm = ChatOpenAI(
            model=cfg["model"],
            base_url=cfg["base_url"],
            api_key=cfg["api_key"],
            temperature=0.7,
            timeout=120,
        )
        self._instances[provider_name] = llm
        return llm

    # ── 增删改 ────────────────────────────────────
    def add_provider(self, name: str, cfg: dict):
        """添加或覆盖提供商"""
        self.config.setdefault("llm_providers", {})[name] = {
            "base_url": cfg.get("base_url", ""),
            "api_key": cfg.get("api_key", "not-needed"),
            "model": cfg.get("model", ""),
        }
        self._instances.pop(name, None)
        self._save()

    def remove_provider(self, name: str):
        """删除提供商"""
        self.config.get("llm_providers", {}).pop(name, None)
        self._instances.pop(name, None)
        self._save()

    def _save(self):
        """将当前配置写入可写路径"""
        os.makedirs(os.path.dirname(self._writable_path) or ".", exist_ok=True)
        with open(self._writable_path, "w", encoding="utf-8") as f:
            yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
