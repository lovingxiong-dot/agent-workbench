"""agent_workbench/app.py — Agent Workbench V6 应用入口。

边界：
- 属于 Application Layer，不属于 v6-core / v6-service。
- 加载配置、启动 WorkbenchController、提供 CLI / GUI 入口。
"""
from __future__ import annotations

import argparse
import sys
from typing import Any, Dict

from agent_workbench.config.loader import ConfigLoader, default_config
from agent_workbench.controller import WorkbenchController


def run_cli(config: Dict[str, Any], test_input: str | None = None) -> int:
    """命令行交互模式。

    Args:
        config: Agent 配置。
        test_input: 若提供，直接以此输入运行一次后退出（用于测试）。
    """
    print(f"[{config['agent']['name']}] 已启动")

    controller = WorkbenchController()
    controller.start()
    try:
        if test_input is not None:
            ctx = controller.chat(test_input)
            assistant = [m for m in ctx.messages if m.role == "assistant"]
            if assistant:
                print(f"AI: {assistant[-1].content}")
            return 0

        print("输入消息按回车，输入 'exit' 退出。")
        while True:
            text = input("> ").strip()
            if text.lower() in {"exit", "quit"}:
                break
            if not text:
                continue

            ctx = controller.chat(text)
            assistant = [m for m in ctx.messages if m.role == "assistant"]
            if assistant:
                print(f"AI: {assistant[-1].content}")
            else:
                print(f"Status: {ctx.status}")
    finally:
        controller.stop()
    return 0


def run_gui(config: Dict[str, Any]) -> int:
    """Desktop UI 模式。"""
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:  # pragma: no cover - optional
        print("PySide6 未安装，回退到 CLI 模式。")
        return run_cli(config)

    from agent_workbench.ui.main_window import WorkbenchMainWindow
    from agent_workbench.ui.workbench_ui_controller import WorkbenchUIController

    app = QApplication(sys.argv)
    ui_controller = WorkbenchUIController()
    window = WorkbenchMainWindow(ui_controller=ui_controller, config=config)
    window.show()
    return app.exec()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agent Workbench V6")
    parser.add_argument("--config", "-c", default=None, help="配置文件路径")
    parser.add_argument("--mode", "-m", choices=["cli", "gui"], default="cli", help="运行模式")
    parser.add_argument("--test-input", default=None, help="非交互模式：运行一次输入后退出（用于测试）")
    args = parser.parse_args(argv)

    loader = ConfigLoader(args.config)
    loaded = loader.load()
    config = default_config()
    _merge(config, loaded)

    if args.mode == "gui":
        return run_gui(config)
    return run_cli(config, test_input=args.test_input)


def _merge(base: Dict[str, Any], override: Dict[str, Any]) -> None:
    """深度合并两个字典。"""
    for key, value in override.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            _merge(base[key], value)
        else:
            base[key] = value


if __name__ == "__main__":
    sys.exit(main())
