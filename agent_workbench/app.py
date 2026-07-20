"""agent_workbench/app.py — Agent Workbench V6 应用入口。

边界：
- 属于 Application Layer，不属于 v6-core / v6-service。
- 加载配置、启动 WorkbenchController、提供 CLI / GUI 入口。
"""
from __future__ import annotations

import argparse
import os
import sys
from dotenv import load_dotenv

from agent_workbench.controller import WorkbenchController
from agent_workbench.runtime.interaction.cli_renderer import CLIStreamRenderer

# 加载 config/.env 到 os.environ，供 Provider 环境变量展开使用
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config", ".env"))


def run_cli(config_path: str | None = None, test_input: str | None = None) -> int:
    """命令行交互模式 — 支持流式逐字输出 + Session 持久化。

    Args:
        config_path: 配置文件路径，默认使用 default.yaml。
        test_input: 若提供，直接以此输入运行一次后退出（用于测试）。
    """
    controller = WorkbenchController(config_path=config_path)
    controller.start()
    agent_name = controller.runtime.config.get("agent.name", "Agent Workbench V6")
    print(f"[{agent_name}] 已启动")

    # 显示 Session 恢复状态
    if controller.session_id:
        session_module = controller.runtime.module_registry.get("session")
        if session_module is not None:
            history = session_module.history(controller.session_id)
            if history:
                print(f"[Session] 已恢复上次会话 ({len(history)} 条消息, id={controller.session_id})")
            else:
                print(f"[Session] 新建会话 (id={controller.session_id})")

    # 接入 CLI 流式渲染器，通过 Interaction Boundary 接收流式事件
    cli_renderer = CLIStreamRenderer()
    controller.interaction_layer.set_renderer(cli_renderer)

    try:
        if test_input is not None:
            print(f"> {test_input}")
            cli_renderer.reset()
            ctx = controller.chat(test_input)
            _print_fallback(ctx, cli_renderer)
            return 0

        print("输入消息按回车，输入 'exit' 退出。")
        print("命令：/agent <id> 切换 Agent | /agents 查看 Agent 列表 | /model <name> 切换模型")
        while True:
            text = input("> ").strip()
            if text.lower() in {"exit", "quit"}:
                break
            if not text:
                continue

            # 处理 CLI 命令
            if text.startswith("/"):
                result = _handle_cli_command(text, controller)
                if result is not None:
                    print(result)
                continue

            cli_renderer.reset()
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


def _handle_cli_command(text: str, controller) -> str | None:
    """处理 CLI 斜杠命令。

    Returns:
        命令执行结果消息，None 表示不输出。
    """
    parts = text.split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd == "/agents":
        agents = controller.list_agents()
        active = controller.get_active_agent()
        active_id = active["id"] if active else ""
        lines = ["可用 Agent："]
        for a in agents:
            marker = " *" if a["id"] == active_id else "  "
            lines.append(f"  {marker} {a['id']} — {a['name']}: {a['description']}")
        return "\n".join(lines)

    if cmd == "/agent":
        if not arg:
            a = controller.get_active_agent()
            if a:
                return f"当前 Agent: {a['name']} ({a['id']})\n  {a['description']}"
            return "当前无活跃 Agent"
        if controller.switch_agent(arg):
            a = controller.get_active_agent()
            return f"已切换到 Agent: {a['name']} ({a['id']})"
        return f"Agent '{arg}' 不存在。可用: {', '.join(a['id'] for a in controller.list_agents())}"

    if cmd == "/model":
        if not arg:
            return f"当前模型: {controller.get_current_model()} (Provider: {controller.get_current_provider()})"
        if controller.switch_model(arg):
            return f"已切换到模型: {arg}"
        models = controller.list_models()
        return f"模型 '{arg}' 不存在。可用: {', '.join(models)}"

    if cmd == "/provider":
        if not arg:
            return f"当前 Provider: {controller.get_current_provider()}"
        if controller.switch_provider(arg):
            return f"已切换到 Provider: {arg}，模型: {controller.get_current_model()}"
        providers = controller.list_providers()
        return f"Provider '{arg}' 不存在。可用: {', '.join(providers)}"

    return f"未知命令: {cmd}。可用: /agent, /agents, /model, /provider"


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
