"""V6 阶段 0 smoke 测试：所有模块可导入。"""


def test_import_v6_package():
    import v6


def test_import_v6_ui_modules():
    from v6.ui import base, window_frame, left_panel, chat_area, right_panel
    from v6.ui import header_bar, input_area, chat_items, chat_scene
    from v6.ui import session_item, session_group, function_page
    from v6.ui import tab_button, recent_files, more_dropdown
    from v6.ui import terminal_widget, file_reader_widget, browser_widget
    from v6.ui import apple_menu, settings_dialog


def test_import_v6_runtime_modules():
    from v6.runtime import runtime, context, event_bus, scheduler, task
    from v6.runtime.engines import (
        base,
        llm,
        tool,
        memory,
        planner,
        workflow,
        code,
        vision,
        knowledge,
    )


def test_import_v6_managers():
    from v6 import ui_controller, layout_manager, session_manager, config_manager


def test_import_v6_services():
    from v6.services import config_service, session_service, chat_service
