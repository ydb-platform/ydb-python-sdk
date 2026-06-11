import asyncio
from unittest import mock

import pytest

from ydb._grpc.common.protos import ydb_query_pb2
from ydb.aio.pool import ConnectionPool as AsyncConnectionPool
from ydb.pool import ConnectionPool
from ydb.query.session import QuerySession


def _make_session(node_id=42):
    driver = mock.Mock()
    driver._pessimize_node = mock.Mock()
    session = QuerySession(driver)
    session._session_id = "test-session"
    session._node_id = node_id
    return session, driver


class TestQuerySessionAttachHints:
    def test_node_shutdown_pessimizes_node_and_invalidates_session(self):
        session, driver = _make_session(node_id=42)

        session._handle_attach_session_state(
            ydb_query_pb2.SessionState(
                status=0,
                node_shutdown=ydb_query_pb2.NodeShutdownHint(),
            )
        )

        driver._pessimize_node.assert_called_once_with(42)
        assert session._invalidated
        assert session._closed

    def test_session_shutdown_invalidates_without_pessimizing_node(self):
        session, driver = _make_session(node_id=42)

        session._handle_attach_session_state(
            ydb_query_pb2.SessionState(
                status=0,
                session_shutdown=ydb_query_pb2.SessionShutdownHint(),
            )
        )

        driver._pessimize_node.assert_not_called()
        assert session._invalidated
        assert session._closed

    def test_node_shutdown_with_zero_node_id_delegates_to_driver(self):
        session, driver = _make_session(node_id=0)

        session._handle_attach_session_state(
            ydb_query_pb2.SessionState(
                status=0,
                node_shutdown=ydb_query_pb2.NodeShutdownHint(),
            )
        )

        driver._pessimize_node.assert_called_once_with(0)
        assert session._invalidated

    def test_node_shutdown_without_node_id_skips_pessimization(self):
        session, driver = _make_session(node_id=None)

        session._handle_attach_session_state(
            ydb_query_pb2.SessionState(
                status=0,
                node_shutdown=ydb_query_pb2.NodeShutdownHint(),
            )
        )

        driver._pessimize_node.assert_not_called()
        assert session._invalidated
        assert session._closed

    def test_no_hint_does_not_invalidate(self):
        session, driver = _make_session()

        session._handle_attach_session_state(
            ydb_query_pb2.SessionState(status=0),
        )

        driver._pessimize_node.assert_not_called()
        assert not session._invalidated
        assert not session._closed


class TestConnectionPoolAttachHintPessimization:
    def test_sync_pool_pessimizes_node_connection(self):
        pool = ConnectionPool.__new__(ConnectionPool)
        connection = mock.Mock()
        pool._store = mock.Mock()
        pool._store.connections_by_node_id = {42: connection}
        pool._on_disconnected = mock.Mock()

        pool._pessimize_node(42)

        pool._on_disconnected.assert_called_once_with(connection)

    def test_sync_pool_ignores_missing_node_connection(self):
        pool = ConnectionPool.__new__(ConnectionPool)
        pool._store = mock.Mock()
        pool._store.connections_by_node_id = {}
        pool._on_disconnected = mock.Mock()

        pool._pessimize_node(42)
        pool._pessimize_node(0)

        pool._on_disconnected.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_pool_pessimizes_node_connection(self):
        pool = AsyncConnectionPool.__new__(AsyncConnectionPool)
        connection = mock.Mock()
        disconnect = mock.AsyncMock()
        pool._store = mock.Mock()
        pool._store.connections_by_node_id = {42: connection}
        pool._on_disconnected = mock.Mock(return_value=disconnect)

        pool._pessimize_node(42)
        await asyncio.sleep(0)

        pool._on_disconnected.assert_called_once_with(connection)
        disconnect.assert_awaited_once_with()
