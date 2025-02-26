from protos import ydb_operation_pb2 as _ydb_operation_pb2
from protos import ydb_value_pb2 as _ydb_value_pb2
from protos import ydb_table_pb2 as _ydb_table_pb2
from protos import ydb_query_stats_pb2 as _ydb_query_stats_pb2
from protos import ydb_issue_message_pb2 as _ydb_issue_message_pb2
from protos import ydb_status_codes_pb2 as _ydb_status_codes_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ExecuteYqlPartialResponse(_message.Message):
    __slots__ = ["issues", "result", "status"]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    result: ExecuteYqlPartialResult
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., result: _Optional[_Union[ExecuteYqlPartialResult, _Mapping]] = ...) -> None: ...

class ExecuteYqlPartialResult(_message.Message):
    __slots__ = ["query_stats", "result_set", "result_set_index"]
    QUERY_STATS_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_INDEX_FIELD_NUMBER: _ClassVar[int]
    query_stats: _ydb_query_stats_pb2.QueryStats
    result_set: _ydb_value_pb2.ResultSet
    result_set_index: int
    def __init__(self, result_set_index: _Optional[int] = ..., result_set: _Optional[_Union[_ydb_value_pb2.ResultSet, _Mapping]] = ..., query_stats: _Optional[_Union[_ydb_query_stats_pb2.QueryStats, _Mapping]] = ...) -> None: ...

class ExecuteYqlRequest(_message.Message):
    __slots__ = ["collect_stats", "operation_params", "parameters", "script"]
    class ParametersEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _ydb_value_pb2.TypedValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ...) -> None: ...
    COLLECT_STATS_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    SCRIPT_FIELD_NUMBER: _ClassVar[int]
    collect_stats: _ydb_table_pb2.QueryStatsCollection.Mode
    operation_params: _ydb_operation_pb2.OperationParams
    parameters: _containers.MessageMap[str, _ydb_value_pb2.TypedValue]
    script: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., script: _Optional[str] = ..., parameters: _Optional[_Mapping[str, _ydb_value_pb2.TypedValue]] = ..., collect_stats: _Optional[_Union[_ydb_table_pb2.QueryStatsCollection.Mode, str]] = ...) -> None: ...

class ExecuteYqlResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ExecuteYqlResult(_message.Message):
    __slots__ = ["query_stats", "result_sets"]
    QUERY_STATS_FIELD_NUMBER: _ClassVar[int]
    RESULT_SETS_FIELD_NUMBER: _ClassVar[int]
    query_stats: _ydb_query_stats_pb2.QueryStats
    result_sets: _containers.RepeatedCompositeFieldContainer[_ydb_value_pb2.ResultSet]
    def __init__(self, result_sets: _Optional[_Iterable[_Union[_ydb_value_pb2.ResultSet, _Mapping]]] = ..., query_stats: _Optional[_Union[_ydb_query_stats_pb2.QueryStats, _Mapping]] = ...) -> None: ...

class ExplainYqlRequest(_message.Message):
    __slots__ = ["mode", "operation_params", "script"]
    class Mode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    MODE_FIELD_NUMBER: _ClassVar[int]
    MODE_UNSPECIFIED: ExplainYqlRequest.Mode
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PLAN: ExplainYqlRequest.Mode
    SCRIPT_FIELD_NUMBER: _ClassVar[int]
    VALIDATE: ExplainYqlRequest.Mode
    mode: ExplainYqlRequest.Mode
    operation_params: _ydb_operation_pb2.OperationParams
    script: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., script: _Optional[str] = ..., mode: _Optional[_Union[ExplainYqlRequest.Mode, str]] = ...) -> None: ...

class ExplainYqlResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ExplainYqlResult(_message.Message):
    __slots__ = ["parameters_types", "plan"]
    class ParametersTypesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _ydb_value_pb2.Type
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_ydb_value_pb2.Type, _Mapping]] = ...) -> None: ...
    PARAMETERS_TYPES_FIELD_NUMBER: _ClassVar[int]
    PLAN_FIELD_NUMBER: _ClassVar[int]
    parameters_types: _containers.MessageMap[str, _ydb_value_pb2.Type]
    plan: str
    def __init__(self, parameters_types: _Optional[_Mapping[str, _ydb_value_pb2.Type]] = ..., plan: _Optional[str] = ...) -> None: ...
