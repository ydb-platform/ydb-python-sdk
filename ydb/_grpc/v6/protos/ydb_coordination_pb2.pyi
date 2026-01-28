from protos import ydb_operation_pb2 as _ydb_operation_pb2
from protos import ydb_status_codes_pb2 as _ydb_status_codes_pb2
from protos import ydb_issue_message_pb2 as _ydb_issue_message_pb2
from protos import ydb_scheme_pb2 as _ydb_scheme_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ConsistencyMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CONSISTENCY_MODE_UNSET: _ClassVar[ConsistencyMode]
    CONSISTENCY_MODE_STRICT: _ClassVar[ConsistencyMode]
    CONSISTENCY_MODE_RELAXED: _ClassVar[ConsistencyMode]

class RateLimiterCountersMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RATE_LIMITER_COUNTERS_MODE_UNSET: _ClassVar[RateLimiterCountersMode]
    RATE_LIMITER_COUNTERS_MODE_AGGREGATED: _ClassVar[RateLimiterCountersMode]
    RATE_LIMITER_COUNTERS_MODE_DETAILED: _ClassVar[RateLimiterCountersMode]
CONSISTENCY_MODE_UNSET: ConsistencyMode
CONSISTENCY_MODE_STRICT: ConsistencyMode
CONSISTENCY_MODE_RELAXED: ConsistencyMode
RATE_LIMITER_COUNTERS_MODE_UNSET: RateLimiterCountersMode
RATE_LIMITER_COUNTERS_MODE_AGGREGATED: RateLimiterCountersMode
RATE_LIMITER_COUNTERS_MODE_DETAILED: RateLimiterCountersMode

class Unsupported(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Config(_message.Message):
    __slots__ = ("path", "self_check_period_millis", "session_grace_period_millis", "read_consistency_mode", "attach_consistency_mode", "rate_limiter_counters_mode")
    PATH_FIELD_NUMBER: _ClassVar[int]
    SELF_CHECK_PERIOD_MILLIS_FIELD_NUMBER: _ClassVar[int]
    SESSION_GRACE_PERIOD_MILLIS_FIELD_NUMBER: _ClassVar[int]
    READ_CONSISTENCY_MODE_FIELD_NUMBER: _ClassVar[int]
    ATTACH_CONSISTENCY_MODE_FIELD_NUMBER: _ClassVar[int]
    RATE_LIMITER_COUNTERS_MODE_FIELD_NUMBER: _ClassVar[int]
    path: str
    self_check_period_millis: int
    session_grace_period_millis: int
    read_consistency_mode: ConsistencyMode
    attach_consistency_mode: ConsistencyMode
    rate_limiter_counters_mode: RateLimiterCountersMode
    def __init__(self, path: _Optional[str] = ..., self_check_period_millis: _Optional[int] = ..., session_grace_period_millis: _Optional[int] = ..., read_consistency_mode: _Optional[_Union[ConsistencyMode, str]] = ..., attach_consistency_mode: _Optional[_Union[ConsistencyMode, str]] = ..., rate_limiter_counters_mode: _Optional[_Union[RateLimiterCountersMode, str]] = ...) -> None: ...

class SessionDescription(_message.Message):
    __slots__ = ("session_id", "timeout_millis", "description", "attached")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_MILLIS_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    ATTACHED_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    timeout_millis: int
    description: str
    attached: bool
    def __init__(self, session_id: _Optional[int] = ..., timeout_millis: _Optional[int] = ..., description: _Optional[str] = ..., attached: bool = ...) -> None: ...

class SemaphoreSession(_message.Message):
    __slots__ = ("order_id", "session_id", "timeout_millis", "count", "data")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_MILLIS_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    order_id: int
    session_id: int
    timeout_millis: int
    count: int
    data: bytes
    def __init__(self, order_id: _Optional[int] = ..., session_id: _Optional[int] = ..., timeout_millis: _Optional[int] = ..., count: _Optional[int] = ..., data: _Optional[bytes] = ...) -> None: ...

class SemaphoreDescription(_message.Message):
    __slots__ = ("name", "data", "count", "limit", "ephemeral", "owners", "waiters")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    EPHEMERAL_FIELD_NUMBER: _ClassVar[int]
    OWNERS_FIELD_NUMBER: _ClassVar[int]
    WAITERS_FIELD_NUMBER: _ClassVar[int]
    name: str
    data: bytes
    count: int
    limit: int
    ephemeral: bool
    owners: _containers.RepeatedCompositeFieldContainer[SemaphoreSession]
    waiters: _containers.RepeatedCompositeFieldContainer[SemaphoreSession]
    def __init__(self, name: _Optional[str] = ..., data: _Optional[bytes] = ..., count: _Optional[int] = ..., limit: _Optional[int] = ..., ephemeral: bool = ..., owners: _Optional[_Iterable[_Union[SemaphoreSession, _Mapping]]] = ..., waiters: _Optional[_Iterable[_Union[SemaphoreSession, _Mapping]]] = ...) -> None: ...

class SessionRequest(_message.Message):
    __slots__ = ("ping", "pong", "session_start", "session_stop", "unsupported_5", "unsupported_6", "acquire_semaphore", "release_semaphore", "describe_semaphore", "create_semaphore", "update_semaphore", "delete_semaphore", "unsupported_13", "unsupported_14", "unsupported_15")
    class PingPong(_message.Message):
        __slots__ = ("opaque",)
        OPAQUE_FIELD_NUMBER: _ClassVar[int]
        opaque: int
        def __init__(self, opaque: _Optional[int] = ...) -> None: ...
    class SessionStart(_message.Message):
        __slots__ = ("path", "session_id", "timeout_millis", "description", "seq_no", "protection_key")
        PATH_FIELD_NUMBER: _ClassVar[int]
        SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        TIMEOUT_MILLIS_FIELD_NUMBER: _ClassVar[int]
        DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
        SEQ_NO_FIELD_NUMBER: _ClassVar[int]
        PROTECTION_KEY_FIELD_NUMBER: _ClassVar[int]
        path: str
        session_id: int
        timeout_millis: int
        description: str
        seq_no: int
        protection_key: bytes
        def __init__(self, path: _Optional[str] = ..., session_id: _Optional[int] = ..., timeout_millis: _Optional[int] = ..., description: _Optional[str] = ..., seq_no: _Optional[int] = ..., protection_key: _Optional[bytes] = ...) -> None: ...
    class SessionStop(_message.Message):
        __slots__ = ()
        def __init__(self) -> None: ...
    class AcquireSemaphore(_message.Message):
        __slots__ = ("req_id", "name", "timeout_millis", "count", "data", "ephemeral")
        REQ_ID_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        TIMEOUT_MILLIS_FIELD_NUMBER: _ClassVar[int]
        COUNT_FIELD_NUMBER: _ClassVar[int]
        DATA_FIELD_NUMBER: _ClassVar[int]
        EPHEMERAL_FIELD_NUMBER: _ClassVar[int]
        req_id: int
        name: str
        timeout_millis: int
        count: int
        data: bytes
        ephemeral: bool
        def __init__(self, req_id: _Optional[int] = ..., name: _Optional[str] = ..., timeout_millis: _Optional[int] = ..., count: _Optional[int] = ..., data: _Optional[bytes] = ..., ephemeral: bool = ...) -> None: ...
    class ReleaseSemaphore(_message.Message):
        __slots__ = ("req_id", "name")
        REQ_ID_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        req_id: int
        name: str
        def __init__(self, req_id: _Optional[int] = ..., name: _Optional[str] = ...) -> None: ...
    class DescribeSemaphore(_message.Message):
        __slots__ = ("req_id", "name", "include_owners", "include_waiters", "watch_data", "watch_owners")
        REQ_ID_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        INCLUDE_OWNERS_FIELD_NUMBER: _ClassVar[int]
        INCLUDE_WAITERS_FIELD_NUMBER: _ClassVar[int]
        WATCH_DATA_FIELD_NUMBER: _ClassVar[int]
        WATCH_OWNERS_FIELD_NUMBER: _ClassVar[int]
        req_id: int
        name: str
        include_owners: bool
        include_waiters: bool
        watch_data: bool
        watch_owners: bool
        def __init__(self, req_id: _Optional[int] = ..., name: _Optional[str] = ..., include_owners: bool = ..., include_waiters: bool = ..., watch_data: bool = ..., watch_owners: bool = ...) -> None: ...
    class CreateSemaphore(_message.Message):
        __slots__ = ("req_id", "name", "limit", "data")
        REQ_ID_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        LIMIT_FIELD_NUMBER: _ClassVar[int]
        DATA_FIELD_NUMBER: _ClassVar[int]
        req_id: int
        name: str
        limit: int
        data: bytes
        def __init__(self, req_id: _Optional[int] = ..., name: _Optional[str] = ..., limit: _Optional[int] = ..., data: _Optional[bytes] = ...) -> None: ...
    class UpdateSemaphore(_message.Message):
        __slots__ = ("req_id", "name", "data")
        REQ_ID_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        DATA_FIELD_NUMBER: _ClassVar[int]
        req_id: int
        name: str
        data: bytes
        def __init__(self, req_id: _Optional[int] = ..., name: _Optional[str] = ..., data: _Optional[bytes] = ...) -> None: ...
    class DeleteSemaphore(_message.Message):
        __slots__ = ("req_id", "name", "force")
        REQ_ID_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        FORCE_FIELD_NUMBER: _ClassVar[int]
        req_id: int
        name: str
        force: bool
        def __init__(self, req_id: _Optional[int] = ..., name: _Optional[str] = ..., force: bool = ...) -> None: ...
    PING_FIELD_NUMBER: _ClassVar[int]
    PONG_FIELD_NUMBER: _ClassVar[int]
    SESSION_START_FIELD_NUMBER: _ClassVar[int]
    SESSION_STOP_FIELD_NUMBER: _ClassVar[int]
    UNSUPPORTED_5_FIELD_NUMBER: _ClassVar[int]
    UNSUPPORTED_6_FIELD_NUMBER: _ClassVar[int]
    ACQUIRE_SEMAPHORE_FIELD_NUMBER: _ClassVar[int]
    RELEASE_SEMAPHORE_FIELD_NUMBER: _ClassVar[int]
    DESCRIBE_SEMAPHORE_FIELD_NUMBER: _ClassVar[int]
    CREATE_SEMAPHORE_FIELD_NUMBER: _ClassVar[int]
    UPDATE_SEMAPHORE_FIELD_NUMBER: _ClassVar[int]
    DELETE_SEMAPHORE_FIELD_NUMBER: _ClassVar[int]
    UNSUPPORTED_13_FIELD_NUMBER: _ClassVar[int]
    UNSUPPORTED_14_FIELD_NUMBER: _ClassVar[int]
    UNSUPPORTED_15_FIELD_NUMBER: _ClassVar[int]
    ping: SessionRequest.PingPong
    pong: SessionRequest.PingPong
    session_start: SessionRequest.SessionStart
    session_stop: SessionRequest.SessionStop
    unsupported_5: Unsupported
    unsupported_6: Unsupported
    acquire_semaphore: SessionRequest.AcquireSemaphore
    release_semaphore: SessionRequest.ReleaseSemaphore
    describe_semaphore: SessionRequest.DescribeSemaphore
    create_semaphore: SessionRequest.CreateSemaphore
    update_semaphore: SessionRequest.UpdateSemaphore
    delete_semaphore: SessionRequest.DeleteSemaphore
    unsupported_13: Unsupported
    unsupported_14: Unsupported
    unsupported_15: Unsupported
    def __init__(self, ping: _Optional[_Union[SessionRequest.PingPong, _Mapping]] = ..., pong: _Optional[_Union[SessionRequest.PingPong, _Mapping]] = ..., session_start: _Optional[_Union[SessionRequest.SessionStart, _Mapping]] = ..., session_stop: _Optional[_Union[SessionRequest.SessionStop, _Mapping]] = ..., unsupported_5: _Optional[_Union[Unsupported, _Mapping]] = ..., unsupported_6: _Optional[_Union[Unsupported, _Mapping]] = ..., acquire_semaphore: _Optional[_Union[SessionRequest.AcquireSemaphore, _Mapping]] = ..., release_semaphore: _Optional[_Union[SessionRequest.ReleaseSemaphore, _Mapping]] = ..., describe_semaphore: _Optional[_Union[SessionRequest.DescribeSemaphore, _Mapping]] = ..., create_semaphore: _Optional[_Union[SessionRequest.CreateSemaphore, _Mapping]] = ..., update_semaphore: _Optional[_Union[SessionRequest.UpdateSemaphore, _Mapping]] = ..., delete_semaphore: _Optional[_Union[SessionRequest.DeleteSemaphore, _Mapping]] = ..., unsupported_13: _Optional[_Union[Unsupported, _Mapping]] = ..., unsupported_14: _Optional[_Union[Unsupported, _Mapping]] = ..., unsupported_15: _Optional[_Union[Unsupported, _Mapping]] = ...) -> None: ...

class SessionResponse(_message.Message):
    __slots__ = ("ping", "pong", "failure", "session_started", "session_stopped", "unsupported_6", "unsupported_7", "acquire_semaphore_pending", "acquire_semaphore_result", "release_semaphore_result", "describe_semaphore_result", "describe_semaphore_changed", "create_semaphore_result", "update_semaphore_result", "delete_semaphore_result", "unsupported_16", "unsupported_17", "unsupported_18")
    class PingPong(_message.Message):
        __slots__ = ("opaque",)
        OPAQUE_FIELD_NUMBER: _ClassVar[int]
        opaque: int
        def __init__(self, opaque: _Optional[int] = ...) -> None: ...
    class Failure(_message.Message):
        __slots__ = ("status", "issues")
        STATUS_FIELD_NUMBER: _ClassVar[int]
        ISSUES_FIELD_NUMBER: _ClassVar[int]
        status: _ydb_status_codes_pb2.StatusIds.StatusCode
        issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
        def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ...) -> None: ...
    class SessionStarted(_message.Message):
        __slots__ = ("session_id", "timeout_millis")
        SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        TIMEOUT_MILLIS_FIELD_NUMBER: _ClassVar[int]
        session_id: int
        timeout_millis: int
        def __init__(self, session_id: _Optional[int] = ..., timeout_millis: _Optional[int] = ...) -> None: ...
    class SessionStopped(_message.Message):
        __slots__ = ("session_id",)
        SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        session_id: int
        def __init__(self, session_id: _Optional[int] = ...) -> None: ...
    class AcquireSemaphorePending(_message.Message):
        __slots__ = ("req_id",)
        REQ_ID_FIELD_NUMBER: _ClassVar[int]
        req_id: int
        def __init__(self, req_id: _Optional[int] = ...) -> None: ...
    class AcquireSemaphoreResult(_message.Message):
        __slots__ = ("req_id", "status", "issues", "acquired")
        REQ_ID_FIELD_NUMBER: _ClassVar[int]
        STATUS_FIELD_NUMBER: _ClassVar[int]
        ISSUES_FIELD_NUMBER: _ClassVar[int]
        ACQUIRED_FIELD_NUMBER: _ClassVar[int]
        req_id: int
        status: _ydb_status_codes_pb2.StatusIds.StatusCode
        issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
        acquired: bool
        def __init__(self, req_id: _Optional[int] = ..., status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., acquired: bool = ...) -> None: ...
    class ReleaseSemaphoreResult(_message.Message):
        __slots__ = ("req_id", "status", "issues", "released")
        REQ_ID_FIELD_NUMBER: _ClassVar[int]
        STATUS_FIELD_NUMBER: _ClassVar[int]
        ISSUES_FIELD_NUMBER: _ClassVar[int]
        RELEASED_FIELD_NUMBER: _ClassVar[int]
        req_id: int
        status: _ydb_status_codes_pb2.StatusIds.StatusCode
        issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
        released: bool
        def __init__(self, req_id: _Optional[int] = ..., status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., released: bool = ...) -> None: ...
    class DescribeSemaphoreResult(_message.Message):
        __slots__ = ("req_id", "status", "issues", "semaphore_description", "watch_added")
        REQ_ID_FIELD_NUMBER: _ClassVar[int]
        STATUS_FIELD_NUMBER: _ClassVar[int]
        ISSUES_FIELD_NUMBER: _ClassVar[int]
        SEMAPHORE_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
        WATCH_ADDED_FIELD_NUMBER: _ClassVar[int]
        req_id: int
        status: _ydb_status_codes_pb2.StatusIds.StatusCode
        issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
        semaphore_description: SemaphoreDescription
        watch_added: bool
        def __init__(self, req_id: _Optional[int] = ..., status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., semaphore_description: _Optional[_Union[SemaphoreDescription, _Mapping]] = ..., watch_added: bool = ...) -> None: ...
    class DescribeSemaphoreChanged(_message.Message):
        __slots__ = ("req_id", "data_changed", "owners_changed")
        REQ_ID_FIELD_NUMBER: _ClassVar[int]
        DATA_CHANGED_FIELD_NUMBER: _ClassVar[int]
        OWNERS_CHANGED_FIELD_NUMBER: _ClassVar[int]
        req_id: int
        data_changed: bool
        owners_changed: bool
        def __init__(self, req_id: _Optional[int] = ..., data_changed: bool = ..., owners_changed: bool = ...) -> None: ...
    class CreateSemaphoreResult(_message.Message):
        __slots__ = ("req_id", "status", "issues")
        REQ_ID_FIELD_NUMBER: _ClassVar[int]
        STATUS_FIELD_NUMBER: _ClassVar[int]
        ISSUES_FIELD_NUMBER: _ClassVar[int]
        req_id: int
        status: _ydb_status_codes_pb2.StatusIds.StatusCode
        issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
        def __init__(self, req_id: _Optional[int] = ..., status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ...) -> None: ...
    class UpdateSemaphoreResult(_message.Message):
        __slots__ = ("req_id", "status", "issues")
        REQ_ID_FIELD_NUMBER: _ClassVar[int]
        STATUS_FIELD_NUMBER: _ClassVar[int]
        ISSUES_FIELD_NUMBER: _ClassVar[int]
        req_id: int
        status: _ydb_status_codes_pb2.StatusIds.StatusCode
        issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
        def __init__(self, req_id: _Optional[int] = ..., status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ...) -> None: ...
    class DeleteSemaphoreResult(_message.Message):
        __slots__ = ("req_id", "status", "issues")
        REQ_ID_FIELD_NUMBER: _ClassVar[int]
        STATUS_FIELD_NUMBER: _ClassVar[int]
        ISSUES_FIELD_NUMBER: _ClassVar[int]
        req_id: int
        status: _ydb_status_codes_pb2.StatusIds.StatusCode
        issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
        def __init__(self, req_id: _Optional[int] = ..., status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ...) -> None: ...
    PING_FIELD_NUMBER: _ClassVar[int]
    PONG_FIELD_NUMBER: _ClassVar[int]
    FAILURE_FIELD_NUMBER: _ClassVar[int]
    SESSION_STARTED_FIELD_NUMBER: _ClassVar[int]
    SESSION_STOPPED_FIELD_NUMBER: _ClassVar[int]
    UNSUPPORTED_6_FIELD_NUMBER: _ClassVar[int]
    UNSUPPORTED_7_FIELD_NUMBER: _ClassVar[int]
    ACQUIRE_SEMAPHORE_PENDING_FIELD_NUMBER: _ClassVar[int]
    ACQUIRE_SEMAPHORE_RESULT_FIELD_NUMBER: _ClassVar[int]
    RELEASE_SEMAPHORE_RESULT_FIELD_NUMBER: _ClassVar[int]
    DESCRIBE_SEMAPHORE_RESULT_FIELD_NUMBER: _ClassVar[int]
    DESCRIBE_SEMAPHORE_CHANGED_FIELD_NUMBER: _ClassVar[int]
    CREATE_SEMAPHORE_RESULT_FIELD_NUMBER: _ClassVar[int]
    UPDATE_SEMAPHORE_RESULT_FIELD_NUMBER: _ClassVar[int]
    DELETE_SEMAPHORE_RESULT_FIELD_NUMBER: _ClassVar[int]
    UNSUPPORTED_16_FIELD_NUMBER: _ClassVar[int]
    UNSUPPORTED_17_FIELD_NUMBER: _ClassVar[int]
    UNSUPPORTED_18_FIELD_NUMBER: _ClassVar[int]
    ping: SessionResponse.PingPong
    pong: SessionResponse.PingPong
    failure: SessionResponse.Failure
    session_started: SessionResponse.SessionStarted
    session_stopped: SessionResponse.SessionStopped
    unsupported_6: Unsupported
    unsupported_7: Unsupported
    acquire_semaphore_pending: SessionResponse.AcquireSemaphorePending
    acquire_semaphore_result: SessionResponse.AcquireSemaphoreResult
    release_semaphore_result: SessionResponse.ReleaseSemaphoreResult
    describe_semaphore_result: SessionResponse.DescribeSemaphoreResult
    describe_semaphore_changed: SessionResponse.DescribeSemaphoreChanged
    create_semaphore_result: SessionResponse.CreateSemaphoreResult
    update_semaphore_result: SessionResponse.UpdateSemaphoreResult
    delete_semaphore_result: SessionResponse.DeleteSemaphoreResult
    unsupported_16: Unsupported
    unsupported_17: Unsupported
    unsupported_18: Unsupported
    def __init__(self, ping: _Optional[_Union[SessionResponse.PingPong, _Mapping]] = ..., pong: _Optional[_Union[SessionResponse.PingPong, _Mapping]] = ..., failure: _Optional[_Union[SessionResponse.Failure, _Mapping]] = ..., session_started: _Optional[_Union[SessionResponse.SessionStarted, _Mapping]] = ..., session_stopped: _Optional[_Union[SessionResponse.SessionStopped, _Mapping]] = ..., unsupported_6: _Optional[_Union[Unsupported, _Mapping]] = ..., unsupported_7: _Optional[_Union[Unsupported, _Mapping]] = ..., acquire_semaphore_pending: _Optional[_Union[SessionResponse.AcquireSemaphorePending, _Mapping]] = ..., acquire_semaphore_result: _Optional[_Union[SessionResponse.AcquireSemaphoreResult, _Mapping]] = ..., release_semaphore_result: _Optional[_Union[SessionResponse.ReleaseSemaphoreResult, _Mapping]] = ..., describe_semaphore_result: _Optional[_Union[SessionResponse.DescribeSemaphoreResult, _Mapping]] = ..., describe_semaphore_changed: _Optional[_Union[SessionResponse.DescribeSemaphoreChanged, _Mapping]] = ..., create_semaphore_result: _Optional[_Union[SessionResponse.CreateSemaphoreResult, _Mapping]] = ..., update_semaphore_result: _Optional[_Union[SessionResponse.UpdateSemaphoreResult, _Mapping]] = ..., delete_semaphore_result: _Optional[_Union[SessionResponse.DeleteSemaphoreResult, _Mapping]] = ..., unsupported_16: _Optional[_Union[Unsupported, _Mapping]] = ..., unsupported_17: _Optional[_Union[Unsupported, _Mapping]] = ..., unsupported_18: _Optional[_Union[Unsupported, _Mapping]] = ...) -> None: ...

class CreateNodeRequest(_message.Message):
    __slots__ = ("path", "config", "operation_params")
    PATH_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    path: str
    config: Config
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, path: _Optional[str] = ..., config: _Optional[_Union[Config, _Mapping]] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class CreateNodeResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class AlterNodeRequest(_message.Message):
    __slots__ = ("path", "config", "operation_params")
    PATH_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    path: str
    config: Config
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, path: _Optional[str] = ..., config: _Optional[_Union[Config, _Mapping]] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class AlterNodeResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DropNodeRequest(_message.Message):
    __slots__ = ("path", "operation_params")
    PATH_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    path: str
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, path: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class DropNodeResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeNodeRequest(_message.Message):
    __slots__ = ("path", "operation_params")
    PATH_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    path: str
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, path: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class DescribeNodeResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeNodeResult(_message.Message):
    __slots__ = ("self", "config")
    SELF_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    self: _ydb_scheme_pb2.Entry
    config: Config
    def __init__(self_, self: _Optional[_Union[_ydb_scheme_pb2.Entry, _Mapping]] = ..., config: _Optional[_Union[Config, _Mapping]] = ...) -> None: ...
