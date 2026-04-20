"""Unit tests for OpenTelemetry tracing — synchronous SDK operations.

Uses an in-memory span exporter to verify that correct spans, attributes,
parent-child relationships, and error handling are produced by the SDK.
No real YDB connection is needed.
"""

from unittest.mock import MagicMock, patch
from opentelemetry import trace
from opentelemetry.trace import StatusCode, SpanKind
from ydb.opentelemetry.tracing import _registry, create_ydb_span
from ydb.query.transaction import QueryTxStateEnum
from .conftest import FakeDriverConfig

import pytest


def _get_spans(exporter, name=None):
    spans = exporter.get_finished_spans()
    if name is not None:
        spans = [s for s in spans if s.name == name]
    return spans


def _get_single_span(exporter, name):
    spans = _get_spans(exporter, name)
    assert (
        len(spans) == 1
    ), f"Expected 1 span named '{name}', got {len(spans)}: {[s.name for s in exporter.get_finished_spans()]}"
    return spans[0]


def _make_session_mock(driver_config=None, peer_endpoint=None):
    """Create a mock that behaves like a sync QuerySession after create()."""
    cfg = driver_config or FakeDriverConfig()
    driver = MagicMock()
    driver._driver_config = cfg

    session = MagicMock()
    session._driver = driver
    session._session_id = "test-session-id"
    session._node_id = 12345
    session._peer_endpoint = peer_endpoint
    session.session_id = "test-session-id"
    session.node_id = 12345
    return session, driver


def _make_tx(session, driver):
    """Create a real QueryTxContext wired to mocked session/driver."""
    from ydb._grpc.grpcwrapper.ydb_query_public_types import QuerySerializableReadWrite
    from ydb.query.transaction import QueryTxContext

    tx = QueryTxContext(driver, session, QuerySerializableReadWrite())
    # Simulate that the transaction has been started (so commit/rollback create spans)
    tx._tx_state._change_state(QueryTxStateEnum.BEGINED)
    tx._tx_state.tx_id = "test-tx-id"
    return tx


class TestCreateSessionSpan:
    def test_create_session_emits_span(self, otel_setup):
        exporter = otel_setup

        from ydb.query.session import QuerySession

        qs = QuerySession.__new__(QuerySession)
        cfg = FakeDriverConfig()
        driver = MagicMock()
        driver._driver_config = cfg
        qs._driver = driver
        qs._session_id = None
        qs._closed = False

        with patch.object(QuerySession, "_create_call", return_value=None):
            with patch.object(QuerySession, "_attach", return_value=None):
                qs.create()

        span = _get_single_span(exporter, "ydb.CreateSession")
        assert span.kind == SpanKind.CLIENT
        attrs = dict(span.attributes)
        assert attrs["db.system.name"] == "ydb"
        assert attrs["db.namespace"] == "/test_database"
        assert attrs["server.address"] == "test_endpoint"
        assert attrs["server.port"] == 1337
        assert span.status.status_code == StatusCode.UNSET


class TestExecuteQuerySpan:
    def test_session_execute_emits_span(self, otel_setup):
        exporter = otel_setup

        from ydb.query.session import QuerySession

        qs = QuerySession.__new__(QuerySession)
        cfg = FakeDriverConfig()
        driver = MagicMock()
        driver._driver_config = cfg
        qs._driver = driver
        qs._session_id = "test-session-id"
        qs._node_id = 12345
        qs._peer_endpoint = "node-7.cluster:2136"
        qs._closed = False

        fake_stream = iter([])  # empty stream that raises StopIteration immediately
        with patch.object(QuerySession, "_execute_call", return_value=fake_stream):
            result = qs.execute("SELECT 1;")
            # Consume the iterator to finish the span
            list(result)

        span = _get_single_span(exporter, "ydb.ExecuteQuery")
        assert span.kind == SpanKind.CLIENT
        attrs = dict(span.attributes)
        assert attrs["db.system.name"] == "ydb"
        assert attrs["db.namespace"] == "/test_database"
        assert attrs["server.address"] == "test_endpoint"
        assert attrs["server.port"] == 1337
        assert attrs["network.peer.address"] == "node-7.cluster"
        assert attrs["network.peer.port"] == 2136
        assert attrs["ydb.session.id"] == "test-session-id"
        assert attrs["ydb.node.id"] == 12345

    def test_tx_execute_emits_span_with_tx_id(self, otel_setup):
        exporter = otel_setup
        session, driver = _make_session_mock()
        tx = _make_tx(session, driver)

        fake_stream = iter([])
        with patch.object(type(tx), "_execute_call", return_value=fake_stream):
            tx._prev_stream = None
            result = tx.execute("SELECT 1;")
            list(result)

        span = _get_single_span(exporter, "ydb.ExecuteQuery")
        attrs = dict(span.attributes)
        assert attrs["ydb.tx.id"] == "test-tx-id"
        assert attrs["ydb.session.id"] == "test-session-id"
        assert attrs["ydb.node.id"] == 12345


class TestCommitSpan:
    def test_commit_emits_span(self, otel_setup):
        exporter = otel_setup
        session, driver = _make_session_mock()
        tx = _make_tx(session, driver)

        with patch.object(type(tx), "_commit_call", return_value=None):
            tx.commit()

        span = _get_single_span(exporter, "ydb.Commit")
        assert span.kind == SpanKind.CLIENT
        attrs = dict(span.attributes)
        assert attrs["db.system.name"] == "ydb"
        assert attrs["ydb.tx.id"] == "test-tx-id"
        assert attrs["ydb.session.id"] == "test-session-id"
        assert attrs["ydb.node.id"] == 12345


class TestRollbackSpan:
    def test_rollback_emits_span(self, otel_setup):
        exporter = otel_setup
        session, driver = _make_session_mock()
        tx = _make_tx(session, driver)

        with patch.object(type(tx), "_rollback_call", return_value=None):
            tx.rollback()

        span = _get_single_span(exporter, "ydb.Rollback")
        assert span.kind == SpanKind.CLIENT
        attrs = dict(span.attributes)
        assert attrs["db.system.name"] == "ydb"
        assert attrs["ydb.tx.id"] == "test-tx-id"
        assert attrs["ydb.session.id"] == "test-session-id"
        assert attrs["ydb.node.id"] == 12345


class TestErrorHandling:
    def test_error_sets_error_status_and_attributes(self, otel_setup):
        exporter = otel_setup

        from ydb import issues

        exc = issues.SchemeError("Table not found")

        from ydb.query.session import QuerySession

        qs = QuerySession.__new__(QuerySession)
        cfg = FakeDriverConfig()
        driver = MagicMock()
        driver._driver_config = cfg
        qs._driver = driver
        qs._session_id = "test-session-id"
        qs._node_id = 12345
        qs._closed = False

        with patch.object(QuerySession, "_execute_call", side_effect=exc):
            with pytest.raises(issues.SchemeError):
                qs.execute("SELECT * FROM non_existing_table")

        span = _get_single_span(exporter, "ydb.ExecuteQuery")
        assert span.status.status_code == StatusCode.ERROR
        attrs = dict(span.attributes)
        assert attrs["error.type"] == "ydb_error"
        assert attrs["db.response.status_code"] == "SCHEME_ERROR"
        assert len(span.events) > 0


class TestNoSpansWhenDisabled:
    def test_no_spans_without_enable_tracing(self):
        """Without enable_tracing(), the registry uses noop — no spans are created."""

        from tests.tracing.conftest import _exporter

        _registry.set_create_span(None)
        _registry.set_metadata_hook(None)
        _exporter.clear()

        with create_ydb_span("ydb.CreateSession", FakeDriverConfig()):
            pass

        assert len(_exporter.get_finished_spans()) == 0


class TestParentChildRelationship:
    def test_sdk_span_is_child_of_user_span(self, otel_setup):
        exporter = otel_setup

        tracer = trace.get_tracer("test.tracer")

        with tracer.start_as_current_span("user.operation"):
            with create_ydb_span("ydb.ExecuteQuery", FakeDriverConfig(), session_id="s1", node_id=1):
                pass

        spans = exporter.get_finished_spans()
        ydb_span = next(s for s in spans if s.name == "ydb.ExecuteQuery")
        user_span = next(s for s in spans if s.name == "user.operation")

        assert ydb_span.parent is not None
        assert ydb_span.parent.span_id == user_span.context.span_id
        assert ydb_span.context.trace_id == user_span.context.trace_id


class TestTraceMetadataInjection:
    def test_get_trace_metadata_returns_traceparent(self, otel_setup):
        from ydb.opentelemetry.tracing import get_trace_metadata

        tracer = trace.get_tracer("test.tracer")

        with tracer.start_as_current_span("test.span"):
            metadata = get_trace_metadata()

        keys = [k for k, v in metadata]
        assert "traceparent" in keys


class TestDriverInitializeSpan:
    def test_driver_initialize_emits_internal_span(self, otel_setup):
        exporter = otel_setup

        cfg = FakeDriverConfig()

        with create_ydb_span("ydb.Driver.Initialize", cfg, kind="internal"):
            pass

        span = _get_single_span(exporter, "ydb.Driver.Initialize")
        assert span.kind == SpanKind.INTERNAL
        attrs = dict(span.attributes)
        assert attrs["db.system.name"] == "ydb"
        assert attrs["db.namespace"] == "/test_database"


class TestCommonAttributes:
    @pytest.mark.parametrize(
        "endpoint,expected_host,expected_port",
        [
            ("grpc://host.example.com:2136", "grpc://host.example.com", 2136),
            ("localhost:2136", "localhost", 2136),
        ],
    )
    def test_endpoint_parsing(self, otel_setup, endpoint, expected_host, expected_port):
        exporter = otel_setup
        cfg = FakeDriverConfig(endpoint=endpoint, database="/mydb")

        with create_ydb_span("ydb.Test", cfg):
            pass

        span = _get_single_span(exporter, "ydb.Test")
        attrs = dict(span.attributes)
        assert attrs["server.address"] == expected_host
        assert attrs["server.port"] == expected_port
        assert attrs["db.namespace"] == "/mydb"

    def test_peer_attributes_are_optional(self, otel_setup):
        exporter = otel_setup
        cfg = FakeDriverConfig()

        with create_ydb_span("ydb.Test", cfg):
            pass

        span = _get_single_span(exporter, "ydb.Test")
        attrs = dict(span.attributes)
        assert "network.peer.address" not in attrs
        assert "network.peer.port" not in attrs

    def test_peer_attributes_emitted_when_known(self, otel_setup):
        exporter = otel_setup
        cfg = FakeDriverConfig()

        with create_ydb_span("ydb.Test", cfg, peer_endpoint="peer.example.com:2137"):
            pass

        span = _get_single_span(exporter, "ydb.Test")
        attrs = dict(span.attributes)
        assert attrs["network.peer.address"] == "peer.example.com"
        assert attrs["network.peer.port"] == 2137


class TestRetryPolicySpans:
    def test_success_on_first_try_emits_single_try(self, otel_setup):
        from ydb.query._retries import retry_operation_sync

        exporter = otel_setup

        def callee():
            return 42

        assert retry_operation_sync(callee) == 42

        run = _get_single_span(exporter, "ydb.RunWithRetry")
        assert run.kind == SpanKind.INTERNAL
        assert run.status.status_code == StatusCode.UNSET

        tries = _get_spans(exporter, "ydb.Try")
        assert len(tries) == 1
        assert tries[0].kind == SpanKind.INTERNAL
        assert dict(tries[0].attributes)["ydb.retry.backoff_ms"] == 0
        assert tries[0].parent.span_id == run.context.span_id

    def test_retry_backoff_ms_on_each_try(self, otel_setup):
        from ydb import issues
        from ydb.query._retries import retry_operation_sync
        from ydb.retries import RetrySettings, BackoffSettings

        exporter = otel_setup
        counter = {"n": 0}

        def flaky():
            counter["n"] += 1
            if counter["n"] < 3:
                raise issues.Unavailable("transient")
            return "ok"

        retry_settings = RetrySettings(
            max_retries=5,
            fast_backoff_settings=BackoffSettings(ceiling=0, slot_duration=0.05),
            slow_backoff_settings=BackoffSettings(ceiling=0, slot_duration=0.05),
        )

        assert retry_operation_sync(flaky, retry_settings) == "ok"

        tries = _get_spans(exporter, "ydb.Try")
        assert len(tries) == 3
        # first attempt has no preceding backoff, later ones have a positive one
        backoff_values = [dict(s.attributes)["ydb.retry.backoff_ms"] for s in tries]
        assert backoff_values[0] == 0
        assert all(v >= 0 for v in backoff_values)
        assert any(v > 0 for v in backoff_values[1:])
        # failed Try spans record the exception
        assert tries[0].status.status_code == StatusCode.ERROR
        assert tries[1].status.status_code == StatusCode.ERROR
        assert tries[2].status.status_code == StatusCode.UNSET

    def test_non_retryable_error_propagates_to_run_span(self, otel_setup):
        from ydb import issues
        from ydb.query._retries import retry_operation_sync

        exporter = otel_setup

        def broken():
            raise issues.SchemeError("boom")

        with pytest.raises(issues.SchemeError):
            retry_operation_sync(broken)

        run = _get_single_span(exporter, "ydb.RunWithRetry")
        assert run.status.status_code == StatusCode.ERROR

        tries = _get_spans(exporter, "ydb.Try")
        assert len(tries) == 1
        assert tries[0].status.status_code == StatusCode.ERROR
        attrs = dict(tries[0].attributes)
        assert attrs["error.type"] == "ydb_error"
        assert attrs["db.response.status_code"] == "SCHEME_ERROR"
