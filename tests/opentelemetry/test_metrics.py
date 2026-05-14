from unittest.mock import MagicMock

import pytest
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader


@pytest.fixture()
def metrics_reader():
    from ydb.opentelemetry.metrics import _metrics_registry
    from ydb.opentelemetry.plugin import _create_query_session_count_callback

    reader = InMemoryMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    meter = provider.get_meter("ydb.sdk")

    _metrics_registry.set_meter(meter, _create_query_session_count_callback())
    try:
        yield reader
    finally:
        _metrics_registry.clear()
        provider.shutdown()


def _metrics_by_name(reader):
    data = reader.get_metrics_data()
    if data is None:
        return {}

    return {
        metric.name: metric
        for resource_metrics in data.resource_metrics
        for scope_metrics in resource_metrics.scope_metrics
        for metric in scope_metrics.metrics
    }


def _single_point(reader, name):
    metric = _metrics_by_name(reader)[name]
    points = list(metric.data.data_points)
    assert len(points) == 1
    return points[0]


def _histogram_sum(reader, name):
    return _single_point(reader, name).sum


def _sum_value(reader, name):
    return _single_point(reader, name).value


def test_metrics_registry_records_all_instruments(metrics_reader, monkeypatch):
    from ydb import issues
    from ydb.opentelemetry.metrics import (
        CLIENT_OPERATION_DURATION,
        CLIENT_OPERATION_FAILED,
        QUERY_SESSION_COUNT,
        QUERY_SESSION_CREATE_TIME,
        QUERY_SESSION_PENDING_REQUESTS,
        QUERY_SESSION_TIMEOUTS,
        RETRY_ATTEMPTS,
        RETRY_DURATION,
        create_metrics_operation,
        record_query_session_count,
        record_query_session_create_time,
        record_query_session_pending_requests,
        record_query_session_timeout,
        record_retry_metrics,
    )

    monkeypatch.setattr("ydb.opentelemetry.metrics.time.monotonic", MagicMock(side_effect=[1.0, 1.25]))

    with pytest.raises(issues.Unavailable):
        with create_metrics_operation("ExecuteQuery"):
            raise issues.Unavailable("transient")

    record_query_session_count(2, "main", "used")
    record_query_session_create_time(0.5, "main")
    record_query_session_pending_requests(1, "main")
    record_query_session_timeout("main")
    record_retry_metrics(0.75, 3)

    metrics = _metrics_by_name(metrics_reader)

    assert set(metrics) == {
        CLIENT_OPERATION_DURATION,
        CLIENT_OPERATION_FAILED,
        QUERY_SESSION_COUNT,
        QUERY_SESSION_CREATE_TIME,
        QUERY_SESSION_PENDING_REQUESTS,
        QUERY_SESSION_TIMEOUTS,
        RETRY_ATTEMPTS,
        RETRY_DURATION,
    }
    assert metrics[CLIENT_OPERATION_DURATION].unit == "s"
    assert metrics[CLIENT_OPERATION_FAILED].unit == "{command}"
    assert metrics[QUERY_SESSION_COUNT].unit == "{connection}"
    assert metrics[QUERY_SESSION_CREATE_TIME].unit == "s"
    assert metrics[QUERY_SESSION_PENDING_REQUESTS].unit == "{request}"
    assert metrics[QUERY_SESSION_TIMEOUTS].unit == "{connection}"
    assert metrics[RETRY_DURATION].unit == "s"
    assert metrics[RETRY_ATTEMPTS].unit == "{attempt}"


def test_metrics_registry_is_noop_without_meter():
    from ydb.opentelemetry.metrics import (
        _metrics_registry,
        create_metrics_operation,
        record_query_session_create_time,
        record_query_session_pending_requests,
        record_query_session_timeout,
        record_retry_metrics,
    )

    _metrics_registry.clear()

    record_query_session_create_time(1.0, "pool")
    record_query_session_pending_requests(1, "pool")
    record_query_session_timeout("pool")
    record_retry_metrics(1.0, 2)

    with create_metrics_operation("test.operation"):
        pass


def test_metrics_operation_records_duration_once(metrics_reader, monkeypatch):
    from ydb.opentelemetry.metrics import CLIENT_OPERATION_DURATION, create_metrics_operation

    monotonic = MagicMock(side_effect=[10.0, 10.25, 11.0])
    monkeypatch.setattr("ydb.opentelemetry.metrics.time.monotonic", monotonic)

    operation = create_metrics_operation(
        "ExecuteQuery",
        {
            "db.namespace": "/Root/test",
            "server.address": "localhost",
            "server.port": 2136,
        },
    )
    operation.end()
    operation.end()

    point = _single_point(metrics_reader, CLIENT_OPERATION_DURATION)

    assert point.sum == 0.25
    assert point.count == 1
    assert point.attributes == {
        "db.system.name": "ydb",
        "db.namespace": "/Root/test",
        "server.address": "localhost",
        "server.port": 2136,
        "ydb.operation.name": "ExecuteQuery",
    }


def test_metrics_operation_records_ydb_error(metrics_reader, monkeypatch):
    from ydb import issues
    from ydb.opentelemetry.metrics import CLIENT_OPERATION_FAILED, create_metrics_operation

    monkeypatch.setattr("ydb.opentelemetry.metrics.time.monotonic", MagicMock(side_effect=[1.0, 1.1]))

    with pytest.raises(issues.Unavailable):
        with create_metrics_operation("ExecuteQuery"):
            raise issues.Unavailable("transient")

    point = _single_point(metrics_reader, CLIENT_OPERATION_FAILED)

    assert point.value == 1
    assert point.attributes["db.response.status_code"] == "UNAVAILABLE"
    assert point.attributes["ydb.operation.name"] == "ExecuteQuery"


def test_metrics_operation_records_generic_error_status_code(metrics_reader):
    from ydb.opentelemetry.metrics import CLIENT_OPERATION_FAILED, create_metrics_operation

    with pytest.raises(ValueError):
        with create_metrics_operation("ExecuteQuery"):
            raise ValueError("bad value")

    assert _single_point(metrics_reader, CLIENT_OPERATION_FAILED).attributes["db.response.status_code"] == "ValueError"


def test_metrics_operation_set_attribute(metrics_reader):
    from ydb.opentelemetry.metrics import CLIENT_OPERATION_DURATION, create_metrics_operation

    operation = create_metrics_operation("ExecuteQuery")
    operation.set_attribute("ydb.node.id", 123)
    operation.end()

    assert _single_point(metrics_reader, CLIENT_OPERATION_DURATION).attributes["ydb.node.id"] == 123


def test_query_session_count_accumulates_by_attributes(metrics_reader):
    from ydb.opentelemetry.metrics import QUERY_SESSION_COUNT, record_query_session_count

    record_query_session_count(1, "main", "used")
    record_query_session_count(2, "main", "used")
    record_query_session_count(1, None, "idle")

    metric = _metrics_by_name(metrics_reader)[QUERY_SESSION_COUNT]
    values = {tuple(sorted(point.attributes.items())): point.value for point in metric.data.data_points}

    assert (
        values[
            (
                ("ydb.query.session.pool.name", "main"),
                ("ydb.query.session.state", "used"),
            )
        ]
        == 3
    )
    assert (
        values[
            (
                ("ydb.query.session.pool.name", "unknown"),
                ("ydb.query.session.state", "idle"),
            )
        ]
        == 1
    )


def test_query_session_helpers_record_pool_attributes(metrics_reader):
    from ydb.opentelemetry.metrics import (
        QUERY_SESSION_CREATE_TIME,
        QUERY_SESSION_PENDING_REQUESTS,
        QUERY_SESSION_TIMEOUTS,
        record_query_session_create_time,
        record_query_session_pending_requests,
        record_query_session_timeout,
    )

    record_query_session_create_time(0.5, "main")
    record_query_session_pending_requests(1, None)
    record_query_session_timeout("main")

    assert _histogram_sum(metrics_reader, QUERY_SESSION_CREATE_TIME) == 0.5
    assert _single_point(metrics_reader, QUERY_SESSION_CREATE_TIME).attributes == {
        "ydb.query.session.pool.name": "main"
    }
    assert _sum_value(metrics_reader, QUERY_SESSION_PENDING_REQUESTS) == 1
    assert _single_point(metrics_reader, QUERY_SESSION_PENDING_REQUESTS).attributes == {
        "ydb.query.session.pool.name": "unknown"
    }
    assert _sum_value(metrics_reader, QUERY_SESSION_TIMEOUTS) == 1
    assert _single_point(metrics_reader, QUERY_SESSION_TIMEOUTS).attributes == {"ydb.query.session.pool.name": "main"}


def test_retry_operation_sync_records_retry_metrics(metrics_reader):
    from ydb import issues
    from ydb.opentelemetry.metrics import RETRY_ATTEMPTS, RETRY_DURATION
    from ydb.retries import RetrySettings, retry_operation_sync

    attempts = {"count": 0}

    def flaky():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise issues.Aborted("retry")
        return "ok"

    assert retry_operation_sync(flaky, RetrySettings(max_retries=5)) == "ok"

    duration = _single_point(metrics_reader, RETRY_DURATION)
    assert duration.count == 1
    assert duration.sum >= 0
    assert duration.attributes == {}
    assert _histogram_sum(metrics_reader, RETRY_ATTEMPTS) == 3


async def _async_value():
    return "ok"


@pytest.mark.asyncio
async def test_retry_operation_async_records_retry_metrics(metrics_reader):
    from ydb.opentelemetry.metrics import RETRY_ATTEMPTS, RETRY_DURATION
    from ydb.retries import retry_operation_async

    assert await retry_operation_async(_async_value) == "ok"

    duration = _single_point(metrics_reader, RETRY_DURATION)
    assert duration.count == 1
    assert duration.sum >= 0
    assert duration.attributes == {}
    assert _histogram_sum(metrics_reader, RETRY_ATTEMPTS) == 1
