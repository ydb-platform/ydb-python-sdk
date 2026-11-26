# -*- coding: utf-8 -*-
import pytest

from ydb import operation, issues, _apis


class _FakeDriver:
    """Records the arguments the client forwards to the driver."""

    def __init__(self, result="RESULT"):
        self._result = result
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        return self._result


def _operation_response(operation_id="op-1", status=issues.StatusCode.SUCCESS):
    return _apis.ydb_operation.GetOperationResponse(
        operation=_apis.ydb_operation.Operation(id=operation_id, status=status)
    )


def test_forget_operation_request():
    request = operation._forget_operation_request("abc")
    assert request.id == "abc"


def test_cancel_operation_request():
    request = operation._cancel_operation_request("xyz")
    assert request.id == "xyz"


def test_get_operation_request():
    op = operation.Operation(None, _operation_response("op-42"))
    request = operation._get_operation_request(op)
    assert request.id == "op-42"


def test_cancel_and_forget_response_success():
    response = _apis.ydb_operation.Operation(status=issues.StatusCode.SUCCESS)
    assert operation._cancel_operation_response(None, response) is None
    assert operation._forget_operation_response(None, response) is None


def test_cancel_response_raises_on_error():
    response = _apis.ydb_operation.Operation(status=issues.StatusCode.BAD_REQUEST)
    with pytest.raises(issues.BadRequest):
        operation._cancel_operation_response(None, response)


def test_operation_init_sets_id_and_repr():
    op = operation.Operation(None, _operation_response("id-1"))
    assert op.id == "id-1"
    assert repr(op) == "<Operation id-1>"
    assert str(op) == "<Operation id-1>"


def test_operation_init_raises_on_error_status():
    response = _apis.ydb_operation.GetOperationResponse(
        operation=_apis.ydb_operation.Operation(status=issues.StatusCode.BAD_REQUEST)
    )
    with pytest.raises(issues.BadRequest):
        operation.Operation(None, response)


def test_operation_without_driver_cannot_dispatch():
    op = operation.Operation(None, _operation_response())
    with pytest.raises(ValueError):
        op.cancel()
    with pytest.raises(ValueError):
        op.forget()
    with pytest.raises(ValueError):
        op.get()


def test_operation_client_cancel_and_forget():
    driver = _FakeDriver()
    client = operation.OperationClient(driver)

    assert client.cancel("op-1") == "RESULT"
    request, stub, method, wrapper, settings = driver.calls[0]
    assert request.id == "op-1"
    assert stub is _apis.OperationService.Stub
    assert method == _apis.OperationService.CancelOperation
    assert wrapper is operation._cancel_operation_response

    assert client.forget("op-2") == "RESULT"
    request, stub, method, wrapper, settings = driver.calls[1]
    assert request.id == "op-2"
    assert method == _apis.OperationService.ForgetOperation
    assert wrapper is operation._forget_operation_response


def test_operation_methods_dispatch_with_driver():
    driver = _FakeDriver()
    op = operation.Operation(None, _operation_response("op-9"), driver=driver)

    op.cancel()
    assert driver.calls[-1][0].id == "op-9"
    assert driver.calls[-1][2] == _apis.OperationService.CancelOperation

    op.forget()
    assert driver.calls[-1][2] == _apis.OperationService.ForgetOperation

    op.get()
    request, stub, method, wrapper, settings, wrap_args = driver.calls[-1]
    assert request.id == "op-9"
    assert method == _apis.OperationService.GetOperation
    assert wrapper is operation.Operation
    assert wrap_args == (driver,)
