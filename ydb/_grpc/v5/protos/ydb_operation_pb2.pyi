from google.protobuf import any_pb2 as _any_pb2
from google.protobuf import duration_pb2 as _duration_pb2
from protos.annotations import validation_pb2 as _validation_pb2
from protos import ydb_common_pb2 as _ydb_common_pb2
from protos import ydb_issue_message_pb2 as _ydb_issue_message_pb2
from protos import ydb_status_codes_pb2 as _ydb_status_codes_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CancelOperationRequest(_message.Message):
    __slots__ = ["id"]
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class CancelOperationResponse(_message.Message):
    __slots__ = ["issues", "status"]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ...) -> None: ...

class ForgetOperationRequest(_message.Message):
    __slots__ = ["id"]
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class ForgetOperationResponse(_message.Message):
    __slots__ = ["issues", "status"]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ...) -> None: ...

class GetOperationRequest(_message.Message):
    __slots__ = ["id"]
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class GetOperationResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: Operation
    def __init__(self, operation: _Optional[_Union[Operation, _Mapping]] = ...) -> None: ...

class ListOperationsRequest(_message.Message):
    __slots__ = ["kind", "page_size", "page_token"]
    KIND_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    kind: str
    page_size: int
    page_token: str
    def __init__(self, kind: _Optional[str] = ..., page_size: _Optional[int] = ..., page_token: _Optional[str] = ...) -> None: ...

class ListOperationsResponse(_message.Message):
    __slots__ = ["issues", "next_page_token", "operations", "status"]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    OPERATIONS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    next_page_token: str
    operations: _containers.RepeatedCompositeFieldContainer[Operation]
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., operations: _Optional[_Iterable[_Union[Operation, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class Operation(_message.Message):
    __slots__ = ["cost_info", "id", "issues", "metadata", "ready", "result", "status"]
    COST_INFO_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    READY_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    cost_info: _ydb_common_pb2.CostInfo
    id: str
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    metadata: _any_pb2.Any
    ready: bool
    result: _any_pb2.Any
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    def __init__(self, id: _Optional[str] = ..., ready: bool = ..., status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., result: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., metadata: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., cost_info: _Optional[_Union[_ydb_common_pb2.CostInfo, _Mapping]] = ...) -> None: ...

class OperationParams(_message.Message):
    __slots__ = ["cancel_after", "labels", "operation_mode", "operation_timeout", "report_cost_info"]
    class OperationMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    class LabelsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ASYNC: OperationParams.OperationMode
    CANCEL_AFTER_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    OPERATION_MODE_FIELD_NUMBER: _ClassVar[int]
    OPERATION_MODE_UNSPECIFIED: OperationParams.OperationMode
    OPERATION_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    REPORT_COST_INFO_FIELD_NUMBER: _ClassVar[int]
    SYNC: OperationParams.OperationMode
    cancel_after: _duration_pb2.Duration
    labels: _containers.ScalarMap[str, str]
    operation_mode: OperationParams.OperationMode
    operation_timeout: _duration_pb2.Duration
    report_cost_info: _ydb_common_pb2.FeatureFlag.Status
    def __init__(self, operation_mode: _Optional[_Union[OperationParams.OperationMode, str]] = ..., operation_timeout: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., cancel_after: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., labels: _Optional[_Mapping[str, str]] = ..., report_cost_info: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ...) -> None: ...
