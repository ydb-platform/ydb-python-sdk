from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Iterable
from contextlib import contextmanager
from importlib.metadata import version
from os import environ
from typing import Any, Optional, Tuple

OP_TYPE_READ, OP_TYPE_WRITE = "read", "write"
OP_STATUS_SUCCESS, OP_STATUS_FAILURE = "success", "err"

REF = environ.get("REF", "main")
WORKLOAD = environ.get("WORKLOAD", "sync-query")

logger = logging.getLogger(__name__)


def _normalize_labels(labels: Any) -> Tuple[Any, ...]:
    """
    Convert labels into a tuple of label values.

    Important:
    - `str` is an Iterable, but for our purposes it must be treated as a single label value.
    """
    if labels is None:
        return tuple()

    if isinstance(labels, str):
        return (labels,)

    if isinstance(labels, tuple):
        return labels

    if isinstance(labels, list):
        return tuple(labels)

    if isinstance(labels, Iterable):
        return tuple(labels)

    return (labels,)


class BaseMetrics(ABC):
    @abstractmethod
    def start(self, labels) -> float:
        pass

    @abstractmethod
    def stop(
        self,
        labels,
        start_time: float,
        attempts: int = 1,
        error: Optional[Exception] = None,
    ) -> None:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass

    @abstractmethod
    def push(self) -> None:
        pass

    @contextmanager
    def measure(self, labels):
        start_ts = self.start(labels)
        error = None
        try:
            yield self
        except Exception as err:
            error = err
            raise
        finally:
            self.stop(labels, start_ts, error=error)


class DummyMetrics(BaseMetrics):
    def start(self, labels) -> float:
        return 0.0

    def stop(
        self,
        labels,
        start_time: float,
        attempts: int = 1,
        error: Optional[Exception] = None,
    ) -> None:
        return None

    def reset(self) -> None:
        return None

    def push(self) -> None:
        return None


class OtlpMetrics(BaseMetrics):
    """
    Canonical OpenTelemetry metrics implementation.

    This exports metrics via OTLP/HTTP to a Prometheus server with OTLP receiver enabled:
      POST http(s)://<host>:<port>/api/v1/otlp/v1/metrics

    Naming notes:
    - Metric names follow OpenTelemetry conventions (dot-separated namespaces, e.g. `sdk.operations.total`).
    - Prometheus OTLP translation typically converts dots to underscores and may add suffixes like
      `_total` for counters and `_bucket/_sum/_count` for histograms.
    """

    def __init__(self, otlp_metrics_endpoint: str):
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource

        # Resource attributes: Prometheus maps service.name -> job, service.instance.id -> instance.
        resource = Resource.create(
            {
                "service.name": f"workload-{WORKLOAD}",
                "service.instance.id": environ.get("SLO_INSTANCE_ID", f"{REF}-{WORKLOAD}"),
                "ref": REF,
                "sdk": "ydb-python-sdk",
                "sdk_version": version("ydb"),
                "workload": WORKLOAD,
                "workload_version": "0.0.0",
            }
        )

        exporter = OTLPMetricExporter(endpoint=otlp_metrics_endpoint)
        reader = PeriodicExportingMetricReader(exporter)  # we force_flush() explicitly in push()

        self._provider = MeterProvider(resource=resource, metric_readers=[reader])
        self._meter = self._provider.get_meter("ydb-slo")

        # Instruments (sync)
        self._errors = self._meter.create_counter(
            name="sdk.errors.total",
            description="Total number of errors encountered, categorized by error type.",
        )
        self._operations_total = self._meter.create_counter(
            name="sdk.operations.total",
            description="Total number of operations, categorized by type attempted by the SDK.",
        )
        self._operations_success_total = self._meter.create_counter(
            name="sdk.operations.success.total",
            description="Total number of successful operations, categorized by type.",
        )
        self._operations_failure_total = self._meter.create_counter(
            name="sdk.operations.failure.total",
            description="Total number of failed operations, categorized by type.",
        )
        self._latency = self._meter.create_histogram(
            name="sdk.operation.latency",
            unit="s",
            description="Latency of operations performed by the SDK in seconds, categorized by type and status.",
        )

        # Pending operations: sync UpDownCounter (canonical for "in flight" style metrics).
        self._pending = self._meter.create_up_down_counter(
            name="sdk.pending.operations",
            description="Current number of pending operations, categorized by type.",
        )

        # Retry attempts: counter (monotonic). Suitable for rate()/increase() in PromQL.
        self._retry_attempts_total = self._meter.create_counter(
            name="sdk.retry.attempts.total",
            description="Total number of retry attempts, categorized by ref and operation type.",
        )

        self.reset()

    def start(self, labels) -> float:
        labels_t = _normalize_labels(labels)
        self._pending.add(
            1,
            attributes={
                "ref": REF,
                "operation_type": labels_t[0],
            },
        )
        return time.time()

    def stop(
        self,
        labels,
        start_time: float,
        attempts: int = 1,
        error: Optional[Exception] = None,
    ) -> None:
        labels_t = _normalize_labels(labels)
        duration = time.time() - start_time

        op_type = labels_t[0]
        base_attrs = {
            "ref": REF,
            "operation_type": op_type,
        }

        # Update instruments
        self._retry_attempts_total.add(int(attempts), attributes=base_attrs)
        self._pending.add(-1, attributes=base_attrs)

        # Counters + latency
        self._operations_total.add(1, attributes=base_attrs)

        if error is not None:
            self._errors.add(
                1,
                attributes={
                    **base_attrs,
                    "error_type": type(error).__name__,
                },
            )
            self._operations_failure_total.add(1, attributes=base_attrs)
            self._latency.record(
                duration,
                attributes={
                    **base_attrs,
                    "operation_status": OP_STATUS_FAILURE,
                },
            )
            return

        self._operations_success_total.add(1, attributes=base_attrs)
        self._latency.record(
            duration,
            attributes={
                **base_attrs,
                "operation_status": OP_STATUS_SUCCESS,
            },
        )

    def push(self) -> None:
        # Metrics job calls push() with the cadence of --report-period.
        # force_flush() makes the exporter send immediately.
        self._provider.force_flush()

    def reset(self) -> None:
        # OpenTelemetry counters/histograms are cumulative and cannot be reset.
        # Reset is implemented as an immediate push/flush.
        self.push()


def create_metrics(otlp_endpoint: Optional[str]) -> BaseMetrics:
    """
    Factory used by SLO runners.

    Metrics are enabled if either:
    - OTLP_ENDPOINT env var is set, or
    - `--otlp-endpoint` is provided (and non-empty)

    If endpoint is empty, metrics are disabled (DummyMetrics).
    """
    endpoint = (environ.get("OTLP_ENDPOINT") or (otlp_endpoint or "")).strip()
    if not endpoint:
        logger.info("Creating dummy metrics (metrics disabled)")
        return DummyMetrics()

    logger.info("Creating OTLP metrics exporter to Prometheus: %s", endpoint)
    try:
        return OtlpMetrics(endpoint)
    except Exception:
        logger.exception("Failed to initialize OTLP metrics exporter; falling back to DummyMetrics")
        return DummyMetrics()
