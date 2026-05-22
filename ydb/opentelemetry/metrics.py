"""No-op-safe helpers for YDB OpenTelemetry client metrics.

The SDK records metrics only after :func:`ydb.opentelemetry.enable_metrics`
installs the OpenTelemetry-backed registry from ``metrics_plugin``. Until then
every helper delegates to a no-op registry, which keeps metrics independent from
tracing and safe to call from hot paths.
"""

import time
import threading
import itertools
from typing import Any, Dict, Optional

from ydb.opentelemetry._endpoint import split_endpoint

CLIENT_OPERATION_DURATION = "db.client.operation.duration"
CLIENT_OPERATION_FAILED = "ydb.client.operation.failed"
QUERY_SESSION_COUNT = "ydb.query.session.count"
QUERY_SESSION_CREATE_TIME = "ydb.query.session.create_time"
QUERY_SESSION_PENDING_REQUESTS = "ydb.query.session.pending_requests"
QUERY_SESSION_TIMEOUTS = "ydb.query.session.timeouts"
QUERY_SESSION_MAX = "ydb.query.session.max"
QUERY_SESSION_MIN = "ydb.query.session.min"
RETRY_ATTEMPTS = "ydb.client.retry.attempts"
RETRY_DURATION = "ydb.client.retry.duration"

DURATION_BUCKETS_SECONDS = (
    0.001,
    0.005,
    0.01,
    0.05,
    0.1,
    0.5,
    1,
    5,
    10,
)
RETRY_DURATION_BUCKETS_SECONDS = (
    0.001,
    0.005,
    0.01,
    0.05,
    0.1,
    0.5,
    1,
    2,
    5,
    10,
    30,
)
ATTEMPT_BUCKETS = (1, 2, 3, 4, 5, 7, 10, 20)
_UNKNOWN_POOL = "unknown"
_pool_name_counter = itertools.count(1)
_pool_name_lock = threading.Lock()
_OPERATION_ATTR_KEYS = frozenset(
    {
        "database",
        "endpoint",
        "operation.name",
    }
)
_CLIENT_OPERATION_NAMES = frozenset(
    {
        "ExecuteQuery",
        "Commit",
        "Rollback",
        "CreateSession",
        "BeginTransaction",
    }
)
_CLIENT_OPERATION_NAME_BY_INPUT = {
    "ydb.ExecuteQuery": "ExecuteQuery",
    "ExecuteQuery": "ExecuteQuery",
    "ydb.Commit": "Commit",
    "Commit": "Commit",
    "ydb.Rollback": "Rollback",
    "Rollback": "Rollback",
    "ydb.CreateSession": "CreateSession",
    "CreateSession": "CreateSession",
    "ydb.BeginTransaction": "BeginTransaction",
    "BeginTransaction": "BeginTransaction",
}


class MetricRegistry:
    """No-op metric registry used until the OpenTelemetry metrics plugin is enabled."""

    enabled = False

    def create_metrics_operation(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        return _NOOP_METRICS_OPERATION

    def clear(self) -> None:
        pass

    def add(self, name: str, value: int, attributes: Optional[Dict[str, Any]] = None) -> None:
        pass

    def record(self, name: str, value: float, attributes: Optional[Dict[str, Any]] = None) -> None:
        pass

    def add_query_session_count(self, value: int, attributes: Optional[Dict[str, Any]] = None) -> None:
        pass

    def set_query_session_max(self, value: int, attributes: Optional[Dict[str, Any]] = None) -> None:
        pass

    def remove_query_session_pool(self, attributes: Optional[Dict[str, Any]] = None) -> None:
        pass


class _NoopMetricsOperation:
    def set_error(self, exception: BaseException) -> None:
        pass

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def attach_context(self, end_on_exit=True) -> "_NoopMetricsOperationContext":
        return _NoopMetricsOperationContext(self)

    def end(self) -> None:
        pass

    def __enter__(self) -> "_NoopMetricsOperation":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class _NoopMetricsOperationContext:
    def __init__(self, operation: _NoopMetricsOperation) -> None:
        self._operation = operation

    def __enter__(self) -> _NoopMetricsOperation:
        return self._operation

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


_NOOP_METRICS_OPERATION = _NoopMetricsOperation()
_NOOP_METRICS_REGISTRY = MetricRegistry()
_metrics_registry: MetricRegistry = _NOOP_METRICS_REGISTRY


def is_metrics_enabled() -> bool:
    return _metrics_registry.enabled


def next_query_session_pool_name() -> str:
    """Return a process-unique default query session pool name for metric labels."""
    return "query-session-pool-%d" % next(_pool_name_counter)


def query_session_pool_name(name: Optional[str], endpoint: Optional[str]) -> str:
    return name or endpoint or next_query_session_pool_name()


def _set_metrics_registry(metrics_registry: MetricRegistry) -> None:
    global _metrics_registry

    _metrics_registry = metrics_registry


def _reset_metrics_registry() -> None:
    global _metrics_registry

    _metrics_registry.clear()
    _metrics_registry = _NOOP_METRICS_REGISTRY


def _pool_attrs(pool_name: Optional[str]) -> Dict[str, Any]:
    return {"ydb.query.session.pool.name": pool_name or _UNKNOWN_POOL}


def _build_ydb_metrics_attrs(driver_config) -> Dict[str, Any]:
    host, port = split_endpoint(getattr(driver_config, "endpoint", None))
    endpoint = "%s:%d" % (host, port) if port else host
    return {
        "database": getattr(driver_config, "database", None) or "",
        "endpoint": endpoint,
    }


def _operation_name(operation_name: str) -> str:
    return _CLIENT_OPERATION_NAME_BY_INPUT.get(operation_name, operation_name)


def _operation_attrs(operation_name: str, attributes: Dict[str, Any]) -> Dict[str, Any]:
    name = _operation_name(operation_name)
    return {
        "database": attributes.get("database", ""),
        "endpoint": attributes.get("endpoint", ""),
        "operation.name": name,
    }


def _response_status_code(exception: BaseException) -> str:
    status = getattr(exception, "status", None)
    if status is not None:
        return getattr(status, "name", str(status))
    return type(exception).__qualname__


class MetricsOperation:
    """Metric lifecycle object for one user-visible YDB client operation.

    ``MetricsOperation`` mirrors the small span-like interface used by tracing
    so both can be composed by ``create_ydb_span``. It records operation
    duration once, records a failed-operation counter when an exception is
    attached, and accepts only stable operation labels.
    """

    def __init__(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        self._name = name
        self._attributes = _operation_attrs(name, attributes or {})
        self._start_time = time.monotonic()
        self._exception: Optional[BaseException] = None
        self._ended = False
        self._end_lock = threading.Lock()

    def set_error(self, exception: BaseException) -> None:
        """Remember the operation exception for the failed-operation metric."""
        self._exception = exception

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a metric label only when it is part of the operation metric contract."""
        if key in _OPERATION_ATTR_KEYS:
            self._attributes[key] = value

    def attach_context(self, end_on_exit=True) -> "_MetricsOperationContext":
        return _MetricsOperationContext(self, end_on_exit)

    def end(self) -> None:
        with self._end_lock:
            if self._ended:
                return
            self._ended = True

        duration = time.monotonic() - self._start_time
        _metrics_registry.record(CLIENT_OPERATION_DURATION, duration, self._attributes)

        if self._exception is not None:
            attrs = dict(self._attributes)
            attrs["status_code"] = _response_status_code(self._exception)
            _metrics_registry.add(CLIENT_OPERATION_FAILED, 1, attrs)

    def __enter__(self) -> "MetricsOperation":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            self.set_error(exc_val)
        self.end()
        return False


class _MetricsOperationContext:
    """Context manager that optionally leaves ``end()`` to a streaming result iterator."""

    def __init__(self, operation: MetricsOperation, end_on_exit: bool) -> None:
        self._operation = operation
        self._end_on_exit = end_on_exit

    def __enter__(self) -> MetricsOperation:
        return self._operation

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            self._operation.set_error(exc_val)
            self._operation.end()
        elif self._end_on_exit:
            self._operation.end()
        return False


def create_metrics_operation(name: str, attributes: Optional[Dict[str, Any]] = None):
    if _operation_name(name) not in _CLIENT_OPERATION_NAMES:
        return _NOOP_METRICS_OPERATION
    return _metrics_registry.create_metrics_operation(name, attributes)


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


def record_query_session_max(value: int, pool_name: Optional[str]) -> None:
    _metrics_registry.set_query_session_max(value, _pool_attrs(pool_name))


def remove_query_session_pool_metrics(pool_name: Optional[str]) -> None:
    _metrics_registry.remove_query_session_pool(_pool_attrs(pool_name))


def record_retry_metrics(duration: float, attempts: int) -> None:
    _metrics_registry.record(RETRY_DURATION, duration)
    _metrics_registry.record(RETRY_ATTEMPTS, attempts)
