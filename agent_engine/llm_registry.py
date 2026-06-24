import yaml
from langchain_openai import ChatOpenAI

class LLMRegistry:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        self._instances = {}
    
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