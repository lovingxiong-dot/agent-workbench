import sqlite3
import json
import os
from datetime import datetime
from langchain_core.chat_history import InMemoryChatMessageHistory

class MemoryManager:
    """三层记忆管理器：工作记忆（LangChain内置）、短期记忆（SQLite）、长期画像（JSON）"""
    
    def __init__(self, config: dict):
        self.short_term_db = config.get("short_term_db", "storage/short_term.db")
        self.user_profile_path = config.get("user_profile", "storage/user_profile.json")
        self.vector_store_path = config.get("vector_store", "storage/vector_store")
        
        # 工作记忆存储（按 session_id）
        self.store = {}
        self._init_short_term_db()
        self._init_user_profile()
    
    def _init_short_term_db(self):
        os.makedirs(os.path.dirname(self.short_term_db), exist_ok=True)
        conn = sqlite3.connect(self.short_term_db)
        conn.execute('''CREATE TABLE IF NOT EXISTS conversation_summaries
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       session_id TEXT,
                       summary TEXT,
                       timestamp DATETIME)''')
        conn.commit()
        conn.close()
    
    def _init_user_profile(self):
        os.makedirs(os.path.dirname(self.user_profile_path), exist_ok=True)
        if not os.path.exists(self.user_profile_path):
            with open(self.user_profile_path, "w", encoding="utf-8") as f:
                json.dump({
                    "preferred_quant_source": "akshare",
                    "default_python_env": "",
                    "risk_tolerance": "medium",
                    "frequent_tickers": [],
                    "custom_terms": {}
                }, f, indent=2)
    
    def get_session_history(self, session_id: str):
        if session_id not in self.store:
            self.store[session_id] = InMemoryChatMessageHistory()
        return self.store[session_id]
    
    def save_summary(self, session_id: str, summary: str):
        conn = sqlite3.connect(self.short_term_db)
        conn.execute("INSERT INTO conversation_summaries (session_id, summary, timestamp) VALUES (?, ?, ?)",
                     (session_id, summary, datetime.now()))
        conn.commit()
        conn.close()
    
    def load_user_profile(self) -> dict:
        with open(self.user_profile_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def update_user_profile(self, updates: dict):
        profile = self.load_user_profile()
        profile.update(updates)
        with open(self.user_profile_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)