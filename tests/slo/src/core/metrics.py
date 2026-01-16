from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Iterable
from contextlib import contextmanager
from importlib.metadata import version
from os import environ
from typing import Any, Dict, List, Optional, Tuple

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
    def stop(self, labels, start_time: float, attempts: int = 1, error: Exception = None) -> None:
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

    def stop(self, labels, start_time: float, attempts: int = 1, error: Exception = None) -> None:
        return None

    def reset(self) -> None:
        return None

    def push(self) -> None:
        return None


class _GaugeStore:
    """
    Minimal state store for ObservableGauge.

    OpenTelemetry Python implements "gauge" as an ObservableGauge (async instrument).
    We keep the latest value per label-set and expose it via a callback.
    """

    def __init__(self, labelnames: Tuple[str, ...]):
        self._labelnames = labelnames
        self._values: Dict[Tuple[Any, ...], float] = {}

    def _key(self, labelvalues: Tuple[Any, ...]) -> Tuple[Any, ...]:
        if len(labelvalues) != len(self._labelnames):
            raise ValueError(
                f"Expected {len(self._labelnames)} labels {self._labelnames}, got {len(labelvalues)}: {labelvalues}"
            )
        return labelvalues

    def set(self, labelvalues: Tuple[Any, ...], value: float) -> None:
        self._values[self._key(labelvalues)] = float(value)

    def inc(self, labelvalues: Tuple[Any, ...], amount: float = 1.0) -> None:
        k = self._key(labelvalues)
        self._values[k] = float(self._values.get(k, 0.0) + amount)

    def dec(self, labelvalues: Tuple[Any, ...], amount: float = 1.0) -> None:
        k = self._key(labelvalues)
        self._values[k] = float(self._values.get(k, 0.0) - amount)

    def clear(self) -> None:
        self._values.clear()

    def observations(self, Observation) -> List[Any]:
        # Observation type is imported lazily from opentelemetry.metrics
        out = []
        for labelvalues, value in self._values.items():
            attrs = dict(zip(self._labelnames, labelvalues))
            out.append(Observation(value, attributes=attrs))
        return out


class OtlpMetrics(BaseMetrics):
    """
    Canonical OpenTelemetry metrics implementation.

    This exports metrics via OTLP/HTTP to a Prometheus server with OTLP receiver enabled:
      POST http(s)://<host>:<port>/api/v1/otlp/v1/metrics

    Naming notes (to preserve existing Prometheus series names as much as possible):
    - Counters are created WITHOUT `_total` suffix. Prometheus OTLP translation adds `_total`.
    - Histogram is created WITHOUT `_seconds` suffix but with unit="s". Prometheus translation
      typically results in `*_seconds_*` series (depending on Prometheus translation settings).
    """

    def __init__(self, otlp_metrics_endpoint: str):
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.metrics import Observation
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource

        self._Observation = Observation

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
            name="sdk_errors",
            description="Total number of errors encountered, categorized by error type.",
        )
        self._operations_total = self._meter.create_counter(
            name="sdk_operations",
            description="Total number of operations, categorized by type attempted by the SDK.",
        )
        self._operations_success_total = self._meter.create_counter(
            name="sdk_operations_success",
            description="Total number of successful operations, categorized by type.",
        )
        self._operations_failure_total = self._meter.create_counter(
            name="sdk_operations_failure",
            description="Total number of failed operations, categorized by type.",
        )
        self._latency = self._meter.create_histogram(
            name="sdk_operation_latency",
            unit="s",
            description="Latency of operations performed by the SDK in seconds, categorized by type and status.",
        )

        # Pending operations: sync UpDownCounter (canonical for "in flight" style metrics).
        self._pending = self._meter.create_up_down_counter(
            name="sdk_pending_operations",
            description="Current number of pending operations, categorized by type.",
        )

        # Retry attempts: ObservableGauge (we keep last value per label set and expose it via callback).
        self._retry_attempts_store = _GaugeStore(labelnames=("operation_type",))

        def retry_attempts_cb(options=None):
            return self._retry_attempts_store.observations(self._Observation)

        self._meter.create_observable_gauge(
            name="sdk_retry_attempts",
            description="Current retry attempts, categorized by operation type.",
            callbacks=[retry_attempts_cb],
        )

        self.reset()

    def start(self, labels) -> float:
        labels_t = _normalize_labels(labels)
        self._pending.add(1, attributes={"operation_type": labels_t[0]})
        return time.time()

    def stop(self, labels, start_time: float, attempts: int = 1, error: Exception = None) -> None:
        labels_t = _normalize_labels(labels)
        duration = time.time() - start_time

        # Update instruments
        self._retry_attempts_store.set(labels_t, float(attempts))
        self._pending.add(-1, attributes={"operation_type": labels_t[0]})

        # Counters + latency
        self._operations_total.add(1, attributes={"operation_type": labels_t[0]})

        if error is not None:
            self._errors.add(
                1,
                attributes={
                    "operation_type": labels_t[0],
                    "error_type": type(error).__name__,
                },
            )
            self._operations_failure_total.add(1, attributes={"operation_type": labels_t[0]})
            self._latency.record(
                duration,
                attributes={
                    "operation_type": labels_t[0],
                    "operation_status": OP_STATUS_FAILURE,
                },
            )
            return

        self._operations_success_total.add(1, attributes={"operation_type": labels_t[0]})
        self._latency.record(
            duration,
            attributes={
                "operation_type": labels_t[0],
                "operation_status": OP_STATUS_SUCCESS,
            },
        )

    def push(self) -> None:
        # Metrics job calls push() with the cadence of --report-period.
        # force_flush() makes the exporter send immediately.
        self._provider.force_flush()

    def reset(self) -> None:
        # OpenTelemetry counters/histograms are cumulative and cannot be reset.
        # Reset only affects the ObservableGauge-backed state.
        self._retry_attempts_store.clear()
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
