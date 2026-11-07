import asyncio
import inspect
import time
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call

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


def _points_for_pool(reader, name, pool_name):
    return [
        point for point in _points(reader, name) if point.attributes.get("ydb.query.session.pool.name") == pool_name
    ]


def _single_point_for_pool(reader, name, pool_name):
    points = _points_for_pool(reader, name, pool_name)
    assert len(points) == 1
    return points[0]


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


def _topic_reader_batch(message_count, topic, partition_session_id=1, reader_stream_id=1):
    return SimpleNamespace(
        messages=[object()] * message_count,
        _partition_session=SimpleNamespace(
            topic_path=topic,
            id=partition_session_id,
            reader_stream_id=reader_stream_id,
        ),
    )


def _topic_reader_partition_session(topic, partition_session_id, reader_stream_id, committed_offset=0):
    return SimpleNamespace(
        topic_path=topic,
        id=partition_session_id,
        reader_stream_id=reader_stream_id,
        committed_offset=committed_offset,
    )


def _topic_read_response(partition_messages, bytes_size=30):
    import datetime

    from ydb._grpc.grpcwrapper.ydb_topic import Codec, StreamReadMessage

    now = datetime.datetime(2023, 2, 3, 14, 15)
    return StreamReadMessage.ReadResponse(
        partition_data=[
            StreamReadMessage.ReadResponse.PartitionData(
                partition_session_id=partition_session_id,
                batches=[
                    StreamReadMessage.ReadResponse.Batch(
                        message_data=[
                            StreamReadMessage.ReadResponse.MessageData(
                                offset=offset,
                                seq_no=offset + 1,
                                created_at=now,
                                data=("message-%d" % offset).encode(),
                                metadata_items={},
                                uncompresed_size=10,
                                message_group_id="group",
                            )
                            for offset in range(message_count)
                        ],
                        producer_id="producer",
                        write_session_meta={},
                        codec=Codec.CODEC_RAW,
                        written_at=now,
                    )
                ],
            )
            for partition_session_id, message_count in partition_messages
        ],
        bytes_size=bytes_size,
    )


async def _decode_pending_topic_batches(stream):
    while not stream._batches_to_decode.empty():
        batch = stream._batches_to_decode.get_nowait()
        await stream._decode_batch_inplace(batch)
        stream._add_batch_to_queue(batch)
    stream._state_changed.set()


def _histogram_boundaries_advisory_supported():
    return "explicit_bucket_boundaries_advisory" in inspect.signature(Meter.create_histogram).parameters


def test_metrics_build_info_version(metrics_setup):
    from ydb.observability.metrics import _metrics_build_info_tokens

    assert _metrics_build_info_tokens() == ["ydb-sdk-metrics/0.14.0"]


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
        RETRY_DURATION_BUCKETS_SECONDS,
        SessionMetrics,
        TopicReaderMetrics,
        create_metrics_operation,
        record_query_session_count,
        record_query_session_create_time,
        record_query_session_max,
        record_query_session_pending_requests,
        record_query_session_timeout,
        record_retry_metrics,
    )

    monkeypatch.setattr(
        "ydb.observability.metrics.time.monotonic",
        MagicMock(side_effect=[1.0, 1.25, 2.0, 2.5]),
    )

    with pytest.raises(issues.Unavailable):
        with create_metrics_operation("ExecuteQuery"):
            raise issues.Unavailable("transient")

    record_query_session_count(2, "main", "used")
    session_metrics = SessionMetrics()
    session_metrics.pool_name = "main"
    session_metrics.count_open()
    session_metrics.count_open()
    session_metrics.count_closed("pool_graceful_shutdown")
    record_query_session_create_time(0.5, "main")
    record_query_session_max(100, "main")
    record_query_session_pending_requests(1, "main")
    record_query_session_timeout("main")
    record_retry_metrics(0.75, 3)
    reader_metrics = TopicReaderMetrics(
        object(),
        consumer_name="analytics",
        reader_name="reader-test",
    )
    reader_metrics.record_received_messages([_topic_reader_batch(2, "/Root/events")])
    reader_metrics.record_received_bytes(128)
    reader_metrics.record_delivered_messages(2, "/Root/events")
    reader_metrics.record_compression_duration(0.01, "gzip", "/Root/events")
    reader_metrics.record_message_processing_duration(0.02, "gzip", "/Root/events")
    reader_metrics.record_commit_queued(2, "/Root/events")
    reader_metrics.record_commit_acknowledged(2, "/Root/events")
    reader_metrics.record_session_error(issues.Unavailable("retry"), True)
    reader_metrics.reset_credit_balance_bytes(1024)
    partition_session = _topic_reader_partition_session("/Root/events", 1, 1)
    reader_metrics.add_partition_session("/Root/events", partition_session)
    reader_metrics.record_commit_offset_queued(partition_session, 2)

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
    assert metrics[TOPIC_READER_COMMIT_ACKNOWLEDGED].unit == "{message}"
    assert metrics[TOPIC_READER_COMMIT_OFFSET_LAG_MAX].unit == "{message}"
    assert metrics[TOPIC_READER_COMMIT_QUEUED].unit == "{message}"
    assert metrics[TOPIC_READER_COMPRESSION_DURATION].unit == "s"
    assert metrics[TOPIC_READER_CREDIT_BALANCE_BYTES].unit == "By"
    assert metrics[TOPIC_READER_DELIVERED_MESSAGES].unit == "{message}"
    assert metrics[TOPIC_READER_LOCAL_BUFFER_MESSAGE_AGE_MAX].unit == "s"
    assert metrics[TOPIC_READER_LOCAL_BUFFER_MESSAGES].unit == "{message}"
    assert metrics[TOPIC_READER_MESSAGE_PROCESSING_DURATION].unit == "s"
    assert metrics[TOPIC_READER_PARTITION_SESSION_COUNT].unit == "{session}"
    assert metrics[TOPIC_READER_RECEIVED_MESSAGES].unit == "{message}"
    assert metrics[TOPIC_READER_RECEIVED_BYTES].unit == "By"
    assert metrics[TOPIC_READER_SESSION_ERRORS].unit == "{error}"
    assert metrics[TOPIC_READER_CREDIT_BALANCE_BYTES].data.__class__.__name__ == "Gauge"
    assert metrics[TOPIC_READER_COMMIT_OFFSET_LAG_MAX].data.__class__.__name__ == "Gauge"
    assert metrics[TOPIC_READER_LOCAL_BUFFER_MESSAGE_AGE_MAX].data.__class__.__name__ == "Gauge"
    assert metrics[TOPIC_READER_PARTITION_SESSION_COUNT].data.__class__.__name__ == "Sum"
    if _histogram_boundaries_advisory_supported():
        assert (
            _single_point_from_metrics(metrics, CLIENT_OPERATION_DURATION).explicit_bounds == DURATION_BUCKETS_SECONDS
        )
        assert (
            _single_point_from_metrics(metrics, QUERY_SESSION_CREATE_TIME).explicit_bounds == DURATION_BUCKETS_SECONDS
        )
        assert _single_point_from_metrics(metrics, RETRY_DURATION).explicit_bounds == RETRY_DURATION_BUCKETS_SECONDS
        assert _single_point_from_metrics(metrics, RETRY_ATTEMPTS).explicit_bounds == ATTEMPT_BUCKETS
        assert (
            _single_point_from_metrics(metrics, TOPIC_READER_COMPRESSION_DURATION).explicit_bounds
            == DURATION_BUCKETS_SECONDS
        )
        assert (
            _single_point_from_metrics(metrics, TOPIC_READER_MESSAGE_PROCESSING_DURATION).explicit_bounds
            == DURATION_BUCKETS_SECONDS
        )


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

        def create_observable_gauge(self, name, callbacks=None, unit="", description=""):
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


def test_metrics_registry_is_noop_without_meter(monkeypatch):
    from ydb.observability import disable_metrics
    from ydb.observability.metrics import (
        _NOOP_PROVIDER,
        _NOOP_QUERY_SESSION_POOL_METRICS,
        _NOOP_SESSION_METRICS,
        _NOOP_TOPIC_READER_METRICS,
        QuerySessionPoolMetrics,
        SessionMetrics,
        create_query_session_pool_metrics,
        create_session_metrics,
        create_metrics_operation,
        create_topic_reader_metrics,
        record_query_session_create_time,
        record_query_session_max,
        record_query_session_pending_requests,
        record_query_session_timeout,
        record_retry_metrics,
        remove_query_session_pool_metrics,
    )

    monotonic = MagicMock()
    noop_add = MagicMock()
    monkeypatch.setattr("ydb.observability.metrics.time.monotonic", monotonic)
    monkeypatch.setattr(_NOOP_PROVIDER, "add", noop_add)
    disable_metrics()

    record_query_session_create_time(1.0, "pool")
    record_query_session_max(10, "pool")
    record_query_session_pending_requests(1, "pool")
    record_query_session_timeout("pool")
    record_retry_metrics(1.0, 2)
    remove_query_session_pool_metrics("pool")

    operation = create_metrics_operation("ExecuteQuery")
    assert operation.attach_context() is operation.attach_context()
    operation.set_error(ValueError("noop"))
    operation.set_attribute("database", "/db")
    operation.end()
    with operation:
        pass
    with operation.attach_context() as attached_operation:
        assert attached_operation is operation

    pool_metrics = QuerySessionPoolMetrics("pool", object(), 10)
    session = MagicMock()
    session._session_metrics = SessionMetrics()
    pool_metrics.attach(session)
    session._session_metrics.count_open()
    pool_metrics.on_released(session)
    with pool_metrics.measure_create(), pool_metrics.track_pending():
        pass
    session._session_metrics.count_closed("client_cancelled")

    noop_session_metrics = create_session_metrics()
    assert noop_session_metrics is _NOOP_SESSION_METRICS
    noop_session_metrics.count_open()
    noop_session_metrics.count_closed("client_cancelled")
    noop_session_metrics.bind("disabled")
    noop_session_metrics.transition("idle")

    noop_pool_metrics = create_query_session_pool_metrics("disabled", object(), 10)
    assert noop_pool_metrics is _NOOP_QUERY_SESSION_POOL_METRICS
    noop_session = MagicMock()
    noop_pool_metrics.attach(noop_session)
    with noop_pool_metrics.measure_create(), noop_pool_metrics.track_pending():
        pass
    noop_pool_metrics.on_timeout()
    noop_pool_metrics.on_acquired(noop_session)
    noop_pool_metrics.on_released(noop_session)
    noop_pool_metrics.close()

    def fail_on_iteration():
        raise AssertionError("noop topic reader metrics iterated over batches")
        yield

    noop_reader_metrics = create_topic_reader_metrics(
        object(),
        consumer_name="analytics",
        reader_name="reader-test",
        topics=fail_on_iteration(),
    )
    assert noop_reader_metrics is _NOOP_TOPIC_READER_METRICS

    noop_reader_metrics.record_received_messages(fail_on_iteration())
    assert noop_reader_metrics.capture_received_at() is None
    noop_reader_metrics.record_received_bytes(10)
    noop_reader_metrics.record_delivered_messages(1, "/Root/events")
    noop_reader_metrics.record_compression_duration(0.01, "gzip", "/Root/events")
    noop_reader_metrics.record_message_processing_duration(0.02, "gzip", "/Root/events")
    noop_reader_metrics.record_commit_queued(1, "/Root/events")
    noop_reader_metrics.record_commit_acknowledged(1, "/Root/events")
    noop_reader_metrics.record_commit_offset_queued(object(), 1)
    noop_reader_metrics.record_commit_offset_acknowledged(object(), 1)
    noop_reader_metrics.record_session_error(RuntimeError("ignored"), True)
    noop_reader_metrics.add_credit_balance_bytes(-10)
    noop_reader_metrics.reset_credit_balance_bytes(10)
    noop_reader_metrics.remove_local_buffer_messages(1, object())
    noop_reader_metrics.reset_local_buffer_messages()
    noop_reader_metrics.add_partition_session("/Root/events")
    noop_reader_metrics.remove_partition_session("/Root/events")
    noop_reader_metrics.reset_partition_sessions()
    noop_reader_metrics.close()

    assert not monotonic.called
    assert not noop_add.called
    pool_metrics.close()
    pool_metrics.close()


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


def test_metrics_operation_context_records_duration(metrics_setup):
    from ydb.observability.metrics import CLIENT_OPERATION_DURATION, create_metrics_operation

    with create_metrics_operation("ExecuteQuery"):
        pass

    assert _single_point(metrics_setup, CLIENT_OPERATION_DURATION).count == 1


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
    from ydb.observability.metrics import CLIENT_OPERATION_DURATION, MetricsOperation
    from ydb.observability.tracing import create_ydb_span

    disable_tracing()

    operation = create_ydb_span("ydb.ExecuteQuery", FakeDriverConfig())
    assert isinstance(operation, MetricsOperation)

    with operation.attach_context():
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

    pool = QuerySessionPool(driver=object(), size=42, name="sync-pool")

    assert _single_point(metrics_setup, QUERY_SESSION_MAX).value == 42
    assert _single_point(metrics_setup, QUERY_SESSION_MAX).attributes == {"ydb.query.session.pool.name": "sync-pool"}
    assert _single_point(metrics_setup, QUERY_SESSION_MIN).value == 0
    assert _single_point(metrics_setup, QUERY_SESSION_MIN).attributes == {"ydb.query.session.pool.name": "sync-pool"}
    pool.stop()


def test_duplicate_query_session_pool_name_uses_latest_size(metrics_setup):
    from ydb.observability.metrics import QUERY_SESSION_MAX, QuerySessionPoolMetrics

    first = QuerySessionPoolMetrics("shared", object(), 10)
    second = QuerySessionPoolMetrics("shared", object(), 20)

    try:
        assert _single_point_for_pool(metrics_setup, QUERY_SESSION_MAX, "shared").value == 20
        second.close()
        assert _single_point_for_pool(metrics_setup, QUERY_SESSION_MAX, "shared").value == 10
    finally:
        first.close()
        second.close()


def test_sync_query_session_pool_stop_removes_observable_metrics(metrics_setup):
    from ydb.observability.metrics import QUERY_SESSION_COUNT, QUERY_SESSION_MAX, QUERY_SESSION_MIN
    from ydb.query.pool import QuerySessionPool

    pool = QuerySessionPool(driver=object(), size=42, name="sync-pool")
    pool.stop()

    assert _points_for_pool(metrics_setup, QUERY_SESSION_COUNT, "sync-pool") == []
    assert _points_for_pool(metrics_setup, QUERY_SESSION_MAX, "sync-pool") == []
    assert _points_for_pool(metrics_setup, QUERY_SESSION_MIN, "sync-pool") == []


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

    pool = QuerySessionPool(driver=FakeDriver(), size=42)

    assert _single_point(metrics_setup, QUERY_SESSION_MAX).value == 42
    assert _single_point(metrics_setup, QUERY_SESSION_MAX).attributes == {
        "ydb.query.session.pool.name": "grpc://localhost:2136/local"
    }
    pool.stop()


@pytest.mark.asyncio
async def test_async_query_session_pool_records_max(metrics_setup):
    from ydb.aio.query.pool import QuerySessionPool
    from ydb.observability.metrics import QUERY_SESSION_MAX, QUERY_SESSION_MIN

    pool = QuerySessionPool(driver=object(), size=24, name="async-pool")

    assert _single_point(metrics_setup, QUERY_SESSION_MAX).value == 24
    assert _single_point(metrics_setup, QUERY_SESSION_MAX).attributes == {"ydb.query.session.pool.name": "async-pool"}
    assert _single_point(metrics_setup, QUERY_SESSION_MIN).value == 0
    assert _single_point(metrics_setup, QUERY_SESSION_MIN).attributes == {"ydb.query.session.pool.name": "async-pool"}
    await pool.stop()


@pytest.mark.asyncio
async def test_async_query_session_pool_stop_removes_observable_metrics(metrics_setup):
    from ydb.aio.query.pool import QuerySessionPool
    from ydb.observability.metrics import QUERY_SESSION_COUNT, QUERY_SESSION_MAX, QUERY_SESSION_MIN

    pool = QuerySessionPool(driver=object(), size=24, name="async-pool")
    await pool.stop()

    assert _points_for_pool(metrics_setup, QUERY_SESSION_COUNT, "async-pool") == []
    assert _points_for_pool(metrics_setup, QUERY_SESSION_MAX, "async-pool") == []
    assert _points_for_pool(metrics_setup, QUERY_SESSION_MIN, "async-pool") == []


@pytest.mark.asyncio
async def test_async_query_session_pool_uses_connection_string_as_default_pool_name(metrics_setup):
    from tests.observability.conftest import FakeDriverConfig
    from ydb.aio.query.pool import QuerySessionPool
    from ydb.observability.metrics import QUERY_SESSION_MAX

    class FakeDriver:
        _driver_config = FakeDriverConfig(endpoint="grpc://localhost:2136", database="/local")

    pool = QuerySessionPool(driver=FakeDriver(), size=24)

    assert _single_point(metrics_setup, QUERY_SESSION_MAX).value == 24
    assert _single_point(metrics_setup, QUERY_SESSION_MAX).attributes == {
        "ydb.query.session.pool.name": "grpc://localhost:2136/local"
    }
    await pool.stop()


@pytest.mark.asyncio
async def test_sync_and_async_query_session_pool_auto_names_do_not_collide(metrics_setup):
    from ydb.aio.query.pool import QuerySessionPool as AsyncQuerySessionPool
    from ydb.observability.metrics import QUERY_SESSION_MAX
    from ydb.query.pool import QuerySessionPool

    sync_pool = QuerySessionPool(driver=object(), size=42)
    async_pool = AsyncQuerySessionPool(driver=object(), size=24)

    metric = _metrics_by_name(metrics_setup)[QUERY_SESSION_MAX]
    values = {point.attributes["ydb.query.session.pool.name"]: point.value for point in metric.data.data_points}

    assert len(values) == 2
    assert sorted(values.values()) == [24, 42]
    sync_pool.stop()
    await async_pool.stop()


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

    def test_enable_metrics_does_not_retrofit_existing_pool(self):
        from ydb.observability.metrics import (
            QUERY_SESSION_MAX,
            _NOOP_QUERY_SESSION_POOL_METRICS,
            _NOOP_SESSION_METRICS,
        )
        from ydb.opentelemetry import disable_metrics, enable_metrics
        from ydb.query.pool import QuerySessionPool
        from ydb.query.session import QuerySession

        disable_metrics()
        pool = QuerySessionPool(driver=object(), size=3, name="late-enable")
        assert pool._metrics is _NOOP_QUERY_SESSION_POOL_METRICS

        reader = InMemoryMetricReader()
        provider = MeterProvider(metric_readers=[reader])
        try:
            enable_metrics(provider)
            session = QuerySession(MagicMock())
            assert session._session_metrics is not _NOOP_SESSION_METRICS
            pool._metrics.attach(session)
            assert session._session_metrics is _NOOP_SESSION_METRICS
            assert _points_for_pool(reader, QUERY_SESSION_MAX, "late-enable") == []
        finally:
            pool.stop()
            disable_metrics()
            provider.shutdown()

    @pytest.mark.asyncio
    async def test_enable_metrics_does_not_retrofit_existing_async_pool(self):
        from ydb.aio.query.pool import QuerySessionPool
        from ydb.observability.metrics import (
            QUERY_SESSION_MAX,
            _NOOP_QUERY_SESSION_POOL_METRICS,
        )
        from ydb.opentelemetry import disable_metrics, enable_metrics

        disable_metrics()
        pool = QuerySessionPool(driver=object(), size=3, name="late-enable-async")
        assert pool._metrics is _NOOP_QUERY_SESSION_POOL_METRICS

        reader = InMemoryMetricReader()
        provider = MeterProvider(metric_readers=[reader])
        try:
            enable_metrics(provider)
            assert _points_for_pool(reader, QUERY_SESSION_MAX, "late-enable-async") == []
        finally:
            await pool.stop()
            disable_metrics()
            provider.shutdown()

    def test_instrumented_pool_upgrades_sessions_created_while_temporarily_disabled(self):
        from ydb.observability.metrics import (
            _NOOP_SESSION_METRICS,
            SessionMetrics,
            create_query_session_pool_metrics,
            create_session_metrics,
        )
        from ydb.opentelemetry import disable_metrics, enable_metrics

        provider = MeterProvider(metric_readers=[InMemoryMetricReader()])
        enable_metrics(provider)
        pool_metrics = create_query_session_pool_metrics("temporarily-disabled", object(), 2)
        disable_metrics()

        session = MagicMock()
        session._session_metrics = create_session_metrics()
        assert session._session_metrics is _NOOP_SESSION_METRICS

        try:
            pool_metrics.attach(session)
            assert isinstance(session._session_metrics, SessionMetrics)
            assert session._session_metrics is not _NOOP_SESSION_METRICS
            assert session._session_metrics.pool_name == "temporarily-disabled"
        finally:
            pool_metrics.close()
            disable_metrics()
            provider.shutdown()

    def test_reconfigure_metrics_quiesces_old_gauge_callbacks(self):
        from ydb.observability.metrics import (
            QUERY_SESSION_COUNT,
            create_query_session_pool_metrics,
            create_session_metrics,
        )
        from ydb.opentelemetry import disable_metrics, enable_metrics

        first_reader = InMemoryMetricReader()
        first_provider = MeterProvider(metric_readers=[first_reader])
        second_reader = InMemoryMetricReader()
        second_provider = MeterProvider(metric_readers=[second_reader])

        disable_metrics()
        enable_metrics(first_provider)
        pool_metrics = create_query_session_pool_metrics("reconfigured", object(), 2)
        session = MagicMock()
        session._session_metrics = create_session_metrics()
        pool_metrics.attach(session)
        session._session_metrics.count_open()
        try:
            assert (
                _single_point_for_pool(first_reader, QUERY_SESSION_COUNT, "reconfigured").attributes[
                    "ydb.query.session.state"
                ]
                == "used"
            )

            disable_metrics()
            pool_metrics.on_released(session)
            enable_metrics(second_provider)

            assert _points(first_reader, QUERY_SESSION_COUNT) == []
            second_point = _single_point_for_pool(second_reader, QUERY_SESSION_COUNT, "reconfigured")
            assert second_point.value == 1
            assert second_point.attributes["ydb.query.session.state"] == "idle"
        finally:
            session._session_metrics.count_closed()
            pool_metrics.close()
            disable_metrics()
            first_provider.shutdown()
            second_provider.shutdown()

    def test_topic_reader_gauges_keep_state_while_metrics_are_reconfigured(self, monkeypatch):
        from ydb.observability.metrics import (
            TOPIC_READER_COMMIT_OFFSET_LAG_MAX,
            TOPIC_READER_CREDIT_BALANCE_BYTES,
            TOPIC_READER_LOCAL_BUFFER_MESSAGE_AGE_MAX,
            TOPIC_READER_LOCAL_BUFFER_MESSAGES,
            TOPIC_READER_PARTITION_SESSION_COUNT,
            create_topic_reader_metrics,
        )
        from ydb.opentelemetry import disable_metrics, enable_metrics

        first_reader = InMemoryMetricReader()
        first_provider = MeterProvider(metric_readers=[first_reader])
        second_reader = InMemoryMetricReader()
        second_provider = MeterProvider(metric_readers=[second_reader])

        disable_metrics()
        enable_metrics(first_provider)
        reader_metrics = create_topic_reader_metrics(object(), consumer_name=None, reader_name="reconfigured")
        first_batch = _topic_reader_batch(2, "/Root/events")
        reader_metrics.record_received_messages(
            [first_batch],
            received_at=10.0,
        )
        reader_metrics.reset_credit_balance_bytes(100)
        partition_session = _topic_reader_partition_session("/Root/events", 1, 1)
        reader_metrics.add_partition_session("/Root/events", partition_session)
        reader_metrics.record_commit_offset_queued(partition_session, 5)
        monkeypatch.setattr("ydb.observability.metrics.time.monotonic", MagicMock(return_value=30.0))
        try:
            assert _single_point(first_reader, TOPIC_READER_LOCAL_BUFFER_MESSAGES).value == 2
            assert _single_point(first_reader, TOPIC_READER_LOCAL_BUFFER_MESSAGE_AGE_MAX).value == 20.0
            assert _single_point(first_reader, TOPIC_READER_PARTITION_SESSION_COUNT).value == 1
            assert _single_point(first_reader, TOPIC_READER_CREDIT_BALANCE_BYTES).value == 100
            assert _single_point(first_reader, TOPIC_READER_COMMIT_OFFSET_LAG_MAX).value == 5

            disable_metrics()
            second_batch = _topic_reader_batch(3, "/Root/events")
            reader_metrics.record_received_messages(
                [second_batch],
                received_at=20.0,
            )
            reader_metrics.remove_local_buffer_messages(1, first_batch._partition_session)
            reader_metrics.add_credit_balance_bytes(-20)
            reader_metrics.record_commit_offset_acknowledged(partition_session, 2)
            reader_metrics.add_partition_session("/Root/events")
            enable_metrics(second_provider)

            assert _points(first_reader, TOPIC_READER_LOCAL_BUFFER_MESSAGES) == []
            assert _points(first_reader, TOPIC_READER_COMMIT_OFFSET_LAG_MAX) == []
            assert _single_point(second_reader, TOPIC_READER_LOCAL_BUFFER_MESSAGES).value == 4
            assert _single_point(second_reader, TOPIC_READER_LOCAL_BUFFER_MESSAGE_AGE_MAX).value == 20.0
            assert _single_point(second_reader, TOPIC_READER_PARTITION_SESSION_COUNT).value == 2
            assert _single_point(second_reader, TOPIC_READER_CREDIT_BALANCE_BYTES).value == 80
            assert _single_point(second_reader, TOPIC_READER_COMMIT_OFFSET_LAG_MAX).value == 3
        finally:
            reader_metrics.close()
            disable_metrics()
            first_provider.shutdown()
            second_provider.shutdown()

    def test_gauge_callback_drops_snapshot_if_provider_changes_during_collection(self):
        from ydb.observability import disable_metrics, enable_metrics
        from ydb.observability import metrics

        first_provider = MagicMock()
        second_provider = MagicMock()

        disable_metrics()
        enable_metrics(first_provider)
        generation = metrics._provider_generation

        def reconfigure_and_observe():
            enable_metrics(second_provider)
            return [(1, {"state": "stale"})]

        callback = metrics._guard_gauge_callback(first_provider, generation, reconfigure_and_observe)
        try:
            assert callback() == ()
        finally:
            disable_metrics()

    def test_opentelemetry_enable_recovers_after_vendor_neutral_disable(self):
        from ydb.observability import disable_metrics as disable_observability_metrics
        from ydb.observability.metrics import QUERY_SESSION_MAX, QuerySessionPoolMetrics
        from ydb.opentelemetry import disable_metrics, enable_metrics

        first_provider = MeterProvider(metric_readers=[InMemoryMetricReader()])
        second_reader = InMemoryMetricReader()
        second_provider = MeterProvider(metric_readers=[second_reader])
        pool_metrics = QuerySessionPoolMetrics("mixed-api", object(), 4)

        disable_metrics()
        try:
            enable_metrics(first_provider)
            disable_observability_metrics()
            enable_metrics(second_provider)

            assert _single_point_for_pool(second_reader, QUERY_SESSION_MAX, "mixed-api").value == 4
        finally:
            pool_metrics.close()
            disable_metrics()
            first_provider.shutdown()
            second_provider.shutdown()

    def test_in_flight_metrics_finish_on_their_original_provider(self):
        from ydb.observability import disable_metrics, enable_metrics
        from ydb.observability.metrics import (
            CLIENT_OPERATION_DURATION,
            QUERY_SESSION_CREATE_TIME,
            QUERY_SESSION_PENDING_REQUESTS,
            QuerySessionPoolMetrics,
            create_metrics_operation,
        )

        class RecordingProvider:
            def __init__(self):
                self.records = []
                self.adds = []

            def record(self, name, value, attributes=None):
                self.records.append((name, value, attributes))

            def add(self, name, value, attributes=None):
                self.adds.append((name, value, attributes))

            def observe_gauge(self, name, callback):
                pass

        first_provider = RecordingProvider()
        second_provider = RecordingProvider()

        disable_metrics()
        pool_metrics = QuerySessionPoolMetrics("in-flight", object(), 1)
        try:
            enable_metrics(first_provider)
            operation = create_metrics_operation("ExecuteQuery")
            with pool_metrics.measure_create(), pool_metrics.track_pending():
                enable_metrics(second_provider)
                operation.end()

            assert [record[0] for record in first_provider.records] == [
                CLIENT_OPERATION_DURATION,
                QUERY_SESSION_CREATE_TIME,
            ]
            assert [(entry[0], entry[1]) for entry in first_provider.adds] == [
                (QUERY_SESSION_PENDING_REQUESTS, 1),
                (QUERY_SESSION_PENDING_REQUESTS, -1),
            ]
            assert second_provider.records == []
            assert second_provider.adds == []
        finally:
            pool_metrics.close()
            disable_metrics()

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


def test_topic_reader_received_metrics_attributes(metrics_setup):
    from tests.observability.conftest import FakeDriverConfig
    from ydb.observability.metrics import (
        TOPIC_READER_RECEIVED_BYTES,
        TOPIC_READER_RECEIVED_MESSAGES,
        create_topic_reader_metrics,
    )

    class FakeDriver:
        _driver_config = FakeDriverConfig(
            endpoint="grpc://localhost:2136",
            database="/Root",
        )

    reader_metrics = create_topic_reader_metrics(
        FakeDriver(),
        consumer_name="analytics",
        reader_name="payments-worker",
    )
    reader_metrics.record_received_messages([_topic_reader_batch(2, "/Root/events")])
    reader_metrics.record_received_bytes(128)
    reader_metrics.record_received_messages([_topic_reader_batch(3, "/Root/events")])
    reader_metrics.record_received_bytes(256)

    expected_reader_attributes = {
        "endpoint": "localhost:2136",
        "database": "/Root",
        "consumer": "analytics",
        "reader.name": "payments-worker",
    }
    expected_message_attributes = dict(expected_reader_attributes, topic="/Root/events")
    messages = _single_point(metrics_setup, TOPIC_READER_RECEIVED_MESSAGES)
    received_bytes = _single_point(metrics_setup, TOPIC_READER_RECEIVED_BYTES)
    assert (messages.value, messages.attributes) == (5, expected_message_attributes)
    assert (received_bytes.value, received_bytes.attributes) == (384, expected_reader_attributes)


def test_topic_reader_received_messages_are_split_by_topic(metrics_setup):
    from tests.observability.conftest import FakeDriverConfig
    from ydb.observability.metrics import (
        TOPIC_READER_RECEIVED_BYTES,
        TOPIC_READER_RECEIVED_MESSAGES,
        create_topic_reader_metrics,
    )

    class FakeDriver:
        _driver_config = FakeDriverConfig(
            endpoint="grpc://localhost:2136",
            database="/Root",
        )

    reader_metrics = create_topic_reader_metrics(
        FakeDriver(),
        consumer_name="analytics",
        reader_name="payments-worker",
    )
    reader_metrics.record_received_messages(
        [
            _topic_reader_batch(2, "/Root/orders"),
            _topic_reader_batch(3, "/Root/refunds"),
            _topic_reader_batch(1, "/Root/orders"),
        ]
    )
    reader_metrics.record_received_bytes(128)

    message_points = _points(metrics_setup, TOPIC_READER_RECEIVED_MESSAGES)
    assert sorted((point.attributes["topic"], point.value) for point in message_points) == [
        ("/Root/orders", 3),
        ("/Root/refunds", 3),
    ]

    received_bytes = _single_point(metrics_setup, TOPIC_READER_RECEIVED_BYTES)
    assert received_bytes.value == 128
    assert "topic" not in received_bytes.attributes


def test_topic_reader_received_messages_are_aggregated_before_provider_calls(monkeypatch):
    from ydb.observability import metrics

    provider = MagicMock()
    monkeypatch.setattr(metrics, "_provider", provider)
    reader_metrics = metrics.TopicReaderMetrics(
        object(),
        consumer_name="analytics",
        reader_name="payments-worker",
    )
    try:
        reader_metrics.record_received_messages(
            [
                _topic_reader_batch(2, "/Root/orders"),
                _topic_reader_batch(3, "/Root/refunds"),
                _topic_reader_batch(1, "/Root/orders"),
            ]
        )
    finally:
        reader_metrics.close()

    base_attributes = {
        "endpoint": "",
        "database": "",
        "consumer": "analytics",
        "reader.name": "payments-worker",
    }
    assert provider.add.call_args_list == [
        call(
            metrics.TOPIC_READER_RECEIVED_MESSAGES,
            3,
            dict(base_attributes, topic="/Root/orders"),
        ),
        call(
            metrics.TOPIC_READER_RECEIVED_MESSAGES,
            3,
            dict(base_attributes, topic="/Root/refunds"),
        ),
    ]


def test_topic_reader_delivered_messages_are_split_by_topic(metrics_setup):
    from tests.observability.conftest import FakeDriverConfig
    from ydb.observability.metrics import (
        TOPIC_READER_DELIVERED_MESSAGES,
        create_topic_reader_metrics,
    )

    class FakeDriver:
        _driver_config = FakeDriverConfig(
            endpoint="grpc://localhost:2136",
            database="/Root",
        )

    reader_metrics = create_topic_reader_metrics(
        FakeDriver(),
        consumer_name="analytics",
        reader_name="payments-worker",
    )
    reader_metrics.record_delivered_messages(2, "/Root/orders")
    reader_metrics.record_delivered_messages(3, "/Root/refunds")
    reader_metrics.record_delivered_messages(1, "/Root/orders")
    reader_metrics.record_delivered_messages(0, "/Root/ignored")

    points = _points(metrics_setup, TOPIC_READER_DELIVERED_MESSAGES)
    values = {point.attributes["topic"]: (point.value, point.attributes) for point in points}
    assert values == {
        "/Root/orders": (
            3,
            {
                "endpoint": "localhost:2136",
                "database": "/Root",
                "consumer": "analytics",
                "reader.name": "payments-worker",
                "topic": "/Root/orders",
            },
        ),
        "/Root/refunds": (
            3,
            {
                "endpoint": "localhost:2136",
                "database": "/Root",
                "consumer": "analytics",
                "reader.name": "payments-worker",
                "topic": "/Root/refunds",
            },
        ),
    }


def test_topic_reader_processing_histograms_record_success_and_error_per_message(metrics_setup):
    from tests.observability.conftest import FakeDriverConfig
    from ydb.observability.metrics import (
        TOPIC_READER_COMPRESSION_DURATION,
        TOPIC_READER_MESSAGE_PROCESSING_DURATION,
        create_topic_reader_metrics,
    )

    class FakeDriver:
        _driver_config = FakeDriverConfig(
            endpoint="grpc://localhost:2136",
            database="/Root",
        )

    reader_metrics = create_topic_reader_metrics(
        FakeDriver(),
        consumer_name="analytics",
        reader_name="payments-worker",
    )
    error = ValueError("cannot decode")
    reader_metrics.record_compression_duration(0.01, "gzip", "/Root/orders")
    reader_metrics.record_message_processing_duration(0.04, "gzip", "/Root/orders")
    reader_metrics.record_compression_duration(0.02, "gzip", "/Root/orders", error)
    reader_metrics.record_message_processing_duration(0.06, "gzip", "/Root/orders", error)

    expected_base = {
        "endpoint": "localhost:2136",
        "database": "/Root",
        "consumer": "analytics",
        "reader.name": "payments-worker",
        "topic": "/Root/orders",
        "codec": "gzip",
    }
    compression = {
        point.attributes["outcome"]: point for point in _points(metrics_setup, TOPIC_READER_COMPRESSION_DURATION)
    }
    processing = {
        point.attributes["outcome"]: point for point in _points(metrics_setup, TOPIC_READER_MESSAGE_PROCESSING_DURATION)
    }

    assert (compression["ok"].count, compression["ok"].sum, compression["ok"].attributes) == (
        1,
        pytest.approx(0.01),
        dict(expected_base, outcome="ok"),
    )
    assert (processing["ok"].count, processing["ok"].sum, processing["ok"].attributes) == (
        1,
        pytest.approx(0.04),
        dict(expected_base, outcome="ok"),
    )
    assert (compression["error"].count, compression["error"].sum, compression["error"].attributes) == (
        1,
        pytest.approx(0.02),
        dict(expected_base, outcome="error", **{"error.type": "ValueError"}),
    )
    assert (processing["error"].count, processing["error"].sum, processing["error"].attributes) == (
        1,
        pytest.approx(0.06),
        dict(expected_base, outcome="error", **{"error.type": "ValueError"}),
    )


def test_topic_reader_commit_queued_messages_are_split_by_topic(metrics_setup):
    from tests.observability.conftest import FakeDriverConfig
    from ydb.observability.metrics import (
        TOPIC_READER_COMMIT_QUEUED,
        create_topic_reader_metrics,
    )

    class FakeDriver:
        _driver_config = FakeDriverConfig(
            endpoint="grpc://localhost:2136",
            database="/Root",
        )

    reader_metrics = create_topic_reader_metrics(
        FakeDriver(),
        consumer_name="analytics",
        reader_name="payments-worker",
    )
    reader_metrics.record_commit_queued(2, "/Root/orders")
    reader_metrics.record_commit_queued(3, "/Root/refunds")
    reader_metrics.record_commit_queued(1, "/Root/orders")
    reader_metrics.record_commit_queued(0, "/Root/ignored")

    points = _points(metrics_setup, TOPIC_READER_COMMIT_QUEUED)
    values = {point.attributes["topic"]: (point.value, point.attributes) for point in points}
    assert values == {
        "/Root/orders": (
            3,
            {
                "endpoint": "localhost:2136",
                "database": "/Root",
                "consumer": "analytics",
                "reader.name": "payments-worker",
                "topic": "/Root/orders",
            },
        ),
        "/Root/refunds": (
            3,
            {
                "endpoint": "localhost:2136",
                "database": "/Root",
                "consumer": "analytics",
                "reader.name": "payments-worker",
                "topic": "/Root/refunds",
            },
        ),
    }


def test_topic_reader_commit_acknowledged_messages_are_split_by_topic(metrics_setup):
    from tests.observability.conftest import FakeDriverConfig
    from ydb.observability.metrics import (
        TOPIC_READER_COMMIT_ACKNOWLEDGED,
        create_topic_reader_metrics,
    )

    class FakeDriver:
        _driver_config = FakeDriverConfig(
            endpoint="grpc://localhost:2136",
            database="/Root",
        )

    reader_metrics = create_topic_reader_metrics(
        FakeDriver(),
        consumer_name="analytics",
        reader_name="payments-worker",
    )
    reader_metrics.record_commit_acknowledged(2, "/Root/orders")
    reader_metrics.record_commit_acknowledged(3, "/Root/refunds")
    reader_metrics.record_commit_acknowledged(1, "/Root/orders")
    reader_metrics.record_commit_acknowledged(0, "/Root/ignored")

    points = _points(metrics_setup, TOPIC_READER_COMMIT_ACKNOWLEDGED)
    values = {point.attributes["topic"]: (point.value, point.attributes) for point in points}
    assert values == {
        "/Root/orders": (
            3,
            {
                "endpoint": "localhost:2136",
                "database": "/Root",
                "consumer": "analytics",
                "reader.name": "payments-worker",
                "topic": "/Root/orders",
            },
        ),
        "/Root/refunds": (
            3,
            {
                "endpoint": "localhost:2136",
                "database": "/Root",
                "consumer": "analytics",
                "reader.name": "payments-worker",
                "topic": "/Root/refunds",
            },
        ),
    }


def test_topic_reader_commit_offset_lag_tracks_maximum_across_partitions(metrics_setup):
    from ydb.observability.metrics import (
        TOPIC_READER_COMMIT_OFFSET_LAG_MAX,
        create_topic_reader_metrics,
    )

    reader_metrics = create_topic_reader_metrics(
        object(),
        consumer_name="analytics",
        reader_name="payments-worker",
    )
    first = _topic_reader_partition_session("/Root/orders", 1, 10, committed_offset=10)
    second = _topic_reader_partition_session("/Root/orders", 2, 10, committed_offset=100)
    other = _topic_reader_partition_session("/Root/refunds", 3, 10, committed_offset=20)
    try:
        reader_metrics.add_partition_session(first.topic_path, first)
        reader_metrics.add_partition_session(second.topic_path, second)
        reader_metrics.add_partition_session(other.topic_path, other)

        assert {
            point.attributes["topic"]: point.value
            for point in _points(metrics_setup, TOPIC_READER_COMMIT_OFFSET_LAG_MAX)
        } == {"/Root/orders": 0, "/Root/refunds": 0}

        reader_metrics.record_commit_offset_queued(first, 15)
        reader_metrics.record_commit_offset_queued(second, 108)
        reader_metrics.record_commit_offset_queued(other, 23)
        assert {
            point.attributes["topic"]: (point.value, point.attributes)
            for point in _points(metrics_setup, TOPIC_READER_COMMIT_OFFSET_LAG_MAX)
        } == {
            "/Root/orders": (
                8,
                {
                    "endpoint": "",
                    "database": "",
                    "consumer": "analytics",
                    "reader.name": "payments-worker",
                    "topic": "/Root/orders",
                },
            ),
            "/Root/refunds": (
                3,
                {
                    "endpoint": "",
                    "database": "",
                    "consumer": "analytics",
                    "reader.name": "payments-worker",
                    "topic": "/Root/refunds",
                },
            ),
        }

        reader_metrics.record_commit_offset_acknowledged(second, 108)
        assert {
            point.attributes["topic"]: point.value
            for point in _points(metrics_setup, TOPIC_READER_COMMIT_OFFSET_LAG_MAX)
        } == {"/Root/orders": 5, "/Root/refunds": 3}

        reader_metrics.record_commit_offset_acknowledged(first, 9)
        assert {
            point.attributes["topic"]: point.value
            for point in _points(metrics_setup, TOPIC_READER_COMMIT_OFFSET_LAG_MAX)
        } == {"/Root/orders": 5, "/Root/refunds": 3}

        reader_metrics.record_commit_offset_acknowledged(first, 15)
        reader_metrics.record_commit_offset_acknowledged(other, 23)
        assert {
            point.attributes["topic"]: point.value
            for point in _points(metrics_setup, TOPIC_READER_COMMIT_OFFSET_LAG_MAX)
        } == {"/Root/orders": 0, "/Root/refunds": 0}

        reader_metrics.remove_partition_session(first.topic_path, first)
        reader_metrics.remove_partition_session(second.topic_path, second)
        assert {
            point.attributes["topic"]: point.value
            for point in _points(metrics_setup, TOPIC_READER_COMMIT_OFFSET_LAG_MAX)
        } == {"/Root/refunds": 0}

        reader_metrics.reset_partition_sessions()
        assert _points(metrics_setup, TOPIC_READER_COMMIT_OFFSET_LAG_MAX) == []
    finally:
        reader_metrics.close()


def test_topic_reader_session_errors_are_split_by_retry_decision(metrics_setup):
    from ydb.observability.metrics import (
        TOPIC_READER_SESSION_ERRORS,
        create_topic_reader_metrics,
    )

    reader_metrics = create_topic_reader_metrics(
        object(),
        consumer_name="analytics",
        reader_name="payments-worker",
    )
    reader_metrics.record_session_error(issues.Unavailable("retry"), True)
    reader_metrics.record_session_error(issues.Unavailable("retry"), True)
    reader_metrics.record_session_error(issues.BadRequest("stop"), False)

    points = _points(metrics_setup, TOPIC_READER_SESSION_ERRORS)
    assert {point.attributes["retry_decision"]: (point.value, point.attributes) for point in points} == {
        "retry": (
            2,
            {
                "endpoint": "",
                "database": "",
                "consumer": "analytics",
                "reader.name": "payments-worker",
                "retry_decision": "retry",
                "status_code": "UNAVAILABLE",
                "error.type": "ydb_error",
            },
        ),
        "stop": (
            1,
            {
                "endpoint": "",
                "database": "",
                "consumer": "analytics",
                "reader.name": "payments-worker",
                "retry_decision": "stop",
                "status_code": "BAD_REQUEST",
                "error.type": "ydb_error",
            },
        ),
    }


@pytest.mark.parametrize(
    ("error", "status_code", "error_type"),
    [
        (issues.ConnectionLost("lost"), "CONNECTION_LOST", "transport_error"),
        (issues.ConnectionError("connection"), "ConnectionError", "transport_error"),
        (issues.BadRequest("bad request"), "BAD_REQUEST", "ydb_error"),
        (RuntimeError("unexpected"), "RuntimeError", "RuntimeError"),
    ],
)
def test_topic_reader_session_errors_classify_failure(metrics_setup, error, status_code, error_type):
    from ydb.observability.metrics import (
        TOPIC_READER_SESSION_ERRORS,
        create_topic_reader_metrics,
    )

    reader_metrics = create_topic_reader_metrics(
        object(),
        consumer_name="analytics",
        reader_name="payments-worker",
    )
    reader_metrics.record_session_error(error, True)

    point = _single_point(metrics_setup, TOPIC_READER_SESSION_ERRORS)
    assert point.attributes["status_code"] == status_code
    assert point.attributes["error.type"] == error_type


def test_topic_reader_credit_balance_tracks_stream_credit(metrics_setup):
    from ydb.observability.metrics import (
        TOPIC_READER_CREDIT_BALANCE_BYTES,
        create_topic_reader_metrics,
    )

    reader_metrics = create_topic_reader_metrics(
        object(),
        consumer_name="analytics",
        reader_name="payments-worker",
    )
    try:
        assert _single_point(metrics_setup, TOPIC_READER_CREDIT_BALANCE_BYTES).value == 0

        reader_metrics.reset_credit_balance_bytes(100)
        assert _single_point(metrics_setup, TOPIC_READER_CREDIT_BALANCE_BYTES).value == 100

        reader_metrics.add_credit_balance_bytes(-12)
        assert _single_point(metrics_setup, TOPIC_READER_CREDIT_BALANCE_BYTES).value == 88

        reader_metrics.add_credit_balance_bytes(4)
        assert _single_point(metrics_setup, TOPIC_READER_CREDIT_BALANCE_BYTES).value == 92

        reader_metrics.reset_credit_balance_bytes()
        assert _single_point(metrics_setup, TOPIC_READER_CREDIT_BALANCE_BYTES).value == 0
    finally:
        reader_metrics.close()

    assert _points(metrics_setup, TOPIC_READER_CREDIT_BALANCE_BYTES) == []


def test_topic_reader_local_buffer_messages_tracks_current_reader_buffer(metrics_setup):
    from tests.observability.conftest import FakeDriverConfig
    from ydb.observability.metrics import (
        TOPIC_READER_LOCAL_BUFFER_MESSAGES,
        create_topic_reader_metrics,
    )

    class FakeDriver:
        _driver_config = FakeDriverConfig(
            endpoint="grpc://localhost:2136",
            database="/Root",
        )

    reader_metrics = create_topic_reader_metrics(
        FakeDriver(),
        consumer_name="analytics",
        reader_name="payments-worker",
    )
    try:
        orders_batch = _topic_reader_batch(2, "/Root/orders", partition_session_id=1)
        refunds_batch = _topic_reader_batch(3, "/Root/refunds", partition_session_id=2)
        reader_metrics.record_received_messages([orders_batch, refunds_batch])

        point = _single_point(metrics_setup, TOPIC_READER_LOCAL_BUFFER_MESSAGES)
        assert (point.value, point.attributes) == (
            5,
            {
                "endpoint": "localhost:2136",
                "database": "/Root",
                "consumer": "analytics",
                "reader.name": "payments-worker",
            },
        )
        assert "topic" not in point.attributes

        reader_metrics.remove_local_buffer_messages(2, orders_batch._partition_session)
        assert _single_point(metrics_setup, TOPIC_READER_LOCAL_BUFFER_MESSAGES).value == 3

        reader_metrics.reset_local_buffer_messages()
        assert _single_point(metrics_setup, TOPIC_READER_LOCAL_BUFFER_MESSAGES).value == 0
    finally:
        reader_metrics.close()

    assert _points(metrics_setup, TOPIC_READER_LOCAL_BUFFER_MESSAGES) == []


def test_topic_reader_local_buffer_age_tracks_oldest_message_per_partition(metrics_setup, monkeypatch):
    from ydb.observability import metrics

    reader_metrics = metrics.create_topic_reader_metrics(
        object(),
        consumer_name="analytics",
        reader_name="payments-worker",
    )
    first_partition_early = _topic_reader_batch(
        1,
        "/Root/events",
        partition_session_id=1,
    )
    second_partition = _topic_reader_batch(
        1,
        "/Root/events",
        partition_session_id=2,
    )
    first_partition_late = _topic_reader_batch(
        1,
        "/Root/events",
        partition_session_id=1,
    )

    try:
        assert _single_point(metrics_setup, metrics.TOPIC_READER_LOCAL_BUFFER_MESSAGE_AGE_MAX).value == 0

        reader_metrics.record_received_messages([first_partition_early], received_at=10.0)
        reader_metrics.record_received_messages([second_partition], received_at=20.0)
        reader_metrics.record_received_messages([first_partition_late], received_at=30.0)
        monkeypatch.setattr(metrics.time, "monotonic", MagicMock(return_value=40.0))

        age = _single_point(metrics_setup, metrics.TOPIC_READER_LOCAL_BUFFER_MESSAGE_AGE_MAX)
        assert (age.value, age.attributes) == (
            30.0,
            {
                "endpoint": "",
                "database": "",
                "consumer": "analytics",
                "reader.name": "payments-worker",
            },
        )

        reader_metrics.remove_local_buffer_messages(1, second_partition._partition_session)
        assert _single_point(metrics_setup, metrics.TOPIC_READER_LOCAL_BUFFER_MESSAGE_AGE_MAX).value == 30.0

        reader_metrics.remove_local_buffer_messages(1, first_partition_early._partition_session)
        assert _single_point(metrics_setup, metrics.TOPIC_READER_LOCAL_BUFFER_MESSAGE_AGE_MAX).value == 10.0

        reader_metrics.remove_local_buffer_messages(1, first_partition_late._partition_session)
        assert _single_point(metrics_setup, metrics.TOPIC_READER_LOCAL_BUFFER_MESSAGE_AGE_MAX).value == 0
        assert _single_point(metrics_setup, metrics.TOPIC_READER_LOCAL_BUFFER_MESSAGES).value == 0
    finally:
        reader_metrics.close()

    assert _points(metrics_setup, metrics.TOPIC_READER_LOCAL_BUFFER_MESSAGE_AGE_MAX) == []


def test_topic_reader_partition_session_count_is_split_by_topic(metrics_setup):
    from ydb.observability.metrics import (
        TOPIC_READER_PARTITION_SESSION_COUNT,
        create_topic_reader_metrics,
    )

    reader_metrics = create_topic_reader_metrics(
        object(),
        consumer_name="analytics",
        reader_name="payments-worker",
        topics=("/Root/orders", "/Root/refunds"),
    )
    try:
        assert {
            point.attributes["topic"]: point.value
            for point in _points(metrics_setup, TOPIC_READER_PARTITION_SESSION_COUNT)
        } == {
            "/Root/orders": 0,
            "/Root/refunds": 0,
        }

        reader_metrics.add_partition_session("/Root/orders")
        reader_metrics.add_partition_session("/Root/orders")
        reader_metrics.add_partition_session("/Root/refunds")

        points = _points(metrics_setup, TOPIC_READER_PARTITION_SESSION_COUNT)
        assert {point.attributes["topic"]: (point.value, point.attributes) for point in points} == {
            "/Root/orders": (
                2,
                {
                    "endpoint": "",
                    "database": "",
                    "consumer": "analytics",
                    "reader.name": "payments-worker",
                    "topic": "/Root/orders",
                },
            ),
            "/Root/refunds": (
                1,
                {
                    "endpoint": "",
                    "database": "",
                    "consumer": "analytics",
                    "reader.name": "payments-worker",
                    "topic": "/Root/refunds",
                },
            ),
        }

        reader_metrics.remove_partition_session("/Root/orders")
        reader_metrics.remove_partition_session("/Root/refunds")
        points = _points(metrics_setup, TOPIC_READER_PARTITION_SESSION_COUNT)
        assert {point.attributes["topic"]: point.value for point in points} == {
            "/Root/orders": 1,
            "/Root/refunds": 0,
        }

        reader_metrics.reset_partition_sessions()
        assert {
            point.attributes["topic"]: point.value
            for point in _points(metrics_setup, TOPIC_READER_PARTITION_SESSION_COUNT)
        } == {
            "/Root/orders": 0,
            "/Root/refunds": 0,
        }
    finally:
        reader_metrics.close()

    assert _points(metrics_setup, TOPIC_READER_PARTITION_SESSION_COUNT) == []


@pytest.mark.asyncio
async def test_topic_reader_metrics_follow_reader_lifecycle_across_topics(metrics_setup):
    from unittest import mock

    from tests.observability.conftest import FakeDriverConfig
    from ydb._topic_reader.datatypes import PartitionSession
    from ydb._topic_reader.topic_reader import PublicReaderSettings
    from ydb._topic_reader.topic_reader_asyncio import PublicAsyncIOReader, ReaderStream
    from ydb.observability.metrics import (
        TOPIC_READER_DELIVERED_MESSAGES,
        TOPIC_READER_LOCAL_BUFFER_MESSAGES,
        TOPIC_READER_RECEIVED_BYTES,
        TOPIC_READER_RECEIVED_MESSAGES,
    )

    class FakeDriver:
        _driver_config = FakeDriverConfig(
            endpoint="grpc://localhost:2136",
            database="/Root",
        )

    settings = PublicReaderSettings(
        consumer="analytics",
        topic="/Root/orders",
        reader_name="payments-worker",
    )
    stream_ready = asyncio.Event()
    stream_holder = []

    async def create_stream(reader_reconnector_id, driver, stream_settings, *, reader_name, metrics):
        stream = ReaderStream(
            reader_reconnector_id,
            stream_settings,
            reader_name=reader_name,
            metrics=metrics,
        )
        for session_id, topic in [(1, "/Root/orders"), (2, "/Root/refunds")]:
            stream._partition_sessions[session_id] = PartitionSession(
                id=session_id,
                state=PartitionSession.State.Active,
                topic_path=topic,
                partition_id=session_id,
                committed_offset=0,
                reader_reconnector_id=reader_reconnector_id,
                reader_stream_id=stream._id,
            )
        stream_holder.append(stream)
        stream_ready.set()
        return stream

    reader_attributes = {
        "endpoint": "localhost:2136",
        "database": "/Root",
        "consumer": "analytics",
        "reader.name": "payments-worker",
    }
    with mock.patch.object(ReaderStream, "create", create_stream):
        reader = PublicAsyncIOReader(FakeDriver(), settings)
        try:
            await asyncio.wait_for(stream_ready.wait(), timeout=1)
            stream = stream_holder[0]
            assert (
                _single_point(metrics_setup, TOPIC_READER_LOCAL_BUFFER_MESSAGES).value,
                _single_point(metrics_setup, TOPIC_READER_LOCAL_BUFFER_MESSAGES).attributes,
            ) == (0, reader_attributes)

            stream._on_read_response(_topic_read_response([(1, 2), (2, 1)]))
            await _decode_pending_topic_batches(stream)

            assert _single_point(metrics_setup, TOPIC_READER_LOCAL_BUFFER_MESSAGES).value == 3
            assert len(_points(metrics_setup, TOPIC_READER_LOCAL_BUFFER_MESSAGES)) == 1
            assert _single_point(metrics_setup, TOPIC_READER_RECEIVED_BYTES).value == 30

            assert await reader.receive_message() is not None
            assert _single_point(metrics_setup, TOPIC_READER_LOCAL_BUFFER_MESSAGES).value == 2
            assert len((await reader.receive_batch(max_messages=1)).messages) == 1
            assert _single_point(metrics_setup, TOPIC_READER_LOCAL_BUFFER_MESSAGES).value == 1
            assert len((await reader.receive_batch()).messages) == 1
            assert _single_point(metrics_setup, TOPIC_READER_LOCAL_BUFFER_MESSAGES).value == 0

            received = {
                point.attributes["topic"]: point.value
                for point in _points(metrics_setup, TOPIC_READER_RECEIVED_MESSAGES)
            }
            delivered = {
                point.attributes["topic"]: point.value
                for point in _points(metrics_setup, TOPIC_READER_DELIVERED_MESSAGES)
            }
            assert received == {"/Root/orders": 2, "/Root/refunds": 1}
            assert delivered == received
        finally:
            await reader.close(flush=False)

    assert _points(metrics_setup, TOPIC_READER_LOCAL_BUFFER_MESSAGES) == []


@pytest.mark.asyncio
async def test_topic_reader_gauges_reset_across_stream_reconnect(metrics_setup, monkeypatch):
    from unittest import mock

    from tests.observability.conftest import FakeDriverConfig
    from ydb._topic_reader.datatypes import PartitionSession
    from ydb._topic_reader.topic_reader import PublicReaderSettings
    from ydb._topic_reader.topic_reader_asyncio import PublicAsyncIOReader, ReaderStream
    from ydb.observability.metrics import (
        TOPIC_READER_CREDIT_BALANCE_BYTES,
        TOPIC_READER_LOCAL_BUFFER_MESSAGE_AGE_MAX,
        TOPIC_READER_LOCAL_BUFFER_MESSAGES,
        TOPIC_READER_PARTITION_SESSION_COUNT,
        TopicReaderMetrics,
    )

    class FakeDriver:
        _driver_config = FakeDriverConfig()

    settings = PublicReaderSettings(
        consumer="analytics",
        topic="/Root/orders",
        reader_name="reconnecting-reader",
    )
    first_stream_ready = asyncio.Event()
    second_stream_create_started = asyncio.Event()
    allow_second_stream = asyncio.Event()
    second_stream_ready = asyncio.Event()
    streams = []
    monkeypatch.setattr(
        TopicReaderMetrics,
        "capture_received_at",
        lambda self: time.monotonic() - 5.0,
    )

    async def create_stream(reader_reconnector_id, driver, stream_settings, *, reader_name, metrics):
        stream = ReaderStream(
            reader_reconnector_id,
            stream_settings,
            reader_name=reader_name,
            metrics=metrics,
        )
        stream._partition_sessions[1] = PartitionSession(
            id=1,
            state=PartitionSession.State.Active,
            topic_path="/Root/orders",
            partition_id=1,
            committed_offset=0,
            reader_reconnector_id=reader_reconnector_id,
            reader_stream_id=stream._id,
        )
        streams.append(stream)
        if len(streams) == 1:
            metrics.reset_credit_balance_bytes(stream_settings.buffer_size_bytes)
            metrics.add_partition_session("/Root/orders")
            stream._on_read_response(_topic_read_response([(1, 2)], bytes_size=20))
            await _decode_pending_topic_batches(stream)
            first_stream_ready.set()
        else:
            second_stream_create_started.set()
            await allow_second_stream.wait()
            metrics.reset_credit_balance_bytes(stream_settings.buffer_size_bytes)
            metrics.add_partition_session("/Root/orders")
            stream._on_read_response(_topic_read_response([(1, 1)], bytes_size=10))
            await _decode_pending_topic_batches(stream)
            second_stream_ready.set()
        return stream

    with mock.patch.object(ReaderStream, "create", create_stream):
        reader = PublicAsyncIOReader(FakeDriver(), settings)
        try:
            await asyncio.wait_for(first_stream_ready.wait(), timeout=1)
            assert _single_point(metrics_setup, TOPIC_READER_LOCAL_BUFFER_MESSAGES).value == 2
            first_age = _single_point(metrics_setup, TOPIC_READER_LOCAL_BUFFER_MESSAGE_AGE_MAX).value
            assert 5.0 <= first_age < 10.0
            assert _single_point(metrics_setup, TOPIC_READER_PARTITION_SESSION_COUNT).value == 1
            assert (
                _single_point(metrics_setup, TOPIC_READER_CREDIT_BALANCE_BYTES).value == settings.buffer_size_bytes - 20
            )

            streams[0]._set_first_error(issues.Unavailable("reconnect"))
            await asyncio.wait_for(second_stream_create_started.wait(), timeout=2)
            assert _single_point(metrics_setup, TOPIC_READER_LOCAL_BUFFER_MESSAGES).value == 0
            assert _single_point(metrics_setup, TOPIC_READER_LOCAL_BUFFER_MESSAGE_AGE_MAX).value == 0
            assert _single_point(metrics_setup, TOPIC_READER_PARTITION_SESSION_COUNT).value == 0
            assert _single_point(metrics_setup, TOPIC_READER_CREDIT_BALANCE_BYTES).value == 0

            allow_second_stream.set()
            await asyncio.wait_for(second_stream_ready.wait(), timeout=1)

            async def wait_until_second_stream_is_installed():
                while reader._reconnector._stream_reader is not streams[1]:
                    await asyncio.sleep(0)

            await asyncio.wait_for(wait_until_second_stream_is_installed(), timeout=1)
            assert _single_point(metrics_setup, TOPIC_READER_LOCAL_BUFFER_MESSAGES).value == 1
            second_age = _single_point(metrics_setup, TOPIC_READER_LOCAL_BUFFER_MESSAGE_AGE_MAX).value
            assert 5.0 <= second_age < 10.0
            assert _single_point(metrics_setup, TOPIC_READER_PARTITION_SESSION_COUNT).value == 1
            assert (
                _single_point(metrics_setup, TOPIC_READER_CREDIT_BALANCE_BYTES).value == settings.buffer_size_bytes - 10
            )
        finally:
            allow_second_stream.set()
            await reader.close(flush=False)

    assert _points(metrics_setup, TOPIC_READER_LOCAL_BUFFER_MESSAGES) == []
    assert _points(metrics_setup, TOPIC_READER_LOCAL_BUFFER_MESSAGE_AGE_MAX) == []
    assert _points(metrics_setup, TOPIC_READER_PARTITION_SESSION_COUNT) == []
    assert _points(metrics_setup, TOPIC_READER_CREDIT_BALANCE_BYTES) == []


def test_topic_reader_gauges_aggregate_duplicate_reader_attributes(metrics_setup, monkeypatch):
    from ydb.observability.metrics import (
        TOPIC_READER_COMMIT_OFFSET_LAG_MAX,
        TOPIC_READER_CREDIT_BALANCE_BYTES,
        TOPIC_READER_LOCAL_BUFFER_MESSAGE_AGE_MAX,
        TOPIC_READER_LOCAL_BUFFER_MESSAGES,
        TOPIC_READER_PARTITION_SESSION_COUNT,
        create_topic_reader_metrics,
    )

    first = create_topic_reader_metrics(object(), consumer_name=None, reader_name="shared")
    second = create_topic_reader_metrics(object(), consumer_name=None, reader_name="shared")
    first_partition = _topic_reader_partition_session("/Root/events", 1, 1)
    second_partition = _topic_reader_partition_session("/Root/events", 2, 1)
    third_partition = _topic_reader_partition_session("/Root/events", 3, 2)
    try:
        first.record_received_messages([_topic_reader_batch(2, "/Root/events")], received_at=10.0)
        second.record_received_messages([_topic_reader_batch(3, "/Root/events")], received_at=20.0)
        first.reset_credit_balance_bytes(100)
        second.reset_credit_balance_bytes(50)
        first.add_partition_session("/Root/events", first_partition)
        first.add_partition_session("/Root/events", second_partition)
        second.add_partition_session("/Root/events", third_partition)
        first.record_commit_offset_queued(first_partition, 5)
        first.record_commit_offset_queued(second_partition, 2)
        second.record_commit_offset_queued(third_partition, 8)
        monkeypatch.setattr("ydb.observability.metrics.time.monotonic", MagicMock(return_value=30.0))

        assert _single_point(metrics_setup, TOPIC_READER_LOCAL_BUFFER_MESSAGES).value == 5
        assert _single_point(metrics_setup, TOPIC_READER_LOCAL_BUFFER_MESSAGE_AGE_MAX).value == 20.0
        assert _single_point(metrics_setup, TOPIC_READER_PARTITION_SESSION_COUNT).value == 3
        assert _single_point(metrics_setup, TOPIC_READER_CREDIT_BALANCE_BYTES).value == 150
        assert _single_point(metrics_setup, TOPIC_READER_COMMIT_OFFSET_LAG_MAX).value == 8
    finally:
        first.close()
        second.close()


def test_topic_reader_metrics_omit_consumer(metrics_setup):
    from ydb.observability.metrics import (
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
        create_topic_reader_metrics,
    )

    reader_metrics = create_topic_reader_metrics(
        object(),
        consumer_name=None,
        reader_name="reader-42",
    )
    try:
        reader_metrics.record_received_messages([_topic_reader_batch(1, "/Root/events")])
        reader_metrics.record_received_bytes(10)
        reader_metrics.record_delivered_messages(1, "/Root/events")
        reader_metrics.record_compression_duration(0.01, "gzip", "/Root/events")
        reader_metrics.record_message_processing_duration(0.02, "gzip", "/Root/events")
        reader_metrics.record_commit_queued(1, "/Root/events")
        reader_metrics.record_commit_acknowledged(1, "/Root/events")
        reader_metrics.record_session_error(issues.BadRequest("stop"), False)
        reader_metrics.reset_credit_balance_bytes(100)
        partition_session = _topic_reader_partition_session("/Root/events", 1, 1)
        reader_metrics.add_partition_session("/Root/events", partition_session)
        reader_metrics.record_commit_offset_queued(partition_session, 1)

        reader_attributes = {
            "endpoint": "",
            "database": "",
            "reader.name": "reader-42",
        }
        message_attributes = _single_point(metrics_setup, TOPIC_READER_RECEIVED_MESSAGES).attributes
        bytes_attributes = _single_point(metrics_setup, TOPIC_READER_RECEIVED_BYTES).attributes
        delivered_attributes = _single_point(metrics_setup, TOPIC_READER_DELIVERED_MESSAGES).attributes
        compression_attributes = _single_point(metrics_setup, TOPIC_READER_COMPRESSION_DURATION).attributes
        processing_attributes = _single_point(metrics_setup, TOPIC_READER_MESSAGE_PROCESSING_DURATION).attributes
        commit_queued_attributes = _single_point(metrics_setup, TOPIC_READER_COMMIT_QUEUED).attributes
        commit_acknowledged_attributes = _single_point(
            metrics_setup,
            TOPIC_READER_COMMIT_ACKNOWLEDGED,
        ).attributes
        commit_offset_lag_attributes = _single_point(
            metrics_setup,
            TOPIC_READER_COMMIT_OFFSET_LAG_MAX,
        ).attributes
        session_error_attributes = _single_point(metrics_setup, TOPIC_READER_SESSION_ERRORS).attributes
        credit_attributes = _single_point(metrics_setup, TOPIC_READER_CREDIT_BALANCE_BYTES).attributes
        buffer_attributes = _single_point(metrics_setup, TOPIC_READER_LOCAL_BUFFER_MESSAGES).attributes
        buffer_age_attributes = _single_point(
            metrics_setup,
            TOPIC_READER_LOCAL_BUFFER_MESSAGE_AGE_MAX,
        ).attributes
        partition_session_attributes = _single_point(
            metrics_setup,
            TOPIC_READER_PARTITION_SESSION_COUNT,
        ).attributes
        assert message_attributes == dict(reader_attributes, topic="/Root/events")
        assert bytes_attributes == reader_attributes
        assert delivered_attributes == dict(reader_attributes, topic="/Root/events")
        duration_attributes = dict(reader_attributes, topic="/Root/events", codec="gzip", outcome="ok")
        assert compression_attributes == duration_attributes
        assert processing_attributes == duration_attributes
        assert commit_queued_attributes == dict(reader_attributes, topic="/Root/events")
        assert commit_acknowledged_attributes == dict(reader_attributes, topic="/Root/events")
        assert commit_offset_lag_attributes == dict(reader_attributes, topic="/Root/events")
        assert session_error_attributes == dict(
            reader_attributes,
            retry_decision="stop",
            status_code="BAD_REQUEST",
            **{"error.type": "ydb_error"},
        )
        assert credit_attributes == reader_attributes
        assert buffer_attributes == reader_attributes
        assert buffer_age_attributes == reader_attributes
        assert partition_session_attributes == dict(reader_attributes, topic="/Root/events")
    finally:
        reader_metrics.close()


@pytest.mark.parametrize("reader_name", [None, ""])
def test_topic_reader_metrics_require_explicit_reader_name(metrics_setup, reader_name):
    from ydb.observability.metrics import (
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
        create_topic_reader_metrics,
    )

    reader_metrics = create_topic_reader_metrics(
        object(),
        consumer_name="analytics",
        reader_name=reader_name,
    )
    reader_metrics.record_received_messages([_topic_reader_batch(1, "/Root/events")])
    reader_metrics.record_received_bytes(10)
    reader_metrics.record_delivered_messages(1, "/Root/events")
    reader_metrics.record_compression_duration(0.01, "gzip", "/Root/events")
    reader_metrics.record_message_processing_duration(0.02, "gzip", "/Root/events")
    reader_metrics.record_commit_queued(1, "/Root/events")
    reader_metrics.record_commit_acknowledged(1, "/Root/events")
    reader_metrics.record_session_error(issues.Unavailable("retry"), True)
    reader_metrics.reset_credit_balance_bytes(100)
    reader_metrics.add_partition_session("/Root/events")

    metrics = _metrics_by_name(metrics_setup)
    assert TOPIC_READER_RECEIVED_MESSAGES not in metrics
    assert TOPIC_READER_RECEIVED_BYTES not in metrics
    assert TOPIC_READER_COMMIT_ACKNOWLEDGED not in metrics
    assert TOPIC_READER_COMMIT_OFFSET_LAG_MAX not in metrics
    assert TOPIC_READER_COMMIT_QUEUED not in metrics
    assert TOPIC_READER_COMPRESSION_DURATION not in metrics
    assert TOPIC_READER_SESSION_ERRORS not in metrics
    assert TOPIC_READER_CREDIT_BALANCE_BYTES not in metrics
    assert TOPIC_READER_DELIVERED_MESSAGES not in metrics
    assert TOPIC_READER_LOCAL_BUFFER_MESSAGES not in metrics
    assert TOPIC_READER_MESSAGE_PROCESSING_DURATION not in metrics
    assert TOPIC_READER_LOCAL_BUFFER_MESSAGE_AGE_MAX not in metrics
    assert TOPIC_READER_PARTITION_SESSION_COUNT not in metrics


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
        from ydb.observability import disable_metrics
        from ydb.observability.metrics import _NOOP_SESSION_METRICS
        from ydb.query.session import QuerySession

        disable_metrics()
        session = QuerySession(MagicMock())
        assert session._session_metrics is _NOOP_SESSION_METRICS
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
        pool._metrics.attach(session)
        session._session_metrics.count_open()
        session._session_metrics.transition("idle")
        pool._queue.put_nowait(session)

        acquired = pool.acquire()
        assert acquired is session

        values = {
            tuple(sorted(point.attributes.items())): point.value
            for point in _points(metrics_setup, QUERY_SESSION_COUNT)
        }
        assert values[(("ydb.query.session.pool.name", "sync-pool"), ("ydb.query.session.state", "used"))] == 1
        assert (("ydb.query.session.pool.name", "sync-pool"), ("ydb.query.session.state", "idle")) not in values
        session._session_metrics.count_closed()
        pool._metrics.close()

    def test_sync_pool_release_updates_session_count(self, metrics_setup):
        from ydb.observability.metrics import QUERY_SESSION_COUNT, SessionMetrics
        from ydb.query.pool import QuerySessionPool

        pool = QuerySessionPool(driver=MagicMock(), size=2, name="sync-pool")
        session = MagicMock()
        session.session_id = "session-1"
        session._session_metrics = SessionMetrics()
        pool._metrics.attach(session)
        session._session_metrics.count_open()
        pool.release(session)

        values = {
            tuple(sorted(point.attributes.items())): point.value
            for point in _points(metrics_setup, QUERY_SESSION_COUNT)
        }
        assert values[(("ydb.query.session.pool.name", "sync-pool"), ("ydb.query.session.state", "idle"))] == 1
        assert (("ydb.query.session.pool.name", "sync-pool"), ("ydb.query.session.state", "used")) not in values
        session._session_metrics.count_closed()
        pool._metrics.close()

    def test_invalidated_session_release_does_not_publish_phantom_idle_session(self, metrics_setup):
        from ydb.observability.metrics import QUERY_SESSION_COUNT, SessionMetrics
        from ydb.query.pool import QuerySessionPool

        pool = QuerySessionPool(driver=MagicMock(), size=1, name="invalidated")
        session = MagicMock()
        session.is_active = True
        session.session_id = "session-1"
        session._session_metrics = SessionMetrics()
        pool._metrics.attach(session)
        session._session_metrics.count_open()

        pool.release(session)
        assert pool.acquire() is session

        session._session_metrics.count_closed("transport_error")
        session.is_active = False
        pool.release(session)

        assert _points_for_pool(metrics_setup, QUERY_SESSION_COUNT, "invalidated") == []
        _assert_closed_metric(metrics_setup, "invalidated", "transport_error")
        pool._metrics.close()

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
        pool._metrics.close()

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
        pool._metrics.close()

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
        point = _single_point_for_pool(metrics_setup, QUERY_SESSION_COUNT, "session-pool")
        assert point.attributes["ydb.query.session.state"] == "used"
        qs._close_session()

    def test_sync_session_close_decrements_session_count(self, metrics_setup):
        from ydb.observability.metrics import QUERY_SESSION_COUNT, SessionMetrics
        from ydb.query.session import QuerySession

        qs = QuerySession.__new__(QuerySession)
        qs._closed = False
        qs._invalidated = False
        qs._session_metrics = SessionMetrics()
        qs._session_metrics.pool_name = "session-pool"
        qs._session_metrics.count_open()
        qs._stream = None

        qs._close_session()
        assert not qs._session_metrics._counted
        assert _points_for_pool(metrics_setup, QUERY_SESSION_COUNT, "session-pool") == []

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

    @pytest.mark.parametrize("async_", [False, True], ids=["sync", "async"])
    @pytest.mark.parametrize(
        ("status", "reason"),
        [
            (issues.StatusCode.BAD_SESSION, "bad_session"),
            (issues.StatusCode.SESSION_EXPIRED, "bad_session"),
            (issues.StatusCode.SESSION_BUSY, "session_busy"),
            (issues.StatusCode.UNAVAILABLE, "transport_error"),
        ],
    )
    @pytest.mark.asyncio
    async def test_attach_stream_status_records_closed_session(self, metrics_setup, async_, status, reason):
        pool_name = "async-pool" if async_ else "sync-pool"
        session = self._counted_session(pool_name, async_=async_)
        status = ServerStatus(status, [])

        if async_:
            session._status_stream = MagicMock()
            session._status_stream.__aiter__.return_value = [status]
            await session._check_session_status_loop()
        else:
            session._check_session_status_loop(iter([status]))

        _assert_closed_metric(metrics_setup, pool_name, reason)

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
        session._close_session()

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
            session._close_session()
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
    @pytest.mark.parametrize("async_", [False, True], ids=["sync", "async"])
    @pytest.mark.parametrize("closed_before_count", [False, True], ids=["open", "closed"])
    async def test_initial_attach_counts_only_open_session(
        self, metrics_setup, monkeypatch, async_, closed_before_count
    ):
        QuerySession = AsyncQuerySession if async_ else SyncQuerySession
        module = "ydb.aio.query.session" if async_ else "ydb.query.session"
        session = QuerySession(MagicMock())
        session._session_id = "session-1"
        session._session_metrics.pool_name = "async-pool" if async_ else "sync-pool"
        stream = MagicMock()
        session._attach_call = AsyncMock(return_value=stream) if async_ else MagicMock(return_value=stream)
        status_stream = MagicMock()

        if async_:
            status_stream.__aiter__.return_value = []
            monkeypatch.setattr(module + "._utilities.AsyncResponseIterator", lambda *args: status_stream)

            async def first_response(*args):
                if closed_before_count:
                    session._close_session(invalidate=True)
                return ServerStatus(issues.StatusCode.SUCCESS, [])

            def discard_task(coroutine, name):
                coroutine.close()

            session._loop = MagicMock()
            session._loop.create_task.side_effect = discard_task
        else:
            monkeypatch.setattr(module + "._utilities.SyncResponseIterator", lambda *args: status_stream)

            def first_response(*args):
                if closed_before_count:
                    session._close_session(invalidate=True)
                return ServerStatus(issues.StatusCode.SUCCESS, [])

            monkeypatch.setattr(module + ".threading.Thread", MagicMock())

        monkeypatch.setattr(module + "._utilities.get_first_message_with_timeout", first_response)

        if async_:
            await session._attach()
        else:
            session._attach()

        assert session.is_closed is closed_before_count
        assert session._session_metrics._counted is not closed_before_count
        assert _points(metrics_setup, QUERY_SESSION_CLOSED) == []
        session._close_session()

    @pytest.mark.asyncio
    async def test_async_pool_acquire_from_queue_updates_session_count(self, metrics_setup):
        from ydb.aio.query.pool import QuerySessionPool
        from ydb.observability.metrics import QUERY_SESSION_COUNT, SessionMetrics

        pool = QuerySessionPool(driver=MagicMock(), size=2, name="async-pool")
        session = MagicMock()
        session.is_active = True
        session.session_id = "session-1"
        session._session_metrics = SessionMetrics()
        pool._metrics.attach(session)
        session._session_metrics.count_open()
        session._session_metrics.transition("idle")
        pool._queue.put_nowait(session)

        acquired = await pool.acquire()
        assert acquired is session

        values = {
            tuple(sorted(point.attributes.items())): point.value
            for point in _points(metrics_setup, QUERY_SESSION_COUNT)
        }
        assert values[(("ydb.query.session.pool.name", "async-pool"), ("ydb.query.session.state", "used"))] == 1
        assert (("ydb.query.session.pool.name", "async-pool"), ("ydb.query.session.state", "idle")) not in values
        session._session_metrics.count_closed()
        pool._metrics.close()

    @pytest.mark.asyncio
    async def test_async_pool_release_updates_session_count(self, metrics_setup):
        from ydb.aio.query.pool import QuerySessionPool
        from ydb.observability.metrics import QUERY_SESSION_COUNT, SessionMetrics

        pool = QuerySessionPool(driver=MagicMock(), size=2, name="async-pool")
        session = MagicMock()
        session.session_id = "session-1"
        session._session_metrics = SessionMetrics()
        pool._metrics.attach(session)
        session._session_metrics.count_open()
        await pool.release(session)

        values = {
            tuple(sorted(point.attributes.items())): point.value
            for point in _points(metrics_setup, QUERY_SESSION_COUNT)
        }
        assert values[(("ydb.query.session.pool.name", "async-pool"), ("ydb.query.session.state", "idle"))] == 1
        assert (("ydb.query.session.pool.name", "async-pool"), ("ydb.query.session.state", "used")) not in values
        session._session_metrics.count_closed()
        pool._metrics.close()

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
        pool._metrics.close()

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
        pool._metrics.close()

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
        assert _single_point_for_pool(metrics_setup, QUERY_SESSION_COUNT, "async-session-pool").value == 1
        qs._close_session()


def test_opentelemetry_load_tank_topic_payload_has_exact_size():
    from examples.opentelemetry.load_tank import _topic_payload

    assert _topic_payload(42, 64).startswith(b"42:")
    assert len(_topic_payload(42, 64)) == 64
    assert len(_topic_payload(42, 1)) == 1


@pytest.mark.asyncio
async def test_opentelemetry_load_tank_retry_probe_records_multiple_attempts(metrics_setup, monkeypatch):
    import asyncio
    from types import SimpleNamespace

    import ydb
    from examples.opentelemetry.load_tank import _retry_probe_worker
    from ydb.observability.metrics import RETRY_ATTEMPTS

    stop = asyncio.Event()
    retry_operation_async = ydb.retry_operation_async

    async def run_once(*args, **kwargs):
        result = await retry_operation_async(*args, **kwargs)
        stop.set()
        return result

    monkeypatch.setattr(ydb, "retry_operation_async", run_once)
    await _retry_probe_worker(
        SimpleNamespace(retry_probe_interval=1.0, retry_probe_failures=2),
        stop,
    )

    retry_attempts = _single_point(metrics_setup, RETRY_ATTEMPTS)
    assert retry_attempts.count == 1
    assert retry_attempts.sum == 3


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("query_error", "should_raise"),
    [
        (issues.SchemeError("expected query failure"), False),
        (RuntimeError("unexpected failure"), True),
    ],
)
async def test_opentelemetry_load_tank_error_worker_only_suppresses_expected_error(
    query_error,
    should_raise,
):
    from examples.opentelemetry.load_tank import _error_worker

    stop = asyncio.Event()

    async def execute_with_retries(_):
        stop.set()
        raise query_error

    pool = SimpleNamespace(execute_with_retries=execute_with_retries)
    config = SimpleNamespace(error_query="missing table", error_rps=1)
    if should_raise:
        with pytest.raises(RuntimeError, match="unexpected failure"):
            await _error_worker(pool, config, stop)
    else:
        await _error_worker(pool, config, stop)


def test_opentelemetry_metric_verifier_detects_prometheus_series(monkeypatch):
    from examples.opentelemetry.verify_metrics import _prometheus_has_series

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def read(self):
            return b'{"status":"success","data":{"result":[{"value":[1,"1"]}]}}'

    urlopen = MagicMock(return_value=FakeResponse())
    monkeypatch.setattr("urllib.request.urlopen", urlopen)

    assert _prometheus_has_series("http://prometheus:9090", "ydb_query_session_count")
    assert "query=count%28ydb_query_session_count%29" in urlopen.call_args.args[0]


def test_opentelemetry_metric_verifier_scopes_every_check_to_current_run():
    from examples.opentelemetry.verify_metrics import _metric_checks

    checks = _metric_checks('current-run"with\\escaping')

    assert all('service_instance_id="current-run\\"with\\\\escaping"' in check.promql for check in checks)
    error_check = next(check for check in checks if check.requires_error_probe)
    assert 'reader_name="load-tank-topic-error-probe"' in error_check.promql
    assert 'retry_decision="stop"' in error_check.promql
    assert 'status_code="SCHEME_ERROR"' in error_check.promql


def test_opentelemetry_metric_verifier_respects_total_timeout(monkeypatch):
    from examples.opentelemetry import verify_metrics

    now = 100.0
    request_timeouts = []

    def monotonic():
        return now

    def query_has_result(_, __, timeout):
        nonlocal now
        request_timeouts.append(timeout)
        now += timeout
        return False

    monkeypatch.setattr(verify_metrics.time, "monotonic", monotonic)
    monkeypatch.setattr(verify_metrics, "_prometheus_query_has_result", query_has_result)

    checks = (
        verify_metrics.MetricCheck("first", "first_metric"),
        verify_metrics.MetricCheck("second", "second_metric"),
    )
    missing = verify_metrics.wait_for_metrics(
        "http://prometheus:9090",
        checks,
        timeout=3,
        poll_interval=10,
    )

    assert request_timeouts == [3]
    assert tuple(missing) == ("first_metric", "second_metric")


def test_opentelemetry_dashboard_keeps_topic_reader_instances_separate():
    import json
    from pathlib import Path

    dashboard = json.loads(
        Path("examples/opentelemetry/grafana/dashboards/ydb-python-sdk-metrics.json").read_text(encoding="utf-8")
    )
    topic_reader_targets = [
        target
        for panel in dashboard["panels"]
        for target in panel.get("targets", ())
        if "ydb_topic_reader_" in target.get("expr", "")
    ]

    assert topic_reader_targets
    for target in topic_reader_targets:
        assert all(label in target["expr"] for label in ("service_instance_id", "endpoint", "database", "consumer"))


def test_opentelemetry_load_tank_publishes_current_run_id():
    from pathlib import Path
    from tempfile import TemporaryDirectory

    from examples.opentelemetry.load_tank import _publish_run_id

    with TemporaryDirectory(dir=".") as directory:
        run_id_file = Path(directory) / "metrics" / "run-id"
        ready_file = Path(directory) / "ready"
        _publish_run_id("current-run", str(run_id_file), str(ready_file))

        assert run_id_file.read_text(encoding="utf-8") == "current-run\n"
        assert ready_file.is_file()


@pytest.mark.asyncio
async def test_opentelemetry_load_tank_propagates_background_failure():
    from examples.opentelemetry.load_tank import _await_with_background

    async def fail():
        raise ValueError("topic failed")

    task = asyncio.create_task(fail())
    with pytest.raises(RuntimeError, match="topic stream worker failed") as error:
        await _await_with_background(asyncio.sleep(60), {task: "topic stream worker"})

    assert isinstance(error.value.__cause__, ValueError)


@pytest.mark.asyncio
@pytest.mark.parametrize("cancelled", [False, True])
async def test_opentelemetry_load_tank_detects_stopped_background_task(cancelled):
    from examples.opentelemetry.load_tank import _await_with_background

    task = asyncio.create_task(asyncio.sleep(0 if not cancelled else 60))
    if cancelled:
        task.cancel()

    message = "worker was cancelled unexpectedly" if cancelled else "worker stopped unexpectedly"
    with pytest.raises(RuntimeError, match=message):
        await _await_with_background(asyncio.sleep(60), {task: "worker"})


@pytest.mark.asyncio
async def test_opentelemetry_load_tank_propagates_failure_during_worker_cancellation():
    from examples.opentelemetry.load_tank import _cancel_background_tasks

    async def fail_during_cancellation():
        try:
            await asyncio.sleep(60)
        except asyncio.CancelledError as error:
            raise ValueError("cleanup failed") from error

    task = asyncio.create_task(fail_during_cancellation())
    await asyncio.sleep(0)
    with pytest.raises(RuntimeError, match="worker failed") as error:
        await _cancel_background_tasks({task: "worker"}, raise_failures=True)

    assert isinstance(error.value.__cause__, ValueError)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("probe_error", "expected_error"),
    [
        (issues.SchemeError("missing topic"), None),
        (RuntimeError("unexpected failure"), RuntimeError),
    ],
)
async def test_opentelemetry_load_tank_topic_error_probe_is_strict(
    monkeypatch,
    probe_error,
    expected_error,
):
    import ydb
    from examples.opentelemetry.load_tank import _topic_error_probe

    class Reader:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        async def wait_message(self):
            raise probe_error

    class Driver:
        def __init__(self, **_):
            self.topic_client = SimpleNamespace(reader=lambda *args, **kwargs: Reader())

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

    monkeypatch.setattr(ydb.aio, "Driver", Driver)
    config = SimpleNamespace(
        database="/local",
        topic_error_probe_endpoint="grpc://localhost:2136",
        topic_error_probe_seconds=1,
    )

    if expected_error is None:
        await _topic_error_probe(config)
    else:
        with pytest.raises(expected_error, match="unexpected failure"):
            await _topic_error_probe(config)
