"""
MainWindow UI 自动化测试

不依赖 pytest-qt，直接实例化 QApplication + MainWindow，通过 processEvents()
驱动 Qt 事件循环，模拟用户点击与输入，验证：
1. 新会话按钮可无限添加标签
2. 发送第一条消息后会话标题更新为内容摘要
3. 新建/切换会话后输入框自动获得焦点

所有测试使用临时 storage 目录，避免污染真实数据。
"""
import os
import shutil
import sys
import tempfile

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer


@pytest.fixture(scope="module")
def qt_app():
    """提供全局 QApplication 单例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def _process_events(app, ms=50):
    """处理 Qt 事件并短暂等待定时器"""
    app.processEvents()
    # 让可能存在的 singleShot 定时器有机会执行
    QTimer.singleShot(ms, app.quit)
    # 非阻塞：仅处理事件，不进入 exec()
    for _ in range(10):
        app.processEvents()


def _count_sessions(window):
    """返回当前项目会话与全局会话数量"""
    return (
        window.conversation_list.project_list.count(),
        window.conversation_list.global_list.count(),
    )


@pytest.fixture
def main_window(qt_app):
    """创建使用临时 storage 的 MainWindow"""
    tmp_dir = tempfile.mkdtemp(prefix="awb_ui_test_")
    storage_dir = os.path.join(tmp_dir, "storage")
    os.makedirs(storage_dir, exist_ok=True)

    from services.app_context import AppContext
    from services.session_orchestrator import SessionOrchestrator
    from ui.main_window import MainWindow

    app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(app_root, "config.yaml")

    app_ctx = AppContext(
        config_path=config_path,
        writable_config_path=config_path,
        storage_dir=storage_dir,
        app_root=app_root,
    )
    orchestrator = SessionOrchestrator(
        app_context=app_ctx,
        message_bus=app_ctx.message_bus,
        task_service=app_ctx.task_service,
    )
    window = MainWindow(app_context=app_ctx, session_orchestrator=orchestrator)
    window.show()
    _process_events(qt_app, 100)

    yield window

    # 清理：尝试停止 Worker 并关闭窗口
    try:
        window.close()
        qt_app.processEvents()
    except Exception:
        pass
    shutil.rmtree(tmp_dir, ignore_errors=True)


class TestNewConversation:
    """验证新会话按钮可无限添加"""

    def test_global_new_conversation_multiple_times(self, qt_app, main_window):
        initial_project, initial_global = _count_sessions(main_window)
        clicks = 3

        for _ in range(clicks):
            main_window._on_new_conversation_requested("")
            _process_events(qt_app, 50)

        final_project, final_global = _count_sessions(main_window)
        assert final_project == initial_project, "项目会话不应被全局按钮影响"
        assert final_global == initial_global + clicks, (
            f"全局会话数应为 {initial_global + clicks}，实际为 {final_global}"
        )

    def test_project_new_conversation_multiple_times(self, qt_app, main_window):
        # 确保 _project_root 有效，否则测试无意义
        project_root = main_window._project_root or main_window.file_tree.get_root_path()
        if not project_root:
            pytest.skip("当前未检测到项目路径，跳过项目会话测试")

        initial_project, initial_global = _count_sessions(main_window)
        clicks = 3

        for _ in range(clicks):
            main_window._on_new_conversation_requested("<project>")
            _process_events(qt_app, 50)

        final_project, final_global = _count_sessions(main_window)
        assert final_global == initial_global, "项目按钮不应创建全局会话"
        assert final_project == initial_project + clicks, (
            f"项目会话数应为 {initial_project + clicks}，实际为 {final_project}"
        )


class TestConversationTitle:
    """验证发送第一条消息后标题更新为内容摘要"""

    def test_title_updates_after_first_message(self, qt_app, main_window):
        # 先新建一个干净的全局会话，避免受启动默认会话历史影响
        main_window._on_new_conversation_requested("")
        _process_events(qt_app, 50)

        session_id = main_window._current_session
        test_text = "hello this is a test message for title update"
        main_window.chat_view.input_field.setText(test_text)
        main_window._send_message(test_text)
        _process_events(qt_app, 100)

        session = main_window._session_mgr.get_session_data(session_id)
        title = session.get("title", "")
        expected = test_text[:20] + "..." if len(test_text) > 20 else test_text
        assert title == expected, f"会话标题应为 {expected!r}，实际为 {title!r}"

        # 验证列表项同步更新
        list_text = None
        for lst in (main_window.conversation_list.project_list,
                    main_window.conversation_list.global_list):
            for i in range(lst.count()):
                item = lst.item(i)
                if item.data(Qt.UserRole) == session_id:
                    list_text = item.text()
                    break
            if list_text:
                break

        # tooltip 不含状态图标，适合作为标题真实值断言
        list_tooltip = None
        for lst in (main_window.conversation_list.project_list,
                    main_window.conversation_list.global_list):
            for i in range(lst.count()):
                item = lst.item(i)
                if item.data(Qt.UserRole) == session_id:
                    list_tooltip = item.toolTip()
                    break
            if list_tooltip:
                break

        assert list_tooltip == expected, f"列表项 tooltip 应为 {expected!r}，实际为 {list_tooltip!r}"


class TestInputFocus:
    """验证新建/切换会话后输入框焦点"""

    def test_input_field_focus_after_new_conversation(self, qt_app, main_window):
        main_window._on_new_conversation_requested("")
        _process_events(qt_app, 50)
        # hasFocus 在窗口未真正激活时可能为 False，此处验证代码路径已调用 setFocus()
        # 通过检查输入框是窗口焦点链中的最后一个 FocusWidget 来间接验证
        assert main_window.chat_view.input_field == main_window.focusWidget(), (
            "新建会话后输入框应成为当前焦点控件"
        )
