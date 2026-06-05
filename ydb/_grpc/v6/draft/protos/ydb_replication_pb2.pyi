import datetime

from protos.annotations import validation_pb2 as _validation_pb2
from protos import ydb_issue_message_pb2 as _ydb_issue_message_pb2
from protos import ydb_operation_pb2 as _ydb_operation_pb2
from protos import ydb_scheme_pb2 as _ydb_scheme_pb2
from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DescribeReplicationRequest(_message.Message):
    __slots__ = ("operation_params", "path", "include_stats")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_STATS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    include_stats: bool
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., include_stats: bool = ...) -> None: ...

class DescribeReplicationResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ConnectionParams(_message.Message):
    __slots__ = ("endpoint", "database", "enable_ssl", "connection_string", "static_credentials", "oauth")
    class StaticCredentials(_message.Message):
        __slots__ = ("user", "password_secret_name")
        USER_FIELD_NUMBER: _ClassVar[int]
        PASSWORD_SECRET_NAME_FIELD_NUMBER: _ClassVar[int]
        user: str
        password_secret_name: str
        def __init__(self, user: _Optional[str] = ..., password_secret_name: _Optional[str] = ...) -> None: ...
    class OAuth(_message.Message):
        __slots__ = ("token_secret_name",)
        TOKEN_SECRET_NAME_FIELD_NUMBER: _ClassVar[int]
        token_secret_name: str
        def __init__(self, token_secret_name: _Optional[str] = ...) -> None: ...
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    DATABASE_FIELD_NUMBER: _ClassVar[int]
    ENABLE_SSL_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_STRING_FIELD_NUMBER: _ClassVar[int]
    STATIC_CREDENTIALS_FIELD_NUMBER: _ClassVar[int]
    OAUTH_FIELD_NUMBER: _ClassVar[int]
    endpoint: str
    database: str
    enable_ssl: bool
    connection_string: str
    static_credentials: ConnectionParams.StaticCredentials
    oauth: ConnectionParams.OAuth
    def __init__(self, endpoint: _Optional[str] = ..., database: _Optional[str] = ..., enable_ssl: bool = ..., connection_string: _Optional[str] = ..., static_credentials: _Optional[_Union[ConnectionParams.StaticCredentials, _Mapping]] = ..., oauth: _Optional[_Union[ConnectionParams.OAuth, _Mapping]] = ...) -> None: ...

class ConsistencyLevelRow(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ConsistencyLevelGlobal(_message.Message):
    __slots__ = ("commit_interval",)
    COMMIT_INTERVAL_FIELD_NUMBER: _ClassVar[int]
    commit_interval: _duration_pb2.Duration
    def __init__(self, commit_interval: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ...) -> None: ...

class DescribeReplicationResult(_message.Message):
    __slots__ = ("self", "connection_params", "row_consistency", "global_consistency", "items", "running", "error", "done", "paused")
    class Stats(_message.Message):
        __slots__ = ("lag", "initial_scan_progress")
        LAG_FIELD_NUMBER: _ClassVar[int]
        INITIAL_SCAN_PROGRESS_FIELD_NUMBER: _ClassVar[int]
        lag: _duration_pb2.Duration
        initial_scan_progress: float
        def __init__(self, lag: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., initial_scan_progress: _Optional[float] = ...) -> None: ...
    class Item(_message.Message):
        __slots__ = ("source_path", "destination_path", "source_changefeed_name", "id", "stats")
        SOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
        DESTINATION_PATH_FIELD_NUMBER: _ClassVar[int]
        SOURCE_CHANGEFEED_NAME_FIELD_NUMBER: _ClassVar[int]
        ID_FIELD_NUMBER: _ClassVar[int]
        STATS_FIELD_NUMBER: _ClassVar[int]
        source_path: str
        destination_path: str
        source_changefeed_name: str
        id: int
        stats: DescribeReplicationResult.Stats
        def __init__(self, source_path: _Optional[str] = ..., destination_path: _Optional[str] = ..., source_changefeed_name: _Optional[str] = ..., id: _Optional[int] = ..., stats: _Optional[_Union[DescribeReplicationResult.Stats, _Mapping]] = ...) -> None: ...
    class RunningState(_message.Message):
        __slots__ = ("stats",)
        STATS_FIELD_NUMBER: _ClassVar[int]
        stats: DescribeReplicationResult.Stats
        def __init__(self, stats: _Optional[_Union[DescribeReplicationResult.Stats, _Mapping]] = ...) -> None: ...
    class ErrorState(_message.Message):
        __slots__ = ("issues",)
        ISSUES_FIELD_NUMBER: _ClassVar[int]
        issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
        def __init__(self, issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ...) -> None: ...
    class DoneState(_message.Message):
        __slots__ = ()
        def __init__(self) -> None: ...
    class PausedState(_message.Message):
        __slots__ = ()
        def __init__(self) -> None: ...
    SELF_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    ROW_CONSISTENCY_FIELD_NUMBER: _ClassVar[int]
    GLOBAL_CONSISTENCY_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    RUNNING_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    DONE_FIELD_NUMBER: _ClassVar[int]
    PAUSED_FIELD_NUMBER: _ClassVar[int]
    self: _ydb_scheme_pb2.Entry
    connection_params: ConnectionParams
    row_consistency: ConsistencyLevelRow
    global_consistency: ConsistencyLevelGlobal
    items: _containers.RepeatedCompositeFieldContainer[DescribeReplicationResult.Item]
    running: DescribeReplicationResult.RunningState
    error: DescribeReplicationResult.ErrorState
    done: DescribeReplicationResult.DoneState
    paused: DescribeReplicationResult.PausedState
    def __init__(self_, self: _Optional[_Union[_ydb_scheme_pb2.Entry, _Mapping]] = ..., connection_params: _Optional[_Union[ConnectionParams, _Mapping]] = ..., row_consistency: _Optional[_Union[ConsistencyLevelRow, _Mapping]] = ..., global_consistency: _Optional[_Union[ConsistencyLevelGlobal, _Mapping]] = ..., items: _Optional[_Iterable[_Union[DescribeReplicationResult.Item, _Mapping]]] = ..., running: _Optional[_Union[DescribeReplicationResult.RunningState, _Mapping]] = ..., error: _Optional[_Union[DescribeReplicationResult.ErrorState, _Mapping]] = ..., done: _Optional[_Union[DescribeReplicationResult.DoneState, _Mapping]] = ..., paused: _Optional[_Union[DescribeReplicationResult.PausedState, _Mapping]] = ...) -> None: ...

class DescribeTransferRequest(_message.Message):
    __slots__ = ("operation_params", "path")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ...) -> None: ...

class DescribeTransferResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeTransferResult(_message.Message):
    __slots__ = ("self", "connection_params", "running", "error", "done", "paused", "source_path", "destination_path", "transformation_lambda", "consumer_name", "batch_settings")
    class RunningState(_message.Message):
        __slots__ = ()
        def __init__(self) -> None: ...
    class ErrorState(_message.Message):
        __slots__ = ("issues",)
        ISSUES_FIELD_NUMBER: _ClassVar[int]
        issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
        def __init__(self, issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ...) -> None: ...
    class DoneState(_message.Message):
        __slots__ = ()
        def __init__(self) -> None: ...
    class PausedState(_message.Message):
        __slots__ = ()
        def __init__(self) -> None: ...
    class BatchSettings(_message.Message):
        __slots__ = ("size_bytes", "flush_interval")
        SIZE_BYTES_FIELD_NUMBER: _ClassVar[int]
        FLUSH_INTERVAL_FIELD_NUMBER: _ClassVar[int]
        size_bytes: int
        flush_interval: _duration_pb2.Duration
        def __init__(self, size_bytes: _Optional[int] = ..., flush_interval: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ...) -> None: ...
    SELF_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    RUNNING_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    DONE_FIELD_NUMBER: _ClassVar[int]
    PAUSED_FIELD_NUMBER: _ClassVar[int]
    SOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
    DESTINATION_PATH_FIELD_NUMBER: _ClassVar[int]
    TRANSFORMATION_LAMBDA_FIELD_NUMBER: _ClassVar[int]
    CONSUMER_NAME_FIELD_NUMBER: _ClassVar[int]
    BATCH_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    self: _ydb_scheme_pb2.Entry
    connection_params: ConnectionParams
    running: DescribeTransferResult.RunningState
    error: DescribeTransferResult.ErrorState
    done: DescribeTransferResult.DoneState
    paused: DescribeTransferResult.PausedState
    source_path: str
    destination_path: str
    transformation_lambda: str
    consumer_name: str
    batch_settings: DescribeTransferResult.BatchSettings
    def __init__(self_, self: _Optional[_Union[_ydb_scheme_pb2.Entry, _Mapping]] = ..., connection_params: _Optional[_Union[ConnectionParams, _Mapping]] = ..., running: _Optional[_Union[DescribeTransferResult.RunningState, _Mapping]] = ..., error: _Optional[_Union[DescribeTransferResult.ErrorState, _Mapping]] = ..., done: _Optional[_Union[DescribeTransferResult.DoneState, _Mapping]] = ..., paused: _Optional[_Union[DescribeTransferResult.PausedState, _Mapping]] = ..., source_path: _Optional[str] = ..., destination_path: _Optional[str] = ..., transformation_lambda: _Optional[str] = ..., consumer_name: _Optional[str] = ..., batch_settings: _Optional[_Union[DescribeTransferResult.BatchSettings, _Mapping]] = ...) -> None: ...
