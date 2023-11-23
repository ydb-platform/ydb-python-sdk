from google.protobuf import duration_pb2 as _duration_pb2
from protos.annotations import validation_pb2 as _validation_pb2
from protos import ydb_issue_message_pb2 as _ydb_issue_message_pb2
from protos import ydb_operation_pb2 as _ydb_operation_pb2
from protos import ydb_query_stats_pb2 as _ydb_query_stats_pb2
from protos import ydb_status_codes_pb2 as _ydb_status_codes_pb2
from protos import ydb_value_pb2 as _ydb_value_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor
EXEC_MODE_EXECUTE: ExecMode
EXEC_MODE_EXPLAIN: ExecMode
EXEC_MODE_PARSE: ExecMode
EXEC_MODE_UNSPECIFIED: ExecMode
EXEC_MODE_VALIDATE: ExecMode
EXEC_STATUS_ABORTED: ExecStatus
EXEC_STATUS_CANCELLED: ExecStatus
EXEC_STATUS_COMPLETED: ExecStatus
EXEC_STATUS_FAILED: ExecStatus
EXEC_STATUS_STARTING: ExecStatus
EXEC_STATUS_UNSPECIFIED: ExecStatus
STATS_MODE_BASIC: StatsMode
STATS_MODE_FULL: StatsMode
STATS_MODE_NONE: StatsMode
STATS_MODE_PROFILE: StatsMode
STATS_MODE_UNSPECIFIED: StatsMode
SYNTAX_PG: Syntax
SYNTAX_UNSPECIFIED: Syntax
SYNTAX_YQL_V1: Syntax

class AttachSessionRequest(_message.Message):
    __slots__ = ["session_id"]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    def __init__(self, session_id: _Optional[str] = ...) -> None: ...

class BeginTransactionRequest(_message.Message):
    __slots__ = ["session_id", "tx_settings"]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TX_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    tx_settings: TransactionSettings
    def __init__(self, session_id: _Optional[str] = ..., tx_settings: _Optional[_Union[TransactionSettings, _Mapping]] = ...) -> None: ...

class BeginTransactionResponse(_message.Message):
    __slots__ = ["issues", "status", "tx_meta"]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    TX_META_FIELD_NUMBER: _ClassVar[int]
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    tx_meta: TransactionMeta
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., tx_meta: _Optional[_Union[TransactionMeta, _Mapping]] = ...) -> None: ...

class CommitTransactionRequest(_message.Message):
    __slots__ = ["session_id", "tx_id"]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TX_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    tx_id: str
    def __init__(self, session_id: _Optional[str] = ..., tx_id: _Optional[str] = ...) -> None: ...

class CommitTransactionResponse(_message.Message):
    __slots__ = ["issues", "status"]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ...) -> None: ...

class CreateSessionRequest(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class CreateSessionResponse(_message.Message):
    __slots__ = ["issues", "node_id", "session_id", "status"]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    node_id: int
    session_id: str
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., session_id: _Optional[str] = ..., node_id: _Optional[int] = ...) -> None: ...

class DeleteSessionRequest(_message.Message):
    __slots__ = ["session_id"]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    def __init__(self, session_id: _Optional[str] = ...) -> None: ...

class DeleteSessionResponse(_message.Message):
    __slots__ = ["issues", "status"]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ...) -> None: ...

class ExecuteQueryRequest(_message.Message):
    __slots__ = ["concurrent_result_sets", "exec_mode", "parameters", "query_content", "session_id", "stats_mode", "tx_control"]
    class ParametersEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _ydb_value_pb2.TypedValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ...) -> None: ...
    CONCURRENT_RESULT_SETS_FIELD_NUMBER: _ClassVar[int]
    EXEC_MODE_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    QUERY_CONTENT_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    STATS_MODE_FIELD_NUMBER: _ClassVar[int]
    TX_CONTROL_FIELD_NUMBER: _ClassVar[int]
    concurrent_result_sets: bool
    exec_mode: ExecMode
    parameters: _containers.MessageMap[str, _ydb_value_pb2.TypedValue]
    query_content: QueryContent
    session_id: str
    stats_mode: StatsMode
    tx_control: TransactionControl
    def __init__(self, session_id: _Optional[str] = ..., exec_mode: _Optional[_Union[ExecMode, str]] = ..., tx_control: _Optional[_Union[TransactionControl, _Mapping]] = ..., query_content: _Optional[_Union[QueryContent, _Mapping]] = ..., parameters: _Optional[_Mapping[str, _ydb_value_pb2.TypedValue]] = ..., stats_mode: _Optional[_Union[StatsMode, str]] = ..., concurrent_result_sets: bool = ...) -> None: ...

class ExecuteQueryResponsePart(_message.Message):
    __slots__ = ["exec_stats", "issues", "result_set", "result_set_index", "status"]
    EXEC_STATS_FIELD_NUMBER: _ClassVar[int]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_INDEX_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    exec_stats: _ydb_query_stats_pb2.QueryStats
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    result_set: _ydb_value_pb2.ResultSet
    result_set_index: int
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., result_set_index: _Optional[int] = ..., result_set: _Optional[_Union[_ydb_value_pb2.ResultSet, _Mapping]] = ..., exec_stats: _Optional[_Union[_ydb_query_stats_pb2.QueryStats, _Mapping]] = ...) -> None: ...

class ExecuteScriptMetadata(_message.Message):
    __slots__ = ["exec_mode", "exec_stats", "exec_status", "execution_id", "result_sets_meta", "script_content"]
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    EXEC_MODE_FIELD_NUMBER: _ClassVar[int]
    EXEC_STATS_FIELD_NUMBER: _ClassVar[int]
    EXEC_STATUS_FIELD_NUMBER: _ClassVar[int]
    RESULT_SETS_META_FIELD_NUMBER: _ClassVar[int]
    SCRIPT_CONTENT_FIELD_NUMBER: _ClassVar[int]
    exec_mode: ExecMode
    exec_stats: _ydb_query_stats_pb2.QueryStats
    exec_status: ExecStatus
    execution_id: str
    result_sets_meta: _containers.RepeatedCompositeFieldContainer[ResultSetMeta]
    script_content: QueryContent
    def __init__(self, execution_id: _Optional[str] = ..., exec_status: _Optional[_Union[ExecStatus, str]] = ..., script_content: _Optional[_Union[QueryContent, _Mapping]] = ..., result_sets_meta: _Optional[_Iterable[_Union[ResultSetMeta, _Mapping]]] = ..., exec_mode: _Optional[_Union[ExecMode, str]] = ..., exec_stats: _Optional[_Union[_ydb_query_stats_pb2.QueryStats, _Mapping]] = ...) -> None: ...

class ExecuteScriptRequest(_message.Message):
    __slots__ = ["exec_mode", "operation_params", "parameters", "results_ttl", "script_content", "stats_mode"]
    class ParametersEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _ydb_value_pb2.TypedValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ...) -> None: ...
    EXEC_MODE_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    RESULTS_TTL_FIELD_NUMBER: _ClassVar[int]
    SCRIPT_CONTENT_FIELD_NUMBER: _ClassVar[int]
    STATS_MODE_FIELD_NUMBER: _ClassVar[int]
    exec_mode: ExecMode
    operation_params: _ydb_operation_pb2.OperationParams
    parameters: _containers.MessageMap[str, _ydb_value_pb2.TypedValue]
    results_ttl: _duration_pb2.Duration
    script_content: QueryContent
    stats_mode: StatsMode
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., exec_mode: _Optional[_Union[ExecMode, str]] = ..., script_content: _Optional[_Union[QueryContent, _Mapping]] = ..., parameters: _Optional[_Mapping[str, _ydb_value_pb2.TypedValue]] = ..., stats_mode: _Optional[_Union[StatsMode, str]] = ..., results_ttl: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ...) -> None: ...

class FetchScriptResultsRequest(_message.Message):
    __slots__ = ["fetch_token", "operation_id", "result_set_index", "rows_limit"]
    FETCH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    OPERATION_ID_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_INDEX_FIELD_NUMBER: _ClassVar[int]
    ROWS_LIMIT_FIELD_NUMBER: _ClassVar[int]
    fetch_token: str
    operation_id: str
    result_set_index: int
    rows_limit: int
    def __init__(self, operation_id: _Optional[str] = ..., result_set_index: _Optional[int] = ..., fetch_token: _Optional[str] = ..., rows_limit: _Optional[int] = ...) -> None: ...

class FetchScriptResultsResponse(_message.Message):
    __slots__ = ["issues", "next_fetch_token", "result_set", "result_set_index", "status"]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    NEXT_FETCH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_INDEX_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    next_fetch_token: str
    result_set: _ydb_value_pb2.ResultSet
    result_set_index: int
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., result_set_index: _Optional[int] = ..., result_set: _Optional[_Union[_ydb_value_pb2.ResultSet, _Mapping]] = ..., next_fetch_token: _Optional[str] = ...) -> None: ...

class OnlineModeSettings(_message.Message):
    __slots__ = ["allow_inconsistent_reads"]
    ALLOW_INCONSISTENT_READS_FIELD_NUMBER: _ClassVar[int]
    allow_inconsistent_reads: bool
    def __init__(self, allow_inconsistent_reads: bool = ...) -> None: ...

class QueryContent(_message.Message):
    __slots__ = ["syntax", "text"]
    SYNTAX_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    syntax: Syntax
    text: str
    def __init__(self, syntax: _Optional[_Union[Syntax, str]] = ..., text: _Optional[str] = ...) -> None: ...

class ResultSetMeta(_message.Message):
    __slots__ = ["columns"]
    COLUMNS_FIELD_NUMBER: _ClassVar[int]
    columns: _containers.RepeatedCompositeFieldContainer[_ydb_value_pb2.Column]
    def __init__(self, columns: _Optional[_Iterable[_Union[_ydb_value_pb2.Column, _Mapping]]] = ...) -> None: ...

class RollbackTransactionRequest(_message.Message):
    __slots__ = ["session_id", "tx_id"]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TX_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    tx_id: str
    def __init__(self, session_id: _Optional[str] = ..., tx_id: _Optional[str] = ...) -> None: ...

class RollbackTransactionResponse(_message.Message):
    __slots__ = ["issues", "status"]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ...) -> None: ...

class Script(_message.Message):
    __slots__ = ["script_content"]
    SCRIPT_CONTENT_FIELD_NUMBER: _ClassVar[int]
    script_content: QueryContent
    def __init__(self, script_content: _Optional[_Union[QueryContent, _Mapping]] = ...) -> None: ...

class SerializableModeSettings(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class SessionState(_message.Message):
    __slots__ = ["issues", "status"]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ...) -> None: ...

class SnapshotModeSettings(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class StaleModeSettings(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class TransactionControl(_message.Message):
    __slots__ = ["begin_tx", "commit_tx", "tx_id"]
    BEGIN_TX_FIELD_NUMBER: _ClassVar[int]
    COMMIT_TX_FIELD_NUMBER: _ClassVar[int]
    TX_ID_FIELD_NUMBER: _ClassVar[int]
    begin_tx: TransactionSettings
    commit_tx: bool
    tx_id: str
    def __init__(self, tx_id: _Optional[str] = ..., begin_tx: _Optional[_Union[TransactionSettings, _Mapping]] = ..., commit_tx: bool = ...) -> None: ...

class TransactionMeta(_message.Message):
    __slots__ = ["id"]
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class TransactionSettings(_message.Message):
    __slots__ = ["online_read_only", "serializable_read_write", "snapshot_read_only", "stale_read_only"]
    ONLINE_READ_ONLY_FIELD_NUMBER: _ClassVar[int]
    SERIALIZABLE_READ_WRITE_FIELD_NUMBER: _ClassVar[int]
    SNAPSHOT_READ_ONLY_FIELD_NUMBER: _ClassVar[int]
    STALE_READ_ONLY_FIELD_NUMBER: _ClassVar[int]
    online_read_only: OnlineModeSettings
    serializable_read_write: SerializableModeSettings
    snapshot_read_only: SnapshotModeSettings
    stale_read_only: StaleModeSettings
    def __init__(self, serializable_read_write: _Optional[_Union[SerializableModeSettings, _Mapping]] = ..., online_read_only: _Optional[_Union[OnlineModeSettings, _Mapping]] = ..., stale_read_only: _Optional[_Union[StaleModeSettings, _Mapping]] = ..., snapshot_read_only: _Optional[_Union[SnapshotModeSettings, _Mapping]] = ...) -> None: ...

class Syntax(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class ExecMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class StatsMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class ExecStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
