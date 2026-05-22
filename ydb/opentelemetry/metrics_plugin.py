"""OpenTelemetry metrics bridge for YDB."""

import threading
from typing import Any, Dict, Iterable, Optional, Union

from opentelemetry import metrics as otel_metrics
from opentelemetry.metrics import (
    CallbackOptions,
    Counter,
    Histogram,
    Meter,
    MeterProvider,
    ObservableUpDownCounter,
    Observation,
    UpDownCounter,
)

from ydb.opentelemetry.metrics import (
    CLIENT_OPERATION_DURATION,
    CLIENT_OPERATION_FAILED,
    QUERY_SESSION_COUNT,
    QUERY_SESSION_CREATE_TIME,
    QUERY_SESSION_MAX,
    QUERY_SESSION_MIN,
    QUERY_SESSION_PENDING_REQUESTS,
    QUERY_SESSION_TIMEOUTS,
    RETRY_ATTEMPTS,
    RETRY_DURATION,
    ATTEMPT_BUCKETS,
    DURATION_BUCKETS_SECONDS,
    RETRY_DURATION_BUCKETS_SECONDS,
    MetricRegistry as NoOpMetricRegistry,
    MetricsOperation,
    _reset_metrics_registry,
    _set_metrics_registry,
)

_MetricInstrument = Union[Counter, Histogram, ObservableUpDownCounter, UpDownCounter]

_meter: Optional[Meter] = None


class MetricsRegistry(NoOpMetricRegistry):
    """Process-wide OpenTelemetry metric instrument registry."""

    enabled = True

    def __init__(self, meter: Meter) -> None:
        self._query_session_count_values: Dict[Any, int] = {}
        self._query_session_max_values: Dict[Any, int] = {}
        self._observable_values_lock = threading.Lock()
        self._instruments: Dict[str, _MetricInstrument] = {
            CLIENT_OPERATION_DURATION: meter.create_histogram(
                CLIENT_OPERATION_DURATION,
                unit="s",
                description="Duration of YDB client operations.",
                explicit_bucket_boundaries_advisory=DURATION_BUCKETS_SECONDS,
            ),
            CLIENT_OPERATION_FAILED: meter.create_counter(
                CLIENT_OPERATION_FAILED,
                unit="{command}",
                description="Number of failed YDB client operations.",
            ),
            QUERY_SESSION_COUNT: meter.create_observable_up_down_counter(
                QUERY_SESSION_COUNT,
                callbacks=[self._observe_query_session_count],
                unit="{connection}",
                description="Number of open YDB query sessions.",
            ),
            QUERY_SESSION_CREATE_TIME: meter.create_histogram(
                QUERY_SESSION_CREATE_TIME,
                unit="s",
                description="Duration of YDB query session creation.",
                explicit_bucket_boundaries_advisory=DURATION_BUCKETS_SECONDS,
            ),
            QUERY_SESSION_PENDING_REQUESTS: meter.create_up_down_counter(
                QUERY_SESSION_PENDING_REQUESTS,
                unit="{request}",
                description="Number of requests waiting for a YDB query session.",
            ),
            QUERY_SESSION_TIMEOUTS: meter.create_counter(
                QUERY_SESSION_TIMEOUTS,
                unit="{connection}",
                description="Number of YDB query session acquisition timeouts.",
            ),
            QUERY_SESSION_MAX: meter.create_observable_up_down_counter(
                QUERY_SESSION_MAX,
                callbacks=[self._observe_query_session_max],
                unit="{connection}",
                description="Maximum configured number of YDB query sessions.",
            ),
            QUERY_SESSION_MIN: meter.create_observable_up_down_counter(
                QUERY_SESSION_MIN,
                callbacks=[self._observe_query_session_min],
                unit="{connection}",
                description="Minimum configured number of YDB query sessions.",
            ),
            RETRY_DURATION: meter.create_histogram(
                RETRY_DURATION,
                unit="s",
                description=(
                    "Total user-visible duration of a logical operation executed through the retry policy, "
                    "including all attempts and back-off delays."
                ),
                explicit_bucket_boundaries_advisory=RETRY_DURATION_BUCKETS_SECONDS,
            ),
            RETRY_ATTEMPTS: meter.create_histogram(
                RETRY_ATTEMPTS,
                unit="{attempt}",
                description=(
                    "Total number of attempts performed by the retry policy for one logical operation. "
                    "A value of 1 means the operation succeeded on the first try."
                ),
                explicit_bucket_boundaries_advisory=ATTEMPT_BUCKETS,
            ),
        }

    def create_metrics_operation(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> MetricsOperation:
        return MetricsOperation(name, attributes)

    def clear(self) -> None:
        self._instruments = {}
        with self._observable_values_lock:
            self._query_session_count_values = {}
            self._query_session_max_values = {}

    def add(self, name: str, value: int, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add ``value`` to a counter-like instrument if metrics are enabled."""
        instrument = self._instruments.get(name)
        if instrument is not None:
            instrument.add(value, attributes=attributes or {})

    def record(self, name: str, value: float, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Record ``value`` in a histogram-like instrument if metrics are enabled."""
        instrument = self._instruments.get(name)
        if instrument is not None:
            instrument.record(value, attributes=attributes or {})

    def add_query_session_count(self, value: int, attributes: Optional[Dict[str, Any]] = None) -> None:
        attrs = tuple(sorted((attributes or {}).items()))

        with self._observable_values_lock:
            new_value = self._query_session_count_values.get(attrs, 0) + value

            self._query_session_count_values.pop(attrs, None)
            self._query_session_count_values[attrs] = new_value

    def set_query_session_max(self, value: int, attributes: Optional[Dict[str, Any]] = None) -> None:
        attrs = tuple(sorted((attributes or {}).items()))

        with self._observable_values_lock:
            self._query_session_max_values[attrs] = value

    def remove_query_session_pool(self, attributes: Optional[Dict[str, Any]] = None) -> None:
        base_attrs = list((attributes or {}).items())
        attrs = tuple(sorted(base_attrs))
        idle_attrs = tuple(sorted(base_attrs + [("ydb.query.session.state", "idle")]))
        used_attrs = tuple(sorted(base_attrs + [("ydb.query.session.state", "used")]))

        with self._observable_values_lock:
            self._query_session_count_values.pop(idle_attrs, None)
            self._query_session_count_values.pop(used_attrs, None)
            self._query_session_max_values.pop(attrs, None)


    def _observe_query_session_count(self, _: CallbackOptions) -> Iterable[Observation]:
        return self._observe(self._query_session_count_values)

    def _observe_query_session_max(self, _: CallbackOptions) -> Iterable[Observation]:
        return self._observe(self._query_session_max_values)

    def _observe_query_session_min(self, _: CallbackOptions) -> Iterable[Observation]:
        with self._observable_values_lock:
            return [Observation(0, attributes=dict(attrs)) for attrs in self._query_session_max_values]

    def _observe(self, values: Dict[Any, int]) -> Iterable[Observation]:
        with self._observable_values_lock:
            return [Observation(value, attributes=dict(attrs)) for attrs, value in values.items()]


def _enable_metrics(meter_provider: Optional[MeterProvider]) -> None:
    """Create SDK metric instruments from an OTel MeterProvider and enable recording."""
    global _meter

    if _meter is not None:
        return

    if meter_provider is None:
        _meter = otel_metrics.get_meter("ydb.sdk")
    elif hasattr(meter_provider, "get_meter"):
        _meter = meter_provider.get_meter("ydb.sdk")
    else:
        raise TypeError("meter_provider must be an OpenTelemetry MeterProvider")

    registry = MetricsRegistry(_meter)
    _set_metrics_registry(registry)


def _disable_metrics() -> None:
    global _meter

    _reset_metrics_registry()
    _meter = None
