#!/usr/bin/env python3
"""
craft 模式 Phase 工作流真实 LLM 端到端冒烟脚本。
使用 deepseek-pro，验证 analyze→confirm→execute→verify→archive 全链路。
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QEventLoop

from v4.main_window import MainWindow
from v4.events import WorkerResultEvent, WorkerErrorEvent, PhaseCompleteEvent, PhaseErrorEvent


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # 1. 切换到 craft 模式
    mode_selector = window.conversation_list.mode_selector
    idx = mode_selector.findData("craft")
    assert idx >= 0, f"模式下拉框中未找到 craft。可用模式: {[mode_selector.itemData(i) for i in range(mode_selector.count())]}"
    mode_selector.setCurrentIndex(idx)
    print(f"[OK] 模式已选择: {mode_selector.currentData()}")

    # 2. 输入消息并发送
    message = "请列出当前目录下的前3个文件"
    window.chat_area.input_field.setPlainText(message)
    window._on_send_message(message)
    print(f"[OK] 已发送消息: {message}")

    # 3. 等待确认条出现（analyze phase 完成后）
    loop = QEventLoop()
    QTimer.singleShot(60_000, loop.quit)  # 最多等 60 秒 analyze
    confirm_check_timer = QTimer()

    def check_confirm():
        if window.chat_area.confirm_bar.isVisible():
            print("[OK] 确认条已显示")
            confirm_check_timer.stop()
            loop.quit()

    confirm_check_timer.timeout.connect(check_confirm)
    confirm_check_timer.start(500)
    loop.exec()

    if not window.chat_area.confirm_bar.isVisible():
        print("[FAIL] 超时：确认条未显示（analyze phase 可能失败或未生成任务清单）")
        sys.exit(1)

    # 4. 自动点击确认
    print("[OK] 自动点击确认执行")
    window.chat_area.confirm_btn.click()

    # 5. 等待 phase 完成或错误
    result = {"done": False, "success": False, "text": "", "error": None}
    loop2 = QEventLoop()

    def on_phase_complete(event: PhaseCompleteEvent):
        result["done"] = True
        result["success"] = event.success
        result["text"] = event.message
        print(f"[OK] 收到 PhaseCompleteEvent: success={event.success}, message={event.message}")
        loop2.quit()

    def on_phase_error(event: PhaseErrorEvent):
        result["done"] = True
        result["success"] = False
        result["error"] = f"{event.code}: {event.detail}"
        print(f"[ERROR] 收到 PhaseErrorEvent: {result['error']}")
        loop2.quit()

    def on_worker_error(event: WorkerErrorEvent):
        result["done"] = True
        result["success"] = False
        result["error"] = f"{event.code}: {event.detail}"
        print(f"[ERROR] 收到 WorkerErrorEvent: {result['error']}")
        loop2.quit()

    window._bus.subscribe_name("phase", "complete", on_phase_complete)
    window._bus.subscribe_name("phase", "error", on_phase_error)
    window._bus.subscribe_name("worker", "error", on_worker_error)

    # 最多等 180 秒（craft task_timeout）
    QTimer.singleShot(180_000, loop2.quit)
    loop2.exec()

    if not result["done"]:
        print("[FAIL] 超时：未收到 phase 完成或错误事件")
        sys.exit(1)

    if not result["success"]:
        print(f"[FAIL] Phase 失败: {result.get('error') or result.get('text')}")
        sys.exit(1)

    # 6. 验证会话出现在列表中
    list_count = window.conversation_list._list.count()
    if list_count < 1:
        print("[FAIL] 会话未出现在列表中")
        sys.exit(1)
    print(f"[OK] 会话列表项数: {list_count}")

    print("\n[SUCCESS] craft 模式 Phase 工作流真实 LLM 冒烟通过")
    app.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
