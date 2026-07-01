"""
event_bus.py — v4 消息总线

基于 PySide6 Signal 的强类型事件总线，默认 QueuedConnection。

核心设计：
- 所有事件携带 session_id，便于路由
- 生产者不阻塞，消费者按需处理
- 后台事件被丢弃，不阻塞 Worker
"""
from typing import Callable, Optional, List
from PySide6.QtCore import QObject, Signal, Qt

from .events import Event


class MessageBus(QObject):
    """全局事件总线
    
    - 所有事件统一通过 event_emitted Signal 分发
    - 默认使用 Qt.QueuedConnection，避免跨组件同步调用导致重入
    - 支持按 namespace 订阅，也支持自定义 filter 订阅
    - 内置追踪日志，便于调试事件风暴
    """

    event_emitted = Signal(object)  # payload: Event 实例

    def __init__(self, parent=None, trace: bool = False):
        super().__init__(parent)
        self._trace = trace
        self._handlers: List[tuple[
            Optional[str],
            Optional[Callable[[Event], bool]],
            Callable[[Event], None]
        ]] = []

    def emit(self, event: Event):
        """发射事件。默认 QueuedConnection。"""
        if self._trace or (event.namespace == "worker" and event.name == "create"):
            print(f"[BUS] emit {event.namespace}.{event.name}", flush=True)
        self.event_emitted.emit(event)

    def subscribe(
        self,
        handler: Callable[[Event], None],
        namespace: Optional[str] = None,
        event_filter: Optional[Callable[[Event], bool]] = None,
    ):
        """
        订阅事件
        
        :param handler: 事件处理函数
        :param namespace: 仅接收指定 namespace 的事件
        :param event_filter: 额外过滤函数，返回 True 才调用 handler
        """
        print(f"[DEBUG bus subscribe] ns={namespace} handler={handler}", flush=True)
        self._handlers.append((namespace, event_filter, handler))

    def subscribe_namespace(self, namespace: str, handler: Callable[[Event], None]):
        """按 namespace 订阅。"""
        self.subscribe(handler, namespace=namespace)

    def subscribe_name(self, namespace: str, name: str, handler: Callable[[Event], None]):
        """按 namespace + event name 精确订阅。"""
        self.subscribe(handler, namespace=namespace, event_filter=lambda e: e.name == name)

    def subscribe_session(self, session_id: str, handler: Callable[[Event], None]):
        """按 session_id 订阅（只接收指定会话的事件）。"""
        self.subscribe(handler, event_filter=lambda e: e.session_id == session_id)

    def unsubscribe(self, handler: Callable[[Event], None]):
        """移除指定 handler 的所有订阅。"""
        before = len(self._handlers)
        self._handlers = [
            (ns, filt, h) for ns, filt, h in self._handlers if h != handler
        ]
        print(f"[DEBUG bus unsubscribe] handler={handler} removed={before - len(self._handlers)} left={len(self._handlers)}", flush=True)

    def process(self, event: Event):
        """同步处理单个事件（主要用于测试）。"""
        self._dispatch(event)

    def _dispatch(self, event: Event):
        """内部分发逻辑。"""
        print(f"[DEBUG bus dispatch] ns={event.namespace} name={event.name}", flush=True)
        if event.namespace == "worker" and event.name == "create":
            print(f"[DEBUG bus dispatch] worker.create handlers={len(self._handlers)}", flush=True)
        for ns, filt, handler in self._handlers:
            if ns is not None and event.namespace != ns:
                continue
            if filt is not None and not filt(event):
                continue
            if event.namespace == "worker" and event.name == "create":
                print(f"[DEBUG bus dispatch] calling handler={handler}", flush=True)
            try:
                handler(event)
            except Exception as e:
                print(f"[BUS] error: {e}", flush=True)
                raise

    def connect_dispatch(self):
        """将 event_emitted 信号连接到内部分发器。"""
        self.event_emitted.connect(self._dispatch, Qt.QueuedConnection)
