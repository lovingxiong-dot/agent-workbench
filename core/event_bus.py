"""
event_bus.py — v3 事件总线

基于 PySide6 Signal 的强类型事件总线，默认 QueuedConnection 保证同线程事件顺序。
"""
from typing import Callable, Optional
from PySide6.QtCore import QObject, Signal, Qt

from core.events import Event


class MessageBus(QObject):
    """
    全局事件总线。

    - 所有事件统一通过 event_emitted Signal 分发
    - 默认使用 Qt.QueuedConnection，避免跨组件同步调用导致重入
    - 支持按 namespace 订阅，也支持自定义 filter 订阅
    - 内置追踪日志，便于调试事件风暴
    """

    event_emitted = Signal(object)  # payload: Event 实例

    def __init__(self, parent=None, trace: bool = False):
        super().__init__(parent)
        self._trace = trace
        self._handlers: list[tuple[Optional[str], Optional[Callable[[Event], bool]], Callable[[Event], None]]] = []

    def emit(self, event: Event):
        """发射事件。默认 QueuedConnection。"""
        if self._trace:
            print(f"[BUS] emit {event.event_type()}", flush=True)
        self.event_emitted.emit(event)

    def subscribe(
        self,
        handler: Callable[[Event], None],
        namespace: Optional[str] = None,
        event_filter: Optional[Callable[[Event], bool]] = None,
    ):
        """
        订阅事件。

        :param handler: 事件处理函数
        :param namespace: 仅接收指定 namespace 的事件（如 "user"）
        :param event_filter: 额外过滤函数，返回 True 才调用 handler
        """
        self._handlers.append((namespace, event_filter, handler))

    def subscribe_namespace(self, namespace: str, handler: Callable[[Event], None]):
        """按 namespace 订阅。"""
        self.subscribe(handler, namespace=namespace)

    def process(self, event: Event):
        """
        同步处理单个事件（主要用于测试）。
        正常场景由 Qt 信号机制自动调用。
        """
        self._dispatch(event)

    def _dispatch(self, event: Event):
        """内部分发逻辑。"""
        if self._trace:
            print(f"[BUS] dispatch {event.event_type()}", flush=True)
        for ns, filt, handler in self._handlers:
            if ns is not None and event.namespace != ns:
                continue
            if filt is not None and not filt(event):
                continue
            try:
                handler(event)
            except Exception as e:
                print(f"[BUS] handler error for {event.event_type()}: {e}", flush=True)
                raise

    def connect_dispatch(self):
        """将 event_emitted 信号连接到内部分发器。"""
        self.event_emitted.connect(self._dispatch, Qt.QueuedConnection)
