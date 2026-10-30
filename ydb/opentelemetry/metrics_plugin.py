"""OpenTelemetry metrics adapter for the YDB observability interface.

Implements :class:`ydb.observability.MetricsProvider` on top of the ``opentelemetry``
packages. The SDK core does not import it — the OTel dependency is only pulled in when a
user calls :func:`ydb.opentelemetry.enable_metrics`.
"""

from typing import Any, Dict, Optional

from opentelemetry import metrics as otel_metrics
from opentelemetry.metrics import (
    CallbackOptions,
    Histogram,
    Meter,
    MeterProvider,
    Observation,
)

from ydb.observability import enable_metrics as _observability_enable_metrics
from ydb.observability import disable_metrics as _observability_disable_metrics
from ydb.observability.metrics import (
    CLIENT_OPERATION_DURATION,
    CLIENT_OPERATION_FAILED,
    QUERY_SESSION_CLOSED,
    QUERY_SESSION_COUNT,
    QUERY_SESSION_CREATE_TIME,
    QUERY_SESSION_MAX,
    QUERY_SESSION_MIN,
    QUERY_SESSION_PENDING_REQUESTS,
    QUERY_SESSION_TIMEOUTS,
    RETRY_ATTEMPTS,
    RETRY_DURATION,
    TOPIC_READER_COMMIT_ACKNOWLEDGED,
    TOPIC_READER_COMMIT_OFFSET_LAG_MAX,
    TOPIC_READER_COMMIT_QUEUED,
    TOPIC_READER_COMPRESSION_DURATION,
    TOPIC_READER_CREDIT_BALANCE_BYTES,
    TOPIC_READER_DELIVERED_MESSAGES,
    TOPIC_READER_LOCAL_BUFFER_MESSAGE_AGE_MAX,
    TOPIC_READER_LOCAL_BUFFER_MESSAGES,
    TOPIC_READER_MESSAGE_PROCESSING_DURATION,
    TOPIC_READER_PARTITION_SESSION_COUNT,
    TOPIC_READER_RECEIVED_BYTES,
    TOPIC_READER_RECEIVED_MESSAGES,
    TOPIC_READER_SESSION_ERRORS,
    ATTEMPT_BUCKETS,
    DURATION_BUCKETS_SECONDS,
    GaugeCallback,
    RETRY_DURATION_BUCKETS_SECONDS,
    _get_metrics_provider,
)

_meter: Optional[Meter] = None
_otel_provider: Optional["OtelMetricsProvider"] = None

# Unit/description for the asynchronous gauges the SDK registers via observe_gauge.
_GAUGE_META = {
    QUERY_SESSION_COUNT: ("{connection}", "Number of open YDB query sessions."),
    QUERY_SESSION_MAX: ("{connection}", "Maximum configured number of YDB query sessions."),
    QUERY_SESSION_MIN: ("{connection}", "Minimum configured number of YDB query sessions."),
    TOPIC_READER_CREDIT_BALANCE_BYTES: (
        "By",
        "The protocol credit granted to the server and not yet consumed by read responses.",
    ),
    TOPIC_READER_COMMIT_OFFSET_LAG_MAX: (
        "{message}",
        "The maximum gap between requested and acknowledged commit offsets.",
    ),
    TOPIC_READER_LOCAL_BUFFER_MESSAGES: (
        "{message}",
        "The number of messages currently buffered by the reader.",
    ),
    TOPIC_READER_LOCAL_BUFFER_MESSAGE_AGE_MAX: (
        "s",
        "Age of the oldest message currently buffered by the reader.",
    ),
    TOPIC_READER_PARTITION_SESSION_COUNT: (
        "{session}",
        "The number of active partition sessions owned by the reader.",
    ),
}
_OBSERVABLE_GAUGE_INSTRUMENTS = frozenset(
    {
        TOPIC_READER_CREDIT_BALANCE_BYTES,
        TOPIC_READER_COMMIT_OFFSET_LAG_MAX,
        TOPIC_READER_LOCAL_BUFFER_MESSAGE_AGE_MAX,
    }
)


class OtelMetricsProvider:
    """OpenTelemetry-backed :class:`ydb.observability.MetricsProvider`.

    Push instruments (histograms, counters) are created eagerly with the SDK's
    units/buckets; asynchronous gauges are created lazily via :meth:`observe_gauge`.
    """

    def __init__(self, meter: Meter) -> None:
        self._meter = meter
        self._histograms: Dict[str, Histogram] = {
            CLIENT_OPERATION_DURATION: _create_histogram(
                meter,
                CLIENT_OPERATION_DURATION,
                unit="s",
                description="Duration of YDB client operations.",
                bucket_boundaries=DURATION_BUCKETS_SECONDS,
            ),
            QUERY_SESSION_CREATE_TIME: _create_histogram(
                meter,
                QUERY_SESSION_CREATE_TIME,
                unit="s",
                description="Duration of YDB query session creation.",
                bucket_boundaries=DURATION_BUCKETS_SECONDS,
            ),
            RETRY_DURATION: _create_histogram(
                meter,
                RETRY_DURATION,
                unit="s",
                description=(
                    "Total user-visible duration of a logical operation executed through the retry policy, "
                    "including all attempts and back-off delays."
                ),
                bucket_boundaries=RETRY_DURATION_BUCKETS_SECONDS,
            ),
            RETRY_ATTEMPTS: _create_histogram(
                meter,
                RETRY_ATTEMPTS,
                unit="{attempt}",
                description=(
                    "Total number of attempts performed by the retry policy for one logical operation. "
                    "A value of 1 means the operation succeeded on the first try."
                ),
                bucket_boundaries=ATTEMPT_BUCKETS,
            ),
            TOPIC_READER_COMPRESSION_DURATION: _create_histogram(
                meter,
                TOPIC_READER_COMPRESSION_DURATION,
                unit="s",
                description="The time spent decompressing a message, excluding queueing.",
                bucket_boundaries=DURATION_BUCKETS_SECONDS,
            ),
            TOPIC_READER_MESSAGE_PROCESSING_DURATION: _create_histogram(
                meter,
                TOPIC_READER_MESSAGE_PROCESSING_DURATION,
                unit="s",
                description="The time from receipt until a message is ready for delivery.",
                bucket_boundaries=DURATION_BUCKETS_SECONDS,
            ),
        }
        self._counters: Dict[str, Any] = {
            CLIENT_OPERATION_FAILED: meter.create_counter(
                CLIENT_OPERATION_FAILED,
                unit="{command}",
                description="Number of failed YDB client operations.",
            ),
            QUERY_SESSION_CLOSED: meter.create_counter(
                QUERY_SESSION_CLOSED,
                unit="{session}",
                description="Number of closed YDB query sessions.",
            ),
            QUERY_SESSION_TIMEOUTS: meter.create_counter(
                QUERY_SESSION_TIMEOUTS,
                unit="{connection}",
                description="Number of YDB query session acquisition timeouts.",
            ),
            QUERY_SESSION_PENDING_REQUESTS: meter.create_up_down_counter(
                QUERY_SESSION_PENDING_REQUESTS,
                unit="{request}",
                description="Number of requests waiting for a YDB query session.",
            ),
            TOPIC_READER_DELIVERED_MESSAGES: meter.create_counter(
                TOPIC_READER_DELIVERED_MESSAGES,
                unit="{message}",
                description="Number of messages delivered by the YDB topic reader to the application.",
            ),
            TOPIC_READER_COMMIT_QUEUED: meter.create_counter(
                TOPIC_READER_COMMIT_QUEUED,
                unit="{message}",
                description="The number of messages in commit ranges accepted by the SDK.",
            ),
            TOPIC_READER_COMMIT_ACKNOWLEDGED: meter.create_counter(
                TOPIC_READER_COMMIT_ACKNOWLEDGED,
                unit="{message}",
                description="The number of messages acknowledged by regular or transactional commits.",
            ),
            TOPIC_READER_RECEIVED_MESSAGES: meter.create_counter(
                TOPIC_READER_RECEIVED_MESSAGES,
                unit="{message}",
                description="The number of messages accepted by the SDK for an active partition session.",
            ),
            TOPIC_READER_RECEIVED_BYTES: meter.create_counter(
                TOPIC_READER_RECEIVED_BYTES,
                unit="By",
                description="The protocol bytes_size received in read responses.",
            ),
            TOPIC_READER_SESSION_ERRORS: meter.create_counter(
                TOPIC_READER_SESSION_ERRORS,
                unit="{error}",
                description="Number of YDB topic reader session errors.",
            ),
        }

    def record(self, name: str, value: float, attributes: Optional[Dict[str, Any]] = None) -> None:
        instrument = self._histograms.get(name)
        if instrument is not None:
            instrument.record(value, attributes=attributes or {})

    def add(self, name: str, value: int, attributes: Optional[Dict[str, Any]] = None) -> None:
        instrument = self._counters.get(name)
        if instrument is not None:
            instrument.add(value, attributes=attributes or {})

    def observe_gauge(self, name: str, callback: GaugeCallback) -> None:
        unit, description = _GAUGE_META.get(name, ("", ""))

        def _otel_callback(_: CallbackOptions):
            return [Observation(value, attributes=attrs) for value, attrs in callback()]

        create_instrument = (
            self._meter.create_observable_gauge
            if name in _OBSERVABLE_GAUGE_INSTRUMENTS
            else self._meter.create_observable_up_down_counter
        )
        create_instrument(
            name,
            callbacks=[_otel_callback],
            unit=unit,
            description=description,
        )


def _enable_metrics(meter_provider: Optional[MeterProvider]) -> None:
    """Build an :class:`OtelMetricsProvider` from an OTel MeterProvider and install it.

    Called by :func:`ydb.opentelemetry.enable_metrics`. Idempotent: if metrics are
    already enabled the call is a no-op (re-registering OpenTelemetry observable
    callbacks would double-count). Call :func:`ydb.opentelemetry.disable_metrics`
    first to reconfigure.
    """
    global _meter, _otel_provider

    if _otel_provider is not None and _get_metrics_provider() is _otel_provider:
        return

    if meter_provider is None:
        meter = otel_metrics.get_meter("ydb.sdk")
    elif hasattr(meter_provider, "get_meter"):
        meter = meter_provider.get_meter("ydb.sdk")
    else:
        raise TypeError("meter_provider must be an OpenTelemetry MeterProvider")

    provider = OtelMetricsProvider(meter)
    _observability_enable_metrics(provider)
    _meter = meter
    _otel_provider = provider


def _disable_metrics() -> None:
    global _meter, _otel_provider

    _observability_disable_metrics()
    _meter = None
    _otel_provider = None


def _create_histogram(
    meter: Meter,
    name: str,
    unit: str,
    description: str,
    bucket_boundaries,
) -> Histogram:
    """Create a histogram with bucket advice when the installed OpenTelemetry SDK supports it."""
    try:
        return meter.create_histogram(
            name,
            unit=unit,
            description=description,
            explicit_bucket_boundaries_advisory=bucket_boundaries,
        )
    except TypeError as e:
        if "explicit_bucket_boundaries_advisory" not in str(e):
            raise
        return meter.create_histogram(
            name,
            unit=unit,
            description=description,
        )
