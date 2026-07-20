"""agent_workbench/app.py — Agent Workbench V6 应用入口。

边界：
- 属于 Application Layer，不属于 v6-core / v6-service。
- 加载配置、启动 WorkbenchController、提供 CLI / GUI 入口。
"""
from __future__ import annotations

import argparse
import os
import sys
import uuid

from dotenv import load_dotenv

from agent_workbench.controller import WorkbenchController
from agent_workbench.runtime.interaction.cli_renderer import CLIStreamRenderer

# 加载 config/.env 到 os.environ，供 Provider 环境变量展开使用
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config", ".env"))


def run_cli(config_path: str | None = None, test_input: str | None = None) -> int:
    """命令行交互模式 — 支持流式逐字输出。

    Args:
        config_path: 配置文件路径，默认使用 default.yaml。
        test_input: 若提供，直接以此输入运行一次后退出（用于测试）。
    """
    controller = WorkbenchController(config_path=config_path)
    controller.start()
    agent_name = controller.runtime.config.get("agent.name", "Agent Workbench V6")
    print(f"[{agent_name}] 已启动")

    # 接入 CLI 流式渲染器，通过 Interaction Boundary 接收流式事件
    cli_renderer = CLIStreamRenderer()
    controller.interaction_layer.set_renderer(cli_renderer)

    try:
        if test_input is not None:
            print(f"> {test_input}")
            cli_renderer.reset(str(uuid.uuid4()))
            ctx = controller.chat(test_input)
            _print_fallback(ctx, cli_renderer)
            return 0

        print("输入消息按回车，输入 'exit' 退出。")
        while True:
            text = input("> ").strip()
            if text.lower() in {"exit", "quit"}:
                break
            if not text:
                continue

            cli_renderer.reset(str(uuid.uuid4()))
            ctx = controller.chat(text)
            _print_fallback(ctx, cli_renderer)
    finally:
        controller.interaction_layer.set_renderer(None)
        controller.stop()
    return 0


def _print_fallback(ctx, cli_renderer: CLIStreamRenderer) -> None:
    """流式输出未触发时的兜底：输出完整回复。

    当 DecisionManager 将请求路由到 CHAT 模式（不进入 Orchestrator）
    或流式事件未正确映射时，通过 RuntimeContext 提取完整回复。
    """
    if cli_renderer._streaming:
        return  # 已通过流式输出，不需要兜底
    assistant = [m for m in ctx.messages if m.role == "assistant"]
    if assistant:
        print(f"AI: {assistant[-1].content}")
    else:
        status = ctx.status.value if hasattr(ctx.status, 'value') else str(ctx.status)
        if status == "failed":
            error = ctx.result.error if ctx.result and ctx.result.error else "未知错误"
            print(f"[失败] {error}")


def run_gui(config_path: str | None = None) -> int:
    """Desktop UI 模式。"""
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:  # pragma: no cover - optional
        print("PySide6 未安装，回退到 CLI 模式。")
        return run_cli(config_path=config_path)

    from agent_workbench.ui.main_window import WorkbenchMainWindow
    from agent_workbench.ui.workbench_ui_controller import WorkbenchUIController

    app = QApplication(sys.argv)
    ui_controller = WorkbenchUIController(config_path=config_path)
    window = WorkbenchMainWindow(ui_controller=ui_controller)
    window.show()
    return app.exec()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agent Workbench V6")
    parser.add_argument("--config", "-c", default=None, help="配置文件路径")
    parser.add_argument("--mode", "-m", choices=["cli", "gui"], default="cli", help="运行模式")
    parser.add_argument("--test-input", default=None, help="非交互模式：运行一次输入后退出（用于测试）")
    args = parser.parse_args(argv)

    if args.mode == "gui":
        return run_gui(config_path=args.config)
    return run_cli(config_path=args.config, test_input=args.test_input)


if __name__ == "__main__":
    sys.exit(main())
