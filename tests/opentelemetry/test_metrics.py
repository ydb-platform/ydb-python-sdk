from unittest.mock import MagicMock

import pytest


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
    return _single_point_from_metrics(_metrics_by_name(reader), name)


def _single_point_from_metrics(metrics, name):
    metric = metrics[name]
    points = list(metric.data.data_points)
    assert len(points) == 1
    return points[0]


def _histogram_sum(reader, name):
    return _single_point(reader, name).sum


def _sum_value(reader, name):
    return _single_point(reader, name).value


def test_metrics_registry_records_all_instruments(metrics_setup, monkeypatch):
    from ydb import issues
    from ydb.opentelemetry.metrics import (
        CLIENT_OPERATION_DURATION,
        CLIENT_OPERATION_FAILED,
        QUERY_SESSION_COUNT,
        QUERY_SESSION_CREATE_TIME,
        QUERY_SESSION_MAX,
        QUERY_SESSION_PENDING_REQUESTS,
        QUERY_SESSION_TIMEOUTS,
        RETRY_ATTEMPTS,
        RETRY_DURATION,
        create_metrics_operation,
        record_query_session_count,
        record_query_session_create_time,
        record_query_session_max,
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
    record_query_session_max(100, "main")
    record_query_session_pending_requests(1, "main")
    record_query_session_timeout("main")
    record_retry_metrics(0.75, 3)

    metrics = _metrics_by_name(metrics_setup)

    assert set(metrics) == {
        CLIENT_OPERATION_DURATION,
        CLIENT_OPERATION_FAILED,
        QUERY_SESSION_COUNT,
        QUERY_SESSION_CREATE_TIME,
        QUERY_SESSION_MAX,
        QUERY_SESSION_PENDING_REQUESTS,
        QUERY_SESSION_TIMEOUTS,
        RETRY_ATTEMPTS,
        RETRY_DURATION,
    }
    assert metrics[CLIENT_OPERATION_DURATION].unit == "s"
    assert metrics[CLIENT_OPERATION_FAILED].unit == "{command}"
    assert metrics[QUERY_SESSION_COUNT].unit == "{connection}"
    assert metrics[QUERY_SESSION_CREATE_TIME].unit == "s"
    assert metrics[QUERY_SESSION_MAX].unit == "{connection}"
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


def test_metrics_operation_records_duration_once(metrics_setup, monkeypatch):
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

    point = _single_point(metrics_setup, CLIENT_OPERATION_DURATION)

    assert point.sum == 0.25
    assert point.count == 1
    assert point.attributes == {
        "db.system.name": "ydb",
        "db.namespace": "/Root/test",
        "server.address": "localhost",
        "server.port": 2136,
        "ydb.operation.name": "ExecuteQuery",
    }


def test_metrics_operation_records_ydb_error(metrics_setup, monkeypatch):
    from ydb import issues
    from ydb.opentelemetry.metrics import CLIENT_OPERATION_FAILED, create_metrics_operation

    monkeypatch.setattr("ydb.opentelemetry.metrics.time.monotonic", MagicMock(side_effect=[1.0, 1.1]))

    with pytest.raises(issues.Unavailable):
        with create_metrics_operation("ExecuteQuery"):
            raise issues.Unavailable("transient")

    point = _single_point(metrics_setup, CLIENT_OPERATION_FAILED)

    assert point.value == 1
    assert point.attributes["db.response.status_code"] == "UNAVAILABLE"
    assert point.attributes["ydb.operation.name"] == "ExecuteQuery"


def test_metrics_operation_records_generic_error_status_code(metrics_setup):
    from ydb.opentelemetry.metrics import CLIENT_OPERATION_FAILED, create_metrics_operation

    with pytest.raises(ValueError):
        with create_metrics_operation("ExecuteQuery"):
            raise ValueError("bad value")

    assert _single_point(metrics_setup, CLIENT_OPERATION_FAILED).attributes["db.response.status_code"] == "ValueError"


def test_metrics_operation_set_attribute(metrics_setup):
    from ydb.opentelemetry.metrics import CLIENT_OPERATION_DURATION, create_metrics_operation

    operation = create_metrics_operation("ExecuteQuery")
    operation.set_attribute("db.namespace", "/Root/test")
    operation.end()

    assert _single_point(metrics_setup, CLIENT_OPERATION_DURATION).attributes["db.namespace"] == "/Root/test"


def test_metrics_operation_ignores_non_metric_attributes(metrics_setup):
    from ydb.opentelemetry.metrics import CLIENT_OPERATION_DURATION, create_metrics_operation

    operation = create_metrics_operation("ExecuteQuery")
    operation.set_attribute("network.peer.address", "node.example.net")
    operation.set_attribute("network.peer.port", 2136)
    operation.set_attribute("ydb.node.dc", "dc-a")
    operation.set_attribute("ydb.node.id", 123)
    operation.end()

    attrs = _single_point(metrics_setup, CLIENT_OPERATION_DURATION).attributes

    assert "network.peer.address" not in attrs
    assert "network.peer.port" not in attrs
    assert "ydb.node.dc" not in attrs
    assert "ydb.node.id" not in attrs


def test_metrics_operation_respects_end_on_exit_false(metrics_setup):
    from ydb.opentelemetry.metrics import CLIENT_OPERATION_DURATION, create_metrics_operation

    operation = create_metrics_operation("ExecuteQuery")
    with operation.attach_context(end_on_exit=False):
        pass

    assert CLIENT_OPERATION_DURATION not in _metrics_by_name(metrics_setup)

    operation.end()

    point = _single_point(metrics_setup, CLIENT_OPERATION_DURATION)
    assert point.count == 1
    assert point.sum >= 0


def test_create_ydb_span_records_metrics_when_tracing_is_active(metrics_setup, tracing_setup):
    from tests.opentelemetry.conftest import FakeDriverConfig
    from ydb.opentelemetry.metrics import CLIENT_OPERATION_DURATION
    from ydb.opentelemetry.tracing import create_ydb_span

    exporter = tracing_setup

    with create_ydb_span(
        "ydb.ExecuteQuery",
        FakeDriverConfig(),
        node_id=123,
        peer=("node.example.net", 2136, "dc-a"),
    ).attach_context():
        pass

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    span_attrs = dict(spans[0].attributes)
    assert span_attrs["network.peer.address"] == "node.example.net"
    assert span_attrs["network.peer.port"] == 2136
    assert span_attrs["ydb.node.dc"] == "dc-a"
    assert span_attrs["ydb.node.id"] == 123

    metric_attrs = _single_point(metrics_setup, CLIENT_OPERATION_DURATION).attributes
    assert metric_attrs["ydb.operation.name"] == "ydb.ExecuteQuery"
    assert "network.peer.address" not in metric_attrs
    assert "network.peer.port" not in metric_attrs
    assert "ydb.node.dc" not in metric_attrs
    assert "ydb.node.id" not in metric_attrs


def test_create_ydb_span_records_metrics_when_tracing_is_disabled(metrics_setup):
    from tests.opentelemetry.conftest import FakeDriverConfig
    from ydb.opentelemetry.metrics import CLIENT_OPERATION_DURATION
    from ydb.opentelemetry.tracing import _registry, create_ydb_span

    _registry.set_create_span(None)

    with create_ydb_span("ydb.ExecuteQuery", FakeDriverConfig()).attach_context():
        pass

    assert (
        _single_point(metrics_setup, CLIENT_OPERATION_DURATION).attributes["ydb.operation.name"] == "ydb.ExecuteQuery"
    )


def test_query_session_count_accumulates_by_attributes(metrics_setup):
    from ydb.opentelemetry.metrics import QUERY_SESSION_COUNT, record_query_session_count

    record_query_session_count(1, "main", "used")
    record_query_session_count(2, "main", "used")
    record_query_session_count(1, None, "idle")

    metric = _metrics_by_name(metrics_setup)[QUERY_SESSION_COUNT]
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


def test_query_session_helpers_record_pool_attributes(metrics_setup):
    from ydb.opentelemetry.metrics import (
        QUERY_SESSION_CREATE_TIME,
        QUERY_SESSION_MAX,
        QUERY_SESSION_PENDING_REQUESTS,
        QUERY_SESSION_TIMEOUTS,
        record_query_session_create_time,
        record_query_session_max,
        record_query_session_pending_requests,
        record_query_session_timeout,
    )

    record_query_session_create_time(0.5, "main")
    record_query_session_max(100, "main")
    record_query_session_pending_requests(1, None)
    record_query_session_timeout("main")

    metrics = _metrics_by_name(metrics_setup)
    create_time = _single_point_from_metrics(metrics, QUERY_SESSION_CREATE_TIME)
    pending_requests = _single_point_from_metrics(metrics, QUERY_SESSION_PENDING_REQUESTS)
    timeouts = _single_point_from_metrics(metrics, QUERY_SESSION_TIMEOUTS)
    session_max = _single_point_from_metrics(metrics, QUERY_SESSION_MAX)

    assert create_time.sum == 0.5
    assert create_time.attributes == {"ydb.query.session.pool.name": "main"}
    assert pending_requests.value == 1
    assert pending_requests.attributes == {"ydb.query.session.pool.name": "unknown"}
    assert timeouts.value == 1
    assert timeouts.attributes == {"ydb.query.session.pool.name": "main"}
    assert session_max.value == 100
    assert session_max.attributes == {"ydb.query.session.pool.name": "main"}


def test_sync_query_session_pool_records_max(metrics_setup):
    from ydb.opentelemetry.metrics import QUERY_SESSION_MAX
    from ydb.query.pool import QuerySessionPool

    QuerySessionPool(driver=object(), size=42, name="sync-pool")

    assert _single_point(metrics_setup, QUERY_SESSION_MAX).value == 42
    assert _single_point(metrics_setup, QUERY_SESSION_MAX).attributes == {"ydb.query.session.pool.name": "sync-pool"}


@pytest.mark.asyncio
async def test_async_query_session_pool_records_max(metrics_setup):
    from ydb.aio.query.pool import QuerySessionPool
    from ydb.opentelemetry.metrics import QUERY_SESSION_MAX

    QuerySessionPool(driver=object(), size=24, name="async-pool")

    assert _single_point(metrics_setup, QUERY_SESSION_MAX).value == 24
    assert _single_point(metrics_setup, QUERY_SESSION_MAX).attributes == {"ydb.query.session.pool.name": "async-pool"}


@pytest.mark.asyncio
async def test_sync_and_async_query_session_pool_auto_names_do_not_collide(metrics_setup):
    from ydb.aio.query.pool import QuerySessionPool as AsyncQuerySessionPool
    from ydb.opentelemetry.metrics import QUERY_SESSION_MAX
    from ydb.query.pool import QuerySessionPool

    QuerySessionPool(driver=object(), size=42)
    AsyncQuerySessionPool(driver=object(), size=24)

    metric = _metrics_by_name(metrics_setup)[QUERY_SESSION_MAX]
    values = {point.attributes["ydb.query.session.pool.name"]: point.value for point in metric.data.data_points}

    assert len(values) == 2
    assert sorted(values.values()) == [24, 42]


def test_retry_operation_sync_records_retry_metrics(metrics_setup):
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

    metrics = _metrics_by_name(metrics_setup)
    duration = _single_point_from_metrics(metrics, RETRY_DURATION)
    retry_attempts = _single_point_from_metrics(metrics, RETRY_ATTEMPTS)

    assert duration.count == 1
    assert duration.sum >= 0
    assert duration.attributes == {}
    assert retry_attempts.sum == 3


async def _async_value():
    return "ok"


@pytest.mark.asyncio
async def test_retry_operation_async_records_retry_metrics(metrics_setup):
    from ydb.opentelemetry.metrics import RETRY_ATTEMPTS, RETRY_DURATION
    from ydb.retries import retry_operation_async

    assert await retry_operation_async(_async_value) == "ok"

    metrics = _metrics_by_name(metrics_setup)
    duration = _single_point_from_metrics(metrics, RETRY_DURATION)
    retry_attempts = _single_point_from_metrics(metrics, RETRY_ATTEMPTS)

    assert duration.count == 1
    assert duration.sum >= 0
    assert duration.attributes == {}
    assert retry_attempts.sum == 1
