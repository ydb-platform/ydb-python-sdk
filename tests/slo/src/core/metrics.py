from abc import ABC, abstractmethod

import time
from contextlib import contextmanager
from importlib.metadata import version
from collections.abc import Iterable
import logging
from os import environ

environ["PROMETHEUS_DISABLE_CREATED_SERIES"] = "True"

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, push_to_gateway  # noqa: E402

OP_TYPE_READ, OP_TYPE_WRITE = "read", "write"
OP_STATUS_SUCCESS, OP_STATUS_FAILURE = "success", "err"

REF = environ.get("REF", "main")
WORKLOAD = environ.get("WORKLOAD", "sync-query")


logger = logging.getLogger(__name__)


class BaseMetrics(ABC):
    @abstractmethod
    def start(self, labels):
        pass

    @abstractmethod
    def stop(self, labels, start_time, attempts=1, error=None):
        pass

    @abstractmethod
    def reset(self):
        pass


def create_metrics(push_gateway) -> BaseMetrics:
    if push_gateway:
        logger.info("Creating metrics with push gateway: %s", push_gateway)
        return Metrics(push_gateway)
    else:
        logger.info("Creating dummy metrics")
        return DummyMetrics()


class DummyMetrics(BaseMetrics):
    def start(self, labels):
        return 0

    def stop(self, labels, start_time, attempts=1, error=None):
        pass

    def reset(self):
        pass


class Metrics(BaseMetrics):
    def __init__(self, push_gateway):
        self._push_gtw = push_gateway
        self._registry = CollectorRegistry()
        self._metrics = dict(
            errors_total=Counter(
                "sdk_errors_total",
                "Total number of errors encountered, categorized by error type.",
                labelnames=("operation_type", "error_type"),
                registry=self._registry,
            ),
            operations_total=Counter(
                "sdk_operations_total",
                "Total number of operations, categorized by type attempted by the SDK.",
                labelnames=("operation_type",),
                registry=self._registry,
            ),
            operations_success_total=Counter(
                "sdk_operations_success_total",
                "Total number of successful operations, categorized by type.",
                labelnames=("operation_type",),
                registry=self._registry,
            ),
            operations_failure_total=Counter(
                "sdk_operations_failure_total",
                "Total number of failed operations, categorized by type.",
                labelnames=("operation_type",),
                registry=self._registry,
            ),
            operation_latency_seconds=Histogram(
                "sdk_operation_latency_seconds",
                "Latency of operations performed by the SDK in seconds, categorized by type and status.",
                labelnames=(
                    "operation_type",
                    "operation_status",
                ),
                registry=self._registry,
                buckets=(
                    0.001,  # 1 ms
                    0.002,  # 2 ms
                    0.003,  # 3 ms
                    0.004,  # 4 ms
                    0.005,  # 5 ms
                    0.0075,  # 7.5 ms
                    0.010,  # 10 ms
                    0.020,  # 20 ms
                    0.050,  # 50 ms
                    0.100,  # 100 ms
                    0.200,  # 200 ms
                    0.500,  # 500 ms
                    1.000,  # 1 s
                ),
            ),
            retry_attempts=Gauge(
                "sdk_retry_attempts",
                "Current retry attempts, categorized by operation type.",
                labelnames=("operation_type",),
                registry=self._registry,
            ),
            # retry_attempts_total=Counter(
            #     "sdk_retry_attempts_total",
            #     "Total number of retry attempts, categorized by operation type.",
            #     labelnames=("operation_type",),
            #     registry=self._registry,
            # ),
            # retries_success_total=Counter(
            #     "sdk_retries_success_total",
            #     "Total number of successful retries, categorized by operation type.",
            #     labelnames=("operation_type",),
            #     registry=self._registry,
            # ),
            # retries_failure_total=Counter(
            #     "sdk_retries_failure_total",
            #     "Total number of failed retries, categorized by operation type.",
            #     labelnames=("operation_type",),
            #     registry=self._registry,
            # ),
            pending_operations=Gauge(
                "sdk_pending_operations",
                "Current number of pending operations, categorized by type.",
                labelnames=("operation_type",),
                registry=self._registry,
            ),
        )
        self.reset()

    def __getattr__(self, item):
        try:
            return self._metrics[item]
        except KeyError:
            raise AttributeError(f"'{Metrics.__name__}' object has no attribute '{item}'")

    @contextmanager
    def measure(self, labels):
        start_ts = self.start(labels)
        error = None
        try:
            yield self
        except Exception as err:
            error = err
        finally:
            self.stop(labels, start_ts, error=error)

    def start(self, labels):
        if not isinstance(labels, Iterable):
            labels = (labels,)

        self.pending_operations.labels(*labels).inc()
        return time.time()

    def stop(self, labels, start_time, attempts=1, error=None):
        duration = time.time() - start_time

        if not isinstance(labels, Iterable):
            labels = (labels,)

        self.retry_attempts.labels(*labels).set(attempts)
        self.operations_total.labels(*labels).inc()
        self.pending_operations.labels(*labels).dec()
        # self.retry_attempts_total.labels(*labels).inc(attempts)

        if error:
            self.errors_total.labels(*labels, type(error).__name__).inc()
            # self.retries_failure_total.labels(*labels).inc(attempts)
            self.operations_failure_total.labels(*labels).inc()
            self.operation_latency_seconds.labels(*labels, OP_STATUS_FAILURE).observe(duration)
            return

        # self.retries_success_total.labels(*labels).inc(attempts)
        self.operations_success_total.labels(*labels).inc()
        self.operation_latency_seconds.labels(*labels, OP_STATUS_SUCCESS).observe(duration)

    def push(self):
        push_to_gateway(
            self._push_gtw,
            job=f"workload-{WORKLOAD}",
            registry=self._registry,
            grouping_key={
                "ref": REF,
                "sdk": "ydb-python-sdk",
                "sdk_version": version("ydb"),
                "workload": WORKLOAD,
                "workload_version": "0.0.0",
            },
        )

    def reset(self):
        for m in self._metrics.values():
            m.clear()

        self.push()
