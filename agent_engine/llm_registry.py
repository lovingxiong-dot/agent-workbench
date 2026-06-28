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
        self._resolve_env_vars(self.config)
        self._instances = {}

    def _resolve_env_vars(self, data, seen=None):
        """递归替换 ${ENV_VAR} 占位符"""
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
                    data[key] = os.environ.get(var_name, value)
                elif isinstance(value, (dict, list)):
                    self._resolve_env_vars(value, seen)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, str) and item.startswith("${"):
                    var_name = item.strip("${}")
                    data[i] = os.environ.get(var_name, item)
                elif isinstance(item, (dict, list)):
                    self._resolve_env_vars(item, seen)

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
        """保存配置，自动将 API Key 替换回 ${VAR} 占位符以防泄露"""
        import copy
        cfg = copy.deepcopy(self.config)
        for name, provider in cfg.get("llm_providers", {}).items():
            api_key = provider.get("api_key", "")
            env_key = f"{name.upper().replace('-', '_')}_API_KEY"
            if os.environ.get(env_key) and os.environ.get(env_key) == api_key:
                provider[env_key.lower()] = f"${{{env_key}}}"
                provider["api_key"] = f"${{{env_key}}}"
        os.makedirs(os.path.dirname(self._writable_path) or ".", exist_ok=True)
        with open(self._writable_path, "w", encoding="utf-8") as f:
            yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
