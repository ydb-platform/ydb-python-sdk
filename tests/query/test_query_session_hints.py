from unittest import mock

from ydb._grpc.common.protos import ydb_query_pb2
from ydb.query.session import QuerySession


def _make_session(node_id=42):
    driver = mock.Mock()
    driver._store = mock.Mock()
    driver._store.connections_by_node_id = {node_id: mock.Mock()}
    driver._on_disconnected = mock.Mock(return_value=None)
    session = QuerySession(driver)
    session._session_id = "test-session"
    session._node_id = node_id
    return session, driver


class TestQuerySessionAttachHints:
    def test_node_shutdown_pessimizes_node_and_invalidates_session(self):
        session, driver = _make_session(node_id=42)
        connection = driver._store.connections_by_node_id[42]

        session._handle_attach_session_state(
            ydb_query_pb2.SessionState(
                status=0,
                node_shutdown=ydb_query_pb2.NodeShutdownHint(),
            )
        )

        driver._on_disconnected.assert_called_once_with(connection)
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

        driver._on_disconnected.assert_not_called()
        assert session._invalidated
        assert session._closed

    def test_node_shutdown_with_zero_node_id_skips_pessimization(self):
        session, driver = _make_session(node_id=0)

        session._handle_attach_session_state(
            ydb_query_pb2.SessionState(
                status=0,
                node_shutdown=ydb_query_pb2.NodeShutdownHint(),
            )
        )

        driver._on_disconnected.assert_not_called()
        assert session._invalidated

    def test_no_hint_does_not_invalidate(self):
        session, driver = _make_session()

        session._handle_attach_session_state(
            ydb_query_pb2.SessionState(status=0),
        )

        driver._on_disconnected.assert_not_called()
        assert not session._invalidated
        assert not session._closed
