import copy
import json
import logging
import os
import sqlite3
from datetime import datetime

from langchain_core.chat_history import InMemoryChatMessageHistory

logger = logging.getLogger(__name__)


class MemoryManager:
    """三层记忆管理器：工作记忆（LangChain内置）、短期记忆（SQLite）、长期画像（JSON）"""

    def __init__(self, config: dict, storage_dir: str = ""):
        self.short_term_db = self._resolve_path(config.get("short_term_db", "storage/short_term.db"), storage_dir)
        self.user_profile_path = self._resolve_path(config.get("user_profile", "storage/user_profile.json"), storage_dir)
        self.vector_store_path = self._resolve_path(config.get("vector_store", "storage/vector_store"), storage_dir)

        # 框架层声明的默认画像（含 schema_version，作为结构迁移的锚点）
        self._profile_defaults = config.get("user_profile_defaults", {})

        # 工作记忆存储（按 session_id）
        self.store = {}
        self._init_short_term_db()
        self._profile = self._load_or_init_user_profile()

    @staticmethod
    def _resolve_path(path: str, storage_dir: str) -> str:
        """如果 path 是相对路径且提供了 storage_dir，则解析为绝对路径"""
        if not path:
            return path
        if os.path.isabs(path):
            return os.path.normpath(path)
        if storage_dir:
            return os.path.normpath(os.path.join(storage_dir, path))
        return os.path.normpath(path)

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

    def _load_or_init_user_profile(self) -> dict:
        """
        加载或初始化用户画像文件。
        - 文件不存在：用 config defaults 初始化并写入 schema_version。
        - 文件存在：比较文件 schema_version 与框架 schema_version，按需迁移。
        - 安全合并：仅补齐缺失的顶层 key，不覆盖用户已有值。
        """
        os.makedirs(os.path.dirname(self.user_profile_path), exist_ok=True)
        defaults = copy.deepcopy(self._profile_defaults)
        framework_version = defaults.get("schema_version", 0)

        if not os.path.exists(self.user_profile_path):
            profile = defaults
            self._save_profile(profile)
            return profile

        with open(self.user_profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)

        file_version = profile.get("schema_version", 0)

        if file_version < framework_version:
            profile = self._migrate_profile(profile, file_version, framework_version, defaults)
        elif file_version > framework_version:
            logger.warning(
                "Profile schema_version %s is newer than framework version %s. "
                "Possible config downgrade.",
                file_version,
                framework_version,
            )

        # 安全合并：仅补齐缺失的顶层 key，已有值完全保留
        for key, default_val in defaults.items():
            if key not in profile:
                profile[key] = copy.deepcopy(default_val)

        self._save_profile(profile)
        return profile

    def _migrate_profile(self, profile: dict, from_version: int, to_version: int, defaults: dict) -> dict:
        """
        画像结构迁移钩子。
        当前 v1 的核心语义是“补齐缺失字段”，已在主流程处理；
        后续版本可在此加入重命名、删除、类型转换等显式迁移逻辑。
        """
        profile["schema_version"] = to_version
        return profile

    def _save_profile(self, profile: dict):
        with open(self.user_profile_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)

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
        """返回当前用户画像的深拷贝，防止外部直接修改内部状态。"""
        return copy.deepcopy(self._profile)

    def update_user_profile(self, updates: dict):
        """更新用户画像。外部不允许覆盖 schema_version，避免破坏迁移锚点。"""
        updates = dict(updates)
        updates.pop("schema_version", None)

        profile = self.load_user_profile()
        profile.update(updates)
        self._profile = profile
        self._save_profile(profile)
