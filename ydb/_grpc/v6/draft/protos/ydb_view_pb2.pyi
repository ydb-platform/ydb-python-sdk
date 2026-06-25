from protos.annotations import validation_pb2 as _validation_pb2
from protos import ydb_operation_pb2 as _ydb_operation_pb2
from protos import ydb_scheme_pb2 as _ydb_scheme_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DescribeViewRequest(_message.Message):
    __slots__ = ("operation_params", "path")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ...) -> None: ...

class DescribeViewResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeViewResult(_message.Message):
    __slots__ = ("self", "query_text")
    SELF_FIELD_NUMBER: _ClassVar[int]
    QUERY_TEXT_FIELD_NUMBER: _ClassVar[int]
    self: _ydb_scheme_pb2.Entry
    query_text: str
    def __init__(self_, self: _Optional[_Union[_ydb_scheme_pb2.Entry, _Mapping]] = ..., query_text: _Optional[str] = ...) -> None: ...
