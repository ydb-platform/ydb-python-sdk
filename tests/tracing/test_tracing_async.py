"""Unit tests for OpenTelemetry tracing — asynchronous SDK operations.

Mirrors the sync tests but exercises the async code paths in ydb.aio.query.
"""

from opentelemetry.trace import StatusCode, SpanKind
from ydb.query.transaction import QueryTxStateEnum
from .conftest import FakeDriverConfig
from unittest.mock import AsyncMock, MagicMock, patch

import asyncio
import pytest


async def _empty_async_iter():
    return
    yield  # noqa: makes this an async generator


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


def _make_async_session_mock(driver_config=None, peer=None):
    """Create a mock that behaves like an async QuerySession after create()."""
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


def _make_async_tx(session, driver):
    """Create a real async QueryTxContext wired to mocked session/driver."""
    from ydb._grpc.grpcwrapper.ydb_query_public_types import QuerySerializableReadWrite
    from ydb.aio.query.transaction import QueryTxContext

    tx = QueryTxContext(driver, session, QuerySerializableReadWrite())
    tx._tx_state._change_state(QueryTxStateEnum.BEGINED)
    tx._tx_state.tx_id = "test-tx-id"
    return tx


class TestAsyncCreateSessionSpan:
    @pytest.mark.asyncio
    async def test_create_session_emits_span(self, otel_setup):
        exporter = otel_setup

        from ydb.aio.query.session import QuerySession

        qs = QuerySession.__new__(QuerySession)
        cfg = FakeDriverConfig()
        driver = MagicMock()
        driver._driver_config = cfg
        qs._driver = driver
        qs._session_id = None
        qs._closed = False

        with patch.object(QuerySession, "_create_call", new_callable=AsyncMock):
            with patch.object(QuerySession, "_attach", new_callable=AsyncMock):
                await qs.create()

        span = _get_single_span(exporter, "ydb.CreateSession")
        assert span.kind == SpanKind.CLIENT
        attrs = dict(span.attributes)
        assert attrs["db.system.name"] == "ydb"
        assert attrs["db.namespace"] == "/test_database"
        assert attrs["server.address"] == "test_endpoint"
        assert attrs["server.port"] == 1337


class TestAsyncExecuteQuerySpan:
    @pytest.mark.asyncio
    async def test_session_execute_emits_span(self, otel_setup):
        exporter = otel_setup

        from ydb.aio.query.session import QuerySession

        qs = QuerySession.__new__(QuerySession)
        cfg = FakeDriverConfig()
        driver = MagicMock()
        driver._driver_config = cfg
        qs._driver = driver
        qs._session_id = "test-session-id"
        qs._node_id = 12345
        qs._peer = ("n1", 2136, "dc-a")
        qs._closed = False

        fake_stream = _empty_async_iter()
        with patch.object(QuerySession, "_execute_call", new_callable=AsyncMock, return_value=fake_stream):
            result = await qs.execute("SELECT 1;")
            async for _ in result:
                pass

        span = _get_single_span(exporter, "ydb.ExecuteQuery")
        attrs = dict(span.attributes)
        assert attrs["ydb.node.id"] == 12345
        assert attrs["network.peer.address"] == "n1"
        assert attrs["ydb.node.dc"] == "dc-a"
        assert "ydb.session.id" not in attrs

    @pytest.mark.asyncio
    async def test_tx_execute_emits_span(self, otel_setup):
        exporter = otel_setup
        session, driver = _make_async_session_mock(peer=("n1", 2136, "dc-a"))
        tx = _make_async_tx(session, driver)

        fake_stream = _empty_async_iter()
        with patch.object(type(tx), "_execute_call", new_callable=AsyncMock, return_value=fake_stream):
            tx._prev_stream = None
            result = await tx.execute("SELECT 1;")
            async for _ in result:
                pass

        span = _get_single_span(exporter, "ydb.ExecuteQuery")
        attrs = dict(span.attributes)
        assert attrs["ydb.node.id"] == 12345
        assert attrs["network.peer.address"] == "n1"
        assert attrs["ydb.node.dc"] == "dc-a"
        assert "ydb.tx.id" not in attrs
        assert "ydb.session.id" not in attrs


class TestAsyncCommitSpan:
    @pytest.mark.asyncio
    async def test_commit_emits_span(self, otel_setup):
        exporter = otel_setup
        session, driver = _make_async_session_mock(peer=("n1", 2136, "dc-a"))
        tx = _make_async_tx(session, driver)

        with patch.object(type(tx), "_commit_call", new_callable=AsyncMock):
            await tx.commit()

        span = _get_single_span(exporter, "ydb.Commit")
        assert span.kind == SpanKind.CLIENT
        attrs = dict(span.attributes)
        assert attrs["network.peer.address"] == "n1"
        assert attrs["ydb.node.dc"] == "dc-a"
        assert "ydb.tx.id" not in attrs
        assert "ydb.session.id" not in attrs


class TestAsyncRollbackSpan:
    @pytest.mark.asyncio
    async def test_rollback_emits_span(self, otel_setup):
        exporter = otel_setup
        session, driver = _make_async_session_mock(peer=("n1", 2136, "dc-a"))
        tx = _make_async_tx(session, driver)

        with patch.object(type(tx), "_rollback_call", new_callable=AsyncMock):
            await tx.rollback()

        span = _get_single_span(exporter, "ydb.Rollback")
        assert span.kind == SpanKind.CLIENT
        attrs = dict(span.attributes)
        assert attrs["network.peer.address"] == "n1"
        assert attrs["ydb.node.dc"] == "dc-a"
        assert "ydb.tx.id" not in attrs
        assert "ydb.session.id" not in attrs


class TestAsyncErrorHandling:
    @pytest.mark.asyncio
    async def test_error_sets_error_status_and_attributes(self, otel_setup):
        exporter = otel_setup

        from ydb import issues

        exc = issues.SchemeError("Table not found")

        from ydb.aio.query.session import QuerySession

        qs = QuerySession.__new__(QuerySession)
        cfg = FakeDriverConfig()
        driver = MagicMock()
        driver._driver_config = cfg
        qs._driver = driver
        qs._session_id = "test-session-id"
        qs._node_id = 12345
        qs._closed = False

        with patch.object(QuerySession, "_execute_call", new_callable=AsyncMock, side_effect=exc):
            with pytest.raises(issues.SchemeError):
                await qs.execute("SELECT * FROM non_existing_table")

        span = _get_single_span(exporter, "ydb.ExecuteQuery")
        assert span.status.status_code == StatusCode.ERROR
        attrs = dict(span.attributes)
        assert attrs["error.type"] == "ydb_error"
        assert attrs["db.response.status_code"] == "SCHEME_ERROR"
        assert len(span.events) > 0


class TestAsyncRetryPolicySpans:
    @pytest.mark.asyncio
    async def test_success_emits_single_try(self, otel_setup):
        from ydb.retries import retry_operation_async

        exporter = otel_setup

        async def callee():
            return 7

        assert await retry_operation_async(callee) == 7

        run = _get_single_span(exporter, "ydb.RunWithRetry")
        assert run.kind == SpanKind.INTERNAL

        tries = _get_spans(exporter, "ydb.Try")
        assert len(tries) == 1
        assert tries[0].parent.span_id == run.context.span_id
        assert "ydb.retry.backoff_ms" not in dict(tries[0].attributes)
        assert tries[0].status.status_code == StatusCode.UNSET

    @pytest.mark.asyncio
    async def test_retry_failed_tries_set_error_status(self, otel_setup):
        """Failed async attempts must set ``ydb.Try`` status to ERROR (not UNSET)."""
        from ydb import issues
        from ydb.retries import BackoffSettings, RetrySettings, retry_operation_async

        exporter = otel_setup
        counter = {"n": 0}

        async def flaky():
            counter["n"] += 1
            if counter["n"] < 3:
                raise issues.Unavailable("transient")
            return "ok"

        retry_settings = RetrySettings(
            max_retries=5,
            fast_backoff_settings=BackoffSettings(ceiling=0, slot_duration=0.05),
            slow_backoff_settings=BackoffSettings(ceiling=0, slot_duration=0.05),
        )

        assert await retry_operation_async(flaky, retry_settings) == "ok"

        tries = _get_spans(exporter, "ydb.Try")
        assert len(tries) == 3
        assert tries[0].status.status_code == StatusCode.ERROR
        assert tries[1].status.status_code == StatusCode.ERROR
        assert tries[2].status.status_code == StatusCode.UNSET

    @pytest.mark.asyncio
    async def test_context_cancel_during_backoff_records_exception(self, otel_setup):
        """Inter-attempt sleep is outside ``ydb.Try``; cancellation during
        ``asyncio.sleep`` is recorded on ``ydb.RunWithRetry`` (``record_exception``).
        """
        from ydb import issues
        from ydb.retries import BackoffSettings, RetrySettings, retry_operation_async

        exporter = otel_setup
        calls = {"n": 0}

        async def flaky():
            calls["n"] += 1
            raise issues.Unavailable("transient")

        retry_settings = RetrySettings(
            max_retries=10,
            fast_backoff_settings=BackoffSettings(ceiling=0, slot_duration=10.0),
            slow_backoff_settings=BackoffSettings(ceiling=0, slot_duration=10.0),
        )

        task = asyncio.ensure_future(retry_operation_async(flaky, retry_settings))
        for _ in range(10):
            await asyncio.sleep(0.01)
            if calls["n"] >= 1:
                break
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        run = _get_single_span(exporter, "ydb.RunWithRetry")
        assert run.status.status_code == StatusCode.ERROR
        # TracingSpan / OTel will attach the cancellation as span events (record_exception) when enabled.
        assert run.events is not None
        # First attempt: ``ydb.Try``; cancel hits ``ydb.RunWithRetry`` during the inter-attempt sleep.
        tries = _get_spans(exporter, "ydb.Try")
        assert len(tries) >= 1


class TestAsyncRetrySpanNesting:
    @pytest.mark.asyncio
    async def test_execute_query_is_child_of_try_under_run_with_retry(self, otel_setup):
        """``ydb.RunWithRetry`` -> ``ydb.Try`` -> ``ydb.ExecuteQuery`` (deep nesting).

        The previous implementation produced sibling spans because ``ydb.Try`` was
        opened *after* the awaitable was created, leaving the gRPC span without an
        active ``ydb.Try`` context. This test pins the corrected nesting.
        """
        from ydb.aio.query.session import QuerySession
        from ydb.retries import retry_operation_async

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

        async def callee():
            fake_stream = _empty_async_iter()
            with patch.object(QuerySession, "_execute_call", new_callable=AsyncMock, return_value=fake_stream):
                result = await qs.execute("SELECT 1;")
                async for _ in result:
                    pass
            return "ok"

        assert await retry_operation_async(callee) == "ok"

        run = _get_single_span(exporter, "ydb.RunWithRetry")
        try_span = _get_single_span(exporter, "ydb.Try")
        exec_span = _get_single_span(exporter, "ydb.ExecuteQuery")

        assert try_span.parent.span_id == run.context.span_id
        assert exec_span.parent.span_id == try_span.context.span_id
        assert exec_span.context.trace_id == run.context.trace_id


class TestAsyncConcurrentSpansIsolation:
    @pytest.mark.asyncio
    async def test_parallel_executes_do_not_become_parent_child(self, otel_setup):
        """Two concurrent execute calls must produce sibling spans, not parent-child."""
        exporter = otel_setup

        from ydb.aio.query.session import QuerySession

        async def _slow_async_iter():
            await asyncio.sleep(0.5)
            return
            yield  # noqa

        def _make_session():
            qs = QuerySession.__new__(QuerySession)
            cfg = FakeDriverConfig()
            driver = MagicMock()
            driver._driver_config = cfg
            qs._driver = driver
            qs._session_id = "test-session-id"
            qs._node_id = 1
            qs._closed = False
            return qs

        async def do_execute(qs):
            fake_stream = _slow_async_iter()
            with patch.object(QuerySession, "_execute_call", new_callable=AsyncMock, return_value=fake_stream):
                result = await qs.execute("SELECT 1")
                async for _ in result:
                    pass

        qs1 = _make_session()
        qs2 = _make_session()
        await asyncio.gather(do_execute(qs1), do_execute(qs2))

        spans = _get_spans(exporter, "ydb.ExecuteQuery")
        assert len(spans) == 2

        ids = {s.context.span_id for s in spans}
        for s in spans:
            if s.parent is not None:
                assert s.parent.span_id not in ids, "Concurrent spans must be siblings, not parent-child"
