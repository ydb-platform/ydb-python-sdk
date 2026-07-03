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
OP_STATUS_SUCCESS, OP_STATUS_FAILURE = "success", "error"

REF = environ.get("WORKLOAD_REF") or environ.get("REF") or "main"
WORKLOAD = environ.get("WORKLOAD_NAME") or environ.get("WORKLOAD") or "sync-query"

logger = logging.getLogger(__name__)


def _normalize_labels(labels: Any) -> Tuple[Any, ...]:
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

    # --- Topic workload extensions (no-ops unless overridden) ---
    def record_e2e(self, seconds: float) -> None:
        """Record an end-to-end (write -> read) message latency, in seconds."""
        return None

    def inc_delivered(self, n: int = 1) -> None:
        """Count messages successfully read back."""
        return None

    def inc_lost(self, n: int = 1) -> None:
        """Count messages detected as lost (a forward gap in a producer's seqno)."""
        return None

    def inc_duplicated(self, n: int = 1) -> None:
        """Count messages detected as duplicates (redelivery of an already-seen seqno)."""
        return None

    def inc_tli(self, n: int = 1) -> None:
        """Count transaction-locks-invalidated (TLI) aborts absorbed by the tx retry loop."""
        return None


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
    Exports metrics via OTLP/HTTP to a Prometheus endpoint with OTLP receiver enabled.

    Latency percentiles (p50/p95/p99) are computed client-side per push window via
    HdrHistogram and emitted as gauges; counters are emitted via OTel counters.
    Histogram is reset after each push so each sample represents the last window only.
    """

    _HDR_MIN_US = 1
    _HDR_MAX_US = 60_000_000  # 60s
    _HDR_SIG_FIGS = 3
    _PERCENTILES = (("p50", 50.0), ("p95", 95.0), ("p99", 99.0))

    def __init__(self, otlp_metrics_endpoint: str):
        from hdrh.histogram import HdrHistogram
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource

        self._HdrHistogram = HdrHistogram

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
        reader = PeriodicExportingMetricReader(exporter)
        self._provider = MeterProvider(resource=resource, metric_readers=[reader])
        self._meter = self._provider.get_meter("ydb-slo")

        self._errors = self._meter.create_counter(
            name="sdk.errors.total",
            description="Total number of errors encountered, categorized by error type.",
        )
        self._operations_total = self._meter.create_counter(
            name="sdk.operations.total",
            description="Total number of operations attempted by the SDK.",
        )
        self._operations_success_total = self._meter.create_counter(
            name="sdk.operations.success.total",
            description="Total number of successful operations.",
        )
        self._operations_failure_total = self._meter.create_counter(
            name="sdk.operations.failure.total",
            description="Total number of failed operations.",
        )
        self._retry_attempts_total = self._meter.create_counter(
            name="sdk.retry.attempts.total",
            description="Total number of retry attempts.",
        )
        self._pending = self._meter.create_up_down_counter(
            name="sdk.pending.operations",
            description="Current number of pending operations.",
        )
        self._latency_gauges = {
            name: self._meter.create_gauge(
                name=f"sdk.operation.latency.{name}.seconds",
                unit="s",
                description=f"Operation latency {name} computed over the last push window.",
            )
            for name, _ in self._PERCENTILES
        }

        # Topic-workload metrics: end-to-end (write -> read) latency + delivery counters.
        self._topic_e2e_gauges = {
            name: self._meter.create_gauge(
                name=f"sdk.topic.e2e.latency.{name}.seconds",
                unit="s",
                description=f"Topic end-to-end latency {name} computed over the last push window.",
            )
            for name, _ in self._PERCENTILES
        }
        self._topic_delivered = self._meter.create_counter(
            name="sdk.topic.messages.delivered.total",
            description="Total number of messages successfully read back from the topic.",
        )
        self._topic_lost = self._meter.create_counter(
            name="sdk.topic.messages.lost.total",
            description="Total number of messages detected as lost (forward gap in a producer's seqno).",
        )
        self._topic_duplicated = self._meter.create_counter(
            name="sdk.topic.messages.duplicated.total",
            description="Total number of messages detected as duplicates (redelivered seqno).",
        )
        self._topic_tx_tli = self._meter.create_counter(
            name="sdk.topic.tx.tli.total",
            description="Total number of TLI (transaction locks invalidated) aborts absorbed by the tx retry loop.",
        )

        self._lock = threading.Lock()
        self._hdr: dict = {}
        self._e2e_hdr = self._HdrHistogram(self._HDR_MIN_US, self._HDR_MAX_US, self._HDR_SIG_FIGS)

    def _get_hdr(self, op_type: str, op_status: str):
        key = (op_type, op_status)
        hist = self._hdr.get(key)
        if hist is None:
            hist = self._HdrHistogram(self._HDR_MIN_US, self._HDR_MAX_US, self._HDR_SIG_FIGS)
            self._hdr[key] = hist
        return hist

    def start(self, labels) -> float:
        labels_t = _normalize_labels(labels)
        self._pending.add(
            1,
            attributes={"ref": REF, "operation_type": labels_t[0]},
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
        duration_us = min(max(int(duration * 1_000_000), self._HDR_MIN_US), self._HDR_MAX_US)

        op_type = labels_t[0]
        op_status = OP_STATUS_SUCCESS if error is None else OP_STATUS_FAILURE
        base_attrs = {"ref": REF, "operation_type": op_type}
        op_attrs = {**base_attrs, "operation_status": op_status}

        self._retry_attempts_total.add(int(attempts), attributes=base_attrs)
        self._pending.add(-1, attributes=base_attrs)
        self._operations_total.add(1, attributes=op_attrs)

        if error is not None:
            self._errors.add(1, attributes={**base_attrs, "error_type": type(error).__name__})
            self._operations_failure_total.add(1, attributes=base_attrs)
        else:
            self._operations_success_total.add(1, attributes=base_attrs)

        with self._lock:
            self._get_hdr(op_type, op_status).record_value(duration_us)

    def push(self) -> None:
        with self._lock:
            for (op_type, op_status), hist in self._hdr.items():
                if hist.get_total_count() == 0:
                    continue
                attrs = {"ref": REF, "operation_type": op_type, "operation_status": op_status}
                for name, percentile in self._PERCENTILES:
                    value_s = hist.get_value_at_percentile(percentile) / 1_000_000
                    self._latency_gauges[name].set(value_s, attributes=attrs)
            for hist in self._hdr.values():
                hist.reset()

            if self._e2e_hdr.get_total_count() > 0:
                attrs = {"ref": REF}
                for name, percentile in self._PERCENTILES:
                    value_s = self._e2e_hdr.get_value_at_percentile(percentile) / 1_000_000
                    self._topic_e2e_gauges[name].set(value_s, attributes=attrs)
                self._e2e_hdr.reset()
        self._provider.force_flush()

    def reset(self) -> None:
        with self._lock:
            for hist in self._hdr.values():
                hist.reset()
            self._e2e_hdr.reset()
        self._provider.force_flush()

    def record_e2e(self, seconds: float) -> None:
        duration_us = min(max(int(seconds * 1_000_000), self._HDR_MIN_US), self._HDR_MAX_US)
        with self._lock:
            self._e2e_hdr.record_value(duration_us)

    def inc_delivered(self, n: int = 1) -> None:
        self._topic_delivered.add(int(n), attributes={"ref": REF})

    def inc_lost(self, n: int = 1) -> None:
        self._topic_lost.add(int(n), attributes={"ref": REF})

    def inc_duplicated(self, n: int = 1) -> None:
        self._topic_duplicated.add(int(n), attributes={"ref": REF})

    def inc_tli(self, n: int = 1) -> None:
        self._topic_tx_tli.add(int(n), attributes={"ref": REF})


def _resolve_metrics_endpoint(cli_endpoint: Optional[str]) -> str:
    """
    Resolution order:
      1. OTEL_EXPORTER_OTLP_METRICS_ENDPOINT (used as-is)
      2. OTEL_EXPORTER_OTLP_ENDPOINT + /v1/metrics suffix
      3. CLI --otlp-endpoint
    """
    metrics_env = environ.get("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", "").strip()
    if metrics_env:
        return metrics_env

    base_env = environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if base_env:
        base = base_env.rstrip("/")
        if base.endswith("/v1/metrics"):
            return base
        return f"{base}/v1/metrics"

    return (cli_endpoint or "").strip()


def create_metrics(otlp_endpoint: Optional[str]) -> BaseMetrics:
    """
    Build a metrics exporter.

    Metrics are enabled if a non-empty endpoint can be derived from either the
    OTEL_EXPORTER_OTLP_METRICS_ENDPOINT / OTEL_EXPORTER_OTLP_ENDPOINT env vars
    or the explicit `--otlp-endpoint` CLI flag. Otherwise DummyMetrics is used.
    """
    endpoint = _resolve_metrics_endpoint(otlp_endpoint)
    if not endpoint:
        logger.info("Creating dummy metrics (metrics disabled)")
        return DummyMetrics()

    logger.info("Creating OTLP metrics exporter to: %s", endpoint)
    try:
        return OtlpMetrics(endpoint)
    except Exception:
        logger.exception("Failed to initialize OTLP metrics exporter; falling back to DummyMetrics")
        return DummyMetrics()
