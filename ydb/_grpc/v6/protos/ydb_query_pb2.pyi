import datetime

from google.protobuf import duration_pb2 as _duration_pb2
from protos.annotations import validation_pb2 as _validation_pb2
from protos import ydb_issue_message_pb2 as _ydb_issue_message_pb2
from protos import ydb_operation_pb2 as _ydb_operation_pb2
from protos import ydb_query_stats_pb2 as _ydb_query_stats_pb2
from protos import ydb_status_codes_pb2 as _ydb_status_codes_pb2
from protos import ydb_formats_pb2 as _ydb_formats_pb2
from protos import ydb_value_pb2 as _ydb_value_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Syntax(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SYNTAX_UNSPECIFIED: _ClassVar[Syntax]
    SYNTAX_YQL_V1: _ClassVar[Syntax]
    SYNTAX_PG: _ClassVar[Syntax]

class ExecMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EXEC_MODE_UNSPECIFIED: _ClassVar[ExecMode]
    EXEC_MODE_PARSE: _ClassVar[ExecMode]
    EXEC_MODE_VALIDATE: _ClassVar[ExecMode]
    EXEC_MODE_EXPLAIN: _ClassVar[ExecMode]
    EXEC_MODE_EXECUTE: _ClassVar[ExecMode]

class StatsMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    STATS_MODE_UNSPECIFIED: _ClassVar[StatsMode]
    STATS_MODE_NONE: _ClassVar[StatsMode]
    STATS_MODE_BASIC: _ClassVar[StatsMode]
    STATS_MODE_FULL: _ClassVar[StatsMode]
    STATS_MODE_PROFILE: _ClassVar[StatsMode]

class SchemaInclusionMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SCHEMA_INCLUSION_MODE_UNSPECIFIED: _ClassVar[SchemaInclusionMode]
    SCHEMA_INCLUSION_MODE_ALWAYS: _ClassVar[SchemaInclusionMode]
    SCHEMA_INCLUSION_MODE_FIRST_ONLY: _ClassVar[SchemaInclusionMode]

class ExecStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EXEC_STATUS_UNSPECIFIED: _ClassVar[ExecStatus]
    EXEC_STATUS_STARTING: _ClassVar[ExecStatus]
    EXEC_STATUS_ABORTED: _ClassVar[ExecStatus]
    EXEC_STATUS_CANCELLED: _ClassVar[ExecStatus]
    EXEC_STATUS_COMPLETED: _ClassVar[ExecStatus]
    EXEC_STATUS_FAILED: _ClassVar[ExecStatus]
SYNTAX_UNSPECIFIED: Syntax
SYNTAX_YQL_V1: Syntax
SYNTAX_PG: Syntax
EXEC_MODE_UNSPECIFIED: ExecMode
EXEC_MODE_PARSE: ExecMode
EXEC_MODE_VALIDATE: ExecMode
EXEC_MODE_EXPLAIN: ExecMode
EXEC_MODE_EXECUTE: ExecMode
STATS_MODE_UNSPECIFIED: StatsMode
STATS_MODE_NONE: StatsMode
STATS_MODE_BASIC: StatsMode
STATS_MODE_FULL: StatsMode
STATS_MODE_PROFILE: StatsMode
SCHEMA_INCLUSION_MODE_UNSPECIFIED: SchemaInclusionMode
SCHEMA_INCLUSION_MODE_ALWAYS: SchemaInclusionMode
SCHEMA_INCLUSION_MODE_FIRST_ONLY: SchemaInclusionMode
EXEC_STATUS_UNSPECIFIED: ExecStatus
EXEC_STATUS_STARTING: ExecStatus
EXEC_STATUS_ABORTED: ExecStatus
EXEC_STATUS_CANCELLED: ExecStatus
EXEC_STATUS_COMPLETED: ExecStatus
EXEC_STATUS_FAILED: ExecStatus

class CreateSessionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CreateSessionResponse(_message.Message):
    __slots__ = ("status", "issues", "session_id", "node_id")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    session_id: str
    node_id: int
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., session_id: _Optional[str] = ..., node_id: _Optional[int] = ...) -> None: ...

class DeleteSessionRequest(_message.Message):
    __slots__ = ("session_id",)
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    def __init__(self, session_id: _Optional[str] = ...) -> None: ...

class DeleteSessionResponse(_message.Message):
    __slots__ = ("status", "issues")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ...) -> None: ...

class AttachSessionRequest(_message.Message):
    __slots__ = ("session_id",)
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    def __init__(self, session_id: _Optional[str] = ...) -> None: ...

class SessionState(_message.Message):
    __slots__ = ("status", "issues")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ...) -> None: ...

class SerializableModeSettings(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class OnlineModeSettings(_message.Message):
    __slots__ = ("allow_inconsistent_reads",)
    ALLOW_INCONSISTENT_READS_FIELD_NUMBER: _ClassVar[int]
    allow_inconsistent_reads: bool
    def __init__(self, allow_inconsistent_reads: bool = ...) -> None: ...

class StaleModeSettings(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SnapshotModeSettings(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SnapshotRWModeSettings(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class TransactionSettings(_message.Message):
    __slots__ = ("serializable_read_write", "online_read_only", "stale_read_only", "snapshot_read_only", "snapshot_read_write")
    SERIALIZABLE_READ_WRITE_FIELD_NUMBER: _ClassVar[int]
    ONLINE_READ_ONLY_FIELD_NUMBER: _ClassVar[int]
    STALE_READ_ONLY_FIELD_NUMBER: _ClassVar[int]
    SNAPSHOT_READ_ONLY_FIELD_NUMBER: _ClassVar[int]
    SNAPSHOT_READ_WRITE_FIELD_NUMBER: _ClassVar[int]
    serializable_read_write: SerializableModeSettings
    online_read_only: OnlineModeSettings
    stale_read_only: StaleModeSettings
    snapshot_read_only: SnapshotModeSettings
    snapshot_read_write: SnapshotRWModeSettings
    def __init__(self, serializable_read_write: _Optional[_Union[SerializableModeSettings, _Mapping]] = ..., online_read_only: _Optional[_Union[OnlineModeSettings, _Mapping]] = ..., stale_read_only: _Optional[_Union[StaleModeSettings, _Mapping]] = ..., snapshot_read_only: _Optional[_Union[SnapshotModeSettings, _Mapping]] = ..., snapshot_read_write: _Optional[_Union[SnapshotRWModeSettings, _Mapping]] = ...) -> None: ...

class TransactionControl(_message.Message):
    __slots__ = ("tx_id", "begin_tx", "commit_tx")
    TX_ID_FIELD_NUMBER: _ClassVar[int]
    BEGIN_TX_FIELD_NUMBER: _ClassVar[int]
    COMMIT_TX_FIELD_NUMBER: _ClassVar[int]
    tx_id: str
    begin_tx: TransactionSettings
    commit_tx: bool
    def __init__(self, tx_id: _Optional[str] = ..., begin_tx: _Optional[_Union[TransactionSettings, _Mapping]] = ..., commit_tx: bool = ...) -> None: ...

class BeginTransactionRequest(_message.Message):
    __slots__ = ("session_id", "tx_settings")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TX_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    tx_settings: TransactionSettings
    def __init__(self, session_id: _Optional[str] = ..., tx_settings: _Optional[_Union[TransactionSettings, _Mapping]] = ...) -> None: ...

class TransactionMeta(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class BeginTransactionResponse(_message.Message):
    __slots__ = ("status", "issues", "tx_meta")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    TX_META_FIELD_NUMBER: _ClassVar[int]
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    tx_meta: TransactionMeta
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., tx_meta: _Optional[_Union[TransactionMeta, _Mapping]] = ...) -> None: ...

class CommitTransactionRequest(_message.Message):
    __slots__ = ("session_id", "tx_id")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TX_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    tx_id: str
    def __init__(self, session_id: _Optional[str] = ..., tx_id: _Optional[str] = ...) -> None: ...

class CommitTransactionResponse(_message.Message):
    __slots__ = ("status", "issues")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ...) -> None: ...

class RollbackTransactionRequest(_message.Message):
    __slots__ = ("session_id", "tx_id")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TX_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    tx_id: str
    def __init__(self, session_id: _Optional[str] = ..., tx_id: _Optional[str] = ...) -> None: ...

class RollbackTransactionResponse(_message.Message):
    __slots__ = ("status", "issues")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ...) -> None: ...

class QueryContent(_message.Message):
    __slots__ = ("syntax", "text")
    SYNTAX_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    syntax: Syntax
    text: str
    def __init__(self, syntax: _Optional[_Union[Syntax, str]] = ..., text: _Optional[str] = ...) -> None: ...

class ExecuteQueryRequest(_message.Message):
    __slots__ = ("session_id", "exec_mode", "tx_control", "query_content", "parameters", "stats_mode", "concurrent_result_sets", "response_part_limit_bytes", "pool_id", "stats_period_ms", "schema_inclusion_mode", "result_set_format", "arrow_format_settings")
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _ydb_value_pb2.TypedValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ...) -> None: ...
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    EXEC_MODE_FIELD_NUMBER: _ClassVar[int]
    TX_CONTROL_FIELD_NUMBER: _ClassVar[int]
    QUERY_CONTENT_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    STATS_MODE_FIELD_NUMBER: _ClassVar[int]
    CONCURRENT_RESULT_SETS_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_PART_LIMIT_BYTES_FIELD_NUMBER: _ClassVar[int]
    POOL_ID_FIELD_NUMBER: _ClassVar[int]
    STATS_PERIOD_MS_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_INCLUSION_MODE_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_FORMAT_FIELD_NUMBER: _ClassVar[int]
    ARROW_FORMAT_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    exec_mode: ExecMode
    tx_control: TransactionControl
    query_content: QueryContent
    parameters: _containers.MessageMap[str, _ydb_value_pb2.TypedValue]
    stats_mode: StatsMode
    concurrent_result_sets: bool
    response_part_limit_bytes: int
    pool_id: str
    stats_period_ms: int
    schema_inclusion_mode: SchemaInclusionMode
    result_set_format: _ydb_value_pb2.ResultSet.Format
    arrow_format_settings: _ydb_formats_pb2.ArrowFormatSettings
    def __init__(self, session_id: _Optional[str] = ..., exec_mode: _Optional[_Union[ExecMode, str]] = ..., tx_control: _Optional[_Union[TransactionControl, _Mapping]] = ..., query_content: _Optional[_Union[QueryContent, _Mapping]] = ..., parameters: _Optional[_Mapping[str, _ydb_value_pb2.TypedValue]] = ..., stats_mode: _Optional[_Union[StatsMode, str]] = ..., concurrent_result_sets: bool = ..., response_part_limit_bytes: _Optional[int] = ..., pool_id: _Optional[str] = ..., stats_period_ms: _Optional[int] = ..., schema_inclusion_mode: _Optional[_Union[SchemaInclusionMode, str]] = ..., result_set_format: _Optional[_Union[_ydb_value_pb2.ResultSet.Format, str]] = ..., arrow_format_settings: _Optional[_Union[_ydb_formats_pb2.ArrowFormatSettings, _Mapping]] = ...) -> None: ...

class ResultSetMeta(_message.Message):
    __slots__ = ("columns",)
    COLUMNS_FIELD_NUMBER: _ClassVar[int]
    columns: _containers.RepeatedCompositeFieldContainer[_ydb_value_pb2.Column]
    def __init__(self, columns: _Optional[_Iterable[_Union[_ydb_value_pb2.Column, _Mapping]]] = ...) -> None: ...

class ExecuteQueryResponsePart(_message.Message):
    __slots__ = ("status", "issues", "result_set_index", "result_set", "exec_stats", "tx_meta")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_INDEX_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_FIELD_NUMBER: _ClassVar[int]
    EXEC_STATS_FIELD_NUMBER: _ClassVar[int]
    TX_META_FIELD_NUMBER: _ClassVar[int]
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    result_set_index: int
    result_set: _ydb_value_pb2.ResultSet
    exec_stats: _ydb_query_stats_pb2.QueryStats
    tx_meta: TransactionMeta
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., result_set_index: _Optional[int] = ..., result_set: _Optional[_Union[_ydb_value_pb2.ResultSet, _Mapping]] = ..., exec_stats: _Optional[_Union[_ydb_query_stats_pb2.QueryStats, _Mapping]] = ..., tx_meta: _Optional[_Union[TransactionMeta, _Mapping]] = ...) -> None: ...

class ExecuteScriptRequest(_message.Message):
    __slots__ = ("operation_params", "exec_mode", "script_content", "parameters", "stats_mode", "results_ttl", "pool_id")
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _ydb_value_pb2.TypedValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ...) -> None: ...
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    EXEC_MODE_FIELD_NUMBER: _ClassVar[int]
    SCRIPT_CONTENT_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    STATS_MODE_FIELD_NUMBER: _ClassVar[int]
    RESULTS_TTL_FIELD_NUMBER: _ClassVar[int]
    POOL_ID_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    exec_mode: ExecMode
    script_content: QueryContent
    parameters: _containers.MessageMap[str, _ydb_value_pb2.TypedValue]
    stats_mode: StatsMode
    results_ttl: _duration_pb2.Duration
    pool_id: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., exec_mode: _Optional[_Union[ExecMode, str]] = ..., script_content: _Optional[_Union[QueryContent, _Mapping]] = ..., parameters: _Optional[_Mapping[str, _ydb_value_pb2.TypedValue]] = ..., stats_mode: _Optional[_Union[StatsMode, str]] = ..., results_ttl: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., pool_id: _Optional[str] = ...) -> None: ...

class ExecuteScriptMetadata(_message.Message):
    __slots__ = ("execution_id", "exec_status", "script_content", "result_sets_meta", "exec_mode", "exec_stats")
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    EXEC_STATUS_FIELD_NUMBER: _ClassVar[int]
    SCRIPT_CONTENT_FIELD_NUMBER: _ClassVar[int]
    RESULT_SETS_META_FIELD_NUMBER: _ClassVar[int]
    EXEC_MODE_FIELD_NUMBER: _ClassVar[int]
    EXEC_STATS_FIELD_NUMBER: _ClassVar[int]
    execution_id: str
    exec_status: ExecStatus
    script_content: QueryContent
    result_sets_meta: _containers.RepeatedCompositeFieldContainer[ResultSetMeta]
    exec_mode: ExecMode
    exec_stats: _ydb_query_stats_pb2.QueryStats
    def __init__(self, execution_id: _Optional[str] = ..., exec_status: _Optional[_Union[ExecStatus, str]] = ..., script_content: _Optional[_Union[QueryContent, _Mapping]] = ..., result_sets_meta: _Optional[_Iterable[_Union[ResultSetMeta, _Mapping]]] = ..., exec_mode: _Optional[_Union[ExecMode, str]] = ..., exec_stats: _Optional[_Union[_ydb_query_stats_pb2.QueryStats, _Mapping]] = ...) -> None: ...

class FetchScriptResultsRequest(_message.Message):
    __slots__ = ("operation_id", "result_set_index", "fetch_token", "rows_limit")
    OPERATION_ID_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_INDEX_FIELD_NUMBER: _ClassVar[int]
    FETCH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    ROWS_LIMIT_FIELD_NUMBER: _ClassVar[int]
    operation_id: str
    result_set_index: int
    fetch_token: str
    rows_limit: int
    def __init__(self, operation_id: _Optional[str] = ..., result_set_index: _Optional[int] = ..., fetch_token: _Optional[str] = ..., rows_limit: _Optional[int] = ...) -> None: ...

class FetchScriptResultsResponse(_message.Message):
    __slots__ = ("status", "issues", "result_set_index", "result_set", "next_fetch_token")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_INDEX_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_FIELD_NUMBER: _ClassVar[int]
    NEXT_FETCH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    result_set_index: int
    result_set: _ydb_value_pb2.ResultSet
    next_fetch_token: str
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., result_set_index: _Optional[int] = ..., result_set: _Optional[_Union[_ydb_value_pb2.ResultSet, _Mapping]] = ..., next_fetch_token: _Optional[str] = ...) -> None: ...

class Script(_message.Message):
    __slots__ = ("script_content",)
    SCRIPT_CONTENT_FIELD_NUMBER: _ClassVar[int]
    script_content: QueryContent
    def __init__(self, script_content: _Optional[_Union[QueryContent, _Mapping]] = ...) -> None: ...
