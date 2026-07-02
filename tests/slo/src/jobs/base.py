import asyncio
import logging
import threading
import time
from abc import ABC, abstractmethod

import ydb

logger = logging.getLogger(__name__)


class SyncRateLimiter:
    """
    A lightweight, thread-safe synchronous rate limiter.

    It enforces a minimum time interval between consecutive "permits" across all
    threads sharing the same instance.
    """

    def __init__(self, min_interval_s: float) -> None:
        self._min_interval_s = max(0.0, float(min_interval_s))
        self._lock = threading.Lock()
        self._next_allowed_ts = 0.0  # monotonic timestamp

    def __enter__(self):
        # Fast-path: no limiting.
        if self._min_interval_s <= 0.0:
            return self

        while True:
            with self._lock:
                now = time.monotonic()
                if now >= self._next_allowed_ts:
                    self._next_allowed_ts = now + self._min_interval_s
                    return self
                sleep_for = self._next_allowed_ts - now

            # Sleep outside the lock so other threads can observe the schedule.
            if sleep_for > 0:
                time.sleep(sleep_for)

    def __exit__(self, exc_type, exc, tb) -> bool:
        # Do not suppress exceptions.
        return False


class BaseJobManager(ABC):
    def __init__(self, driver, args, metrics):
        self.driver: ydb.Driver = driver
        self.args = args
        self.metrics = metrics

    @abstractmethod
    def run_tests(self):
        pass

    def _run_metric_job(self):
        if not getattr(self.args, "otlp_endpoint", None):
            return []

        report_period_ms = max(1, int(self.args.report_period))
        limiter = SyncRateLimiter(min_interval_s=report_period_ms / 1000.0)

        future = threading.Thread(
            name="slo_metrics_sender",
            target=self._metric_sender,
            args=(limiter, self.args.time),
        )
        future.start()
        return [future]

    def _metric_sender(self, limiter, runtime):
        start_time = time.time()
        logger.info("Start push metrics")

        while time.time() - start_time < runtime:
            with limiter:
                self.metrics.push()

        logger.info("Stop push metrics")


class AsyncBaseJobManager(BaseJobManager):
    """Base for asyncio-based job managers.

    Overrides the metrics job with an asyncio task so it can be awaited
    together with the read/write tasks via ``asyncio.gather``.
    """

    @abstractmethod
    async def run_tests(self):
        pass

    def _run_metric_job(self):
        if not getattr(self.args, "otlp_endpoint", None):
            return []

        task = asyncio.create_task(
            self._async_metric_sender(self.args.time),
            name="slo_metrics_sender",
        )
        return [task]

    async def _async_metric_sender(self, runtime):
        # `aiolimiter` is a runtime dependency (see `tests/slo/requirements.txt`).
        from aiolimiter import AsyncLimiter  # pyright: ignore[reportMissingImports]

        start_time = time.time()
        logger.info("Start push metrics (async)")

        # One push per report_period (mirrors the sync SyncRateLimiter); guard 0.
        report_period_ms = max(1, int(self.args.report_period))
        limiter = AsyncLimiter(max_rate=1, time_period=report_period_ms / 1000.0)

        while time.time() - start_time < runtime:
            async with limiter:
                # Call sync metrics.push() in executor to avoid blocking the event loop.
                await asyncio.get_running_loop().run_in_executor(None, self.metrics.push)

        logger.info("Stop push metrics (async)")
