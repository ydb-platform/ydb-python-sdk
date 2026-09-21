# -*- coding: utf-8 -*-
import pytest

from ydb import scripting, issues, types, _apis
from ydb._grpc.common.protos import ydb_scripting_pb2
from ydb._grpc.common import ydb_scripting_v1_pb2_grpc


class _FakeDriver:
    def __init__(self, result="RESULT"):
        self._result = result
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self._result


def _execute_response(status=issues.StatusCode.SUCCESS, result=None):
    op = _apis.ydb_operation.Operation(status=status)
    op.result.Pack(result if result is not None else ydb_scripting_pb2.ExecuteYqlResult())
    return ydb_scripting_pb2.ExecuteYqlResponse(operation=op)


def _explain_response(status=issues.StatusCode.SUCCESS, plan=""):
    op = _apis.ydb_operation.Operation(status=status)
    op.result.Pack(ydb_scripting_pb2.ExplainYqlResult(plan=plan))
    return ydb_scripting_pb2.ExplainYqlResponse(operation=op)


def test_scripting_client_settings_builders():
    s = scripting.ScriptingClientSettings()
    assert s._native_date_in_result_sets is False
    assert s.with_native_date_in_result_sets(True) is s
    assert s._native_date_in_result_sets is True
    assert s.with_native_datetime_in_result_sets(True) is s
    assert s._native_datetime_in_result_sets is True


def test_explain_settings_with_mode():
    s = scripting.ExplainYqlScriptSettings()
    assert s.with_mode(scripting.ExplainYqlScriptSettings.MODE_EXPLAIN) is s
    assert s.mode == scripting.ExplainYqlScriptSettings.MODE_EXPLAIN


def test_execute_request_factory_without_parameters():
    request = scripting._execute_yql_query_request_factory("SELECT 1")
    assert request.script == "SELECT 1"
    assert len(request.parameters) == 0


def test_execute_request_factory_with_parameters():
    tp = scripting.TypedParameters(
        {"$x": types.PrimitiveType.Int64},
        {"$x": 10},
    )
    request = scripting._execute_yql_query_request_factory("SELECT $x", tp)
    assert request.script == "SELECT $x"
    assert "$x" in request.parameters


def test_wrap_response_success_and_error():
    result = scripting._wrap_response(None, _execute_response(), None)
    assert isinstance(result, scripting.YqlQueryResult)

    with pytest.raises(issues.PreconditionFailed):
        scripting._wrap_response(None, _execute_response(status=issues.StatusCode.PRECONDITION_FAILED), None)


def test_wrap_explain_response_success_and_error():
    result = scripting._wrap_explain_response(None, _explain_response(plan="PLAN-TEXT"))
    assert isinstance(result, scripting.YqlExplainResult)
    assert result.plan == "PLAN-TEXT"

    with pytest.raises(issues.BadRequest):
        scripting._wrap_explain_response(None, _explain_response(status=issues.StatusCode.BAD_REQUEST))


def test_execute_yql_dispatch():
    driver = _FakeDriver()
    client = scripting.ScriptingClient(driver)
    assert client.execute_yql("SELECT 1") == "RESULT"

    args, kwargs = driver.calls[0]
    assert args[0].script == "SELECT 1"
    assert args[1] is ydb_scripting_v1_pb2_grpc.ScriptingServiceStub
    assert args[2] == "ExecuteYql"
    assert args[3] is scripting._wrap_response
    assert kwargs["wrap_args"] == (client.scripting_client_settings,)


def test_explain_yql_dispatch():
    driver = _FakeDriver()
    client = scripting.ScriptingClient(driver)
    settings = scripting.ExplainYqlScriptSettings().with_mode(scripting.ExplainYqlScriptSettings.MODE_VALIDATE)

    assert client.explain_yql("SELECT 1", settings=settings) == "RESULT"
    args, kwargs = driver.calls[0]
    assert args[0].script == "SELECT 1"
    assert args[0].mode == scripting.ExplainYqlScriptSettings.MODE_VALIDATE
    assert args[2] == "ExplainYql"
    assert args[3] is scripting._wrap_explain_response


def test_scripting_client_uses_provided_settings():
    settings = scripting.ScriptingClientSettings().with_native_date_in_result_sets(True)
    client = scripting.ScriptingClient(_FakeDriver(), scripting_client_settings=settings)
    assert client.scripting_client_settings is settings
