from abc import ABC, abstractmethod
import logging
import threading
import time
from ratelimiter import RateLimiter

import ydb

logger = logging.getLogger(__name__)


class BaseJobManager(ABC):
    def __init__(self, driver, args, metrics):
        self.driver: ydb.Driver = driver
        self.args = args
        self.metrics = metrics

    @abstractmethod
    def run_tests(self):
        pass

    def _run_metric_job(self):
        if not self.args.prom_pgw:
            return []

        limiter = RateLimiter(max_calls=10**6 // self.args.report_period, period=1)

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
