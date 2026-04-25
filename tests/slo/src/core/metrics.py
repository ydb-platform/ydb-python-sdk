from __future__ import annotations

import logging
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Iterable
from contextlib import contextmanager
from importlib.metadata import version
from os import environ
from typing import Any, Optional, Tuple

OP_TYPE_READ, OP_TYPE_WRITE = "read", "write"
OP_STATUS_SUCCESS, OP_STATUS_FAILURE = "success", "err"

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
    OpenTelemetry metrics implementation.

    Exports via OTLP/HTTP; the endpoint is configured through standard OTel env vars:
      OTEL_EXPORTER_OTLP_METRICS_ENDPOINT  (e.g. http://ydb-prometheus:9090/api/v1/otlp/v1/metrics)
      OTEL_EXPORTER_OTLP_ENDPOINT          (fallback base URL)
      OTEL_EXPORTER_OTLP_PROTOCOL          (default: http/protobuf)

    Latency is tracked with an HDR histogram per (operation_type, operation_status) label
    combination and published as three Gauge instruments:
      sdk_operation_latency_p50_seconds
      sdk_operation_latency_p95_seconds
      sdk_operation_latency_p99_seconds
    """

    # HDR histogram range: 1 µs … 60 s (in microseconds), 3 significant figures.
    _HDR_MIN_US = 1
    _HDR_MAX_US = 60_000_000
    _HDR_SIG_FIGS = 3

    def __init__(self, workload_name: str, workload_ref: str):
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource

        self._workload_name = workload_name
        self._workload_ref = workload_ref

        resource = Resource.create(
            {
                "service.name": f"workload-{workload_name}",
                "service.instance.id": environ.get("SLO_INSTANCE_ID", f"{workload_ref}-{workload_name}"),
                "ref": workload_ref,
                "sdk": "ydb-python-sdk",
                "sdk_version": version("ydb"),
                "workload": workload_name,
                "workload_version": "0.0.0",
            }
        )

        # Endpoint is read automatically from OTEL_EXPORTER_OTLP_METRICS_ENDPOINT /
        # OTEL_EXPORTER_OTLP_ENDPOINT by the exporter; no need to pass it explicitly.
        exporter = OTLPMetricExporter()
        reader = PeriodicExportingMetricReader(exporter)

        self._provider = MeterProvider(resource=resource, metric_readers=[reader])
        self._meter = self._provider.get_meter("ydb-slo")

        # Counters — names/labels match metrics.yaml in ydb-slo-action
        self._errors = self._meter.create_counter(
            name="sdk.errors.total",
            description="Total number of errors encountered, categorized by error type.",
        )
        self._operations_total = self._meter.create_counter(
            name="sdk.operations.total",
            description="Total number of operations, labeled by operation_status (success/err).",
        )
        self._retry_attempts_total = self._meter.create_counter(
            name="sdk.retry.attempts.total",
            description="Total number of retry attempts.",
        )
        self._pending = self._meter.create_up_down_counter(
            name="sdk.pending.operations",
            description="Current number of pending operations.",
        )

        # Latency gauges (fed from HDR histograms via push())
        self._latency_p50 = self._meter.create_gauge(
            name="sdk_operation_latency_p50_seconds",
            unit="s",
            description="P50 operation latency in seconds.",
        )
        self._latency_p95 = self._meter.create_gauge(
            name="sdk_operation_latency_p95_seconds",
            unit="s",
            description="P95 operation latency in seconds.",
        )
        self._latency_p99 = self._meter.create_gauge(
            name="sdk_operation_latency_p99_seconds",
            unit="s",
            description="P99 operation latency in seconds.",
        )

        # HDR histograms: key → (operation_type, operation_status)
        self._hdr_lock = threading.Lock()
        self._hdr: dict = {}

        self.reset()

    def _hdr_for(self, key: tuple):
        """Return (creating if necessary) an HDR histogram for the given label key."""
        from hdrh.histogram import HdrHistogram

        hist = self._hdr.get(key)
        if hist is None:
            hist = HdrHistogram(self._HDR_MIN_US, self._HDR_MAX_US, self._HDR_SIG_FIGS)
            self._hdr[key] = hist
        return hist

    def start(self, labels) -> float:
        labels_t = _normalize_labels(labels)
        self._pending.add(
            1,
            attributes={"ref": self._workload_ref, "operation_type": labels_t[0]},
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
        duration_us = max(self._HDR_MIN_US, int(duration * 1_000_000))

        op_type = labels_t[0]
        op_status = OP_STATUS_SUCCESS if error is None else OP_STATUS_FAILURE
        base_attrs = {"ref": self._workload_ref, "operation_type": op_type}

        self._retry_attempts_total.add(int(attempts), attributes=base_attrs)
        self._pending.add(-1, attributes=base_attrs)
        self._operations_total.add(1, attributes={**base_attrs, "operation_status": op_status})

        if error is not None:
            self._errors.add(
                1,
                attributes={**base_attrs, "error_type": type(error).__name__},
            )

        with self._hdr_lock:
            self._hdr_for((op_type, op_status)).record_value(duration_us)

    def push(self) -> None:
        values = []
        with self._hdr_lock:
            for (op_type, op_status), hist in self._hdr.items():
                values.append(
                    (
                        op_type,
                        op_status,
                        hist.get_value_at_percentile(50.0) / 1_000_000,
                        hist.get_value_at_percentile(95.0) / 1_000_000,
                        hist.get_value_at_percentile(99.0) / 1_000_000,
                    )
                )
                hist.reset()

        for op_type, op_status, p50, p95, p99 in values:
            attrs = {
                "ref": self._workload_ref,
                "operation_type": op_type,
                "operation_status": op_status,
            }
            self._latency_p50.set(p50, attributes=attrs)
            self._latency_p95.set(p95, attributes=attrs)
            self._latency_p99.set(p99, attributes=attrs)

        self._provider.force_flush()

    def reset(self) -> None:
        self.push()


def create_metrics(args) -> BaseMetrics:
    """
    Factory used by SLO runners.

    Uses args.otlp_endpoint, args.workload_name, args.workload_ref from parsed CLI arguments.
    If the endpoint is empty, returns a no-op DummyMetrics.
    """
    endpoint = (args.otlp_endpoint or "").strip()

    if not endpoint:
        logger.info("OTLP endpoint not configured — metrics disabled")
        return DummyMetrics()

    environ.setdefault("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf")
    environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = endpoint

    logger.info("Creating OTLP metrics exporter (endpoint: %s)", endpoint)
    try:
        return OtlpMetrics(args.workload_name, args.workload_ref)
    except Exception:
        logger.exception("Failed to initialize OTLP metrics — falling back to DummyMetrics")
        return DummyMetrics()
