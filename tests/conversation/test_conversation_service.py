"""Tests for ConversationService and auto title generation."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)

from v6.runtime.context import RuntimeContext
from v6.services.chat_service import ChatService
from v6.services.session_service import SessionService

from agent_workbench.conversation import ConversationService


@pytest.fixture
def services(tmp_path):
    session_service = SessionService(data_dir=tmp_path)
    chat_service = ChatService(session_manager=session_service.manager, data_dir=tmp_path)
    conversation_service = ConversationService(session_service, chat_service)
    return conversation_service, session_service, chat_service


class TestConversationServiceCreate:
    def test_create_conversation_with_empty_title(self, services):
        conversation_service, session_service, _ = services
        sid = conversation_service.create_conversation()
        session = session_service.manager.get(sid)
        assert session is not None
        assert session["title"] == ""

    def test_create_conversation_with_custom_title(self, services):
        conversation_service, session_service, _ = services
        sid = conversation_service.create_conversation("Custom Title")
        session = session_service.manager.get(sid)
        assert session["title"] == "Custom Title"


class TestConversationServiceMessagesAndTitle:
    def test_store_user_message_does_not_generate_title(self, services):
        conversation_service, session_service, _ = services
        sid = conversation_service.create_conversation()
        conversation_service.store_user_message(sid, "帮我分析代码")
        session = session_service.manager.get(sid)
        assert session["title"] == ""

    def test_store_assistant_message_generates_title_from_first_user_message(self, services):
        conversation_service, session_service, _ = services
        sid = conversation_service.create_conversation()
        conversation_service.store_user_message(sid, "帮我分析这个 Python 文件")
        generated = conversation_service.store_assistant_message(sid, "好的，我先看文件结构。")
        assert generated == "帮我分析这个 Python 文件"

        session = session_service.manager.get(sid)
        assert session["title"] == generated

    def test_store_assistant_message_does_not_overwrite_existing_title(self, services):
        conversation_service, session_service, _ = services
        sid = conversation_service.create_conversation("Manual Title")
        conversation_service.store_user_message(sid, "新的用户消息")
        generated = conversation_service.store_assistant_message(sid, "回复")
        assert generated is None

        session = session_service.manager.get(sid)
        assert session["title"] == "Manual Title"

    def test_load_messages_returns_both_roles(self, services):
        conversation_service, _, _ = services
        sid = conversation_service.create_conversation()
        conversation_service.store_user_message(sid, "hello")
        conversation_service.store_assistant_message(sid, "hi")
        messages = conversation_service.load_messages(sid)
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"


class TestConversationServiceLifecycle:
    def test_rename_conversation(self, services):
        conversation_service, session_service, _ = services
        sid = conversation_service.create_conversation()
        conversation_service.rename_conversation(sid, "Renamed")
        assert session_service.manager.get(sid)["title"] == "Renamed"

    def test_delete_conversation(self, services):
        conversation_service, session_service, _ = services
        sid = conversation_service.create_conversation()
        conversation_service.delete_conversation(sid)
        assert session_service.manager.get(sid) is None

    def test_pin_conversation(self, services):
        conversation_service, session_service, _ = services
        sid = conversation_service.create_conversation()
        assert conversation_service.pin_conversation(sid) is True
        assert session_service.manager.get(sid)["is_pinned"] is True
        assert conversation_service.pin_conversation(sid) is False

    def test_list_groups_after_create(self, services):
        conversation_service, _, _ = services
        conversation_service.create_conversation()
        groups = conversation_service.list_groups()
        assert len(groups) == 1
        assert len(groups[0][2]) == 1
