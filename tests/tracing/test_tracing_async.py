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


def _make_async_session_mock(driver_config=None):
    """Create a mock that behaves like an async QuerySession after create()."""
    cfg = driver_config or FakeDriverConfig()
    driver = MagicMock()
    driver._driver_config = cfg

    session = MagicMock()
    session._driver = driver
    session._session_id = "test-session-id"
    session._node_id = 12345
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
        qs._closed = False

        fake_stream = _empty_async_iter()
        with patch.object(QuerySession, "_execute_call", new_callable=AsyncMock, return_value=fake_stream):
            result = await qs.execute("SELECT 1;")
            async for _ in result:
                pass

        span = _get_single_span(exporter, "ydb.ExecuteQuery")
        attrs = dict(span.attributes)
        assert attrs["ydb.session.id"] == "test-session-id"
        assert attrs["ydb.node.id"] == 12345

    @pytest.mark.asyncio
    async def test_tx_execute_emits_span_with_tx_id(self, otel_setup):
        exporter = otel_setup
        session, driver = _make_async_session_mock()
        tx = _make_async_tx(session, driver)

        fake_stream = _empty_async_iter()
        with patch.object(type(tx), "_execute_call", new_callable=AsyncMock, return_value=fake_stream):
            tx._prev_stream = None
            result = await tx.execute("SELECT 1;")
            async for _ in result:
                pass

        span = _get_single_span(exporter, "ydb.ExecuteQuery")
        attrs = dict(span.attributes)
        assert attrs["ydb.tx.id"] == "test-tx-id"
        assert attrs["ydb.session.id"] == "test-session-id"
        assert attrs["ydb.node.id"] == 12345


class TestAsyncCommitSpan:
    @pytest.mark.asyncio
    async def test_commit_emits_span(self, otel_setup):
        exporter = otel_setup
        session, driver = _make_async_session_mock()
        tx = _make_async_tx(session, driver)

        with patch.object(type(tx), "_commit_call", new_callable=AsyncMock):
            await tx.commit()

        span = _get_single_span(exporter, "ydb.Commit")
        assert span.kind == SpanKind.CLIENT
        attrs = dict(span.attributes)
        assert attrs["ydb.tx.id"] == "test-tx-id"
        assert attrs["ydb.session.id"] == "test-session-id"


class TestAsyncRollbackSpan:
    @pytest.mark.asyncio
    async def test_rollback_emits_span(self, otel_setup):
        exporter = otel_setup
        session, driver = _make_async_session_mock()
        tx = _make_async_tx(session, driver)

        with patch.object(type(tx), "_rollback_call", new_callable=AsyncMock):
            await tx.rollback()

        span = _get_single_span(exporter, "ydb.Rollback")
        assert span.kind == SpanKind.CLIENT
        attrs = dict(span.attributes)
        assert attrs["ydb.tx.id"] == "test-tx-id"
        assert attrs["ydb.session.id"] == "test-session-id"


class TestAsyncErrorHandling:
    @pytest.mark.asyncio
    async def test_error_sets_error_status(self, otel_setup):
        exporter = otel_setup

        from ydb import issues

        class FakeStatus:
            name = "SCHEME_ERROR"

        exc = issues.SchemeError("Table not found")
        exc.status = FakeStatus()

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
        assert attrs["error.type"] == "SCHEME_ERROR"
        assert len(span.events) > 0


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
