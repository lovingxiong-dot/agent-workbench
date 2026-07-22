"""tests/v6/test_host_contract.py — Host Adapter Contract 完整性测试。

验证所有 Host 类对外暴露的方法和信号与 Controller/Renderer 的调用保持一致。
防止因 Controller 新增调用而 Host 忘记代理导致的 EXE 启动失败。

不依赖 Qt 运行时，仅做 import + hasattr 检查。
"""
from __future__ import annotations

import pytest


# ── NavigatorHost ──────────────────────────────────────────────


def test_navigator_host_signals():
    """NavigatorHost 必须暴露 Controller 所需的所有信号。"""
    from agent_workbench.ui.workbench.navigator_host import NavigatorHost

    required = [
        "selection_changed",   # Signal(str) — 导航选择
        "add_requested",       # Signal(str) — 添加请求
        "session_selected",    # Signal(str) — 会话选择
        "session_add_requested",  # Signal() — 新建会话
    ]
    for sig in required:
        assert hasattr(NavigatorHost, sig), f"NavigatorHost 缺少信号: {sig}"


def test_navigator_host_methods():
    """NavigatorHost 必须代理 Controller 调用的所有方法。"""
    from agent_workbench.ui.workbench.navigator_host import NavigatorHost

    required = [
        "register_functional_tab",
        "register_settings_category",
        "register_module",
        "load_presentations",
        "clear_modules",
        "set_selection",
        "set_settings_expanded",
        "set_sessions_expanded",
        "load_sessions",
        "set_active_session",
        "modules",
    ]
    for method in required:
        assert hasattr(NavigatorHost, method), f"NavigatorHost 缺少方法: {method}"


# ── InspectorHost ──────────────────────────────────────────────


def test_inspector_host_signals():
    """InspectorHost 必须暴露 Controller 所需的所有信号。"""
    from agent_workbench.ui.workbench.inspector_host import InspectorHost

    required = [
        "property_changed",   # Signal(str, str, object)
        "action_triggered",   # Signal(str, str)
    ]
    for sig in required:
        assert hasattr(InspectorHost, sig), f"InspectorHost 缺少信号: {sig}"


def test_inspector_host_methods():
    """InspectorHost 必须代理 Controller/Renderer 调用的所有方法。"""
    from agent_workbench.ui.workbench.inspector_host import InspectorHost

    required = [
        "set_object",
        "set_schema",
        "clear",
    ]
    for method in required:
        assert hasattr(InspectorHost, method), f"InspectorHost 缺少方法: {method}"


def test_inspector_host_properties():
    """InspectorHost 必须暴露 Controller 所需的属性。"""
    from agent_workbench.ui.workbench.inspector_host import InspectorHost

    required = ["object_id", "title"]
    for prop in required:
        assert hasattr(InspectorHost, prop), f"InspectorHost 缺少属性: {prop}"


# ── StatusBarHost ──────────────────────────────────────────────


def test_status_bar_host_methods():
    """StatusBarHost 必须代理 Controller/Renderer 调用的所有方法。"""
    from agent_workbench.ui.workbench.status_bar_host import StatusBarHost

    required = [
        "set_statistics",
        "set_runtime_status",
    ]
    for method in required:
        assert hasattr(StatusBarHost, method), f"StatusBarHost 缺少方法: {method}"


# ── WorkspaceHost ──────────────────────────────────────────────


def test_workspace_host_methods():
    """WorkspaceHost 必须代理 Controller/Renderer 调用的所有方法。"""
    from agent_workbench.ui.workbench.workspace_host import WorkspaceHost

    required = [
        "register_workspace",
        "switch_to",
    ]
    for method in required:
        assert hasattr(WorkspaceHost, method), f"WorkspaceHost 缺少方法: {method}"


# ── ToolBarHost ────────────────────────────────────────────────


def test_tool_bar_host_signals():
    """ToolBarHost 必须暴露 Controller 所需的信号。"""
    from agent_workbench.ui.workbench.tool_bar_host import ToolBarHost

    required = ["action_triggered"]
    for sig in required:
        assert hasattr(ToolBarHost, sig), f"ToolBarHost 缺少信号: {sig}"


def test_tool_bar_host_methods():
    """ToolBarHost 必须代理 Renderer 调用的方法。"""
    from agent_workbench.ui.workbench.tool_bar_host import ToolBarHost

    required = [
        "set_actions",
        "actions_state",
    ]
    for method in required:
        assert hasattr(ToolBarHost, method), f"ToolBarHost 缺少方法: {method}"


# ── CommandBarHost ─────────────────────────────────────────────


def test_command_bar_host_signals():
    """CommandBarHost 必须暴露 Controller 所需的信号。"""
    from agent_workbench.ui.workbench.command_bar_host import CommandBarHost

    required = ["command_submitted"]
    for sig in required:
        assert hasattr(CommandBarHost, sig), f"CommandBarHost 缺少信号: {sig}"


def test_command_bar_host_methods():
    """CommandBarHost 必须代理 Controller 调用的方法。"""
    from agent_workbench.ui.workbench.command_bar_host import CommandBarHost

    required = [
        "set_enabled",
        "clear",
        "set_placeholder",
    ]
    for method in required:
        assert hasattr(CommandBarHost, method), f"CommandBarHost 缺少方法: {method}"


# ── ControlBar（直接 Widget，非 Host）──────────────────────────


def test_control_bar_signals():
    """ControlBar 必须暴露 Controller 所需的所有信号。"""
    from agent_workbench.ui.workbench.control_bar import ControlBar

    required = [
        "agent_changed",
        "provider_changed",
        "model_changed",
    ]
    for sig in required:
        assert hasattr(ControlBar, sig), f"ControlBar 缺少信号: {sig}"


def test_control_bar_methods():
    """ControlBar 必须暴露 Controller 调用的所有方法。"""
    from agent_workbench.ui.workbench.control_bar import ControlBar

    required = [
        "set_agents",
        "set_providers",
        "set_models",
    ]
    for method in required:
        assert hasattr(ControlBar, method), f"ControlBar 缺少方法: {method}"


# ── Workbench 聚合 ─────────────────────────────────────────────


def test_workbench_host_properties():
    """Workbench 必须暴露所有 Host/Widget 聚合属性。"""
    from agent_workbench.ui.workbench.workbench import Workbench

    required = [
        "navigator",
        "workspace",
        "inspector",
        "tool_bar",
        "control_bar",
        "status_bar",
        "command_bar",
    ]
    for prop in required:
        assert hasattr(Workbench, prop), f"Workbench 缺少属性: {prop}"


def test_workbench_host_signals():
    """Workbench 必须暴露 MainWindow 所需的信号。"""
    from agent_workbench.ui.workbench.workbench import Workbench

    required = [
        "selection_changed",
        "property_changed",
        "action_triggered",
        "command_submitted",
        "tool_bar_action_triggered",
    ]
    for sig in required:
        assert hasattr(Workbench, sig), f"Workbench 缺少信号: {sig}"