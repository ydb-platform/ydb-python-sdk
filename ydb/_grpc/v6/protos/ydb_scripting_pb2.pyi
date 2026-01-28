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
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ExecuteYqlRequest(_message.Message):
    __slots__ = ("operation_params", "script", "parameters", "collect_stats")
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _ydb_value_pb2.TypedValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ...) -> None: ...
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SCRIPT_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    COLLECT_STATS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    script: str
    parameters: _containers.MessageMap[str, _ydb_value_pb2.TypedValue]
    collect_stats: _ydb_table_pb2.QueryStatsCollection.Mode
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., script: _Optional[str] = ..., parameters: _Optional[_Mapping[str, _ydb_value_pb2.TypedValue]] = ..., collect_stats: _Optional[_Union[_ydb_table_pb2.QueryStatsCollection.Mode, str]] = ...) -> None: ...

class ExecuteYqlResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ExecuteYqlResult(_message.Message):
    __slots__ = ("result_sets", "query_stats")
    RESULT_SETS_FIELD_NUMBER: _ClassVar[int]
    QUERY_STATS_FIELD_NUMBER: _ClassVar[int]
    result_sets: _containers.RepeatedCompositeFieldContainer[_ydb_value_pb2.ResultSet]
    query_stats: _ydb_query_stats_pb2.QueryStats
    def __init__(self, result_sets: _Optional[_Iterable[_Union[_ydb_value_pb2.ResultSet, _Mapping]]] = ..., query_stats: _Optional[_Union[_ydb_query_stats_pb2.QueryStats, _Mapping]] = ...) -> None: ...

class ExecuteYqlPartialResponse(_message.Message):
    __slots__ = ("status", "issues", "result")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    result: ExecuteYqlPartialResult
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., result: _Optional[_Union[ExecuteYqlPartialResult, _Mapping]] = ...) -> None: ...

class ExecuteYqlPartialResult(_message.Message):
    __slots__ = ("result_set_index", "result_set", "query_stats")
    RESULT_SET_INDEX_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_FIELD_NUMBER: _ClassVar[int]
    QUERY_STATS_FIELD_NUMBER: _ClassVar[int]
    result_set_index: int
    result_set: _ydb_value_pb2.ResultSet
    query_stats: _ydb_query_stats_pb2.QueryStats
    def __init__(self, result_set_index: _Optional[int] = ..., result_set: _Optional[_Union[_ydb_value_pb2.ResultSet, _Mapping]] = ..., query_stats: _Optional[_Union[_ydb_query_stats_pb2.QueryStats, _Mapping]] = ...) -> None: ...

class ExplainYqlRequest(_message.Message):
    __slots__ = ("operation_params", "script", "mode")
    class Mode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        MODE_UNSPECIFIED: _ClassVar[ExplainYqlRequest.Mode]
        VALIDATE: _ClassVar[ExplainYqlRequest.Mode]
        PLAN: _ClassVar[ExplainYqlRequest.Mode]
    MODE_UNSPECIFIED: ExplainYqlRequest.Mode
    VALIDATE: ExplainYqlRequest.Mode
    PLAN: ExplainYqlRequest.Mode
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SCRIPT_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    script: str
    mode: ExplainYqlRequest.Mode
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., script: _Optional[str] = ..., mode: _Optional[_Union[ExplainYqlRequest.Mode, str]] = ...) -> None: ...

class ExplainYqlResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ExplainYqlResult(_message.Message):
    __slots__ = ("parameters_types", "plan")
    class ParametersTypesEntry(_message.Message):
        __slots__ = ("key", "value")
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
