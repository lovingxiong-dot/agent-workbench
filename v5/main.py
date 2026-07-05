"""v5 程序入口：统一依赖注入，全程无 v4 依赖。"""
import sys

from PySide6.QtWidgets import QApplication

from core.event_bus import MessageBus

from v5.service.config_service import ConfigService
from v5.service.session_service import SessionService
from v5.service.adapter import V5Adapter
from v5.service.chat_service import ChatService
from v5.controller.work_controller import WorkController
from v5.main_window import MainWindow


def bootstrap() -> MainWindow:
    config = ConfigService(config_path="config/config.yaml")
    session_service = SessionService()
    bus = MessageBus()
    bus.connect_dispatch()

    adapter = V5Adapter(
        config=config,
        session_service=session_service,
        message_bus=bus,
    )
    chat_service = ChatService(adapter)

    controller = WorkController(
        config=config,
        session_service=session_service,
        chat_service=chat_service,
    )

    window = MainWindow(controller)
    controller.bootstrap()
    return window


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    window = bootstrap()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
