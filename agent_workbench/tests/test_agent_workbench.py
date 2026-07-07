"""agent_workbench/tests/test_agent_workbench.py — Agent Workbench V6 端到端测试。

验证范围：
- WorkbenchController 装配 AgentWorkbenchRuntime + Workbench Engine。
- 用户消息经 WorkbenchController → Core Runtime → Orchestrator → Engine。
- Task Lifecycle：CREATED → PLANNING → EXECUTING → COMPLETED。
- Trace 记录 Engine 链路。
- Tool Engine 调用链路。
- ConfigStore 配置热更新。
- 默认 YAML 加载。
- CLI 入口可正常退出。
"""
from __future__ import annotations

import pytest
from PySide6.QtCore import Qt

from v6.runtime.enums import RuntimeState, TraceEvent

from agent_workbench.controller import WorkbenchController


@pytest.fixture
def controller() -> WorkbenchController:
    ctrl = WorkbenchController()
    ctrl.start()
    try:
        yield ctrl
    finally:
        ctrl.stop()


def test_agent_lifecycle_chat(controller: WorkbenchController) -> None:
    """验证单 Agent 聊天生命周期完整闭环。"""
    ctx = controller.chat("hello", session_id="sess-001")

    assert ctx.status == RuntimeState.COMPLETED
    assert any(m.role == "assistant" for m in ctx.messages)
    assistant_msg = [m for m in ctx.messages if m.role == "assistant"][-1]
    assert "V6 Agent Workbench" in assistant_msg.content

    timeline = controller.trace_timeline(ctx.task_id)
    nodes = {step["node"] for step in timeline}
    assert "engine:llm" in nodes


def test_agent_lifecycle_tool(controller: WorkbenchController) -> None:
    """验证 Tool Engine 调用链路。"""
    ctx = controller.chat_with_tool("get_time", {})

    assert ctx.status == RuntimeState.COMPLETED
    assert "tool_result" in ctx.result.extra
    assert "time" in ctx.result.extra["tool_result"]

    timeline = controller.trace_timeline(ctx.task_id)
    nodes = {step["node"] for step in timeline}
    assert "engine:tool" in nodes


def test_planner_loop_selects_llm_for_chat(controller: WorkbenchController) -> None:
    """验证 PlannerLoop 对 chat 任务选择 llm engine。"""
    ctx = controller.chat("analyze this text")

    assert ctx.status == RuntimeState.COMPLETED
    timeline = controller.trace_timeline(ctx.task_id)
    engine_steps = [s for s in timeline if s["node"] == "engine:llm"]
    assert len(engine_steps) >= 1


def test_planner_loop_selects_tool_for_tool_task(controller: WorkbenchController) -> None:
    """验证 PlannerLoop 对 tool 任务选择 tool engine。"""
    ctx = controller.chat_with_tool("echo", {"text": "hi"})

    assert ctx.status == RuntimeState.COMPLETED
    timeline = controller.trace_timeline(ctx.task_id)
    engine_steps = [s for s in timeline if s["node"] == "engine:tool"]
    assert len(engine_steps) >= 1


def test_config_store_read_write(controller: WorkbenchController) -> None:
    """验证 ConfigStore 支持点分路径读写。"""
    store = controller._runtime.config
    store.set("model.sampling.temperature", 0.5, persist=False)
    assert store.get("model.sampling.temperature") == 0.5
    assert store.get("model.default_provider") == "echo"


def test_config_loader_reads_default_yaml() -> None:
    """验证配置加载器能读取默认 YAML。"""
    from agent_workbench.config.loader import ConfigLoader

    loader = ConfigLoader()
    loader.load()
    assert loader.get("agent.name") == "Agent Workbench V6"
    assert loader.get("runtime.use_orchestrator") is True


def test_app_cli_mode_exits_cleanly() -> None:
    """验证 app.py CLI 入口可正常退出。"""
    from agent_workbench.app import main

    result = main([
        "--mode", "cli",
        "--config", "agent_workbench/config/default.yaml",
        "--test-input", "hello",
    ])
    assert result == 0


def test_workbench_main_window_assembly(qapp, tmp_path) -> None:
    """验证 WorkbenchMainWindow 可装配 WorkbenchHost + Chat Workspace。"""
    from agent_workbench.ui.main_window import WorkbenchMainWindow
    from agent_workbench.ui.workbench_ui_controller import WorkbenchUIController

    ctrl = WorkbenchUIController(data_dir=str(tmp_path))
    win = WorkbenchMainWindow(ui_controller=ctrl)
    try:
        host = win.centralWidget()
        assert host is not None
        assert host.workbench is not None
        assert ctrl.workbench_controller is not None
    finally:
        win.close()
        ctrl.shutdown()


def test_workbench_chat_workspace_receives_message(qapp, tmp_path) -> None:
    """验证 CommandBar 提交的消息会显示在 Chat Workspace 中。"""
    from agent_workbench.ui.main_window import WorkbenchMainWindow
    from agent_workbench.ui.workbench_ui_controller import WorkbenchUIController

    ctrl = WorkbenchUIController(data_dir=str(tmp_path))
    win = WorkbenchMainWindow(ui_controller=ctrl)
    try:
        ctrl.on_send_msg("hello workbench")
        workspace = ctrl._chat_workspace
        assert workspace is not None
        # 至少渲染了用户消息（AI 回复在下一个用例完整验证）
        assert len(workspace._scene._items) >= 1
        texts = [item.text() for item, _ in workspace._scene._items]
        assert any("hello workbench" in t for t in texts)
    finally:
        win.close()
        ctrl.shutdown()


def test_workbench_chat_workspace_receives_ai_reply(qapp, tmp_path) -> None:
    """验证发送消息后会收到 AI 回复并渲染在 Chat Workspace 中。"""
    from agent_workbench.ui.main_window import WorkbenchMainWindow
    from agent_workbench.ui.workbench_ui_controller import WorkbenchUIController

    ctrl = WorkbenchUIController(data_dir=str(tmp_path))
    win = WorkbenchMainWindow(ui_controller=ctrl)
    try:
        ctrl.on_send_msg("hello")
        thread = getattr(ctrl, "_workbench_thread", None)
        if thread is not None:
            thread.join(timeout=5)
        qapp.processEvents()

        workspace = ctrl._chat_workspace
        assert workspace is not None
        assert len(workspace._scene._items) >= 2
        texts = [item.text() for item, _ in workspace._scene._items]
        assert any("hello" in t.lower() for t in texts)
        assert any("V6 Agent Workbench" in t for t in texts)
    finally:
        win.close()
        ctrl.shutdown()


def test_openai_provider_streams_with_monkeypatched_client() -> None:
    """验证 OpenAIProvider 流式输出可正确分块。"""
    import openai

    from agent_workbench.services.model_provider import ModelProvider
    from agent_workbench.services.openai_provider import OpenAIProvider

    class FakeStream:
        def __iter__(self):
            yield _make_chunk("Hello")
            yield _make_chunk(" ")
            yield _make_chunk("World")

    class FakeCompletions:
        def create(self, **kwargs):
            return FakeStream()

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        chat = FakeChat()

    provider = OpenAIProvider()
    provider.configure(
        {"base_url": "http://test", "api_key": "sk-test", "model": "gpt-test"}
    )

    original_openai = openai.OpenAI
    openai.OpenAI = lambda **kwargs: FakeClient()
    try:
        chunks = list(provider.chat_stream([{"role": "user", "content": "hi"}], {}))
        assert "".join(chunks) == "Hello World"
    finally:
        openai.OpenAI = original_openai


def _make_chunk(text: str):
    class FakeDelta:
        content = text

    class FakeChoice:
        delta = FakeDelta()

    class FakeChunk:
        choices = [FakeChoice()]

    return FakeChunk()


def test_switch_provider_updates_runtime_response(controller: WorkbenchController) -> None:
    """验证在 Inspector 中切换 default_provider 后，下一条消息使用新 Provider。"""
    from agent_workbench.runtime.modules.model_module import ModelModule
    from agent_workbench.services.model_provider import ModelProvider

    class MockProvider(ModelProvider):
        @property
        def name(self) -> str:
            return "mock"

        def chat(self, messages, params):
            return "mock-reply"

        def validate_config(self, config):
            return True

    original_create = ModelModule._create_provider
    ModelModule._create_provider = staticmethod(
        lambda ptype: MockProvider() if ptype == "mock" else original_create(ptype)
    )
    try:
        store = controller._runtime.config
        store.set(
            "model.providers",
            [
                {"name": "echo", "type": "echo", "enabled": True, "config": {}},
                {"name": "mock", "type": "mock", "enabled": True, "config": {}},
            ],
            persist=False,
        )
        store.set("model.default_provider", "mock", persist=False)

        ctx = controller.chat("hello", session_id="switch-test")
        assert any(
            m.role == "assistant" and m.content == "mock-reply" for m in ctx.messages
        )

        store.set("model.default_provider", "echo", persist=False)
        ctx2 = controller.chat("hello", session_id="switch-test")
        assert any(
            m.role == "assistant" and "V6 Agent Workbench" in m.content for m in ctx2.messages
        )
    finally:
        ModelModule._create_provider = staticmethod(original_create)


def test_navigator_registers_runtime_modules(qapp, tmp_path) -> None:
    """验证 Workbench Navigator 动态注册所有 RuntimeModule。"""
    from agent_workbench.ui.main_window import WorkbenchMainWindow
    from agent_workbench.ui.workbench_ui_controller import WorkbenchUIController

    ctrl = WorkbenchUIController(data_dir=str(tmp_path))
    win = WorkbenchMainWindow(ui_controller=ctrl)
    try:
        nav = ctrl._host.workbench.navigator
        registered = {nav._list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(nav._list.count())}
        assert "runtime" in registered
        assert "model" in registered
        assert "prompt" in registered
        assert "memory" in registered
    finally:
        win.close()
        ctrl.shutdown()


def test_inspector_renders_model_properties(qapp, tmp_path) -> None:
    """验证选中 Model 模块后 Inspector 渲染其属性。"""
    from agent_workbench.ui.main_window import WorkbenchMainWindow
    from agent_workbench.ui.workbench_ui_controller import WorkbenchUIController

    ctrl = WorkbenchUIController(data_dir=str(tmp_path))
    win = WorkbenchMainWindow(ui_controller=ctrl)
    try:
        ctrl._on_selection_changed("model")
        qapp.processEvents()

        inspector = ctrl._host.workbench.inspector
        assert inspector._object_id == "model"
        assert inspector._title.text() == "Model"
        prop_names = {p.name for p in ctrl._presentations["model"].properties}
        assert "default_provider" in prop_names
        assert "sampling.temperature" in prop_names
        assert "sampling.max_tokens" in prop_names
    finally:
        win.close()
        ctrl.shutdown()


def test_inspector_property_change_hot_updates_runtime(qapp, tmp_path) -> None:
    """验证在 Inspector 中修改 Model 参数会热更新 Runtime。"""
    from agent_workbench.ui.main_window import WorkbenchMainWindow
    from agent_workbench.ui.workbench_ui_controller import WorkbenchUIController

    config_path = _copy_default_config(tmp_path)
    ctrl = WorkbenchUIController(data_dir=str(tmp_path), config_path=config_path)
    win = WorkbenchMainWindow(ui_controller=ctrl)
    try:
        ctrl._on_selection_changed("model")
        ctrl._on_property_changed("model", "sampling.temperature", "0.3")

        assert ctrl._workbench.get_config_value("model.sampling.temperature") == 0.3
        model_module = ctrl._workbench.runtime.module_registry.get("model")
        assert model_module._sampling["temperature"] == 0.3

        ctrl._on_property_changed("model", "sampling.max_tokens", "1024")
        assert ctrl._workbench.get_config_value("model.sampling.max_tokens") == 1024
        assert model_module._sampling["max_tokens"] == 1024
    finally:
        win.close()
        ctrl.shutdown()


def test_status_bar_reflects_runtime_state(qapp, tmp_path) -> None:
    """验证 StatusBar 启动后显示 Runtime / Provider / Model / Profile 状态。"""
    from agent_workbench.ui.main_window import WorkbenchMainWindow
    from agent_workbench.ui.workbench_ui_controller import WorkbenchUIController

    ctrl = WorkbenchUIController(data_dir=str(tmp_path))
    win = WorkbenchMainWindow(ui_controller=ctrl)
    try:
        sb = ctrl._host.workbench.status_bar
        assert "online" in sb._items["runtime"].text()
        assert "echo" in sb._items["provider"].text()
        assert "default" in sb._items["profile"].text()
    finally:
        win.close()
        ctrl.shutdown()


def _copy_default_config(tmp_path: "Path") -> str:
    """将默认配置复制到临时目录，避免测试污染仓库配置。"""
    import shutil
    from pathlib import Path

    src = Path(__file__).parent.parent / "config" / "default.yaml"
    dst = tmp_path / "default.yaml"
    shutil.copy(src, dst)
    return str(dst)


def test_inspector_switch_provider_changes_chat_response(qapp, tmp_path) -> None:
    """验证用户路径：Inspector 切换 Provider → 重新发送 → 回复来源改变。"""
    from agent_workbench.runtime.modules.model_module import ModelModule
    from agent_workbench.services.model_provider import ModelProvider
    from agent_workbench.ui.main_window import WorkbenchMainWindow
    from agent_workbench.ui.workbench_ui_controller import WorkbenchUIController

    class MockProvider(ModelProvider):
        @property
        def name(self) -> str:
            return "mock"

        def chat(self, messages, params):
            return "inspector-mock-reply"

        def validate_config(self, config):
            return True

    original_create = ModelModule._create_provider
    ModelModule._create_provider = staticmethod(
        lambda ptype: MockProvider() if ptype == "mock" else original_create(ptype)
    )
    config_path = _copy_default_config(tmp_path)
    ctrl = WorkbenchUIController(data_dir=str(tmp_path), config_path=config_path)
    win = WorkbenchMainWindow(ui_controller=ctrl)
    try:
        # 通过 Inspector 路径注册 mock provider 并切换 default_provider
        ctrl._workbench.set_config_value(
            "model.providers",
            [
                {"name": "echo", "type": "echo", "enabled": True, "config": {}},
                {"name": "mock", "type": "mock", "enabled": True, "config": {}},
            ],
        )
        ctrl._on_property_changed("model", "default_provider", "mock")

        ctx = ctrl._workbench.chat("hello", session_id="inspector-switch")
        assert any(
            m.role == "assistant" and m.content == "inspector-mock-reply" for m in ctx.messages
        )
    finally:
        win.close()
        ctrl.shutdown()
        ModelModule._create_provider = staticmethod(original_create)


def test_trace_event_order_after_chat(controller: WorkbenchController) -> None:
    """验证发送消息后 Trace 主链路事件顺序正确。"""
    ctx = controller.chat("hello", session_id="trace-order")
    assert ctx.status == RuntimeState.COMPLETED

    timeline = controller.trace_timeline(ctx.task_id)
    actions = [s["action"] for s in timeline]

    expected_prefix = [
        TraceEvent.TASK_START.value,
        TraceEvent.CAPABILITY_RESOLVED.value,
        TraceEvent.ENGINE_SELECTED.value,
        TraceEvent.EXECUTION_STARTED.value,
        TraceEvent.PROVIDER_SELECTED.value,
        TraceEvent.REQUEST_SENT.value,
        TraceEvent.FIRST_TOKEN.value,
        TraceEvent.EXECUTION_FINISHED.value,
        TraceEvent.ENGINE_END.value,
        TraceEvent.TASK_FINISH.value,
    ]
    # 主链路顺序必须保持一致；允许中间存在 CHUNK_RECEIVED / STREAM_FINISHED 等可选事件。
    filtered = [a for a in actions if a in expected_prefix]
    assert filtered == expected_prefix, f"expected {expected_prefix}, got {filtered}"


def test_trace_parent_child_relationship(controller: WorkbenchController) -> None:
    """验证 Trace 事件父子关系正确：Execution 挂在 Engine 下，Provider/Stream 挂在 Execution 下。"""
    ctx = controller.chat("hello", session_id="trace-tree")
    assert ctx.status == RuntimeState.COMPLETED

    timeline = controller.trace_timeline(ctx.task_id)
    steps_by_id = {s["step_id"]: s for s in timeline}

    engine_step = next(
        (s for s in timeline if s["action"] == TraceEvent.ENGINE_SELECTED.value), None
    )
    execution_step = next(
        (s for s in timeline if s["action"] == TraceEvent.EXECUTION_STARTED.value), None
    )
    provider_step = next(
        (s for s in timeline if s["action"] == TraceEvent.PROVIDER_SELECTED.value), None
    )
    stream_step = next(
        (s for s in timeline if s["action"] == TraceEvent.FIRST_TOKEN.value), None
    )

    assert engine_step is not None, "missing engine_selected step"
    assert execution_step is not None, "missing execution_started step"
    assert provider_step is not None, "missing provider_selected step"
    assert stream_step is not None, "missing first_token step"

    assert execution_step["parent_id"] == engine_step["step_id"], "execution should be child of engine"
    assert provider_step["parent_id"] == execution_step["step_id"], "provider should be child of execution"
    assert stream_step["parent_id"] == execution_step["step_id"], "stream should be child of execution"


def test_trace_workspace_receives_events(qapp, tmp_path) -> None:
    """验证 WorkbenchUIController 将 Runtime 事件追加到 Trace Workspace。"""
    from agent_workbench.ui.main_window import WorkbenchMainWindow
    from agent_workbench.ui.workbench_ui_controller import WorkbenchUIController

    ctrl = WorkbenchUIController(data_dir=str(tmp_path))
    win = WorkbenchMainWindow(ui_controller=ctrl)
    try:
        trace_ws = ctrl._trace_workspace
        assert trace_ws is not None
        initial_count = trace_ws._tree.topLevelItemCount()

        ctrl.on_send_msg("hello trace")
        thread = getattr(ctrl, "_workbench_thread", None)
        if thread is not None:
            thread.join(timeout=5)
        qapp.processEvents()

        # 至少新增了 TaskStart / CapabilityResolved / EngineSelected 等事件
        assert trace_ws._tree.topLevelItemCount() > initial_count
    finally:
        win.close()
        ctrl.shutdown()
