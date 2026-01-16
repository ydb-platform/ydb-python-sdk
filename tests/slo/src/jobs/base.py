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
