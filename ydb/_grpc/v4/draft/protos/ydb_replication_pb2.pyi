from protos.annotations import validation_pb2 as _validation_pb2
from protos import ydb_issue_message_pb2 as _ydb_issue_message_pb2
from protos import ydb_operation_pb2 as _ydb_operation_pb2
from protos import ydb_scheme_pb2 as _ydb_scheme_pb2
from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ConnectionParams(_message.Message):
    __slots__ = ["connection_string", "database", "enable_ssl", "endpoint", "oauth", "static_credentials"]
    class OAuth(_message.Message):
        __slots__ = ["token_secret_name"]
        TOKEN_SECRET_NAME_FIELD_NUMBER: _ClassVar[int]
        token_secret_name: str
        def __init__(self, token_secret_name: _Optional[str] = ...) -> None: ...
    class StaticCredentials(_message.Message):
        __slots__ = ["password_secret_name", "user"]
        PASSWORD_SECRET_NAME_FIELD_NUMBER: _ClassVar[int]
        USER_FIELD_NUMBER: _ClassVar[int]
        password_secret_name: str
        user: str
        def __init__(self, user: _Optional[str] = ..., password_secret_name: _Optional[str] = ...) -> None: ...
    CONNECTION_STRING_FIELD_NUMBER: _ClassVar[int]
    DATABASE_FIELD_NUMBER: _ClassVar[int]
    ENABLE_SSL_FIELD_NUMBER: _ClassVar[int]
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    OAUTH_FIELD_NUMBER: _ClassVar[int]
    STATIC_CREDENTIALS_FIELD_NUMBER: _ClassVar[int]
    connection_string: str
    database: str
    enable_ssl: bool
    endpoint: str
    oauth: ConnectionParams.OAuth
    static_credentials: ConnectionParams.StaticCredentials
    def __init__(self, endpoint: _Optional[str] = ..., database: _Optional[str] = ..., enable_ssl: bool = ..., connection_string: _Optional[str] = ..., static_credentials: _Optional[_Union[ConnectionParams.StaticCredentials, _Mapping]] = ..., oauth: _Optional[_Union[ConnectionParams.OAuth, _Mapping]] = ...) -> None: ...

class ConsistencyLevelGlobal(_message.Message):
    __slots__ = ["commit_interval"]
    COMMIT_INTERVAL_FIELD_NUMBER: _ClassVar[int]
    commit_interval: _duration_pb2.Duration
    def __init__(self, commit_interval: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ...) -> None: ...

class ConsistencyLevelRow(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class DescribeReplicationRequest(_message.Message):
    __slots__ = ["include_stats", "operation_params", "path"]
    INCLUDE_STATS_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    include_stats: bool
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., include_stats: bool = ...) -> None: ...

class DescribeReplicationResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeReplicationResult(_message.Message):
    __slots__ = ["connection_params", "done", "error", "global_consistency", "items", "paused", "row_consistency", "running", "self"]
    class DoneState(_message.Message):
        __slots__ = []
        def __init__(self) -> None: ...
    class ErrorState(_message.Message):
        __slots__ = ["issues"]
        ISSUES_FIELD_NUMBER: _ClassVar[int]
        issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
        def __init__(self, issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ...) -> None: ...
    class Item(_message.Message):
        __slots__ = ["destination_path", "id", "source_changefeed_name", "source_path", "stats"]
        DESTINATION_PATH_FIELD_NUMBER: _ClassVar[int]
        ID_FIELD_NUMBER: _ClassVar[int]
        SOURCE_CHANGEFEED_NAME_FIELD_NUMBER: _ClassVar[int]
        SOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
        STATS_FIELD_NUMBER: _ClassVar[int]
        destination_path: str
        id: int
        source_changefeed_name: str
        source_path: str
        stats: DescribeReplicationResult.Stats
        def __init__(self, source_path: _Optional[str] = ..., destination_path: _Optional[str] = ..., source_changefeed_name: _Optional[str] = ..., id: _Optional[int] = ..., stats: _Optional[_Union[DescribeReplicationResult.Stats, _Mapping]] = ...) -> None: ...
    class PausedState(_message.Message):
        __slots__ = []
        def __init__(self) -> None: ...
    class RunningState(_message.Message):
        __slots__ = ["stats"]
        STATS_FIELD_NUMBER: _ClassVar[int]
        stats: DescribeReplicationResult.Stats
        def __init__(self, stats: _Optional[_Union[DescribeReplicationResult.Stats, _Mapping]] = ...) -> None: ...
    class Stats(_message.Message):
        __slots__ = ["initial_scan_progress", "lag"]
        INITIAL_SCAN_PROGRESS_FIELD_NUMBER: _ClassVar[int]
        LAG_FIELD_NUMBER: _ClassVar[int]
        initial_scan_progress: float
        lag: _duration_pb2.Duration
        def __init__(self, lag: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., initial_scan_progress: _Optional[float] = ...) -> None: ...
    CONNECTION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    DONE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    GLOBAL_CONSISTENCY_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    PAUSED_FIELD_NUMBER: _ClassVar[int]
    ROW_CONSISTENCY_FIELD_NUMBER: _ClassVar[int]
    RUNNING_FIELD_NUMBER: _ClassVar[int]
    SELF_FIELD_NUMBER: _ClassVar[int]
    connection_params: ConnectionParams
    done: DescribeReplicationResult.DoneState
    error: DescribeReplicationResult.ErrorState
    global_consistency: ConsistencyLevelGlobal
    items: _containers.RepeatedCompositeFieldContainer[DescribeReplicationResult.Item]
    paused: DescribeReplicationResult.PausedState
    row_consistency: ConsistencyLevelRow
    running: DescribeReplicationResult.RunningState
    self: _ydb_scheme_pb2.Entry
    def __init__(self, self_: _Optional[_Union[_ydb_scheme_pb2.Entry, _Mapping]] = ..., connection_params: _Optional[_Union[ConnectionParams, _Mapping]] = ..., row_consistency: _Optional[_Union[ConsistencyLevelRow, _Mapping]] = ..., global_consistency: _Optional[_Union[ConsistencyLevelGlobal, _Mapping]] = ..., items: _Optional[_Iterable[_Union[DescribeReplicationResult.Item, _Mapping]]] = ..., running: _Optional[_Union[DescribeReplicationResult.RunningState, _Mapping]] = ..., error: _Optional[_Union[DescribeReplicationResult.ErrorState, _Mapping]] = ..., done: _Optional[_Union[DescribeReplicationResult.DoneState, _Mapping]] = ..., paused: _Optional[_Union[DescribeReplicationResult.PausedState, _Mapping]] = ...) -> None: ...

class DescribeTransferRequest(_message.Message):
    __slots__ = ["operation_params", "path"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ...) -> None: ...

class DescribeTransferResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeTransferResult(_message.Message):
    __slots__ = ["batch_settings", "connection_params", "consumer_name", "destination_path", "done", "error", "paused", "running", "self", "source_path", "transformation_lambda"]
    class BatchSettings(_message.Message):
        __slots__ = ["flush_interval", "size_bytes"]
        FLUSH_INTERVAL_FIELD_NUMBER: _ClassVar[int]
        SIZE_BYTES_FIELD_NUMBER: _ClassVar[int]
        flush_interval: _duration_pb2.Duration
        size_bytes: int
        def __init__(self, size_bytes: _Optional[int] = ..., flush_interval: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ...) -> None: ...
    class DoneState(_message.Message):
        __slots__ = []
        def __init__(self) -> None: ...
    class ErrorState(_message.Message):
        __slots__ = ["issues"]
        ISSUES_FIELD_NUMBER: _ClassVar[int]
        issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
        def __init__(self, issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ...) -> None: ...
    class PausedState(_message.Message):
        __slots__ = []
        def __init__(self) -> None: ...
    class RunningState(_message.Message):
        __slots__ = []
        def __init__(self) -> None: ...
    BATCH_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    CONSUMER_NAME_FIELD_NUMBER: _ClassVar[int]
    DESTINATION_PATH_FIELD_NUMBER: _ClassVar[int]
    DONE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    PAUSED_FIELD_NUMBER: _ClassVar[int]
    RUNNING_FIELD_NUMBER: _ClassVar[int]
    SELF_FIELD_NUMBER: _ClassVar[int]
    SOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
    TRANSFORMATION_LAMBDA_FIELD_NUMBER: _ClassVar[int]
    batch_settings: DescribeTransferResult.BatchSettings
    connection_params: ConnectionParams
    consumer_name: str
    destination_path: str
    done: DescribeTransferResult.DoneState
    error: DescribeTransferResult.ErrorState
    paused: DescribeTransferResult.PausedState
    running: DescribeTransferResult.RunningState
    self: _ydb_scheme_pb2.Entry
    source_path: str
    transformation_lambda: str
    def __init__(self, self_: _Optional[_Union[_ydb_scheme_pb2.Entry, _Mapping]] = ..., connection_params: _Optional[_Union[ConnectionParams, _Mapping]] = ..., running: _Optional[_Union[DescribeTransferResult.RunningState, _Mapping]] = ..., error: _Optional[_Union[DescribeTransferResult.ErrorState, _Mapping]] = ..., done: _Optional[_Union[DescribeTransferResult.DoneState, _Mapping]] = ..., paused: _Optional[_Union[DescribeTransferResult.PausedState, _Mapping]] = ..., source_path: _Optional[str] = ..., destination_path: _Optional[str] = ..., transformation_lambda: _Optional[str] = ..., consumer_name: _Optional[str] = ..., batch_settings: _Optional[_Union[DescribeTransferResult.BatchSettings, _Mapping]] = ...) -> None: ...
