#!/usr/bin/env python3
"""
UI 折叠结构视觉验证脚本（无 LLM 依赖）。
使用 StubWorkerManager 触发 craft 流程事件，检查 ChatArea HTML 中是否包含
阶段面板、工具折叠、思考折叠等预期结构。
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QEventLoop

from v4.main_window import MainWindow
from v4.events import (
    WorkerCreatedEvent, WorkerResultEvent, WorkerToolEvent, PhaseCompleteEvent,
    PhaseChangedEvent, PhaseConfirmRequiredEvent,
)
from v4.worker_manager import WorkerManager


class StubWorkerManager(WorkerManager):
    """不创建真实 Worker，直接按 craft 流程发射事件。"""

    def __init__(self, message_bus):
        super().__init__(message_bus=message_bus, max_workers=WorkerManager.MAX_WORKERS)

    def _create_worker(self, event):
        worker_id = f"worker_{event.session_id[-8:]}"
        self._workers[event.session_id] = object()
        self.worker_count_changed.emit(self.active_count)
        self._bus.emit(WorkerCreatedEvent(session_id=event.session_id, worker_id=worker_id))

        # 模拟 analyze → confirm → execute → verify → archive 事件序列
        QTimer.singleShot(50, lambda: self._emit_analyze(event.session_id, worker_id))

    def _emit_analyze(self, sid, worker_id):
        self._bus.emit(PhaseChangedEvent(session_id=sid, phase="analyze", task_count=0))
        ai_text = (
            "## 任务分析\n\n"
            "需要完成以下子任务：\n"
            "思考过程\n"
            "[x] 读取配置文件\n"
            "[ ] 修改模型选择器\n"
            "[ ] 运行全量测试\n\n"
            "预计改动 3 个文件。"
        )
        self._bus.emit(WorkerResultEvent(session_id=sid, worker_id=worker_id, full_text=ai_text))
        tasks = [
            {"description": "修改 v4/events.py 新增 model 字段"},
            {"description": "修改 v4/main_window.py 模型下拉框"},
            {"description": "修改 v4/orchestrator.py 使用当前模型"},
        ]
        self._bus.emit(PhaseConfirmRequiredEvent(session_id=sid, task_list=tasks))


def main():
    app = QApplication(sys.argv)
    window = MainWindow()

    # 替换为桩 WorkerManager
    old_wm = window._worker_mgr
    window._bus.unsubscribe(old_wm._on_create)
    window._bus.unsubscribe(old_wm._on_destroy)
    stub = StubWorkerManager(window._bus)
    window._worker_mgr = stub
    window._orchestrator._worker_mgr = stub

    window.show()

    # 切换到 craft 模式并发送消息
    mode_selector = window.conversation_list.mode_selector
    idx = mode_selector.findData("craft")
    mode_selector.setCurrentIndex(idx)

    window.chat_area.input_field.setPlainText("验证折叠 UI")
    window.chat_area.send_btn.click()

    # 等待事件处理
    loop = QEventLoop()
    QTimer.singleShot(1500, loop.quit)
    loop.exec()

    html = window.chat_area.chat_area.toHtml()
    msgs = window.chat_area._messages
    print("--- message state check ---")
    print(f"  message count: {len(msgs)}")
    for i, m in enumerate(msgs):
        print(f"  msg[{i}] role={m.get('role')} phase={m.get('phase')} thinking_len={len(m.get('thinking_fold',''))} tools={len(m.get('tools',[]))}")
    print("--- end snippet ---")
    checks = [
        ("phase-panel analyze", any(m.get("phase") == "analyze" for m in msgs if m.get("role") == "ai")),
        ("阶段标题 分析结果", "📋 分析结果" in html),
        ("思考过程折叠", any("fold-block" in m.get("thinking_fold", "") for m in msgs)),
        ("思考任务", any("think-task" in m.get("thinking_fold", "") for m in msgs)),
        ("确认条", window.chat_area.confirm_bar.isVisible()),
    ]

    # 模拟工具事件，验证工具折叠
    sid = window._orchestrator.current_session_id
    if sid:
        window._bus.emit(WorkerToolEvent(
            session_id=sid,
            worker_id="worker_test",
            tool_name="run_command",
            args={"command": "echo hello"},
            result="line1\nline2\n" + "x" * 300,
            elapsed_ms=120,
            success=True,
        ))
        # 处理事件
        QTimer.singleShot(100, loop.quit)
        loop.exec()

    html = window.chat_area.chat_area.toHtml()
    msgs = window.chat_area._messages
    tool_htmls = [t for m in msgs for t in m.get("tools", [])]
    print("--- tool state check ---")
    print(f"  tool blocks: {len(tool_htmls)}")
    for i, t in enumerate(tool_htmls):
        print(f"  tool[{i}] contains run_command: {'run_command' in t}, contains fold-block: {'fold-block' in t}")
    print("--- end snippet ---")
    checks.extend([
        ("工具条目", any("tool-entry" in t for t in tool_htmls)),
        ("工具名称 run_command", any("run_command" in t for t in tool_htmls)),
        ("内部命令输出折叠", any("内部命令输出" in t for t in tool_htmls)),
    ])

    # 验证折叠交互：模拟点击思考过程折叠头，检查 fold_states 是否更新
    thinking_msg = next((m for m in msgs if m.get("thinking_fold")), None)
    if thinking_msg:
        import re
        fold_id_match = re.search(r'id="(think-[^"]+)"', thinking_msg["thinking_fold"])
        if fold_id_match:
            fold_id = fold_id_match.group(1)
            before = fold_id in window.chat_area._fold_states
            from PySide6.QtCore import QUrl
            window.chat_area._on_anchor_clicked(QUrl(f"fold://toggle/{fold_id}"))
            after = fold_id in window.chat_area._fold_states
            checks.append(("折叠点击可展开", not before and after))
            # 再次点击收回
            window.chat_area._on_anchor_clicked(QUrl(f"fold://toggle/{fold_id}"))
            checks.append(("折叠点击可收起", fold_id not in window.chat_area._fold_states))

    all_ok = True
    for name, ok in checks:
        status = "OK" if ok else "FAIL"
        print(f"[{status}] {name}")
        if not ok:
            all_ok = False

    window.close()
    window.deleteLater()
    app.processEvents()

    if all_ok:
        print("\n[SUCCESS] UI 折叠结构验证通过")
        sys.exit(0)
    else:
        print("\n[FAIL] UI 折叠结构验证未通过")
        sys.exit(1)


if __name__ == "__main__":
    main()
