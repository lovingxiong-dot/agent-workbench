import asyncio
from datetime import datetime, timedelta

class ProactiveEngine:
    """主动引擎：定时检查条件并推送建议（当前为占位实现）"""
    
    def __init__(self, memory_manager, llm_registry):
        self.memory = memory_manager
        self.llm_registry = llm_registry
        self.last_push_time = {}
    
    async def check_and_push(self, session_id: str, mode: str, user_profile: dict) -> str | None:
        """返回建议文本或 None"""
        # 简单冷却：同一会话 15 分钟内不重复推送
        now = datetime.now()
        if session_id in self.last_push_time:
            if now - self.last_push_time[session_id] < timedelta(minutes=15):
                return None
        
        # 占位逻辑：量化模式下可以主动推送市场概况
        if mode == "quant_dev":
            self.last_push_time[session_id] = now
            return "📊 主动提醒：您可查看今日市场概况（功能开发中）"
        
        return None