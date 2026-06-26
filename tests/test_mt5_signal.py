"""
MT5 Signal 单元测试

验证信号结构体序列化与异步总线分发。
"""
import asyncio
import unittest

from tools.mt5_signal import MT5Signal, MT5SignalBus, SignalType


class TestMT5Signal(unittest.TestCase):
    def test_price_signal_serialization(self):
        signal = MT5Signal.price("EURUSD", bid=1.0850, ask=1.0852, spread=0.0002)
        data = signal.to_json()
        restored = MT5Signal.from_json(data)
        self.assertEqual(restored.symbol, "EURUSD")
        self.assertEqual(restored.signal_type, SignalType.PRICE.name)
        self.assertEqual(restored.payload["bid"], 1.0850)

    def test_trade_signal_payload(self):
        signal = MT5Signal.trade("XAUUSD", action="buy", volume=0.1, price=1950.0)
        self.assertEqual(signal.payload["action"], "buy")
        self.assertEqual(signal.payload["volume"], 0.1)

    def test_signal_bus_dispatch(self):
        received = []

        async def handler(signal):
            received.append(signal)

        async def main():
            bus = MT5SignalBus()
            bus.subscribe(SignalType.PRICE, handler)
            await bus.start()
            signal = MT5Signal.price("EURUSD", 1.0, 1.1, 0.1)
            await bus.publish(signal)
            await asyncio.sleep(0.1)
            await bus.stop()

        asyncio.run(main())
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].symbol, "EURUSD")

    def test_signal_bus_backpressure(self):
        async def main():
            bus = MT5SignalBus(max_queue=2)
            await bus.start()
            for i in range(5):
                signal = MT5Signal.price("EURUSD", float(i), float(i), 0.1)
                await bus.publish(signal)
            await bus.stop()
            return bus.dropped_count

        dropped = asyncio.run(main())
        self.assertGreater(dropped, 0)
