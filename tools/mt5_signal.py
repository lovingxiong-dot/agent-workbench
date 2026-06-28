"""
MT5 Signal — 异步信号结构体与总线

为 MT5 与 Python 之间的异步信号通信提供标准化数据结构与总线。
未来可接入：交易信号、行情推送、账户状态、错误事件等。

设计原则：
- 数据结构与总线解耦：MT5Signal 是纯数据，MT5SignalBus 负责分发
- 所有 I/O 均为 async，避免阻塞事件循环
- 支持发布-订阅模式，带背压保护
- 为后续 MT5 EA / Python bridge 预留接口
"""
import asyncio
import inspect
import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional


class SignalType(Enum):
    """MT5 信号类型"""
    PRICE = auto()
    TRADE = auto()
    ACCOUNT = auto()
    ERROR = auto()
    HEARTBEAT = auto()


class TradeAction(Enum):
    """交易动作"""
    BUY = "buy"
    SELL = "sell"
    CLOSE = "close"
    MODIFY = "modify"


@dataclass
class MT5Signal:
    """MT5 信号标准结构体"""
    signal_id: str
    timestamp: str
    symbol: str
    signal_type: str
    payload: Dict[str, Any]

    def to_json(self) -> str:
        return json.dumps(
            {
                "signal_id": self.signal_id,
                "timestamp": self.timestamp,
                "symbol": self.symbol,
                "signal_type": self.signal_type,
                "payload": self.payload,
            },
            ensure_ascii=False,
        )

    @classmethod
    def from_json(cls, text: str) -> "MT5Signal":
        data = json.loads(text)
        return cls(**data)

    @classmethod
    def price(cls, symbol: str, bid: float, ask: float, spread: float) -> "MT5Signal":
        return cls(
            signal_id=uuid.uuid4().hex[:12],
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            signal_type=SignalType.PRICE.name,
            payload={"bid": bid, "ask": ask, "spread": spread},
        )

    @classmethod
    def trade(
        cls,
        symbol: str,
        action: str,
        volume: float,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
    ) -> "MT5Signal":
        return cls(
            signal_id=uuid.uuid4().hex[:12],
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            signal_type=SignalType.TRADE.name,
            payload={
                "action": action,
                "volume": volume,
                "price": price,
                "sl": sl,
                "tp": tp,
            },
        )

    @classmethod
    def account(cls, balance: float, equity: float, margin: float) -> "MT5Signal":
        return cls(
            signal_id=uuid.uuid4().hex[:12],
            timestamp=datetime.now().isoformat(),
            symbol="ACCOUNT",
            signal_type=SignalType.ACCOUNT.name,
            payload={"balance": balance, "equity": equity, "margin": margin},
        )

    @classmethod
    def error(cls, symbol: str, message: str) -> "MT5Signal":
        return cls(
            signal_id=uuid.uuid4().hex[:12],
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            signal_type=SignalType.ERROR.name,
            payload={"message": message},
        )

    @classmethod
    def heartbeat(cls) -> "MT5Signal":
        return cls(
            signal_id=uuid.uuid4().hex[:12],
            timestamp=datetime.now().isoformat(),
            symbol="",
            signal_type=SignalType.HEARTBEAT.name,
            payload={},
        )


class MT5SignalBus:
    """异步信号总线：支持发布-订阅和背压保护"""

    def __init__(self, max_queue: int = 1000):
        self._subscribers: Dict[SignalType, List[Callable]] = {}
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue)
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._dropped_count = 0

    @property
    def dropped_count(self) -> int:
        return self._dropped_count

    def subscribe(self, signal_type: SignalType, callback: Callable):
        """订阅指定类型的信号"""
        self._subscribers.setdefault(signal_type, []).append(callback)

    def unsubscribe(self, signal_type: SignalType, callback: Callable):
        """取消订阅"""
        if signal_type in self._subscribers:
            self._subscribers[signal_type] = [
                cb for cb in self._subscribers[signal_type] if cb != callback
            ]

    async def publish(self, signal: MT5Signal):
        """发布信号到总线（非阻塞，队列满时丢弃最旧）"""
        try:
            self._queue.put_nowait(signal)
        except asyncio.QueueFull:
            try:
                self._queue.get_nowait()
                self._queue.put_nowait(signal)
                self._dropped_count += 1
            except asyncio.QueueEmpty:
                pass

    async def start(self):
        """启动分发循环"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._dispatch_loop())

    async def stop(self):
        """停止分发循环"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _dispatch_loop(self):
        """内部调度循环"""
        while self._running:
            try:
                signal = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            signal_type = (
                SignalType[signal.signal_type]
                if signal.signal_type in SignalType.__members__
                else SignalType.ERROR
            )
            callbacks = self._subscribers.get(signal_type, [])
            for callback in callbacks:
                try:
                    if inspect.iscoroutinefunction(callback):
                        asyncio.create_task(callback(signal))
                    else:
                        callback(signal)
                except Exception:
                    # 回调异常不应中断总线
                    pass


class MT5SignalHandler(ABC):
    """MT5 信号处理器接口"""

    @abstractmethod
    async def on_price(self, signal: MT5Signal):
        ...

    @abstractmethod
    async def on_trade(self, signal: MT5Signal):
        ...

    @abstractmethod
    async def on_account(self, signal: MT5Signal):
        ...

    @abstractmethod
    async def on_error(self, signal: MT5Signal):
        ...
