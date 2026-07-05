"""V5 标准化事件定义。"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SessionCreateEvent:
    session_type: str = "chat"
    model: str = "tool-agent"
    mode: str = "ask"
    project_path: str = ""


@dataclass
class SessionSwitchEvent:
    session_id: str = ""


@dataclass
class SessionDeleteEvent:
    session_id: str = ""


@dataclass
class SessionRenameEvent:
    session_id: str = ""
    new_title: str = ""


@dataclass
class SessionPinEvent:
    session_id: str = ""
    pinned: bool = True


@dataclass
class UserSendEvent:
    session_id: str = ""
    text: str = ""
    model: str = "tool-agent"
    mode: str = "ask"
    session_type: str = "chat"
    project_path: str = ""


@dataclass
class UserStopEvent:
    session_id: str = ""


@dataclass
class UIChatUserEvent:
    text: str = ""


@dataclass
class UIChatAIEvent:
    text: str = ""
    phase: str = ""


@dataclass
class UIStreamChunkEvent:
    text: str = ""


@dataclass
class UIStreamDoneEvent:
    pass


@dataclass
class UISetStreamingEvent:
    streaming: bool = False


@dataclass
class UIUpdateSessionsEvent:
    sessions: list = field(default_factory=list)


@dataclass
class UISetActiveSessionEvent:
    session_id: str = ""


@dataclass
class UISetTitleEvent:
    title: str = "新会话"
    env: str = ""


@dataclass
class UIOpenFileEvent:
    path: str = ""


@dataclass
class UITerminalOutputEvent:
    text: str = ""


@dataclass
class UISwitchTabEvent:
    tab: str = ""
