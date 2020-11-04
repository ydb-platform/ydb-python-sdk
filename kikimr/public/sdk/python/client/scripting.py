from kikimr.public.api.protos import ydb_scripting_pb2
from kikimr.public.api.grpc import ydb_scripting_v1_pb2_grpc
from . import issues, convert


class TypedParameters(object):
    def __init__(self, parameters_types, parameters_values):
        self.parameters_types = parameters_types
        self.parameters_values = parameters_values


def _execute_yql_query_request_factory(script, tp=None, settings=None):
    params = None if tp is None else convert.parameters_to_pb(tp.parameters_types, tp.parameters_values)
    return ydb_scripting_pb2.ExecuteYqlRequest(
        script=script,
        parameters=params,
    )


class YqlQueryResult(object):
    def __init__(self, result):
        self.result_sets = convert.ResultSets(result.result_sets)


def _wrap_response(rpc_state, response):
    issues._process_response(response.operation)
    message = ydb_scripting_pb2.ExecuteYqlResult()
    response.operation.result.Unpack(message)
    return YqlQueryResult(message)


class ScriptingClient(object):
    def __init__(self, driver):
        self.driver = driver

    def execute_yql(self, script, typed_parameters=None, settings=None):
        request = _execute_yql_query_request_factory(script, typed_parameters, settings)
        return self.driver(
            request,
            ydb_scripting_v1_pb2_grpc.ScriptingServiceStub,
            'ExecuteYql',
            _wrap_response,
            settings=settings
        )
