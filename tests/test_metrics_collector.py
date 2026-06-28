"""
Tests for services.metrics_collector
"""
import time
import unittest

from services.metrics_collector import TurnMetrics, MetricsCollector


class TestTurnMetrics(unittest.TestCase):
    def test_format_brief(self):
        m = TurnMetrics(total_tokens=33546, total_ms=34)
        self.assertEqual(m.format_brief(), "33546tok/34ms")

    def test_format_brief_zero(self):
        m = TurnMetrics()
        self.assertEqual(m.format_brief(), "0tok/0ms")

    def test_format_detail(self):
        m = TurnMetrics(input_tokens=100, output_tokens=200, total_tokens=300,
                        ttft_ms=8, total_ms=34)
        detail = m.format_detail()
        self.assertIn("TTFT=8ms", detail)
        self.assertIn("Total=34ms", detail)
        self.assertIn("Tokens=100+200=300", detail)


class TestMetricsCollector(unittest.TestCase):
    def test_finish_turn_computes_total_time(self):
        collector = MetricsCollector()
        collector.start_turn()
        time.sleep(0.01)
        metrics = collector.finish_turn(input_tokens=10, output_tokens=20)

        self.assertEqual(metrics.input_tokens, 10)
        self.assertEqual(metrics.output_tokens, 20)
        self.assertEqual(metrics.total_tokens, 30)
        self.assertGreaterEqual(metrics.total_ms, 10)

    def test_first_token_reduces_ttft(self):
        collector = MetricsCollector()
        collector.start_turn()
        time.sleep(0.005)
        collector.mark_first_token()
        time.sleep(0.015)
        metrics = collector.finish_turn(1, 1)

        self.assertGreater(metrics.ttft_ms, 0)
        self.assertLess(metrics.ttft_ms, metrics.total_ms)

    def test_session_accumulation(self):
        collector = MetricsCollector()
        collector.start_turn()
        collector.finish_turn(10, 20)
        collector.start_turn()
        collector.finish_turn(5, 15)

        totals = collector.session_totals()
        self.assertEqual(totals["turns"], 2)
        self.assertEqual(totals["tokens"], 50)

    def test_reset_session_clears_totals(self):
        collector = MetricsCollector()
        collector.start_turn()
        collector.finish_turn(10, 20)
        collector.reset_session()

        totals = collector.session_totals()
        self.assertEqual(totals["turns"], 0)
        self.assertEqual(totals["tokens"], 0)

    def test_negative_tokens_are_clamped(self):
        collector = MetricsCollector()
        collector.start_turn()
        metrics = collector.finish_turn(input_tokens=-5, output_tokens=-10)
        self.assertEqual(metrics.total_tokens, 0)

    def test_static_format(self):
        m = TurnMetrics(total_tokens=128, total_ms=256)
        self.assertEqual(MetricsCollector.format(m), "128tok/256ms")


if __name__ == "__main__":
    unittest.main()
