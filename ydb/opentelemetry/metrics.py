"""No-op-safe helpers for YDB OpenTelemetry metrics."""

import time
from typing import Any, Dict, Optional

CLIENT_OPERATION_DURATION = "db.client.operation.duration"
CLIENT_OPERATION_FAILED = "ydb.client.operation.failed"
QUERY_SESSION_COUNT = "ydb.query.session.count"
QUERY_SESSION_CREATE_TIME = "ydb.query.session.create_time"
QUERY_SESSION_PENDING_REQUESTS = "ydb.query.session.pending_requests"
QUERY_SESSION_TIMEOUTS = "ydb.query.session.timeouts"

_UNKNOWN_POOL = "unknown"


import threading


class MetricsRegistry:
    def __init__(self) -> None:
        self._instruments: Dict[str, Any] = {}
        self._query_session_count_values: Dict[Any, int] = {}
        self._query_session_count_lock = threading.Lock()

    def set_meter(self, meter: Any, observe_query_session_count_callback: Any) -> None:
        self._instruments = {
            CLIENT_OPERATION_DURATION: meter.create_histogram(
                CLIENT_OPERATION_DURATION,
                unit="s",
                description="Duration of YDB client operations.",
            ),
            CLIENT_OPERATION_FAILED: meter.create_counter(
                CLIENT_OPERATION_FAILED,
                unit="{command}",
                description="Number of failed YDB client operations.",
            ),
            QUERY_SESSION_COUNT: meter.create_observable_up_down_counter(
                QUERY_SESSION_COUNT,
                callbacks=[observe_query_session_count_callback],
                unit="{connection}",
                description="Number of open YDB query sessions.",
            ),
            QUERY_SESSION_CREATE_TIME: meter.create_histogram(
                QUERY_SESSION_CREATE_TIME,
                unit="s",
                description="Duration of YDB query session creation.",
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
        }

    def clear(self) -> None:
        self._instruments = {}
        with self._query_session_count_lock:
            self._query_session_count_values = {}

    def add(self, name: str, value: int, attributes: Optional[Dict[str, Any]] = None) -> None:
        """
        Record a metric value, accumulating for observable metrics or adding directly for others.

        For observable metrics, values are accumulated by attributes and sent via callback.
        For regular metrics, values are added immediately to the instrument.

        Args:
            name: Name of the metric.
            value: Value to add (positive or negative).
            attributes: Optional dictionary of metric attributes (labels).
        """
        instrument = self._instruments.get(name)
        if instrument is not None:
            instrument.add(value, attributes=attributes or {})

    def record(self, name: str, value: float, attributes: Optional[Dict[str, Any]] = None) -> None:
        """
        Record a histogram or gauge metric value.

        Args:
            name: Name of the metric.
            value: Value to record.
            attributes: Optional dictionary of metric attributes (labels).
        """
        instrument = self._instruments.get(name)
        if instrument is not None:
            instrument.record(value, attributes=attributes or {})

    def add_query_session_count(self, value: int, attributes: Optional[Dict[str, Any]] = None) -> None:
        attrs = tuple(sorted((attributes or {}).items()))

        with self._query_session_count_lock:
            new_value = self._query_session_count_values.get(attrs, 0) + value

            self._query_session_count_values.pop(attrs, None)
            self._query_session_count_values[attrs] = new_value

    def get_query_session_count_values(self) -> Dict[Any, int]:
        with self._query_session_count_lock:
            return dict(self._query_session_count_values)


_metrics_registry = MetricsRegistry()


def _pool_attrs(pool_name: Optional[str]) -> Dict[str, Any]:
    return {"ydb.query.session.pool.name": pool_name or _UNKNOWN_POOL}


def _operation_attrs(operation_name: str, attributes: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "db.system.name": attributes.get("db.system.name", "ydb"),
        "db.namespace": attributes.get("db.namespace", ""),
        "server.address": attributes.get("server.address", ""),
        "server.port": attributes.get("server.port", 0),
        "ydb.operation.name": operation_name,
    }


def _response_status_code(exception: BaseException) -> str:
    status = getattr(exception, "status", None)
    if status is not None:
        return getattr(status, "name", str(status))
    return type(exception).__qualname__


class MetricsOperation:
    """
    Context manager for tracking metrics of a single YDB operation.

    Records operation duration and captures errors. When the operation ends,
    metrics are recorded to the registry with operation attributes.

    Attributes:
        _name: Name of the operation.
        _attributes: Dictionary of attributes attached to all metrics from this operation.
        _start_time: Timestamp when the operation started (using monotonic).
        _exception: Optional exception that occurred during operation execution.
        _ended: Flag to ensure metrics are recorded only once.
    """

    def __init__(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize a metrics operation.

        Args:
            name: Name of the operation (e.g., 'ExecuteQuery', 'CreateSession').
            attributes: Optional dictionary of initial attributes for the operation.
        """
        self._name = name
        self._attributes = _operation_attrs(name, attributes or {})
        self._start_time = time.monotonic()
        self._exception: Optional[BaseException] = None
        self._ended = False

    def set_error(self, exception: BaseException) -> None:
        """
        Record an exception that occurred during the operation.

        Args:
            exception: The exception to record.
        """
        self._exception = exception

    def set_attribute(self, key: str, value: Any) -> None:
        self._attributes[key] = value

    def attach_context(self) -> "MetricsOperation":
        return self

    def end(self) -> None:
        # todo: consider multi-thread calling

        if self._ended:
            return
        self._ended = True

        duration = time.monotonic() - self._start_time
        _metrics_registry.record(CLIENT_OPERATION_DURATION, duration, self._attributes)

        if self._exception is not None:
            attrs = dict(self._attributes)
            attrs["db.response.status_code"] = _response_status_code(self._exception)
            _metrics_registry.add(CLIENT_OPERATION_FAILED, 1, attrs)

    def __enter__(self) -> "MetricsOperation":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_val is not None:
            self.set_error(exc_val)
        self.end()
        return False


def create_metrics_operation(name: str, attributes: Optional[Dict[str, Any]] = None) -> MetricsOperation:
    return MetricsOperation(name, attributes)


def record_query_session_count(delta: int, pool_name: Optional[str] = None, state: str = "used") -> None:
    attrs = _pool_attrs(pool_name)
    attrs["ydb.query.session.state"] = state
    _metrics_registry.add_query_session_count(delta, attrs)


def record_query_session_create_time(duration: float, pool_name: Optional[str]) -> None:
    _metrics_registry.record(QUERY_SESSION_CREATE_TIME, duration, _pool_attrs(pool_name))


def record_query_session_pending_requests(delta: int, pool_name: Optional[str]) -> None:
    _metrics_registry.add(QUERY_SESSION_PENDING_REQUESTS, delta, _pool_attrs(pool_name))


def record_query_session_timeout(pool_name: Optional[str]) -> None:
    _metrics_registry.add(QUERY_SESSION_TIMEOUTS, 1, _pool_attrs(pool_name))
