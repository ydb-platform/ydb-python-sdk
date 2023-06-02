import time
from contextlib import contextmanager
from importlib.metadata import version
from collections.abc import Iterable

from os import environ

environ["PROMETHEUS_DISABLE_CREATED_SERIES"] = "True"

from prometheus_client import CollectorRegistry, Gauge, Histogram, push_to_gateway  # noqa: E402
from summary import Summary  # noqa: E402

JOB_READ_LABEL, JOB_WRITE_LABEL = "read", "write"
JOB_STATUS_OK, JOB_STATUS_ERR = "ok", "err"


class Metrics:
    def __init__(self, push_gateway):
        self._push_gtw = push_gateway
        self._registry = CollectorRegistry()
        self._metrics = dict(
            oks=Gauge(
                "oks",
                "amount of OK requests",
                labelnames=("jobName",),
                registry=self._registry,
            ),
            not_oks=Gauge(
                "not_oks",
                "amount of not OK requests",
                labelnames=("jobName",),
                registry=self._registry,
            ),
            inflight=Gauge(
                "inflight",
                "amount of requests in flight",
                labelnames=("jobName",),
                registry=self._registry,
            ),
            latency=Summary(
                "latency",
                "summary of latencies in ms",
                labelnames=("jobName", "status"),
                registry=self._registry,
                objectives=(
                    (0.5, 0.01),
                    (0.99, 0.001),
                    (1.0, 0.0),
                ),
            ),
            attempts=Histogram(
                "attempts",
                "histogram of amount of requests",
                labelnames=("jobName", "status"),
                registry=self._registry,
                buckets=tuple(range(1, 11)),
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

        self.inflight.labels(*labels).inc()
        return time.time()

    def stop(self, labels, start_time, attempts=1, error=None):
        runtime_ms = 1000 * (time.time() - start_time)

        if not isinstance(labels, Iterable):
            labels = (labels,)

        self.inflight.labels(*labels).dec()

        if error:
            self.not_oks.labels(*labels).inc()
            self.latency.labels(*labels, JOB_STATUS_ERR).observe(runtime_ms)
            return

        self.oks.labels(*labels).inc()
        self.latency.labels(*labels, JOB_STATUS_OK).observe(runtime_ms)
        self.attempts.labels(*labels, JOB_STATUS_OK).observe(attempts)

    def push(self):
        push_to_gateway(
            self._push_gtw,
            job="workload-sync",
            registry=self._registry,
            grouping_key={
                "sdk": "python-sync",
                "sdkVersion": version("ydb"),
            },
        )

    def reset(self):
        for label in (JOB_READ_LABEL, JOB_WRITE_LABEL):
            self.oks.labels(label).set(0)
            self.not_oks.labels(label).set(0)
            self.inflight.labels(label).set(0)

        self.latency.clear()
        self.attempts.clear()

        self.push()
