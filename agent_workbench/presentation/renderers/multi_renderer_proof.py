"""Phase 2-C.4 Multi Renderer Proof — 证明脚本。

目标：
  证明 PresentationRuntime 可以驱动不同 UI 技术栈的 Renderer，
  且 PresentationRuntime 不感知 Renderer 类型。

证明方法：
  1. 注册两个 Renderer：CLI + Recorder（事件记录器）
  2. 激活 CLI，分发 InteractionEvent → CLI 输出到终端
  3. 停用 CLI，激活 Recorder，分发相同事件 → Recorder 记录
  4. 验证：PresentationRuntime 零类型判断，零 isinstance 检查

约束：
  ✗ 不接 v6/ui
  ✗ 不修改 Workbench UI
  ✗ 不修改 Application
  ✗ 不修改 Frozen Zones

运行方式：
  python -m agent_workbench.presentation.renderers.multi_renderer_proof
"""
from __future__ import annotations

import sys
from typing import List

from agent_workbench.presentation.protocols.interaction.event import (
    InteractionEvent,
    InteractionEventType,
)
from agent_workbench.presentation.renderers.cli_renderer import CLIRenderer
from agent_workbench.presentation.renderers.registry import (
    RendererRegistry,
    RendererRegistryError,
    RendererState,
)
from agent_workbench.presentation.runtime import PresentationRuntime
from agent_workbench.presentation.shell.protocol import (
    CommandState,
    InspectorState,
    NavigationGroup,
    NavigationItem,
    WorkspaceMessage,
    WorkspaceState,
)


class RecorderRenderer:
    """事件记录器 — 用于验证 PresentationRuntime 的 Renderer 无关性。

    不输出任何 UI，只记录收到的事件。
    用于证明：PresentationRuntime 不关心 Renderer 是什么类型。
    """

    def __init__(self) -> None:
        self.started = False
        self.stopped = False
        self.events: list[InteractionEvent] = []
        self.nav_updates: list[list[NavigationGroup]] = []
        self.workspace_updates: list[WorkspaceState] = []
        self.inspector_updates: list[InspectorState] = []
        self.command_updates: list[CommandState] = []

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def render(self, event: InteractionEvent) -> None:
        self.events.append(event)

    def update_navigation(self, groups: List[NavigationGroup]) -> None:
        self.nav_updates.append(groups)

    def update_workspace(self, state: WorkspaceState) -> None:
        self.workspace_updates.append(state)

    def update_inspector(self, state: InspectorState) -> None:
        self.inspector_updates.append(state)

    def update_command(self, state: CommandState) -> None:
        self.command_updates.append(state)


def make_sample_events() -> list[InteractionEvent]:
    """创建一组示例 InteractionEvent，覆盖所有事件类型。"""
    return [
        InteractionEvent(
            type=InteractionEventType.TASK_STARTED,
            request_id="req-1",
            payload={"task": "test"},
        ),
        InteractionEvent(
            type=InteractionEventType.MESSAGE_USER,
            request_id="req-1",
            payload={"text": "你好，帮我分析这个项目"},
        ),
        InteractionEvent(
            type=InteractionEventType.MESSAGE_DELTA,
            request_id="req-1",
            payload={"text": "好的，我来分析..."},
        ),
        InteractionEvent(
            type=InteractionEventType.CAPABILITY_STEP,
            request_id="req-1",
            payload={"capability_id": "read_project", "index": 1},
        ),
        InteractionEvent(
            type=InteractionEventType.TOOL_STARTED,
            request_id="req-1",
            payload={"name": "read_file", "args": {"path": "README.md"}},
        ),
        InteractionEvent(
            type=InteractionEventType.TOOL_COMPLETED,
            request_id="req-1",
            payload={"name": "read_file", "status": "ok", "result": {"content": "..."}},
        ),
        InteractionEvent(
            type=InteractionEventType.MESSAGE_DELTA,
            request_id="req-1",
            payload={"text": "项目结构如下..."},
        ),
        InteractionEvent(
            type=InteractionEventType.MESSAGE_COMPLETE,
            request_id="req-1",
            payload={},
        ),
        InteractionEvent(
            type=InteractionEventType.TASK_FINISHED,
            request_id="req-1",
            payload={},
        ),
    ]


def make_sample_navigation() -> list[NavigationGroup]:
    return [
        NavigationGroup(
            id="g1",
            title="Recent",
            items=[
                NavigationItem(id="s1", title="Session 1", kind="session", preview="Hello..."),
                NavigationItem(id="s2", title="Session 2", kind="session", preview="World..."),
            ],
        ),
    ]


def make_sample_workspace() -> WorkspaceState:
    return WorkspaceState(
        title="Session 1",
        subtitle="GPT-4 · 12 messages",
        messages=[
            WorkspaceMessage(id="m1", role="user", content="你好"),
            WorkspaceMessage(id="m2", role="assistant", content="你好！有什么可以帮助你的？"),
        ],
        models=["GPT-4", "Claude-3"],
    )


def make_sample_inspector() -> InspectorState:
    return InspectorState(
        object_id="agent:main",
        properties=[
            {"name": "model", "value": "GPT-4", "type": "string"},
            {"name": "temperature", "value": 0.7, "type": "number"},
        ],
    )


def make_sample_command() -> CommandState:
    return CommandState(
        prompt="Type a message...",
        status_text="Ready",
        is_processing=False,
    )


def run_proof():
    """执行 Phase 2-C.4 证明。"""
    print("=" * 60)
    print("Phase 2-C.4 Multi Renderer Proof")
    print("=" * 60)
    print()

    errors: list[str] = []

    # ── Step 1: 创建 PresentationRuntime ──
    print("Step 1: 创建 PresentationRuntime")
    pr = PresentationRuntime()
    assert pr.registry is not None, "registry should be initialized"
    print("  ✓ PresentationRuntime created")
    print()

    # ── Step 2: 注册两个 Renderer ──
    print("Step 2: 注册两个 Renderer（CLI + Recorder）")
    cli = CLIRenderer(prefix="CLI")
    recorder = RecorderRenderer()
    pr.register_renderer("cli", cli)
    pr.register_renderer("recorder", recorder)
    assert pr.registry.count == 2
    assert pr.list_renderers() == ["cli", "recorder"]
    print("  ✓ 2 renderers registered: cli, recorder")
    print()

    # ── Step 3: 激活 CLI Renderer ──
    print("Step 3: 激活 CLI Renderer → 分发事件")
    pr.activate_renderer("cli")
    assert pr.active_renderer_id == "cli"
    assert pr.registry.get_state("cli") == RendererState.ACTIVE
    assert pr.registry.get_state("recorder") == RendererState.INACTIVE

    events = make_sample_events()
    for event in events:
        pr.dispatch_event(event)
    print("  ✓ 9 events dispatched to CLI")
    print()

    # ── Step 4: 停用 CLI，激活 Recorder ──
    print("Step 4: 停用 CLI → 激活 Recorder → 分发相同事件")
    pr.deactivate_renderer()
    assert pr.registry.get_state("cli") == RendererState.INACTIVE
    assert pr.active_renderer_id is None

    pr.activate_renderer("recorder")
    assert pr.active_renderer_id == "recorder"
    assert pr.registry.get_state("recorder") == RendererState.ACTIVE

    for event in events:
        pr.dispatch_event(event)
    print("  ✓ 9 events dispatched to Recorder")
    print()

    # ── Step 5: Shell State 同步 ──
    print("Step 5: Shell State 同步")
    nav = make_sample_navigation()
    ws = make_sample_workspace()
    insp = make_sample_inspector()
    cmd = make_sample_command()

    pr.update_navigation(nav)
    pr.update_workspace(ws)
    pr.update_inspector(insp)
    pr.update_command(cmd)
    print("  ✓ 4 state updates dispatched to Recorder")
    print()

    # ── Step 6: 验证 Recorder 收到所有事件 ──
    print("Step 6: 验证 Recorder 记录")
    assert len(recorder.events) == len(events), (
        f"Expected {len(events)} events, got {len(recorder.events)}"
    )
    print(f"  ✓ Recorder received {len(recorder.events)} events")

    # 验证每种事件类型
    event_types_found = {e.type for e in recorder.events}
    expected_types = {e.type for e in events}
    assert event_types_found == expected_types, (
        f"Event type mismatch: {event_types_found} != {expected_types}"
    )
    print(f"  ✓ All {len(expected_types)} event types covered")

    # 验证 Shell State
    assert len(recorder.nav_updates) == 1
    assert len(recorder.workspace_updates) == 1
    assert len(recorder.inspector_updates) == 1
    assert len(recorder.command_updates) == 1
    print("  ✓ 4 Shell State categories received")
    print()

    # ── Step 7: 验证 PresentationRuntime 零 Renderer 类型感知 ──
    print("Step 7: 验证 PresentationRuntime 零 Renderer 类型感知")

    # 证据：PresentationRuntime 源码中不包含任何类型判断
    import inspect
    source = inspect.getsource(pr.dispatch_event)
    assert "isinstance" not in source, "dispatch_event contains isinstance"
    assert "type(" not in source, "dispatch_event contains type()"
    assert "CLI" not in source, "dispatch_event references CLI"
    assert "Recorder" not in source, "dispatch_event references Recorder"
    print("  ✓ dispatch_event: zero isinstance/type checks")
    print("  ✓ dispatch_event: no Renderer name references")

    source = inspect.getsource(pr.update_navigation)
    assert "isinstance" not in source
    assert "CLI" not in source
    print("  ✓ update_navigation: zero type checks")

    print()

    # ── Step 8: Present to stdio 证明 ──
    print("Step 8: Present to stdio 证明")
    print("  [CLI] 输出:")
    print("  " + "-" * 40)
    cli.render(InteractionEvent(
        type=InteractionEventType.MESSAGE_USER,
        request_id="req-9",
        payload={"text": "Hello from CLI Renderer"},
    ))
    cli.render(InteractionEvent(
        type=InteractionEventType.MESSAGE_DELTA,
        request_id="req-9",
        payload={"text": "This is a CLI response."},
    ))
    cli.render(InteractionEvent(
        type=InteractionEventType.MESSAGE_COMPLETE,
        request_id="req-9",
        payload={},
    ))
    print("  " + "-" * 40)
    print()

    # ── Step 9: 清理 ──
    print("Step 9: 清理")
    pr.shutdown()
    assert not pr.is_started
    assert pr.registry.count == 0
    assert cli._started == False  # noqa: stop() sets _started=False
    print("  ✓ PresentationRuntime shutdown complete")
    print()

    # ── 结果 ──
    print("=" * 60)
    print("Phase 2-C.4 Multi Renderer Proof: PASSED")
    print("=" * 60)
    print()
    print("证明结论:")
    print("  1. PresentationRuntime 可以注册多个 Renderer")
    print("  2. 同一时刻只能激活一个 Renderer（Single Active Rule）")
    print("  3. InteractionEvent 可以分发给任意活跃 Renderer")
    print("  4. Shell State 同步对任意 Renderer 透明")
    print("  5. PresentationRuntime 零 Renderer 类型感知")
    print()
    print("Presentation Layer 已与 UI 技术栈完全解耦。")
    return True


def test_single_active_rule():
    """验证 Single Active Renderer Rule 不会被绕过。"""
    pr = PresentationRuntime()
    cli = CLIRenderer(prefix="TEST")
    recorder = RecorderRenderer()
    pr.register_renderer("cli", cli)
    pr.register_renderer("recorder", recorder)

    pr.activate_renderer("cli")
    try:
        pr.activate_renderer("recorder")
        assert False, "Should have raised RendererRegistryError"
    except RendererRegistryError:
        pass  # Expected

    pr.shutdown()
    return True


if __name__ == "__main__":
    success = run_proof()
    test_single_active_rule()
    sys.exit(0 if success else 1)