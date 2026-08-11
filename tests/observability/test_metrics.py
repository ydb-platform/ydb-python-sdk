import asyncio
import inspect
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from opentelemetry.metrics import Meter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from ydb import issues
from ydb._grpc.common.protos import ydb_query_pb2
from ydb._grpc.grpcwrapper.common_utils import ServerStatus
from ydb.aio.query.base import AsyncResponseContextIterator
from ydb.aio.query.pool import QuerySessionPool as AsyncQuerySessionPool
from ydb.aio.query.session import QuerySession as AsyncQuerySession
from ydb.observability.metrics import QUERY_SESSION_CLOSED
from ydb.query.base import SyncResponseContextIterator, bad_session_handler
from ydb.query.pool import QuerySessionPool as SyncQuerySessionPool
from ydb.query.session import QuerySession as SyncQuerySession


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


def _points(reader, name):
    metrics = _metrics_by_name(reader)
    if name not in metrics:
        return []
    return list(metrics[name].data.data_points)


def _histogram_sum(reader, name):
    return _single_point(reader, name).sum


def _sum_value(reader, name):
    return _single_point(reader, name).value


def _assert_closed_metric(reader, pool_name, reason):
    point = _single_point(reader, QUERY_SESSION_CLOSED)
    assert (point.value, point.attributes) == (
        1,
        {"ydb.query.session.pool.name": pool_name, "reason": reason},
    )


def _histogram_boundaries_advisory_supported():
    return "explicit_bucket_boundaries_advisory" in inspect.signature(Meter.create_histogram).parameters


def test_metrics_build_info_version(metrics_setup):
    from ydb.observability.metrics import _metrics_build_info_tokens

    assert _metrics_build_info_tokens() == ["ydb-sdk-metrics/0.2.0"]


def test_metrics_registry_records_all_instruments(metrics_setup, monkeypatch):
    from ydb import issues
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
        ATTEMPT_BUCKETS,
        DURATION_BUCKETS_SECONDS,
        RETRY_DURATION_BUCKETS_SECONDS,
        SessionMetrics,
        create_metrics_operation,
        record_query_session_count,
        record_query_session_create_time,
        record_query_session_max,
        record_query_session_pending_requests,
        record_query_session_timeout,
        record_retry_metrics,
    )

    monkeypatch.setattr("ydb.observability.metrics.time.monotonic", MagicMock(side_effect=[1.0, 1.25]))

    with pytest.raises(issues.Unavailable):
        with create_metrics_operation("ExecuteQuery"):
            raise issues.Unavailable("transient")

    record_query_session_count(2, "main", "used")
    session_metrics = SessionMetrics()
    session_metrics.pool_name = "main"
    session_metrics.count_open()
    session_metrics.count_closed("pool_graceful_shutdown")
    record_query_session_create_time(0.5, "main")
    record_query_session_max(100, "main")
    record_query_session_pending_requests(1, "main")
    record_query_session_timeout("main")
    record_retry_metrics(0.75, 3)

    metrics = _metrics_by_name(metrics_setup)

    assert set(metrics) == {
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
    }
    assert metrics[CLIENT_OPERATION_DURATION].unit == "s"
    assert metrics[CLIENT_OPERATION_FAILED].unit == "{command}"
    assert metrics[QUERY_SESSION_CLOSED].unit == "{session}"
    assert metrics[QUERY_SESSION_COUNT].unit == "{connection}"
    assert metrics[QUERY_SESSION_CREATE_TIME].unit == "s"
    assert metrics[QUERY_SESSION_MAX].unit == "{connection}"
    assert metrics[QUERY_SESSION_MIN].unit == "{connection}"
    assert metrics[QUERY_SESSION_PENDING_REQUESTS].unit == "{request}"
    assert metrics[QUERY_SESSION_TIMEOUTS].unit == "{connection}"
    assert metrics[RETRY_DURATION].unit == "s"
    assert metrics[RETRY_ATTEMPTS].unit == "{attempt}"
    if _histogram_boundaries_advisory_supported():
        assert (
            _single_point_from_metrics(metrics, CLIENT_OPERATION_DURATION).explicit_bounds == DURATION_BUCKETS_SECONDS
        )
        assert (
            _single_point_from_metrics(metrics, QUERY_SESSION_CREATE_TIME).explicit_bounds == DURATION_BUCKETS_SECONDS
        )
        assert _single_point_from_metrics(metrics, RETRY_DURATION).explicit_bounds == RETRY_DURATION_BUCKETS_SECONDS
        assert _single_point_from_metrics(metrics, RETRY_ATTEMPTS).explicit_bounds == ATTEMPT_BUCKETS


def test_metrics_registry_supports_old_histogram_api():
    from ydb.opentelemetry.metrics_plugin import OtelMetricsProvider

    class FakeInstrument:
        def add(self, value, attributes=None):
            pass

        def record(self, value, attributes=None):
            pass

    class FakeMeter:
        def create_histogram(self, name, unit="", description="", **kwargs):
            if "explicit_bucket_boundaries_advisory" in kwargs:
                raise TypeError(
                    "create_histogram() got an unexpected keyword argument 'explicit_bucket_boundaries_advisory'"
                )
            return FakeInstrument()

        def create_counter(self, name, unit="", description=""):
            return FakeInstrument()

        def create_up_down_counter(self, name, unit="", description=""):
            return FakeInstrument()

        def create_observable_up_down_counter(self, name, callbacks=None, unit="", description=""):
            return FakeInstrument()

    OtelMetricsProvider(FakeMeter())


def test_create_histogram_reraises_unrelated_type_error():
    from ydb.opentelemetry.metrics_plugin import _create_histogram

    class BrokenMeter:
        def create_histogram(self, name, unit="", description="", **kwargs):
            raise TypeError("unexpected unit type")

    with pytest.raises(TypeError, match="unexpected unit type"):
        _create_histogram(
            BrokenMeter(),
            "test.histogram",
            unit="s",
            description="test",
            bucket_boundaries=[1.0],
        )


def test_metrics_registry_is_noop_without_meter():
    from ydb.observability.metrics import (
        create_metrics_operation,
        record_query_session_create_time,
        record_query_session_max,
        record_query_session_pending_requests,
        record_query_session_timeout,
        record_retry_metrics,
        remove_query_session_pool_metrics,
    )

    record_query_session_create_time(1.0, "pool")
    record_query_session_max(10, "pool")
    record_query_session_pending_requests(1, "pool")
    record_query_session_timeout("pool")
    record_retry_metrics(1.0, 2)
    remove_query_session_pool_metrics("pool")

    operation = create_metrics_operation("ExecuteQuery")
    operation.set_error(ValueError("noop"))
    operation.set_attribute("database", "/db")
    with operation:
        pass


def test_metrics_operation_records_duration_once(metrics_setup, monkeypatch):
    from ydb.observability.metrics import CLIENT_OPERATION_DURATION, create_metrics_operation

    monotonic = MagicMock(side_effect=[10.0, 10.25, 11.0])
    monkeypatch.setattr("ydb.observability.metrics.time.monotonic", monotonic)

    operation = create_metrics_operation(
        "ExecuteQuery",
        {
            "database": "/Root/test",
            "endpoint": "localhost:2136",
        },
    )
    operation.end()
    operation.end()

    point = _single_point(metrics_setup, CLIENT_OPERATION_DURATION)

    assert point.sum == 0.25
    assert point.count == 1
    assert point.attributes == {
        "database": "/Root/test",
        "endpoint": "localhost:2136",
        "operation.name": "ExecuteQuery",
    }


def test_metrics_operation_records_ydb_error(metrics_setup, monkeypatch):
    from ydb import issues
    from ydb.observability.metrics import CLIENT_OPERATION_FAILED, create_metrics_operation

    monkeypatch.setattr("ydb.observability.metrics.time.monotonic", MagicMock(side_effect=[1.0, 1.1]))

    with pytest.raises(issues.Unavailable):
        with create_metrics_operation("ExecuteQuery"):
            raise issues.Unavailable("transient")

    point = _single_point(metrics_setup, CLIENT_OPERATION_FAILED)

    assert point.value == 1
    assert point.attributes["status_code"] == "UNAVAILABLE"
    assert point.attributes["operation.name"] == "ExecuteQuery"


def test_metrics_operation_records_generic_error_status_code(metrics_setup):
    from ydb.observability.metrics import CLIENT_OPERATION_FAILED, create_metrics_operation

    with pytest.raises(ValueError):
        with create_metrics_operation("ExecuteQuery"):
            raise ValueError("bad value")

    assert _single_point(metrics_setup, CLIENT_OPERATION_FAILED).attributes["status_code"] == "ValueError"


def test_metrics_operation_set_attribute(metrics_setup):
    from ydb.observability.metrics import CLIENT_OPERATION_DURATION, create_metrics_operation

    operation = create_metrics_operation("ExecuteQuery")
    operation.set_attribute("database", "/Root/test")
    operation.end()

    assert _single_point(metrics_setup, CLIENT_OPERATION_DURATION).attributes["database"] == "/Root/test"


def test_metrics_operation_ignores_non_metric_attributes(metrics_setup):
    from ydb.observability.metrics import CLIENT_OPERATION_DURATION, create_metrics_operation

    operation = create_metrics_operation("ExecuteQuery")
    operation.set_attribute("db.namespace", "/Root/test")
    operation.set_attribute("server.address", "localhost")
    operation.set_attribute("server.port", 2136)
    operation.set_attribute("ydb.operation.name", "ydb.Commit")
    operation.set_attribute("network.peer.address", "node.example.net")
    operation.set_attribute("network.peer.port", 2136)
    operation.set_attribute("ydb.node.dc", "dc-a")
    operation.set_attribute("ydb.node.id", 123)
    operation.end()

    attrs = _single_point(metrics_setup, CLIENT_OPERATION_DURATION).attributes

    assert "db.namespace" not in attrs
    assert "server.address" not in attrs
    assert "server.port" not in attrs
    assert "ydb.operation.name" not in attrs
    assert "network.peer.address" not in attrs
    assert "network.peer.port" not in attrs
    assert "ydb.node.dc" not in attrs
    assert "ydb.node.id" not in attrs


def test_metrics_operation_respects_end_on_exit_false(metrics_setup):
    from ydb.observability.metrics import CLIENT_OPERATION_DURATION, create_metrics_operation

    operation = create_metrics_operation("ExecuteQuery")
    with operation.attach_context(end_on_exit=False):
        pass

    assert CLIENT_OPERATION_DURATION not in _metrics_by_name(metrics_setup)

    operation.end()

    point = _single_point(metrics_setup, CLIENT_OPERATION_DURATION)
    assert point.count == 1
    assert point.sum >= 0


def test_metrics_operation_context_records_error_on_exit(metrics_setup):
    from ydb.observability.metrics import CLIENT_OPERATION_FAILED, create_metrics_operation

    operation = create_metrics_operation("ExecuteQuery")
    with pytest.raises(RuntimeError, match="boom"):
        with operation.attach_context():
            raise RuntimeError("boom")

    assert _single_point(metrics_setup, CLIENT_OPERATION_FAILED).attributes["status_code"] == "RuntimeError"


def test_metrics_operation_ignores_unknown_operation_name(metrics_setup):
    from ydb.observability.metrics import CLIENT_OPERATION_DURATION, create_metrics_operation

    with create_metrics_operation("ydb.Driver.Initialize"):
        pass

    assert CLIENT_OPERATION_DURATION not in _metrics_by_name(metrics_setup)


def test_create_ydb_span_records_metrics_when_tracing_is_active(metrics_setup, otel_setup):
    from tests.observability.conftest import FakeDriverConfig
    from ydb.observability.metrics import CLIENT_OPERATION_DURATION
    from ydb.observability.tracing import create_ydb_span

    exporter = otel_setup

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
    assert metric_attrs["database"] == "/test_database"
    assert metric_attrs["endpoint"] == "test_endpoint:1337"
    assert metric_attrs["operation.name"] == "ExecuteQuery"
    assert "network.peer.address" not in metric_attrs
    assert "network.peer.port" not in metric_attrs
    assert "ydb.node.dc" not in metric_attrs
    assert "ydb.node.id" not in metric_attrs


def test_create_ydb_span_records_metrics_when_tracing_is_disabled(metrics_setup):
    from tests.observability.conftest import FakeDriverConfig
    from ydb.observability import disable_tracing
    from ydb.observability.metrics import CLIENT_OPERATION_DURATION
    from ydb.observability.tracing import create_ydb_span

    disable_tracing()

    with create_ydb_span("ydb.ExecuteQuery", FakeDriverConfig()).attach_context():
        pass

    metric_attrs = _single_point(metrics_setup, CLIENT_OPERATION_DURATION).attributes
    assert metric_attrs["database"] == "/test_database"
    assert metric_attrs["endpoint"] == "test_endpoint:1337"
    assert metric_attrs["operation.name"] == "ExecuteQuery"


def test_query_session_count_accumulates_by_attributes(metrics_setup):
    from ydb.observability.metrics import QUERY_SESSION_COUNT, record_query_session_count

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
    from ydb.observability.metrics import (
        QUERY_SESSION_CREATE_TIME,
        QUERY_SESSION_MAX,
        QUERY_SESSION_MIN,
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
    session_min = _single_point_from_metrics(metrics, QUERY_SESSION_MIN)

    assert create_time.sum == 0.5
    assert create_time.attributes == {"ydb.query.session.pool.name": "main"}
    assert pending_requests.value == 1
    assert pending_requests.attributes == {"ydb.query.session.pool.name": "unknown"}
    assert timeouts.value == 1
    assert timeouts.attributes == {"ydb.query.session.pool.name": "main"}
    assert session_max.value == 100
    assert session_max.attributes == {"ydb.query.session.pool.name": "main"}
    assert session_min.value == 0
    assert session_min.attributes == {"ydb.query.session.pool.name": "main"}


def test_sync_query_session_pool_records_max(metrics_setup):
    from ydb.observability.metrics import QUERY_SESSION_MAX, QUERY_SESSION_MIN
    from ydb.query.pool import QuerySessionPool

    QuerySessionPool(driver=object(), size=42, name="sync-pool")

    assert _single_point(metrics_setup, QUERY_SESSION_MAX).value == 42
    assert _single_point(metrics_setup, QUERY_SESSION_MAX).attributes == {"ydb.query.session.pool.name": "sync-pool"}
    assert _single_point(metrics_setup, QUERY_SESSION_MIN).value == 0
    assert _single_point(metrics_setup, QUERY_SESSION_MIN).attributes == {"ydb.query.session.pool.name": "sync-pool"}


def test_sync_query_session_pool_stop_removes_observable_metrics(metrics_setup):
    from ydb.observability.metrics import QUERY_SESSION_COUNT, QUERY_SESSION_MAX, QUERY_SESSION_MIN
    from ydb.query.pool import QuerySessionPool

    pool = QuerySessionPool(driver=object(), size=42, name="sync-pool")
    pool.stop()

    assert _points(metrics_setup, QUERY_SESSION_COUNT) == []
    assert _points(metrics_setup, QUERY_SESSION_MAX) == []
    assert _points(metrics_setup, QUERY_SESSION_MIN) == []


def test_query_session_pool_name_prefers_explicit_name():
    from ydb.observability.metrics import query_session_pool_name

    assert query_session_pool_name("my-pool", endpoint="grpc://localhost:2136", database="/local") == "my-pool"


def test_query_session_pool_name_uses_connection_string():
    from ydb.observability.metrics import query_session_pool_name

    assert (
        query_session_pool_name(None, endpoint="grpc://localhost:2136", database="/local")
        == "grpc://localhost:2136/local"
    )


def test_query_session_pool_name_normalizes_database_without_leading_slash():
    from ydb.observability.metrics import query_session_pool_name

    assert (
        query_session_pool_name(None, endpoint="grpc://localhost:2136", database="local")
        == "grpc://localhost:2136/local"
    )


def test_query_session_pool_name_falls_back_to_counter_when_nothing_known():
    from ydb.observability.metrics import query_session_pool_name

    assert query_session_pool_name(None, endpoint=None, database=None).startswith("query-session-pool-")


def test_sync_query_session_pool_uses_connection_string_as_default_pool_name(metrics_setup):
    from tests.observability.conftest import FakeDriverConfig
    from ydb.observability.metrics import QUERY_SESSION_MAX
    from ydb.query.pool import QuerySessionPool

    class FakeDriver:
        _driver_config = FakeDriverConfig(endpoint="grpc://localhost:2136", database="/local")

    QuerySessionPool(driver=FakeDriver(), size=42)

    assert _single_point(metrics_setup, QUERY_SESSION_MAX).value == 42
    assert _single_point(metrics_setup, QUERY_SESSION_MAX).attributes == {
        "ydb.query.session.pool.name": "grpc://localhost:2136/local"
    }


@pytest.mark.asyncio
async def test_async_query_session_pool_records_max(metrics_setup):
    from ydb.aio.query.pool import QuerySessionPool
    from ydb.observability.metrics import QUERY_SESSION_MAX, QUERY_SESSION_MIN

    QuerySessionPool(driver=object(), size=24, name="async-pool")

    assert _single_point(metrics_setup, QUERY_SESSION_MAX).value == 24
    assert _single_point(metrics_setup, QUERY_SESSION_MAX).attributes == {"ydb.query.session.pool.name": "async-pool"}
    assert _single_point(metrics_setup, QUERY_SESSION_MIN).value == 0
    assert _single_point(metrics_setup, QUERY_SESSION_MIN).attributes == {"ydb.query.session.pool.name": "async-pool"}


@pytest.mark.asyncio
async def test_async_query_session_pool_stop_removes_observable_metrics(metrics_setup):
    from ydb.aio.query.pool import QuerySessionPool
    from ydb.observability.metrics import QUERY_SESSION_COUNT, QUERY_SESSION_MAX, QUERY_SESSION_MIN

    pool = QuerySessionPool(driver=object(), size=24, name="async-pool")
    await pool.stop()

    assert _points(metrics_setup, QUERY_SESSION_COUNT) == []
    assert _points(metrics_setup, QUERY_SESSION_MAX) == []
    assert _points(metrics_setup, QUERY_SESSION_MIN) == []


@pytest.mark.asyncio
async def test_async_query_session_pool_uses_connection_string_as_default_pool_name(metrics_setup):
    from tests.observability.conftest import FakeDriverConfig
    from ydb.aio.query.pool import QuerySessionPool
    from ydb.observability.metrics import QUERY_SESSION_MAX

    class FakeDriver:
        _driver_config = FakeDriverConfig(endpoint="grpc://localhost:2136", database="/local")

    QuerySessionPool(driver=FakeDriver(), size=24)

    assert _single_point(metrics_setup, QUERY_SESSION_MAX).value == 24
    assert _single_point(metrics_setup, QUERY_SESSION_MAX).attributes == {
        "ydb.query.session.pool.name": "grpc://localhost:2136/local"
    }


@pytest.mark.asyncio
async def test_sync_and_async_query_session_pool_auto_names_do_not_collide(metrics_setup):
    from ydb.aio.query.pool import QuerySessionPool as AsyncQuerySessionPool
    from ydb.observability.metrics import QUERY_SESSION_MAX
    from ydb.query.pool import QuerySessionPool

    QuerySessionPool(driver=object(), size=42)
    AsyncQuerySessionPool(driver=object(), size=24)

    metric = _metrics_by_name(metrics_setup)[QUERY_SESSION_MAX]
    values = {point.attributes["ydb.query.session.pool.name"]: point.value for point in metric.data.data_points}

    assert len(values) == 2
    assert sorted(values.values()) == [24, 42]


def test_retry_operation_sync_records_retry_metrics(metrics_setup):
    from ydb import issues
    from ydb.observability.metrics import RETRY_ATTEMPTS, RETRY_DURATION
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
    from ydb.observability.metrics import RETRY_ATTEMPTS, RETRY_DURATION
    from ydb.retries import retry_operation_async

    assert await retry_operation_async(_async_value) == "ok"

    metrics = _metrics_by_name(metrics_setup)
    duration = _single_point_from_metrics(metrics, RETRY_DURATION)
    retry_attempts = _single_point_from_metrics(metrics, RETRY_ATTEMPTS)

    assert duration.count == 1
    assert duration.sum >= 0
    assert duration.attributes == {}
    assert retry_attempts.sum == 1


class TestOpenTelemetryPublicApi:
    def test_enable_disable_metrics_roundtrip(self):
        from ydb.opentelemetry import disable_metrics, enable_metrics
        from ydb.observability.metrics import is_metrics_enabled

        reader = InMemoryMetricReader()
        provider = MeterProvider(metric_readers=[reader])

        disable_metrics()
        assert not is_metrics_enabled()
        enable_metrics(provider)
        assert is_metrics_enabled()
        disable_metrics()
        assert not is_metrics_enabled()
        provider.shutdown()

    def test_enable_metrics_is_idempotent(self):
        from ydb.opentelemetry.metrics_plugin import _enable_metrics
        from ydb.observability.metrics import is_metrics_enabled
        from ydb.opentelemetry import disable_metrics

        disable_metrics()
        reader = InMemoryMetricReader()
        provider = MeterProvider(metric_readers=[reader])
        _enable_metrics(provider)
        _enable_metrics(MeterProvider(metric_readers=[InMemoryMetricReader()]))
        assert is_metrics_enabled()
        disable_metrics()
        provider.shutdown()

    def test_enable_metrics_with_none_uses_default_meter(self):
        from ydb.opentelemetry import disable_metrics
        from ydb.observability.metrics import is_metrics_enabled
        from ydb.opentelemetry.metrics_plugin import _disable_metrics, _enable_metrics

        disable_metrics()
        _enable_metrics(None)
        assert is_metrics_enabled()
        _disable_metrics()
        assert not is_metrics_enabled()

    def test_enable_metrics_rejects_invalid_provider(self):
        from ydb.opentelemetry.metrics_plugin import _enable_metrics
        from ydb.opentelemetry import disable_metrics

        disable_metrics()
        with pytest.raises(TypeError, match="MeterProvider"):
            _enable_metrics(object())

    def test_enable_metrics_import_error(self, monkeypatch):
        import ydb.opentelemetry as otel

        real_import = __import__

        def fake_import(name, *args, **kwargs):
            if name == "ydb.opentelemetry.metrics_plugin":
                raise ImportError("missing otel")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", fake_import)
        with pytest.raises(ImportError, match="opentelemetry"):
            otel.enable_metrics()

    def test_disable_metrics_without_opentelemetry_is_noop(self, monkeypatch):
        import ydb.opentelemetry as otel

        real_import = __import__

        def fake_import(name, *args, **kwargs):
            if name == "ydb.opentelemetry.metrics_plugin":
                raise ImportError("missing otel")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", fake_import)
        otel.disable_metrics()


class TestEndpointHelpers:
    @pytest.mark.parametrize(
        "endpoint,expected",
        [
            ("grpc://localhost:2136", ("localhost", 2136)),
            ("grpcs://localhost:2136", ("localhost", 2136)),
            ("localhost:2135", ("localhost", 2135)),
            ("localhost", ("localhost", 0)),
            ("[::1]:2136", ("[::1]", 2136)),
            ("grpc://[2001:db8::1]:2136", ("[2001:db8::1]", 2136)),
            ("host:badport", ("host", 0)),
            (None, ("", 0)),
        ],
    )
    def test_split_endpoint(self, endpoint, expected):
        from ydb.observability._endpoint import split_endpoint

        assert split_endpoint(endpoint) == expected

    def test_build_ydb_metrics_attrs(self):
        from tests.observability.conftest import FakeDriverConfig
        from ydb.observability.metrics import _build_ydb_metrics_attrs

        attrs = _build_ydb_metrics_attrs(FakeDriverConfig(endpoint="grpc://node:2136", database="/db"))
        assert attrs == {"database": "/db", "endpoint": "node:2136"}


class TestTracingTelemetryFacade:
    def test_telemetry_operation_forwards_to_span_and_metrics(self, metrics_setup, otel_setup):
        from tests.observability.conftest import FakeDriverConfig
        from ydb.observability.tracing import create_ydb_span

        telemetry = create_ydb_span("ydb.ExecuteQuery", FakeDriverConfig())
        telemetry.set_attribute("database", "/db")
        telemetry.set_error(ValueError("fail"))
        telemetry.end()

        spans = otel_setup.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].status.status_code.name == "ERROR"

    def test_telemetry_context_end_on_exit_false(self, metrics_setup, otel_setup):
        from tests.observability.conftest import FakeDriverConfig
        from ydb.observability.metrics import CLIENT_OPERATION_DURATION
        from ydb.observability.tracing import create_ydb_span

        telemetry = create_ydb_span("ydb.ExecuteQuery", FakeDriverConfig())
        with telemetry.attach_context(end_on_exit=False):
            pass

        assert CLIENT_OPERATION_DURATION not in _metrics_by_name(metrics_setup)
        assert len(otel_setup.get_finished_spans()) == 0

        telemetry.end()
        assert len(otel_setup.get_finished_spans()) == 1
        assert CLIENT_OPERATION_DURATION in _metrics_by_name(metrics_setup)

    def test_set_peer_attributes_skips_none(self):
        from ydb.observability.tracing import set_peer_attributes

        span = MagicMock()
        set_peer_attributes(span, None)
        span.set_attribute.assert_not_called()

    def test_set_peer_attributes_sets_network_fields(self):
        from ydb.observability.tracing import set_peer_attributes

        span = MagicMock()
        set_peer_attributes(span, ("node.example.net", 2136, "dc-a"))

        span.set_attribute.assert_any_call("network.peer.address", "node.example.net")
        span.set_attribute.assert_any_call("network.peer.port", 2136)
        span.set_attribute.assert_any_call("ydb.node.dc", "dc-a")

    def test_span_finish_callback_records_error(self):
        from ydb.observability.tracing import span_finish_callback

        span = MagicMock()
        finish = span_finish_callback(span)
        finish(RuntimeError("boom"))

        span.set_error.assert_called_once()
        span.end.assert_called_once()

    def test_tracing_plugin_sets_transport_error(self, otel_setup):
        from opentelemetry import trace
        from ydb import issues
        from ydb.opentelemetry.plugin import _set_error_on_span

        error = issues.Error("lost")
        error.status = issues.StatusCode.CONNECTION_LOST

        raw_span = trace.get_tracer("test").start_span("x")
        _set_error_on_span(raw_span, error)
        raw_span.end()

        finished = otel_setup.get_finished_spans()[0]
        assert finished.attributes["error.type"] == "transport_error"

    def test_tracing_plugin_sets_generic_error_type(self, otel_setup):
        from opentelemetry import trace
        from ydb.opentelemetry.plugin import _set_error_on_span

        raw_span = trace.get_tracer("test").start_span("x")
        _set_error_on_span(raw_span, ValueError("bad"))
        raw_span.end()

        finished = otel_setup.get_finished_spans()[0]
        assert finished.attributes["error.type"] == "ValueError"

    def test_tracing_plugin_attach_context_without_end_on_exit(self, otel_setup):
        from opentelemetry import trace
        from ydb.opentelemetry.plugin import TracingSpan

        raw_span = trace.get_tracer("test").start_span("x")
        wrapper = TracingSpan(raw_span)
        with wrapper.attach_context(end_on_exit=False):
            pass

        assert len(otel_setup.get_finished_spans()) == 0
        wrapper.end()
        assert len(otel_setup.get_finished_spans()) == 1


class TestQuerySessionPoolMetricsInstrumentation:
    @staticmethod
    def _counted_session(pool_name="session-pool", async_=False):
        QuerySession = AsyncQuerySession if async_ else SyncQuerySession
        session = QuerySession(MagicMock())
        session._session_id = "session-1"
        session._session_metrics.pool_name = pool_name
        session._session_metrics.count_open()
        return session

    @staticmethod
    def _failing_status_stream():
        raise RuntimeError("transport error")
        yield

    def test_query_session_init_metrics_defaults(self):
        from ydb.query.session import QuerySession

        session = QuerySession(MagicMock())
        assert session._session_metrics.pool_name is None
        assert session._session_metrics.state == "used"
        assert session._session_metrics._counted is False

    def test_sync_pool_acquire_from_queue_updates_session_count(self, metrics_setup):
        from ydb.observability.metrics import QUERY_SESSION_COUNT, SessionMetrics
        from ydb.query.pool import QuerySessionPool

        pool = QuerySessionPool(driver=MagicMock(), size=2, name="sync-pool")
        session = MagicMock()
        session.is_active = True
        session.session_id = "session-1"
        session._session_metrics = SessionMetrics()
        session._session_metrics.state = "idle"
        pool._queue.put_nowait(session)

        acquired = pool.acquire()
        assert acquired is session

        metric = _metrics_by_name(metrics_setup)[QUERY_SESSION_COUNT]
        values = {tuple(sorted(point.attributes.items())): point.value for point in metric.data.data_points}
        assert values[(("ydb.query.session.pool.name", "sync-pool"), ("ydb.query.session.state", "used"))] == 1
        assert values[(("ydb.query.session.pool.name", "sync-pool"), ("ydb.query.session.state", "idle"))] == -1

    def test_sync_pool_release_updates_session_count(self, metrics_setup):
        from ydb.observability.metrics import QUERY_SESSION_COUNT, SessionMetrics
        from ydb.query.pool import QuerySessionPool

        pool = QuerySessionPool(driver=MagicMock(), size=2, name="sync-pool")
        session = MagicMock()
        session.session_id = "session-1"
        session._session_metrics = SessionMetrics()
        pool.release(session)

        metric = _metrics_by_name(metrics_setup)[QUERY_SESSION_COUNT]
        values = {tuple(sorted(point.attributes.items())): point.value for point in metric.data.data_points}
        assert values[(("ydb.query.session.pool.name", "sync-pool"), ("ydb.query.session.state", "idle"))] == 1
        assert values[(("ydb.query.session.pool.name", "sync-pool"), ("ydb.query.session.state", "used"))] == -1

    def test_sync_pool_acquire_timeout_records_pending_and_timeout(self, metrics_setup):
        from ydb import issues
        from ydb.observability.metrics import QUERY_SESSION_PENDING_REQUESTS, QUERY_SESSION_TIMEOUTS
        from ydb.query.pool import QuerySessionPool

        pool = QuerySessionPool(driver=MagicMock(), size=1, name="sync-pool")
        pool._current_size = 1

        with pytest.raises(issues.SessionPoolEmpty):
            pool.acquire(timeout=0.01)

        assert _single_point(metrics_setup, QUERY_SESSION_TIMEOUTS).value == 1
        assert _sum_value(metrics_setup, QUERY_SESSION_PENDING_REQUESTS) == 0

    def test_sync_pool_create_new_session_records_create_time(self, metrics_setup, monkeypatch):
        from ydb.observability.metrics import QUERY_SESSION_CREATE_TIME
        from ydb.query.pool import QuerySessionPool

        mock_session = MagicMock()
        mock_session.is_active = True
        mock_session.session_id = "new-session"
        mock_session.create = MagicMock()

        pool = QuerySessionPool(driver=MagicMock(), size=2, name="sync-pool")
        monkeypatch.setattr("ydb.query.pool.QuerySession", lambda *args, **kwargs: mock_session)

        acquired = pool.acquire()
        assert acquired is mock_session
        assert _histogram_sum(metrics_setup, QUERY_SESSION_CREATE_TIME) >= 0

    def test_sync_session_create_increments_session_count(self, metrics_setup, monkeypatch):
        from tests.observability.conftest import FakeDriverConfig
        from ydb.observability.metrics import QUERY_SESSION_COUNT, SessionMetrics
        from ydb.query.session import QuerySession

        qs = QuerySession.__new__(QuerySession)
        qs._driver = MagicMock()
        qs._driver._driver_config = FakeDriverConfig()
        qs._session_id = None
        qs._closed = False
        qs._invalidated = False
        qs._session_metrics = SessionMetrics()
        qs._session_metrics.pool_name = "session-pool"
        qs._stream = None

        @contextmanager
        def fake_span_ctx(**kwargs):
            yield MagicMock()

        monkeypatch.setattr(
            "ydb.query.session.create_ydb_span", lambda *args, **kwargs: MagicMock(attach_context=fake_span_ctx)
        )
        monkeypatch.setattr(qs, "_create_call", MagicMock())
        monkeypatch.setattr(qs, "_attach", MagicMock(side_effect=qs._session_metrics.count_open))

        qs.create()
        assert qs._session_metrics._counted
        assert _single_point(metrics_setup, QUERY_SESSION_COUNT).attributes["ydb.query.session.state"] == "used"

    def test_sync_session_close_decrements_session_count(self, metrics_setup):
        from ydb.observability.metrics import QUERY_SESSION_COUNT, SessionMetrics
        from ydb.query.session import QuerySession

        qs = QuerySession.__new__(QuerySession)
        qs._closed = False
        qs._invalidated = False
        qs._session_metrics = SessionMetrics()
        qs._session_metrics.pool_name = "session-pool"
        qs._session_metrics._counted = True
        qs._stream = None

        qs._close_session()
        assert not qs._session_metrics._counted
        assert _sum_value(metrics_setup, QUERY_SESSION_COUNT) == -1

    @pytest.mark.asyncio
    @pytest.mark.parametrize("async_", [False, True], ids=["sync", "async"])
    async def test_pool_graceful_shutdown_records_closed_session(self, metrics_setup, async_):
        QuerySessionPool = AsyncQuerySessionPool if async_ else SyncQuerySessionPool
        pool_name = "async-pool" if async_ else "sync-pool"
        pool = QuerySessionPool(driver=MagicMock(), size=2, name=pool_name)
        session = self._counted_session(pool_name, async_=async_)
        session._delete_call = AsyncMock() if async_ else MagicMock()
        pool._queue.put_nowait(session)

        if async_:
            await pool.stop()
        else:
            pool.stop()

        _assert_closed_metric(metrics_setup, pool_name, "pool_graceful_shutdown")

    @pytest.mark.parametrize(
        ("hint", "reason"),
        [
            ("node_shutdown", "node_shutdown"),
            ("session_shutdown", "session_shutdown"),
        ],
    )
    def test_server_shutdown_hint_records_closed_session(self, metrics_setup, hint, reason):
        session = self._counted_session("sync-pool")
        hint_type = {
            "node_shutdown": ydb_query_pb2.NodeShutdownHint,
            "session_shutdown": ydb_query_pb2.SessionShutdownHint,
        }[hint]
        response = ydb_query_pb2.SessionState(status=0, **{hint: hint_type()})

        session._handle_attach_session_state(response)
        session._handle_attach_session_state(response)

        _assert_closed_metric(metrics_setup, "sync-pool", reason)

    @pytest.mark.parametrize(
        ("async_", "error", "reason"),
        [
            (False, None, "attach_closed"),
            (False, RuntimeError("transport error"), "transport_error"),
            (True, None, "attach_closed"),
            (True, RuntimeError("transport error"), "transport_error"),
        ],
    )
    @pytest.mark.asyncio
    async def test_attach_stream_end_records_closed_session(self, metrics_setup, async_, error, reason):
        pool_name = "async-pool" if async_ else "sync-pool"
        session = self._counted_session(pool_name, async_=async_)

        if async_:
            session._status_stream = MagicMock()
            if error is None:
                session._status_stream.__aiter__.return_value = []
            else:
                session._status_stream.__aiter__.side_effect = error
            await session._check_session_status_loop()
        else:
            status_stream = iter(()) if error is None else self._failing_status_stream()
            session._check_session_status_loop(status_stream)

        _assert_closed_metric(metrics_setup, pool_name, reason)

    @pytest.mark.parametrize(
        ("status", "reason"),
        [
            (issues.StatusCode.BAD_SESSION, "bad_session"),
            (issues.StatusCode.SESSION_EXPIRED, "bad_session"),
            (issues.StatusCode.SESSION_BUSY, "session_busy"),
            (issues.StatusCode.UNAVAILABLE, "transport_error"),
        ],
    )
    def test_attach_stream_status_records_closed_session(self, metrics_setup, status, reason):
        session = self._counted_session("sync-pool")

        session._check_session_status_loop(iter([ServerStatus(status, [])]))

        _assert_closed_metric(metrics_setup, "sync-pool", reason)

    @pytest.mark.parametrize("case", ["attach_status_error", "non_terminal_query_error", "no_client_pool"])
    def test_session_close_not_reported_without_matching_pool_lifecycle(self, metrics_setup, case):
        session = self._counted_session(None if case == "no_client_pool" else "sync-pool")
        if case == "attach_status_error":
            session._check_session_status_loop(iter([ServerStatus(issues.StatusCode.BAD_REQUEST, [])]))
        elif case == "non_terminal_query_error":
            session._on_execute_stream_error(issues.BadRequest("invalid query"))
        else:
            session._check_session_status_loop(iter(()))

        assert session.is_active == (case == "non_terminal_query_error")
        assert _points(metrics_setup, QUERY_SESSION_CLOSED) == []

    @pytest.mark.parametrize(
        ("error", "reason"),
        [
            (issues.DeadlineExceed("deadline"), "client_timeout"),
            (issues.Cancelled("cancelled"), "client_cancelled"),
            (asyncio.CancelledError("cancelled"), "client_cancelled"),
            (issues.SessionBusy("busy"), "session_busy"),
            (issues.BadSession("bad session"), "bad_session"),
            (issues.SessionExpired("expired"), "bad_session"),
            (issues.Unavailable("unavailable"), "transport_error"),
            (issues.ConnectionError("connection error"), "transport_error"),
            (RuntimeError("transport error"), "transport_error"),
        ],
    )
    def test_execute_stream_terminal_error_records_closed_session_once(self, metrics_setup, error, reason):
        session = self._counted_session("sync-pool")

        session._on_execute_stream_error(error)
        session._check_session_status_loop(iter(()))
        session._handle_attach_session_state(
            ydb_query_pb2.SessionState(status=0, session_shutdown=ydb_query_pb2.SessionShutdownHint())
        )
        session._check_session_status_loop(self._failing_status_stream())

        assert session.is_closed
        _assert_closed_metric(metrics_setup, "sync-pool", reason)

    @pytest.mark.parametrize("iterator_type", ["sync", "async"])
    @pytest.mark.parametrize("finished", [False, True])
    def test_explicit_query_stream_cancel_records_only_unfinished_session(self, metrics_setup, iterator_type, finished):
        ResponseContextIterator = (
            SyncResponseContextIterator if iterator_type == "sync" else AsyncResponseContextIterator
        )
        session = self._counted_session("sync-pool")
        iterator = ResponseContextIterator(
            MagicMock(),
            MagicMock(),
            on_error=session._on_execute_stream_error,
            on_finish=MagicMock(),
        )
        iterator.it = MagicMock()

        if finished:
            iterator._call_on_finish()
        iterator.cancel()
        iterator.cancel()

        if finished:
            assert session.is_active
            assert _points(metrics_setup, QUERY_SESSION_CLOSED) == []
            return

        _assert_closed_metric(metrics_setup, "sync-pool", "client_cancelled")

    @pytest.mark.parametrize("error_type", [issues.BadSession, issues.SessionExpired])
    def test_bad_session_response_records_bad_session_once(self, metrics_setup, error_type):
        session = self._counted_session("sync-pool")

        @bad_session_handler
        def fail(rpc_state, response_pb, query_session):
            raise error_type("bad session")

        with pytest.raises(error_type) as error:
            fail(None, None, session)
        session._on_execute_stream_error(error.value)

        _assert_closed_metric(metrics_setup, "sync-pool", "bad_session")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("async_", [False, True], ids=["sync", "async"])
    async def test_initial_attach_error_does_not_record_closed_session(self, metrics_setup, monkeypatch, async_):
        QuerySession = AsyncQuerySession if async_ else SyncQuerySession
        pool_name = "async-pool" if async_ else "sync-pool"
        session = QuerySession(MagicMock())
        session._session_id = "session-1"
        session._session_metrics.pool_name = pool_name
        mock_type = AsyncMock if async_ else MagicMock
        session._attach_call = mock_type(return_value=MagicMock())
        first_response = mock_type(side_effect=RuntimeError("initial attach error"))
        module = "ydb.aio.query.session" if async_ else "ydb.query.session"
        monkeypatch.setattr(module + "._utilities.get_first_message_with_timeout", first_response)

        with pytest.raises(RuntimeError, match="initial attach error"):
            if async_:
                await session._attach()
            else:
                session._attach()

        assert session.is_closed
        assert _points(metrics_setup, QUERY_SESSION_CLOSED) == []

    @pytest.mark.asyncio
    async def test_async_pool_acquire_from_queue_updates_session_count(self, metrics_setup):
        from ydb.aio.query.pool import QuerySessionPool
        from ydb.observability.metrics import QUERY_SESSION_COUNT

        pool = QuerySessionPool(driver=MagicMock(), size=2, name="async-pool")
        session = MagicMock()
        session.is_active = True
        session.session_id = "session-1"
        pool._queue.put_nowait(session)

        acquired = await pool.acquire()
        assert acquired is session

        metric = _metrics_by_name(metrics_setup)[QUERY_SESSION_COUNT]
        values = {tuple(sorted(point.attributes.items())): point.value for point in metric.data.data_points}
        assert values[(("ydb.query.session.pool.name", "async-pool"), ("ydb.query.session.state", "used"))] == 1

    @pytest.mark.asyncio
    async def test_async_pool_release_updates_session_count(self, metrics_setup):
        from ydb.aio.query.pool import QuerySessionPool
        from ydb.observability.metrics import QUERY_SESSION_COUNT

        pool = QuerySessionPool(driver=MagicMock(), size=2, name="async-pool")
        session = MagicMock()
        session.session_id = "session-1"
        await pool.release(session)

        metric = _metrics_by_name(metrics_setup)[QUERY_SESSION_COUNT]
        values = {tuple(sorted(point.attributes.items())): point.value for point in metric.data.data_points}
        assert values[(("ydb.query.session.pool.name", "async-pool"), ("ydb.query.session.state", "idle"))] == 1

    @pytest.mark.asyncio
    async def test_async_pool_acquire_timeout_records_timeout(self, metrics_setup):
        from ydb import issues
        from ydb.aio.query.pool import QuerySessionPool
        from ydb.observability.metrics import QUERY_SESSION_TIMEOUTS

        pool = QuerySessionPool(driver=MagicMock(), size=1, name="async-pool")
        pool._current_size = 1

        with pytest.raises(issues.SessionPoolEmpty):
            await pool.acquire(timeout=0.01)

        assert _single_point(metrics_setup, QUERY_SESSION_TIMEOUTS).value == 1

    @pytest.mark.asyncio
    async def test_async_pool_create_new_session_records_create_time(self, metrics_setup, monkeypatch):
        from ydb.aio.query.pool import QuerySessionPool
        from ydb.observability.metrics import QUERY_SESSION_CREATE_TIME

        mock_session = MagicMock()
        mock_session.is_active = True
        mock_session.session_id = "new-session"
        mock_session.create = AsyncMock()

        pool = QuerySessionPool(driver=MagicMock(), size=2, name="async-pool")
        monkeypatch.setattr("ydb.aio.query.pool.QuerySession", lambda *args, **kwargs: mock_session)

        acquired = await pool.acquire()
        assert acquired is mock_session
        assert _histogram_sum(metrics_setup, QUERY_SESSION_CREATE_TIME) >= 0

    @pytest.mark.asyncio
    async def test_async_session_create_increments_session_count(self, metrics_setup, monkeypatch):
        from tests.observability.conftest import FakeDriverConfig
        from ydb.aio.query.session import QuerySession
        from ydb.observability.metrics import QUERY_SESSION_COUNT, SessionMetrics

        qs = QuerySession.__new__(QuerySession)
        qs._driver = MagicMock()
        qs._driver._driver_config = FakeDriverConfig()
        qs._session_id = None
        qs._closed = False
        qs._invalidated = False
        qs._session_metrics = SessionMetrics()
        qs._session_metrics.pool_name = "async-session-pool"
        qs._stream = None
        qs._status_stream = None
        qs._loop = __import__("asyncio").get_running_loop()

        @contextmanager
        def fake_span_ctx(**kwargs):
            yield MagicMock()

        monkeypatch.setattr(
            "ydb.aio.query.session.create_ydb_span", lambda *args, **kwargs: MagicMock(attach_context=fake_span_ctx)
        )
        monkeypatch.setattr(qs, "_create_call", AsyncMock())
        monkeypatch.setattr(qs, "_attach", AsyncMock(side_effect=qs._session_metrics.count_open))

        await qs.create()
        assert qs._session_metrics._counted
        assert _single_point(metrics_setup, QUERY_SESSION_COUNT).value == 1
