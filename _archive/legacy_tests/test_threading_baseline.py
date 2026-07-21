"""
性能回归基准 — 线程规模

验证 v3.8 的低功耗策略：
- BaseWorker / AgentWorker 的同步线程池上限为 4
- asyncio.to_thread 不会无限制创建线程
- 为后续版本对比留下可复用的基准断言
"""
import asyncio
import threading
import time
import unittest

from workers.agent_worker import AgentWorker


class TestThreadingBaseline(unittest.TestCase):
    def _start_worker(self, worker: AgentWorker):
        """在守护线程中启动 worker，等待事件循环就绪"""
        thread = threading.Thread(target=worker.run)
        thread.daemon = True
        thread.start()
        worker._loop_ready.wait(timeout=3.0)
        self.assertTrue(
            worker._loop_ready.is_set(),
            "Worker 事件循环未在超时内就绪",
        )
        return thread

    def _stop_worker(self, worker: AgentWorker, thread: threading.Thread):
        worker.stop()
        thread.join(timeout=3.0)

    def test_agent_worker_cpu_executor_max_workers(self):
        """AgentWorker 启动后 _cpu_executor 上限应为 4"""
        worker = AgentWorker(
            mode_name="ask",
            current_llm=None,
            project_root="",
        )
        thread = self._start_worker(worker)
        try:
            self.assertIsNotNone(worker._cpu_executor)
            max_workers = getattr(worker._cpu_executor, "max_workers", getattr(worker._cpu_executor, "_max_workers", None))
            self.assertEqual(max_workers, 4)
        finally:
            self._stop_worker(worker, thread)

    def test_asyncio_to_thread_pool_bounded(self):
        """asyncio.to_thread 默认线程池不应在 20 并发任务下失控"""
        async def noop():
            await asyncio.to_thread(lambda: None)

        async def main():
            before = threading.active_count()
            await asyncio.gather(*[noop() for _ in range(20)])
            after = threading.active_count()
            return after - before

        delta = asyncio.run(main())
        # 正常默认线程池规模通常为 min(32, CPU*5)，这里给宽松上限
        self.assertLess(delta, 50)

    def test_run_in_executor_reuses_cpu_pool(self):
        """显式 loop.run_in_executor(_cpu_executor) 应复用固定线程池"""
        worker = AgentWorker(
            mode_name="ask",
            current_llm=None,
            project_root="",
        )
        thread = self._start_worker(worker)
        try:
            executor = worker._cpu_executor
            self.assertIsNotNone(executor)

            async def run_in_pool():
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(executor, lambda: threading.current_thread().name)

            async def main():
                return await asyncio.gather(*[run_in_pool() for _ in range(8)])

            names = asyncio.run(main())
            unique_names = set(names)
            # 8 个任务应复用不超过 4 个线程
            self.assertLessEqual(len(unique_names), 4)
        finally:
            self._stop_worker(worker, thread)
