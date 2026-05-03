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


def _make_session_mock(driver_config=None, peer=None):
    """Create a mock that behaves like a sync QuerySession after create()."""
    cfg = driver_config or FakeDriverConfig()
    driver = MagicMock()
    driver._driver_config = cfg

    session = MagicMock()
    session._driver = driver
    session._session_id = "test-session-id"
    session._node_id = 12345
    session._peer = peer
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


def _make_fresh_tx(session, driver):
    """Create a real QueryTxContext in NOT_INITIALIZED state (for begin())."""
    from ydb._grpc.grpcwrapper.ydb_query_public_types import QuerySerializableReadWrite
    from ydb.query.transaction import QueryTxContext

    return QueryTxContext(driver, session, QuerySerializableReadWrite())


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
        qs._peer = ("node-7.cluster", 2136, "dc-east")
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
        assert attrs["ydb.node.dc"] == "dc-east"
        assert attrs["ydb.node.id"] == 12345
        assert "ydb.session.id" not in attrs
        assert "ydb.tx.id" not in attrs

    def test_tx_execute_emits_span(self, otel_setup):
        exporter = otel_setup
        session, driver = _make_session_mock(peer=("n1", 2136, "dc-a"))
        tx = _make_tx(session, driver)

        fake_stream = iter([])
        with patch.object(type(tx), "_execute_call", return_value=fake_stream):
            tx._prev_stream = None
            result = tx.execute("SELECT 1;")
            list(result)

        span = _get_single_span(exporter, "ydb.ExecuteQuery")
        attrs = dict(span.attributes)
        assert attrs["ydb.node.id"] == 12345
        assert attrs["network.peer.address"] == "n1"
        assert attrs["network.peer.port"] == 2136
        assert attrs["ydb.node.dc"] == "dc-a"
        assert "ydb.session.id" not in attrs
        assert "ydb.tx.id" not in attrs


class TestBeginTransactionSpan:
    def test_begin_emits_span(self, otel_setup):
        exporter = otel_setup
        session, driver = _make_session_mock(peer=("n1", 2136, "dc-a"))
        tx = _make_fresh_tx(session, driver)

        with patch.object(type(tx), "_begin_call", return_value=None):
            tx.begin()

        span = _get_single_span(exporter, "ydb.BeginTransaction")
        assert span.kind == SpanKind.CLIENT
        attrs = dict(span.attributes)
        assert attrs["db.system.name"] == "ydb"
        assert attrs["db.namespace"] == "/test_database"
        assert attrs["ydb.node.id"] == 12345
        assert attrs["network.peer.address"] == "n1"
        assert attrs["network.peer.port"] == 2136
        assert attrs["ydb.node.dc"] == "dc-a"
        assert "ydb.session.id" not in attrs
        assert "ydb.tx.id" not in attrs
        assert span.status.status_code == StatusCode.UNSET

    def test_begin_sets_error_status_on_failure(self, otel_setup):
        from ydb import issues

        exporter = otel_setup
        session, driver = _make_session_mock(peer=("n1", 2136, "dc-a"))
        tx = _make_fresh_tx(session, driver)

        exc = issues.Unavailable("bad node")
        with patch.object(type(tx), "_begin_call", side_effect=exc):
            with pytest.raises(issues.Unavailable):
                tx.begin()

        span = _get_single_span(exporter, "ydb.BeginTransaction")
        assert span.status.status_code == StatusCode.ERROR
        attrs = dict(span.attributes)
        assert attrs["error.type"] == "ydb_error"
        assert attrs["db.response.status_code"] == "UNAVAILABLE"
        assert len(span.events) > 0


class TestCommitSpan:
    def test_commit_emits_span(self, otel_setup):
        exporter = otel_setup
        session, driver = _make_session_mock(peer=("n1", 2136, "dc-a"))
        tx = _make_tx(session, driver)

        with patch.object(type(tx), "_commit_call", return_value=None):
            tx.commit()

        span = _get_single_span(exporter, "ydb.Commit")
        assert span.kind == SpanKind.CLIENT
        attrs = dict(span.attributes)
        assert attrs["db.system.name"] == "ydb"
        assert attrs["ydb.node.id"] == 12345
        assert attrs["network.peer.address"] == "n1"
        assert attrs["ydb.node.dc"] == "dc-a"
        assert "ydb.session.id" not in attrs
        assert "ydb.tx.id" not in attrs


class TestRollbackSpan:
    def test_rollback_emits_span(self, otel_setup):
        exporter = otel_setup
        session, driver = _make_session_mock(peer=("n1", 2136, "dc-a"))
        tx = _make_tx(session, driver)

        with patch.object(type(tx), "_rollback_call", return_value=None):
            tx.rollback()

        span = _get_single_span(exporter, "ydb.Rollback")
        assert span.kind == SpanKind.CLIENT
        attrs = dict(span.attributes)
        assert attrs["db.system.name"] == "ydb"
        assert attrs["ydb.node.id"] == 12345
        assert attrs["network.peer.address"] == "n1"
        assert attrs["ydb.node.dc"] == "dc-a"
        assert "ydb.session.id" not in attrs
        assert "ydb.tx.id" not in attrs


class TestCommitRollbackErrorRecording:
    """When the underlying RPC raises, the span must:
    - end with ``StatusCode.ERROR``
    - have ``error.type`` and ``db.response.status_code`` set
    - have the exception recorded as a span event (``record_exception``)
    """

    def test_commit_records_exception_on_failure(self, otel_setup):
        from ydb import issues

        exporter = otel_setup
        session, driver = _make_session_mock(peer=("n1", 2136, "dc-a"))
        tx = _make_tx(session, driver)

        exc = issues.Aborted("boom")
        with patch.object(type(tx), "_commit_call", side_effect=exc):
            with pytest.raises(issues.Aborted):
                tx.commit()

        span = _get_single_span(exporter, "ydb.Commit")
        assert span.status.status_code == StatusCode.ERROR
        attrs = dict(span.attributes)
        assert attrs["error.type"] == "ydb_error"
        assert attrs["db.response.status_code"] == "ABORTED"
        assert any(e.name == "exception" for e in span.events)

    def test_rollback_records_exception_on_failure(self, otel_setup):
        from ydb import issues

        exporter = otel_setup
        session, driver = _make_session_mock(peer=("n1", 2136, "dc-a"))
        tx = _make_tx(session, driver)

        exc = issues.Unavailable("boom")
        with patch.object(type(tx), "_rollback_call", side_effect=exc):
            with pytest.raises(issues.Unavailable):
                tx.rollback()

        span = _get_single_span(exporter, "ydb.Rollback")
        assert span.status.status_code == StatusCode.ERROR
        attrs = dict(span.attributes)
        assert attrs["error.type"] == "ydb_error"
        assert attrs["db.response.status_code"] == "UNAVAILABLE"
        assert any(e.name == "exception" for e in span.events)


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
            with create_ydb_span("ydb.ExecuteQuery", FakeDriverConfig(), node_id=1):
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
            ("grpc://host.example.com:2136", "host.example.com", 2136),
            ("localhost:2136", "localhost", 2136),
            ("[::1]:2136", "[::1]", 2136),
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

        with create_ydb_span("ydb.Test", cfg, peer=("peer.example.com", 2137, "dc-west")):
            pass

        span = _get_single_span(exporter, "ydb.Test")
        attrs = dict(span.attributes)
        assert attrs["network.peer.address"] == "peer.example.com"
        assert attrs["network.peer.port"] == 2137
        assert attrs["ydb.node.dc"] == "dc-west"


class TestPeerFromEndpointMap:
    def test_wrapper_create_session_pulls_peer_from_store(self, otel_setup):
        """wrapper_create_session must resolve peer (host, port, dc) via the driver's
        connections_by_node_id cache, not via the grpc target string of the rpc call.
        """
        from ydb.query.session import wrapper_create_session

        connection = MagicMock()
        connection.endpoint = "ipv4:10.0.0.1:2136"
        connection.peer_address = "node-42.dc-west.example"
        connection.peer_port = 2136
        connection.peer_location = "dc-west"

        driver = MagicMock()
        driver._store.connections_by_node_id = {42: connection}

        session = MagicMock()
        session._driver = driver

        rpc_state = MagicMock()
        rpc_state.endpoint = "ipv4:10.0.0.1:2136"  # grpc-target string — should be ignored

        proto = MagicMock()
        with patch("ydb.query.session._ydb_query.CreateSessionResponse.from_proto") as from_proto:
            from_proto.return_value = MagicMock(session_id="s-1", node_id=42, status=MagicMock())
            with patch("ydb.issues._process_response"):
                wrapper_create_session(rpc_state, proto, session)

        assert session._peer == ("node-42.dc-west.example", 2136, "dc-west")


class TestRetryPolicySpans:
    def test_success_on_first_try_emits_single_try(self, otel_setup):
        from ydb.retries import retry_operation_sync

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
        assert "ydb.retry.backoff_ms" not in dict(tries[0].attributes)
        assert tries[0].parent.span_id == run.context.span_id

    def test_retry_backoff_ms_on_each_try(self, otel_setup):
        from ydb import issues
        from ydb.retries import retry_operation_sync
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
        # First attempt has no preceding backoff, so no attribute at all; later ones
        # carry a positive integer ms.
        attrs0 = dict(tries[0].attributes)
        assert "ydb.retry.backoff_ms" not in attrs0
        later_values = [dict(s.attributes).get("ydb.retry.backoff_ms") for s in tries[1:]]
        assert all(isinstance(v, int) and v > 0 for v in later_values)
        # failed Try spans record the exception
        assert tries[0].status.status_code == StatusCode.ERROR
        assert tries[1].status.status_code == StatusCode.ERROR
        assert tries[2].status.status_code == StatusCode.UNSET

    def test_backoff_ms_attribute_matches_actual_sleep(self, otel_setup, monkeypatch):
        """Pin the closure: ``ydb.retry.backoff_ms`` on the n-th ``ydb.Try`` equals
        the sleep that preceded it, regardless of which retry attempt triggered it.

        Both ``random.random`` and ``time.sleep`` are mocked so the math is fully
        deterministic and the test does not actually wait. With
        ``ceiling=0, slot_duration=0.1, uncertain_ratio=0.5`` and ``random()=0.5``::

            slots_count    = 1
            max_duration   = 1 * 0.1 * 1000  = 100 ms
            duration       = 100 * (0.5*0.5 + 0.5) = 75 ms
        """
        from ydb import issues
        from ydb.retries import retry_operation_sync, RetrySettings, BackoffSettings

        monkeypatch.setattr("random.random", lambda: 0.5)
        sleeps = []
        monkeypatch.setattr("time.sleep", sleeps.append)

        exporter = otel_setup
        counter = {"n": 0}

        def flaky():
            counter["n"] += 1
            if counter["n"] < 3:
                raise issues.Unavailable("transient")
            return "ok"

        settings = RetrySettings(
            max_retries=5,
            fast_backoff_settings=BackoffSettings(ceiling=0, slot_duration=0.1, uncertain_ratio=0.5),
            slow_backoff_settings=BackoffSettings(ceiling=0, slot_duration=0.1, uncertain_ratio=0.5),
        )
        assert retry_operation_sync(flaky, settings) == "ok"

        expected_ms = 75

        tries = _get_spans(exporter, "ydb.Try")
        assert len(tries) == 3
        assert "ydb.retry.backoff_ms" not in dict(tries[0].attributes)
        assert dict(tries[1].attributes)["ydb.retry.backoff_ms"] == expected_ms
        assert dict(tries[2].attributes)["ydb.retry.backoff_ms"] == expected_ms
        assert sleeps == [expected_ms / 1000.0, expected_ms / 1000.0]

    def test_skip_backoff_errors_still_emit_one_try_per_attempt(self, otel_setup):
        """Aborted/BadSession path yields zero sleep but must rotate ydb.Try spans (sync loop)."""
        from ydb import issues
        from ydb.retries import RetrySettings, retry_operation_sync

        exporter = otel_setup
        counter = {"n": 0}

        def flaky():
            counter["n"] += 1
            if counter["n"] < 3:
                raise issues.Aborted("retry me")
            return "ok"

        assert retry_operation_sync(flaky, RetrySettings(max_retries=5)) == "ok"

        tries = _get_spans(exporter, "ydb.Try")
        assert len(tries) == 3
        assert tries[0].status.status_code == StatusCode.ERROR
        assert tries[1].status.status_code == StatusCode.ERROR
        assert tries[2].status.status_code == StatusCode.UNSET
        # First Try has no preceding sleep -> attribute is absent.
        # Skip-yield path means subsequent Tries had no real wait either, but the
        # attribute is still set to 0 to make "we did go through a retry boundary"
        # explicit.
        assert "ydb.retry.backoff_ms" not in dict(tries[0].attributes)
        assert dict(tries[1].attributes)["ydb.retry.backoff_ms"] == 0
        assert dict(tries[2].attributes)["ydb.retry.backoff_ms"] == 0

    def test_non_retryable_error_propagates_to_run_span(self, otel_setup):
        from ydb import issues
        from ydb.retries import retry_operation_sync

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

    def test_execute_query_is_child_of_try_under_run_with_retry(self, otel_setup):
        """``ydb.RunWithRetry`` -> ``ydb.Try`` -> ``ydb.ExecuteQuery`` (sync path)."""
        from ydb.query.session import QuerySession
        from ydb.retries import retry_operation_sync

        exporter = otel_setup

        qs = QuerySession.__new__(QuerySession)
        cfg = FakeDriverConfig()
        driver = MagicMock()
        driver._driver_config = cfg
        qs._driver = driver
        qs._session_id = "test-session-id"
        qs._node_id = 12345
        qs._peer = ("n1", 2136, "dc-a")
        qs._closed = False

        def callee():
            fake_stream = iter([])
            with patch.object(QuerySession, "_execute_call", return_value=fake_stream):
                result = qs.execute("SELECT 1;")
                list(result)
            return "ok"

        assert retry_operation_sync(callee) == "ok"

        run = _get_single_span(exporter, "ydb.RunWithRetry")
        try_span = _get_single_span(exporter, "ydb.Try")
        exec_span = _get_single_span(exporter, "ydb.ExecuteQuery")

        assert try_span.parent.span_id == run.context.span_id
        assert exec_span.parent.span_id == try_span.context.span_id
        assert exec_span.context.trace_id == run.context.trace_id
