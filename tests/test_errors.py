import unittest.mock

import grpc
import ydb
import pytest

from os import path
from ydb.connection import _rpc_error_handler


def _make_rpc_error(code, details):
    error = unittest.mock.MagicMock(spec=grpc.Call)
    error.code.return_value = code
    error.details.return_value = details
    return error


def test_resource_exhausted_large_message_returns_bad_request():
    rpc_error = _make_rpc_error(
        grpc.StatusCode.RESOURCE_EXHAUSTED,
        "CLIENT: Sent message larger than max (101289032 vs. 64000000)",
    )
    result = _rpc_error_handler("test_rpc", rpc_error)
    assert isinstance(result, ydb.issues.BadRequest)


def test_resource_exhausted_other_reason_returns_connection_lost():
    rpc_error = _make_rpc_error(
        grpc.StatusCode.RESOURCE_EXHAUSTED,
        "Quota exceeded",
    )
    result = _rpc_error_handler("test_rpc", rpc_error)
    assert isinstance(result, ydb.issues.ConnectionLost)


def test_scheme_error(driver_sync, database):
    session = driver_sync.table_client.session().create()
    with pytest.raises(ydb.issues.SchemeError) as exc:
        session.drop_table(path.join(database, "foobartable"))

    server_code = ydb.issues.StatusCode.SCHEME_ERROR

    assert type(exc.value) is ydb.issues.SchemeError
    assert exc.value.status == server_code
    assert f"server_code: {server_code}" in str(exc.value)
    assert "Path does not exist" in str(exc.value)
