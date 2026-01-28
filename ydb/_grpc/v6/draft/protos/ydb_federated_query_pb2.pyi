import datetime

from protos.annotations import sensitive_pb2 as _sensitive_pb2
from protos.annotations import validation_pb2 as _validation_pb2
from protos import ydb_operation_pb2 as _ydb_operation_pb2
from protos import ydb_value_pb2 as _ydb_value_pb2
from protos import ydb_issue_message_pb2 as _ydb_issue_message_pb2
from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ExecuteMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EXECUTE_MODE_UNSPECIFIED: _ClassVar[ExecuteMode]
    SAVE: _ClassVar[ExecuteMode]
    PARSE: _ClassVar[ExecuteMode]
    COMPILE: _ClassVar[ExecuteMode]
    VALIDATE: _ClassVar[ExecuteMode]
    EXPLAIN: _ClassVar[ExecuteMode]
    RUN: _ClassVar[ExecuteMode]

class QueryAction(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    QUERY_ACTION_UNSPECIFIED: _ClassVar[QueryAction]
    PAUSE: _ClassVar[QueryAction]
    PAUSE_GRACEFULLY: _ClassVar[QueryAction]
    ABORT: _ClassVar[QueryAction]
    ABORT_GRACEFULLY: _ClassVar[QueryAction]
    RESUME: _ClassVar[QueryAction]

class StateLoadMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    STATE_LOAD_MODE_UNSPECIFIED: _ClassVar[StateLoadMode]
    EMPTY: _ClassVar[StateLoadMode]
    FROM_LAST_CHECKPOINT: _ClassVar[StateLoadMode]

class AutomaticType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    AUTOMATIC_TYPE_UNSPECIFIED: _ClassVar[AutomaticType]
    AUTOMATIC: _ClassVar[AutomaticType]
    NOT_AUTOMATIC: _ClassVar[AutomaticType]
EXECUTE_MODE_UNSPECIFIED: ExecuteMode
SAVE: ExecuteMode
PARSE: ExecuteMode
COMPILE: ExecuteMode
VALIDATE: ExecuteMode
EXPLAIN: ExecuteMode
RUN: ExecuteMode
QUERY_ACTION_UNSPECIFIED: QueryAction
PAUSE: QueryAction
PAUSE_GRACEFULLY: QueryAction
ABORT: QueryAction
ABORT_GRACEFULLY: QueryAction
RESUME: QueryAction
STATE_LOAD_MODE_UNSPECIFIED: StateLoadMode
EMPTY: StateLoadMode
FROM_LAST_CHECKPOINT: StateLoadMode
AUTOMATIC_TYPE_UNSPECIFIED: AutomaticType
AUTOMATIC: AutomaticType
NOT_AUTOMATIC: AutomaticType

class Acl(_message.Message):
    __slots__ = ("visibility",)
    class Visibility(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        VISIBILITY_UNSPECIFIED: _ClassVar[Acl.Visibility]
        PRIVATE: _ClassVar[Acl.Visibility]
        SCOPE: _ClassVar[Acl.Visibility]
    VISIBILITY_UNSPECIFIED: Acl.Visibility
    PRIVATE: Acl.Visibility
    SCOPE: Acl.Visibility
    VISIBILITY_FIELD_NUMBER: _ClassVar[int]
    visibility: Acl.Visibility
    def __init__(self, visibility: _Optional[_Union[Acl.Visibility, str]] = ...) -> None: ...

class Limits(_message.Message):
    __slots__ = ("vcpu_rate_limit", "flow_rate_limit", "vcpu_time_limit", "max_result_size", "max_result_rows", "memory_limit", "result_ttl", "execution_timeout", "execution_deadline")
    VCPU_RATE_LIMIT_FIELD_NUMBER: _ClassVar[int]
    FLOW_RATE_LIMIT_FIELD_NUMBER: _ClassVar[int]
    VCPU_TIME_LIMIT_FIELD_NUMBER: _ClassVar[int]
    MAX_RESULT_SIZE_FIELD_NUMBER: _ClassVar[int]
    MAX_RESULT_ROWS_FIELD_NUMBER: _ClassVar[int]
    MEMORY_LIMIT_FIELD_NUMBER: _ClassVar[int]
    RESULT_TTL_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_DEADLINE_FIELD_NUMBER: _ClassVar[int]
    vcpu_rate_limit: int
    flow_rate_limit: int
    vcpu_time_limit: int
    max_result_size: int
    max_result_rows: int
    memory_limit: int
    result_ttl: _duration_pb2.Duration
    execution_timeout: _duration_pb2.Duration
    execution_deadline: _timestamp_pb2.Timestamp
    def __init__(self, vcpu_rate_limit: _Optional[int] = ..., flow_rate_limit: _Optional[int] = ..., vcpu_time_limit: _Optional[int] = ..., max_result_size: _Optional[int] = ..., max_result_rows: _Optional[int] = ..., memory_limit: _Optional[int] = ..., result_ttl: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., execution_timeout: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., execution_deadline: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class StreamingDisposition(_message.Message):
    __slots__ = ("oldest", "fresh", "from_time", "time_ago", "from_last_checkpoint")
    class FromTime(_message.Message):
        __slots__ = ("timestamp",)
        TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
        timestamp: _timestamp_pb2.Timestamp
        def __init__(self, timestamp: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
    class TimeAgo(_message.Message):
        __slots__ = ("duration",)
        DURATION_FIELD_NUMBER: _ClassVar[int]
        duration: _duration_pb2.Duration
        def __init__(self, duration: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ...) -> None: ...
    class FromLastCheckpoint(_message.Message):
        __slots__ = ("force",)
        FORCE_FIELD_NUMBER: _ClassVar[int]
        force: bool
        def __init__(self, force: bool = ...) -> None: ...
    OLDEST_FIELD_NUMBER: _ClassVar[int]
    FRESH_FIELD_NUMBER: _ClassVar[int]
    FROM_TIME_FIELD_NUMBER: _ClassVar[int]
    TIME_AGO_FIELD_NUMBER: _ClassVar[int]
    FROM_LAST_CHECKPOINT_FIELD_NUMBER: _ClassVar[int]
    oldest: _empty_pb2.Empty
    fresh: _empty_pb2.Empty
    from_time: StreamingDisposition.FromTime
    time_ago: StreamingDisposition.TimeAgo
    from_last_checkpoint: StreamingDisposition.FromLastCheckpoint
    def __init__(self, oldest: _Optional[_Union[_empty_pb2.Empty, _Mapping]] = ..., fresh: _Optional[_Union[_empty_pb2.Empty, _Mapping]] = ..., from_time: _Optional[_Union[StreamingDisposition.FromTime, _Mapping]] = ..., time_ago: _Optional[_Union[StreamingDisposition.TimeAgo, _Mapping]] = ..., from_last_checkpoint: _Optional[_Union[StreamingDisposition.FromLastCheckpoint, _Mapping]] = ...) -> None: ...

class QueryContent(_message.Message):
    __slots__ = ("type", "name", "acl", "limits", "text", "automatic", "description", "execution_settings", "syntax", "parameters")
    class QueryType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        QUERY_TYPE_UNSPECIFIED: _ClassVar[QueryContent.QueryType]
        ANALYTICS: _ClassVar[QueryContent.QueryType]
        STREAMING: _ClassVar[QueryContent.QueryType]
    QUERY_TYPE_UNSPECIFIED: QueryContent.QueryType
    ANALYTICS: QueryContent.QueryType
    STREAMING: QueryContent.QueryType
    class QuerySyntax(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        QUERY_SYNTAX_UNSPECIFIED: _ClassVar[QueryContent.QuerySyntax]
        YQL_V1: _ClassVar[QueryContent.QuerySyntax]
        PG: _ClassVar[QueryContent.QuerySyntax]
    QUERY_SYNTAX_UNSPECIFIED: QueryContent.QuerySyntax
    YQL_V1: QueryContent.QuerySyntax
    PG: QueryContent.QuerySyntax
    class ExecutionSettingsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _ydb_value_pb2.TypedValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ...) -> None: ...
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ACL_FIELD_NUMBER: _ClassVar[int]
    LIMITS_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    AUTOMATIC_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    SYNTAX_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    type: QueryContent.QueryType
    name: str
    acl: Acl
    limits: Limits
    text: str
    automatic: bool
    description: str
    execution_settings: _containers.ScalarMap[str, str]
    syntax: QueryContent.QuerySyntax
    parameters: _containers.MessageMap[str, _ydb_value_pb2.TypedValue]
    def __init__(self, type: _Optional[_Union[QueryContent.QueryType, str]] = ..., name: _Optional[str] = ..., acl: _Optional[_Union[Acl, _Mapping]] = ..., limits: _Optional[_Union[Limits, _Mapping]] = ..., text: _Optional[str] = ..., automatic: bool = ..., description: _Optional[str] = ..., execution_settings: _Optional[_Mapping[str, str]] = ..., syntax: _Optional[_Union[QueryContent.QuerySyntax, str]] = ..., parameters: _Optional[_Mapping[str, _ydb_value_pb2.TypedValue]] = ...) -> None: ...

class CommonMeta(_message.Message):
    __slots__ = ("id", "created_by", "modified_by", "created_at", "modified_at", "revision")
    ID_FIELD_NUMBER: _ClassVar[int]
    CREATED_BY_FIELD_NUMBER: _ClassVar[int]
    MODIFIED_BY_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    MODIFIED_AT_FIELD_NUMBER: _ClassVar[int]
    REVISION_FIELD_NUMBER: _ClassVar[int]
    id: str
    created_by: str
    modified_by: str
    created_at: _timestamp_pb2.Timestamp
    modified_at: _timestamp_pb2.Timestamp
    revision: int
    def __init__(self, id: _Optional[str] = ..., created_by: _Optional[str] = ..., modified_by: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., modified_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., revision: _Optional[int] = ...) -> None: ...

class QueryMeta(_message.Message):
    __slots__ = ("common", "submitted_at", "started_at", "finished_at", "execute_mode", "status", "last_job_query_revision", "last_job_id", "expire_at", "result_expire_at", "started_by", "aborted_by", "paused_by", "has_saved_checkpoints")
    class ComputeStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        COMPUTE_STATUS_UNSPECIFIED: _ClassVar[QueryMeta.ComputeStatus]
        STARTING: _ClassVar[QueryMeta.ComputeStatus]
        ABORTED_BY_USER: _ClassVar[QueryMeta.ComputeStatus]
        ABORTED_BY_SYSTEM: _ClassVar[QueryMeta.ComputeStatus]
        ABORTING_BY_USER: _ClassVar[QueryMeta.ComputeStatus]
        ABORTING_BY_SYSTEM: _ClassVar[QueryMeta.ComputeStatus]
        RESUMING: _ClassVar[QueryMeta.ComputeStatus]
        RUNNING: _ClassVar[QueryMeta.ComputeStatus]
        COMPLETED: _ClassVar[QueryMeta.ComputeStatus]
        COMPLETING: _ClassVar[QueryMeta.ComputeStatus]
        FAILED: _ClassVar[QueryMeta.ComputeStatus]
        FAILING: _ClassVar[QueryMeta.ComputeStatus]
        PAUSED: _ClassVar[QueryMeta.ComputeStatus]
        PAUSING: _ClassVar[QueryMeta.ComputeStatus]
    COMPUTE_STATUS_UNSPECIFIED: QueryMeta.ComputeStatus
    STARTING: QueryMeta.ComputeStatus
    ABORTED_BY_USER: QueryMeta.ComputeStatus
    ABORTED_BY_SYSTEM: QueryMeta.ComputeStatus
    ABORTING_BY_USER: QueryMeta.ComputeStatus
    ABORTING_BY_SYSTEM: QueryMeta.ComputeStatus
    RESUMING: QueryMeta.ComputeStatus
    RUNNING: QueryMeta.ComputeStatus
    COMPLETED: QueryMeta.ComputeStatus
    COMPLETING: QueryMeta.ComputeStatus
    FAILED: QueryMeta.ComputeStatus
    FAILING: QueryMeta.ComputeStatus
    PAUSED: QueryMeta.ComputeStatus
    PAUSING: QueryMeta.ComputeStatus
    COMMON_FIELD_NUMBER: _ClassVar[int]
    SUBMITTED_AT_FIELD_NUMBER: _ClassVar[int]
    STARTED_AT_FIELD_NUMBER: _ClassVar[int]
    FINISHED_AT_FIELD_NUMBER: _ClassVar[int]
    EXECUTE_MODE_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    LAST_JOB_QUERY_REVISION_FIELD_NUMBER: _ClassVar[int]
    LAST_JOB_ID_FIELD_NUMBER: _ClassVar[int]
    EXPIRE_AT_FIELD_NUMBER: _ClassVar[int]
    RESULT_EXPIRE_AT_FIELD_NUMBER: _ClassVar[int]
    STARTED_BY_FIELD_NUMBER: _ClassVar[int]
    ABORTED_BY_FIELD_NUMBER: _ClassVar[int]
    PAUSED_BY_FIELD_NUMBER: _ClassVar[int]
    HAS_SAVED_CHECKPOINTS_FIELD_NUMBER: _ClassVar[int]
    common: CommonMeta
    submitted_at: _timestamp_pb2.Timestamp
    started_at: _timestamp_pb2.Timestamp
    finished_at: _timestamp_pb2.Timestamp
    execute_mode: ExecuteMode
    status: QueryMeta.ComputeStatus
    last_job_query_revision: int
    last_job_id: str
    expire_at: _timestamp_pb2.Timestamp
    result_expire_at: _timestamp_pb2.Timestamp
    started_by: str
    aborted_by: str
    paused_by: str
    has_saved_checkpoints: bool
    def __init__(self, common: _Optional[_Union[CommonMeta, _Mapping]] = ..., submitted_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., started_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., finished_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., execute_mode: _Optional[_Union[ExecuteMode, str]] = ..., status: _Optional[_Union[QueryMeta.ComputeStatus, str]] = ..., last_job_query_revision: _Optional[int] = ..., last_job_id: _Optional[str] = ..., expire_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., result_expire_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., started_by: _Optional[str] = ..., aborted_by: _Optional[str] = ..., paused_by: _Optional[str] = ..., has_saved_checkpoints: bool = ...) -> None: ...

class BriefQuery(_message.Message):
    __slots__ = ("type", "name", "meta", "visibility", "automatic")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    META_FIELD_NUMBER: _ClassVar[int]
    VISIBILITY_FIELD_NUMBER: _ClassVar[int]
    AUTOMATIC_FIELD_NUMBER: _ClassVar[int]
    type: QueryContent.QueryType
    name: str
    meta: QueryMeta
    visibility: Acl.Visibility
    automatic: bool
    def __init__(self, type: _Optional[_Union[QueryContent.QueryType, str]] = ..., name: _Optional[str] = ..., meta: _Optional[_Union[QueryMeta, _Mapping]] = ..., visibility: _Optional[_Union[Acl.Visibility, str]] = ..., automatic: bool = ...) -> None: ...

class QueryPlan(_message.Message):
    __slots__ = ("json",)
    JSON_FIELD_NUMBER: _ClassVar[int]
    json: str
    def __init__(self, json: _Optional[str] = ...) -> None: ...

class QueryAst(_message.Message):
    __slots__ = ("data",)
    DATA_FIELD_NUMBER: _ClassVar[int]
    data: str
    def __init__(self, data: _Optional[str] = ...) -> None: ...

class ResultSetMeta(_message.Message):
    __slots__ = ("column", "rows_count", "truncated")
    COLUMN_FIELD_NUMBER: _ClassVar[int]
    ROWS_COUNT_FIELD_NUMBER: _ClassVar[int]
    TRUNCATED_FIELD_NUMBER: _ClassVar[int]
    column: _containers.RepeatedCompositeFieldContainer[_ydb_value_pb2.Column]
    rows_count: int
    truncated: bool
    def __init__(self, column: _Optional[_Iterable[_Union[_ydb_value_pb2.Column, _Mapping]]] = ..., rows_count: _Optional[int] = ..., truncated: bool = ...) -> None: ...

class QueryTimeline(_message.Message):
    __slots__ = ("svg",)
    SVG_FIELD_NUMBER: _ClassVar[int]
    svg: str
    def __init__(self, svg: _Optional[str] = ...) -> None: ...

class Query(_message.Message):
    __slots__ = ("meta", "content", "plan", "issue", "transient_issue", "statistics", "result_set_meta", "ast", "timeline")
    META_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    PLAN_FIELD_NUMBER: _ClassVar[int]
    ISSUE_FIELD_NUMBER: _ClassVar[int]
    TRANSIENT_ISSUE_FIELD_NUMBER: _ClassVar[int]
    STATISTICS_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_META_FIELD_NUMBER: _ClassVar[int]
    AST_FIELD_NUMBER: _ClassVar[int]
    TIMELINE_FIELD_NUMBER: _ClassVar[int]
    meta: QueryMeta
    content: QueryContent
    plan: QueryPlan
    issue: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    transient_issue: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    statistics: QueryStatistics
    result_set_meta: _containers.RepeatedCompositeFieldContainer[ResultSetMeta]
    ast: QueryAst
    timeline: QueryTimeline
    def __init__(self, meta: _Optional[_Union[QueryMeta, _Mapping]] = ..., content: _Optional[_Union[QueryContent, _Mapping]] = ..., plan: _Optional[_Union[QueryPlan, _Mapping]] = ..., issue: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., transient_issue: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., statistics: _Optional[_Union[QueryStatistics, _Mapping]] = ..., result_set_meta: _Optional[_Iterable[_Union[ResultSetMeta, _Mapping]]] = ..., ast: _Optional[_Union[QueryAst, _Mapping]] = ..., timeline: _Optional[_Union[QueryTimeline, _Mapping]] = ...) -> None: ...

class QueryStatistics(_message.Message):
    __slots__ = ("json",)
    JSON_FIELD_NUMBER: _ClassVar[int]
    json: str
    def __init__(self, json: _Optional[str] = ...) -> None: ...

class CreateQueryRequest(_message.Message):
    __slots__ = ("operation_params", "content", "execute_mode", "disposition", "idempotency_key")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    EXECUTE_MODE_FIELD_NUMBER: _ClassVar[int]
    DISPOSITION_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    content: QueryContent
    execute_mode: ExecuteMode
    disposition: StreamingDisposition
    idempotency_key: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., content: _Optional[_Union[QueryContent, _Mapping]] = ..., execute_mode: _Optional[_Union[ExecuteMode, str]] = ..., disposition: _Optional[_Union[StreamingDisposition, _Mapping]] = ..., idempotency_key: _Optional[str] = ...) -> None: ...

class CreateQueryResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class CreateQueryResult(_message.Message):
    __slots__ = ("query_id",)
    QUERY_ID_FIELD_NUMBER: _ClassVar[int]
    query_id: str
    def __init__(self, query_id: _Optional[str] = ...) -> None: ...

class ListQueriesRequest(_message.Message):
    __slots__ = ("operation_params", "page_token", "limit", "filter")
    class Filter(_message.Message):
        __slots__ = ("query_type", "status", "mode", "name", "created_by_me", "visibility", "automatic")
        QUERY_TYPE_FIELD_NUMBER: _ClassVar[int]
        STATUS_FIELD_NUMBER: _ClassVar[int]
        MODE_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        CREATED_BY_ME_FIELD_NUMBER: _ClassVar[int]
        VISIBILITY_FIELD_NUMBER: _ClassVar[int]
        AUTOMATIC_FIELD_NUMBER: _ClassVar[int]
        query_type: QueryContent.QueryType
        status: _containers.RepeatedScalarFieldContainer[QueryMeta.ComputeStatus]
        mode: _containers.RepeatedScalarFieldContainer[ExecuteMode]
        name: str
        created_by_me: bool
        visibility: Acl.Visibility
        automatic: AutomaticType
        def __init__(self, query_type: _Optional[_Union[QueryContent.QueryType, str]] = ..., status: _Optional[_Iterable[_Union[QueryMeta.ComputeStatus, str]]] = ..., mode: _Optional[_Iterable[_Union[ExecuteMode, str]]] = ..., name: _Optional[str] = ..., created_by_me: bool = ..., visibility: _Optional[_Union[Acl.Visibility, str]] = ..., automatic: _Optional[_Union[AutomaticType, str]] = ...) -> None: ...
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    page_token: str
    limit: int
    filter: ListQueriesRequest.Filter
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., page_token: _Optional[str] = ..., limit: _Optional[int] = ..., filter: _Optional[_Union[ListQueriesRequest.Filter, _Mapping]] = ...) -> None: ...

class ListQueriesResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListQueriesResult(_message.Message):
    __slots__ = ("query", "next_page_token")
    QUERY_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    query: _containers.RepeatedCompositeFieldContainer[BriefQuery]
    next_page_token: str
    def __init__(self, query: _Optional[_Iterable[_Union[BriefQuery, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class DescribeQueryRequest(_message.Message):
    __slots__ = ("operation_params", "query_id")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    QUERY_ID_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    query_id: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., query_id: _Optional[str] = ...) -> None: ...

class DescribeQueryResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeQueryResult(_message.Message):
    __slots__ = ("query",)
    QUERY_FIELD_NUMBER: _ClassVar[int]
    query: Query
    def __init__(self, query: _Optional[_Union[Query, _Mapping]] = ...) -> None: ...

class GetQueryStatusRequest(_message.Message):
    __slots__ = ("operation_params", "query_id")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    QUERY_ID_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    query_id: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., query_id: _Optional[str] = ...) -> None: ...

class GetQueryStatusResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class GetQueryStatusResult(_message.Message):
    __slots__ = ("status", "meta_revision")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    META_REVISION_FIELD_NUMBER: _ClassVar[int]
    status: QueryMeta.ComputeStatus
    meta_revision: int
    def __init__(self, status: _Optional[_Union[QueryMeta.ComputeStatus, str]] = ..., meta_revision: _Optional[int] = ...) -> None: ...

class DeleteQueryRequest(_message.Message):
    __slots__ = ("operation_params", "query_id", "previous_revision", "idempotency_key")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    QUERY_ID_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_REVISION_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    query_id: str
    previous_revision: int
    idempotency_key: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., query_id: _Optional[str] = ..., previous_revision: _Optional[int] = ..., idempotency_key: _Optional[str] = ...) -> None: ...

class DeleteQueryResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DeleteQueryResult(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ModifyQueryRequest(_message.Message):
    __slots__ = ("operation_params", "query_id", "content", "execute_mode", "disposition", "state_load_mode", "previous_revision", "idempotency_key")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    QUERY_ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    EXECUTE_MODE_FIELD_NUMBER: _ClassVar[int]
    DISPOSITION_FIELD_NUMBER: _ClassVar[int]
    STATE_LOAD_MODE_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_REVISION_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    query_id: str
    content: QueryContent
    execute_mode: ExecuteMode
    disposition: StreamingDisposition
    state_load_mode: StateLoadMode
    previous_revision: int
    idempotency_key: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., query_id: _Optional[str] = ..., content: _Optional[_Union[QueryContent, _Mapping]] = ..., execute_mode: _Optional[_Union[ExecuteMode, str]] = ..., disposition: _Optional[_Union[StreamingDisposition, _Mapping]] = ..., state_load_mode: _Optional[_Union[StateLoadMode, str]] = ..., previous_revision: _Optional[int] = ..., idempotency_key: _Optional[str] = ...) -> None: ...

class ModifyQueryResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ModifyQueryResult(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ControlQueryRequest(_message.Message):
    __slots__ = ("operation_params", "query_id", "action", "previous_revision", "idempotency_key")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    QUERY_ID_FIELD_NUMBER: _ClassVar[int]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_REVISION_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    query_id: str
    action: QueryAction
    previous_revision: int
    idempotency_key: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., query_id: _Optional[str] = ..., action: _Optional[_Union[QueryAction, str]] = ..., previous_revision: _Optional[int] = ..., idempotency_key: _Optional[str] = ...) -> None: ...

class ControlQueryResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ControlQueryResult(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class BriefJob(_message.Message):
    __slots__ = ("meta", "query_meta", "query_name", "visibility", "automatic", "expire_at")
    META_FIELD_NUMBER: _ClassVar[int]
    QUERY_META_FIELD_NUMBER: _ClassVar[int]
    QUERY_NAME_FIELD_NUMBER: _ClassVar[int]
    VISIBILITY_FIELD_NUMBER: _ClassVar[int]
    AUTOMATIC_FIELD_NUMBER: _ClassVar[int]
    EXPIRE_AT_FIELD_NUMBER: _ClassVar[int]
    meta: CommonMeta
    query_meta: QueryMeta
    query_name: str
    visibility: Acl.Visibility
    automatic: bool
    expire_at: _timestamp_pb2.Timestamp
    def __init__(self, meta: _Optional[_Union[CommonMeta, _Mapping]] = ..., query_meta: _Optional[_Union[QueryMeta, _Mapping]] = ..., query_name: _Optional[str] = ..., visibility: _Optional[_Union[Acl.Visibility, str]] = ..., automatic: bool = ..., expire_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class Job(_message.Message):
    __slots__ = ("meta", "text", "query_meta", "plan", "issue", "statistics", "result_set_meta", "ast", "query_name", "acl", "automatic", "expire_at", "syntax", "parameters")
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _ydb_value_pb2.TypedValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ...) -> None: ...
    META_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    QUERY_META_FIELD_NUMBER: _ClassVar[int]
    PLAN_FIELD_NUMBER: _ClassVar[int]
    ISSUE_FIELD_NUMBER: _ClassVar[int]
    STATISTICS_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_META_FIELD_NUMBER: _ClassVar[int]
    AST_FIELD_NUMBER: _ClassVar[int]
    QUERY_NAME_FIELD_NUMBER: _ClassVar[int]
    ACL_FIELD_NUMBER: _ClassVar[int]
    AUTOMATIC_FIELD_NUMBER: _ClassVar[int]
    EXPIRE_AT_FIELD_NUMBER: _ClassVar[int]
    SYNTAX_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    meta: CommonMeta
    text: str
    query_meta: QueryMeta
    plan: QueryPlan
    issue: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    statistics: QueryStatistics
    result_set_meta: _containers.RepeatedCompositeFieldContainer[ResultSetMeta]
    ast: QueryAst
    query_name: str
    acl: Acl
    automatic: bool
    expire_at: _timestamp_pb2.Timestamp
    syntax: QueryContent.QuerySyntax
    parameters: _containers.MessageMap[str, _ydb_value_pb2.TypedValue]
    def __init__(self, meta: _Optional[_Union[CommonMeta, _Mapping]] = ..., text: _Optional[str] = ..., query_meta: _Optional[_Union[QueryMeta, _Mapping]] = ..., plan: _Optional[_Union[QueryPlan, _Mapping]] = ..., issue: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., statistics: _Optional[_Union[QueryStatistics, _Mapping]] = ..., result_set_meta: _Optional[_Iterable[_Union[ResultSetMeta, _Mapping]]] = ..., ast: _Optional[_Union[QueryAst, _Mapping]] = ..., query_name: _Optional[str] = ..., acl: _Optional[_Union[Acl, _Mapping]] = ..., automatic: bool = ..., expire_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., syntax: _Optional[_Union[QueryContent.QuerySyntax, str]] = ..., parameters: _Optional[_Mapping[str, _ydb_value_pb2.TypedValue]] = ...) -> None: ...

class ListJobsRequest(_message.Message):
    __slots__ = ("operation_params", "page_token", "limit", "query_id", "filter")
    class Filter(_message.Message):
        __slots__ = ("query_id", "created_by_me")
        QUERY_ID_FIELD_NUMBER: _ClassVar[int]
        CREATED_BY_ME_FIELD_NUMBER: _ClassVar[int]
        query_id: str
        created_by_me: bool
        def __init__(self, query_id: _Optional[str] = ..., created_by_me: bool = ...) -> None: ...
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    QUERY_ID_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    page_token: str
    limit: int
    query_id: str
    filter: ListJobsRequest.Filter
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., page_token: _Optional[str] = ..., limit: _Optional[int] = ..., query_id: _Optional[str] = ..., filter: _Optional[_Union[ListJobsRequest.Filter, _Mapping]] = ...) -> None: ...

class ListJobsResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListJobsResult(_message.Message):
    __slots__ = ("job", "next_page_token")
    JOB_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    job: _containers.RepeatedCompositeFieldContainer[BriefJob]
    next_page_token: str
    def __init__(self, job: _Optional[_Iterable[_Union[BriefJob, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class DescribeJobRequest(_message.Message):
    __slots__ = ("operation_params", "job_id")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    job_id: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., job_id: _Optional[str] = ...) -> None: ...

class DescribeJobResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeJobResult(_message.Message):
    __slots__ = ("job",)
    JOB_FIELD_NUMBER: _ClassVar[int]
    job: Job
    def __init__(self, job: _Optional[_Union[Job, _Mapping]] = ...) -> None: ...

class CurrentIAMTokenAuth(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class NoneAuth(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ServiceAccountAuth(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class TokenAuth(_message.Message):
    __slots__ = ("token",)
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    token: str
    def __init__(self, token: _Optional[str] = ...) -> None: ...

class IamAuth(_message.Message):
    __slots__ = ("current_iam", "service_account", "none", "token")
    CURRENT_IAM_FIELD_NUMBER: _ClassVar[int]
    SERVICE_ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    NONE_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    current_iam: CurrentIAMTokenAuth
    service_account: ServiceAccountAuth
    none: NoneAuth
    token: TokenAuth
    def __init__(self, current_iam: _Optional[_Union[CurrentIAMTokenAuth, _Mapping]] = ..., service_account: _Optional[_Union[ServiceAccountAuth, _Mapping]] = ..., none: _Optional[_Union[NoneAuth, _Mapping]] = ..., token: _Optional[_Union[TokenAuth, _Mapping]] = ...) -> None: ...

class DataStreams(_message.Message):
    __slots__ = ("database_id", "auth", "endpoint", "database", "secure", "shared_reading")
    DATABASE_ID_FIELD_NUMBER: _ClassVar[int]
    AUTH_FIELD_NUMBER: _ClassVar[int]
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    DATABASE_FIELD_NUMBER: _ClassVar[int]
    SECURE_FIELD_NUMBER: _ClassVar[int]
    SHARED_READING_FIELD_NUMBER: _ClassVar[int]
    database_id: str
    auth: IamAuth
    endpoint: str
    database: str
    secure: bool
    shared_reading: bool
    def __init__(self, database_id: _Optional[str] = ..., auth: _Optional[_Union[IamAuth, _Mapping]] = ..., endpoint: _Optional[str] = ..., database: _Optional[str] = ..., secure: bool = ..., shared_reading: bool = ...) -> None: ...

class Monitoring(_message.Message):
    __slots__ = ("project", "cluster", "auth")
    PROJECT_FIELD_NUMBER: _ClassVar[int]
    CLUSTER_FIELD_NUMBER: _ClassVar[int]
    AUTH_FIELD_NUMBER: _ClassVar[int]
    project: str
    cluster: str
    auth: IamAuth
    def __init__(self, project: _Optional[str] = ..., cluster: _Optional[str] = ..., auth: _Optional[_Union[IamAuth, _Mapping]] = ...) -> None: ...

class YdbDatabase(_message.Message):
    __slots__ = ("database_id", "auth", "endpoint", "database", "secure")
    DATABASE_ID_FIELD_NUMBER: _ClassVar[int]
    AUTH_FIELD_NUMBER: _ClassVar[int]
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    DATABASE_FIELD_NUMBER: _ClassVar[int]
    SECURE_FIELD_NUMBER: _ClassVar[int]
    database_id: str
    auth: IamAuth
    endpoint: str
    database: str
    secure: bool
    def __init__(self, database_id: _Optional[str] = ..., auth: _Optional[_Union[IamAuth, _Mapping]] = ..., endpoint: _Optional[str] = ..., database: _Optional[str] = ..., secure: bool = ...) -> None: ...

class ClickHouseCluster(_message.Message):
    __slots__ = ("database_id", "database_name", "login", "password", "auth", "host", "port", "secure")
    DATABASE_ID_FIELD_NUMBER: _ClassVar[int]
    DATABASE_NAME_FIELD_NUMBER: _ClassVar[int]
    LOGIN_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    AUTH_FIELD_NUMBER: _ClassVar[int]
    HOST_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    SECURE_FIELD_NUMBER: _ClassVar[int]
    database_id: str
    database_name: str
    login: str
    password: str
    auth: IamAuth
    host: str
    port: int
    secure: bool
    def __init__(self, database_id: _Optional[str] = ..., database_name: _Optional[str] = ..., login: _Optional[str] = ..., password: _Optional[str] = ..., auth: _Optional[_Union[IamAuth, _Mapping]] = ..., host: _Optional[str] = ..., port: _Optional[int] = ..., secure: bool = ...) -> None: ...

class ObjectStorageConnection(_message.Message):
    __slots__ = ("bucket", "auth")
    BUCKET_FIELD_NUMBER: _ClassVar[int]
    AUTH_FIELD_NUMBER: _ClassVar[int]
    bucket: str
    auth: IamAuth
    def __init__(self, bucket: _Optional[str] = ..., auth: _Optional[_Union[IamAuth, _Mapping]] = ...) -> None: ...

class PostgreSQLCluster(_message.Message):
    __slots__ = ("database_id", "database_name", "login", "password", "schema", "auth", "host", "port", "secure")
    DATABASE_ID_FIELD_NUMBER: _ClassVar[int]
    DATABASE_NAME_FIELD_NUMBER: _ClassVar[int]
    LOGIN_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    AUTH_FIELD_NUMBER: _ClassVar[int]
    HOST_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    SECURE_FIELD_NUMBER: _ClassVar[int]
    database_id: str
    database_name: str
    login: str
    password: str
    schema: str
    auth: IamAuth
    host: str
    port: int
    secure: bool
    def __init__(self, database_id: _Optional[str] = ..., database_name: _Optional[str] = ..., login: _Optional[str] = ..., password: _Optional[str] = ..., schema: _Optional[str] = ..., auth: _Optional[_Union[IamAuth, _Mapping]] = ..., host: _Optional[str] = ..., port: _Optional[int] = ..., secure: bool = ...) -> None: ...

class GreenplumCluster(_message.Message):
    __slots__ = ("database_id", "database_name", "login", "password", "schema", "auth")
    DATABASE_ID_FIELD_NUMBER: _ClassVar[int]
    DATABASE_NAME_FIELD_NUMBER: _ClassVar[int]
    LOGIN_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    AUTH_FIELD_NUMBER: _ClassVar[int]
    database_id: str
    database_name: str
    login: str
    password: str
    schema: str
    auth: IamAuth
    def __init__(self, database_id: _Optional[str] = ..., database_name: _Optional[str] = ..., login: _Optional[str] = ..., password: _Optional[str] = ..., schema: _Optional[str] = ..., auth: _Optional[_Union[IamAuth, _Mapping]] = ...) -> None: ...

class MySQLCluster(_message.Message):
    __slots__ = ("database_id", "database_name", "login", "password", "auth")
    DATABASE_ID_FIELD_NUMBER: _ClassVar[int]
    DATABASE_NAME_FIELD_NUMBER: _ClassVar[int]
    LOGIN_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    AUTH_FIELD_NUMBER: _ClassVar[int]
    database_id: str
    database_name: str
    login: str
    password: str
    auth: IamAuth
    def __init__(self, database_id: _Optional[str] = ..., database_name: _Optional[str] = ..., login: _Optional[str] = ..., password: _Optional[str] = ..., auth: _Optional[_Union[IamAuth, _Mapping]] = ...) -> None: ...

class Logging(_message.Message):
    __slots__ = ("folder_id", "auth")
    FOLDER_ID_FIELD_NUMBER: _ClassVar[int]
    AUTH_FIELD_NUMBER: _ClassVar[int]
    folder_id: str
    auth: IamAuth
    def __init__(self, folder_id: _Optional[str] = ..., auth: _Optional[_Union[IamAuth, _Mapping]] = ...) -> None: ...

class IcebergWarehouse(_message.Message):
    __slots__ = ("s3",)
    class S3(_message.Message):
        __slots__ = ("bucket", "path")
        BUCKET_FIELD_NUMBER: _ClassVar[int]
        PATH_FIELD_NUMBER: _ClassVar[int]
        bucket: str
        path: str
        def __init__(self, bucket: _Optional[str] = ..., path: _Optional[str] = ...) -> None: ...
    S3_FIELD_NUMBER: _ClassVar[int]
    s3: IcebergWarehouse.S3
    def __init__(self, s3: _Optional[_Union[IcebergWarehouse.S3, _Mapping]] = ...) -> None: ...

class IcebergCatalog(_message.Message):
    __slots__ = ("hadoop", "hive_metastore")
    class Hadoop(_message.Message):
        __slots__ = ("directory",)
        DIRECTORY_FIELD_NUMBER: _ClassVar[int]
        directory: str
        def __init__(self, directory: _Optional[str] = ...) -> None: ...
    class HiveMetastore(_message.Message):
        __slots__ = ("uri", "database_name")
        URI_FIELD_NUMBER: _ClassVar[int]
        DATABASE_NAME_FIELD_NUMBER: _ClassVar[int]
        uri: str
        database_name: str
        def __init__(self, uri: _Optional[str] = ..., database_name: _Optional[str] = ...) -> None: ...
    HADOOP_FIELD_NUMBER: _ClassVar[int]
    HIVE_METASTORE_FIELD_NUMBER: _ClassVar[int]
    hadoop: IcebergCatalog.Hadoop
    hive_metastore: IcebergCatalog.HiveMetastore
    def __init__(self, hadoop: _Optional[_Union[IcebergCatalog.Hadoop, _Mapping]] = ..., hive_metastore: _Optional[_Union[IcebergCatalog.HiveMetastore, _Mapping]] = ...) -> None: ...

class Iceberg(_message.Message):
    __slots__ = ("warehouse_auth", "warehouse", "catalog")
    WAREHOUSE_AUTH_FIELD_NUMBER: _ClassVar[int]
    WAREHOUSE_FIELD_NUMBER: _ClassVar[int]
    CATALOG_FIELD_NUMBER: _ClassVar[int]
    warehouse_auth: IamAuth
    warehouse: IcebergWarehouse
    catalog: IcebergCatalog
    def __init__(self, warehouse_auth: _Optional[_Union[IamAuth, _Mapping]] = ..., warehouse: _Optional[_Union[IcebergWarehouse, _Mapping]] = ..., catalog: _Optional[_Union[IcebergCatalog, _Mapping]] = ...) -> None: ...

class ConnectionSetting(_message.Message):
    __slots__ = ("ydb_database", "clickhouse_cluster", "data_streams", "object_storage", "monitoring", "postgresql_cluster", "greenplum_cluster", "mysql_cluster", "logging", "iceberg")
    class ConnectionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        CONNECTION_TYPE_UNSPECIFIED: _ClassVar[ConnectionSetting.ConnectionType]
        YDB_DATABASE: _ClassVar[ConnectionSetting.ConnectionType]
        CLICKHOUSE_CLUSTER: _ClassVar[ConnectionSetting.ConnectionType]
        DATA_STREAMS: _ClassVar[ConnectionSetting.ConnectionType]
        OBJECT_STORAGE: _ClassVar[ConnectionSetting.ConnectionType]
        MONITORING: _ClassVar[ConnectionSetting.ConnectionType]
        POSTGRESQL_CLUSTER: _ClassVar[ConnectionSetting.ConnectionType]
        GREENPLUM_CLUSTER: _ClassVar[ConnectionSetting.ConnectionType]
        MYSQL_CLUSTER: _ClassVar[ConnectionSetting.ConnectionType]
        LOGGING: _ClassVar[ConnectionSetting.ConnectionType]
        ICEBERG: _ClassVar[ConnectionSetting.ConnectionType]
    CONNECTION_TYPE_UNSPECIFIED: ConnectionSetting.ConnectionType
    YDB_DATABASE: ConnectionSetting.ConnectionType
    CLICKHOUSE_CLUSTER: ConnectionSetting.ConnectionType
    DATA_STREAMS: ConnectionSetting.ConnectionType
    OBJECT_STORAGE: ConnectionSetting.ConnectionType
    MONITORING: ConnectionSetting.ConnectionType
    POSTGRESQL_CLUSTER: ConnectionSetting.ConnectionType
    GREENPLUM_CLUSTER: ConnectionSetting.ConnectionType
    MYSQL_CLUSTER: ConnectionSetting.ConnectionType
    LOGGING: ConnectionSetting.ConnectionType
    ICEBERG: ConnectionSetting.ConnectionType
    YDB_DATABASE_FIELD_NUMBER: _ClassVar[int]
    CLICKHOUSE_CLUSTER_FIELD_NUMBER: _ClassVar[int]
    DATA_STREAMS_FIELD_NUMBER: _ClassVar[int]
    OBJECT_STORAGE_FIELD_NUMBER: _ClassVar[int]
    MONITORING_FIELD_NUMBER: _ClassVar[int]
    POSTGRESQL_CLUSTER_FIELD_NUMBER: _ClassVar[int]
    GREENPLUM_CLUSTER_FIELD_NUMBER: _ClassVar[int]
    MYSQL_CLUSTER_FIELD_NUMBER: _ClassVar[int]
    LOGGING_FIELD_NUMBER: _ClassVar[int]
    ICEBERG_FIELD_NUMBER: _ClassVar[int]
    ydb_database: YdbDatabase
    clickhouse_cluster: ClickHouseCluster
    data_streams: DataStreams
    object_storage: ObjectStorageConnection
    monitoring: Monitoring
    postgresql_cluster: PostgreSQLCluster
    greenplum_cluster: GreenplumCluster
    mysql_cluster: MySQLCluster
    logging: Logging
    iceberg: Iceberg
    def __init__(self, ydb_database: _Optional[_Union[YdbDatabase, _Mapping]] = ..., clickhouse_cluster: _Optional[_Union[ClickHouseCluster, _Mapping]] = ..., data_streams: _Optional[_Union[DataStreams, _Mapping]] = ..., object_storage: _Optional[_Union[ObjectStorageConnection, _Mapping]] = ..., monitoring: _Optional[_Union[Monitoring, _Mapping]] = ..., postgresql_cluster: _Optional[_Union[PostgreSQLCluster, _Mapping]] = ..., greenplum_cluster: _Optional[_Union[GreenplumCluster, _Mapping]] = ..., mysql_cluster: _Optional[_Union[MySQLCluster, _Mapping]] = ..., logging: _Optional[_Union[Logging, _Mapping]] = ..., iceberg: _Optional[_Union[Iceberg, _Mapping]] = ...) -> None: ...

class ConnectionContent(_message.Message):
    __slots__ = ("name", "setting", "acl", "description")
    NAME_FIELD_NUMBER: _ClassVar[int]
    SETTING_FIELD_NUMBER: _ClassVar[int]
    ACL_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    name: str
    setting: ConnectionSetting
    acl: Acl
    description: str
    def __init__(self, name: _Optional[str] = ..., setting: _Optional[_Union[ConnectionSetting, _Mapping]] = ..., acl: _Optional[_Union[Acl, _Mapping]] = ..., description: _Optional[str] = ...) -> None: ...

class Connection(_message.Message):
    __slots__ = ("content", "meta")
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    META_FIELD_NUMBER: _ClassVar[int]
    content: ConnectionContent
    meta: CommonMeta
    def __init__(self, content: _Optional[_Union[ConnectionContent, _Mapping]] = ..., meta: _Optional[_Union[CommonMeta, _Mapping]] = ...) -> None: ...

class CreateConnectionRequest(_message.Message):
    __slots__ = ("operation_params", "content", "idempotency_key")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    content: ConnectionContent
    idempotency_key: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., content: _Optional[_Union[ConnectionContent, _Mapping]] = ..., idempotency_key: _Optional[str] = ...) -> None: ...

class CreateConnectionResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class CreateConnectionResult(_message.Message):
    __slots__ = ("connection_id",)
    CONNECTION_ID_FIELD_NUMBER: _ClassVar[int]
    connection_id: str
    def __init__(self, connection_id: _Optional[str] = ...) -> None: ...

class ListConnectionsRequest(_message.Message):
    __slots__ = ("operation_params", "page_token", "limit", "filter")
    class Filter(_message.Message):
        __slots__ = ("name", "created_by_me", "connection_type", "visibility")
        NAME_FIELD_NUMBER: _ClassVar[int]
        CREATED_BY_ME_FIELD_NUMBER: _ClassVar[int]
        CONNECTION_TYPE_FIELD_NUMBER: _ClassVar[int]
        VISIBILITY_FIELD_NUMBER: _ClassVar[int]
        name: str
        created_by_me: bool
        connection_type: ConnectionSetting.ConnectionType
        visibility: Acl.Visibility
        def __init__(self, name: _Optional[str] = ..., created_by_me: bool = ..., connection_type: _Optional[_Union[ConnectionSetting.ConnectionType, str]] = ..., visibility: _Optional[_Union[Acl.Visibility, str]] = ...) -> None: ...
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    page_token: str
    limit: int
    filter: ListConnectionsRequest.Filter
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., page_token: _Optional[str] = ..., limit: _Optional[int] = ..., filter: _Optional[_Union[ListConnectionsRequest.Filter, _Mapping]] = ...) -> None: ...

class ListConnectionsResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListConnectionsResult(_message.Message):
    __slots__ = ("connection", "next_page_token")
    CONNECTION_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    connection: _containers.RepeatedCompositeFieldContainer[Connection]
    next_page_token: str
    def __init__(self, connection: _Optional[_Iterable[_Union[Connection, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class DescribeConnectionRequest(_message.Message):
    __slots__ = ("operation_params", "connection_id")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_ID_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    connection_id: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., connection_id: _Optional[str] = ...) -> None: ...

class DescribeConnectionResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeConnectionResult(_message.Message):
    __slots__ = ("connection",)
    CONNECTION_FIELD_NUMBER: _ClassVar[int]
    connection: Connection
    def __init__(self, connection: _Optional[_Union[Connection, _Mapping]] = ...) -> None: ...

class ModifyConnectionRequest(_message.Message):
    __slots__ = ("operation_params", "connection_id", "content", "previous_revision", "idempotency_key")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_REVISION_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    connection_id: str
    content: ConnectionContent
    previous_revision: int
    idempotency_key: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., connection_id: _Optional[str] = ..., content: _Optional[_Union[ConnectionContent, _Mapping]] = ..., previous_revision: _Optional[int] = ..., idempotency_key: _Optional[str] = ...) -> None: ...

class ModifyConnectionResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ModifyConnectionResult(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DeleteConnectionRequest(_message.Message):
    __slots__ = ("operation_params", "connection_id", "previous_revision", "idempotency_key")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_ID_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_REVISION_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    connection_id: str
    previous_revision: int
    idempotency_key: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., connection_id: _Optional[str] = ..., previous_revision: _Optional[int] = ..., idempotency_key: _Optional[str] = ...) -> None: ...

class DeleteConnectionResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DeleteConnectionResult(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class TestConnectionRequest(_message.Message):
    __slots__ = ("operation_params", "setting")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SETTING_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    setting: ConnectionSetting
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., setting: _Optional[_Union[ConnectionSetting, _Mapping]] = ...) -> None: ...

class TestConnectionResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class TestConnectionResult(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetResultDataRequest(_message.Message):
    __slots__ = ("operation_params", "query_id", "result_set_index", "offset", "limit")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    QUERY_ID_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_INDEX_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    query_id: str
    result_set_index: int
    offset: int
    limit: int
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., query_id: _Optional[str] = ..., result_set_index: _Optional[int] = ..., offset: _Optional[int] = ..., limit: _Optional[int] = ...) -> None: ...

class GetResultDataResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class GetResultDataResult(_message.Message):
    __slots__ = ("result_set",)
    RESULT_SET_FIELD_NUMBER: _ClassVar[int]
    result_set: _ydb_value_pb2.ResultSet
    def __init__(self, result_set: _Optional[_Union[_ydb_value_pb2.ResultSet, _Mapping]] = ...) -> None: ...

class Schema(_message.Message):
    __slots__ = ("column",)
    COLUMN_FIELD_NUMBER: _ClassVar[int]
    column: _containers.RepeatedCompositeFieldContainer[_ydb_value_pb2.Column]
    def __init__(self, column: _Optional[_Iterable[_Union[_ydb_value_pb2.Column, _Mapping]]] = ...) -> None: ...

class DataStreamsBinding(_message.Message):
    __slots__ = ("stream_name", "format", "compression", "schema", "format_setting")
    class FormatSettingEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    STREAM_NAME_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    COMPRESSION_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    FORMAT_SETTING_FIELD_NUMBER: _ClassVar[int]
    stream_name: str
    format: str
    compression: str
    schema: Schema
    format_setting: _containers.ScalarMap[str, str]
    def __init__(self, stream_name: _Optional[str] = ..., format: _Optional[str] = ..., compression: _Optional[str] = ..., schema: _Optional[_Union[Schema, _Mapping]] = ..., format_setting: _Optional[_Mapping[str, str]] = ...) -> None: ...

class ObjectStorageBinding(_message.Message):
    __slots__ = ("subset",)
    class Subset(_message.Message):
        __slots__ = ("path_pattern", "format", "format_setting", "compression", "schema", "projection", "partitioned_by")
        class FormatSettingEntry(_message.Message):
            __slots__ = ("key", "value")
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        class ProjectionEntry(_message.Message):
            __slots__ = ("key", "value")
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        PATH_PATTERN_FIELD_NUMBER: _ClassVar[int]
        FORMAT_FIELD_NUMBER: _ClassVar[int]
        FORMAT_SETTING_FIELD_NUMBER: _ClassVar[int]
        COMPRESSION_FIELD_NUMBER: _ClassVar[int]
        SCHEMA_FIELD_NUMBER: _ClassVar[int]
        PROJECTION_FIELD_NUMBER: _ClassVar[int]
        PARTITIONED_BY_FIELD_NUMBER: _ClassVar[int]
        path_pattern: str
        format: str
        format_setting: _containers.ScalarMap[str, str]
        compression: str
        schema: Schema
        projection: _containers.ScalarMap[str, str]
        partitioned_by: _containers.RepeatedScalarFieldContainer[str]
        def __init__(self, path_pattern: _Optional[str] = ..., format: _Optional[str] = ..., format_setting: _Optional[_Mapping[str, str]] = ..., compression: _Optional[str] = ..., schema: _Optional[_Union[Schema, _Mapping]] = ..., projection: _Optional[_Mapping[str, str]] = ..., partitioned_by: _Optional[_Iterable[str]] = ...) -> None: ...
    SUBSET_FIELD_NUMBER: _ClassVar[int]
    subset: _containers.RepeatedCompositeFieldContainer[ObjectStorageBinding.Subset]
    def __init__(self, subset: _Optional[_Iterable[_Union[ObjectStorageBinding.Subset, _Mapping]]] = ...) -> None: ...

class BindingSetting(_message.Message):
    __slots__ = ("data_streams", "object_storage")
    class BindingType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        BINDING_TYPE_UNSPECIFIED: _ClassVar[BindingSetting.BindingType]
        DATA_STREAMS: _ClassVar[BindingSetting.BindingType]
        OBJECT_STORAGE: _ClassVar[BindingSetting.BindingType]
    BINDING_TYPE_UNSPECIFIED: BindingSetting.BindingType
    DATA_STREAMS: BindingSetting.BindingType
    OBJECT_STORAGE: BindingSetting.BindingType
    DATA_STREAMS_FIELD_NUMBER: _ClassVar[int]
    OBJECT_STORAGE_FIELD_NUMBER: _ClassVar[int]
    data_streams: DataStreamsBinding
    object_storage: ObjectStorageBinding
    def __init__(self, data_streams: _Optional[_Union[DataStreamsBinding, _Mapping]] = ..., object_storage: _Optional[_Union[ObjectStorageBinding, _Mapping]] = ...) -> None: ...

class BriefBinding(_message.Message):
    __slots__ = ("name", "connection_id", "meta", "type", "visibility")
    NAME_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_ID_FIELD_NUMBER: _ClassVar[int]
    META_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    VISIBILITY_FIELD_NUMBER: _ClassVar[int]
    name: str
    connection_id: str
    meta: CommonMeta
    type: BindingSetting.BindingType
    visibility: Acl.Visibility
    def __init__(self, name: _Optional[str] = ..., connection_id: _Optional[str] = ..., meta: _Optional[_Union[CommonMeta, _Mapping]] = ..., type: _Optional[_Union[BindingSetting.BindingType, str]] = ..., visibility: _Optional[_Union[Acl.Visibility, str]] = ...) -> None: ...

class BindingContent(_message.Message):
    __slots__ = ("name", "connection_id", "setting", "acl", "description")
    NAME_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_ID_FIELD_NUMBER: _ClassVar[int]
    SETTING_FIELD_NUMBER: _ClassVar[int]
    ACL_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    name: str
    connection_id: str
    setting: BindingSetting
    acl: Acl
    description: str
    def __init__(self, name: _Optional[str] = ..., connection_id: _Optional[str] = ..., setting: _Optional[_Union[BindingSetting, _Mapping]] = ..., acl: _Optional[_Union[Acl, _Mapping]] = ..., description: _Optional[str] = ...) -> None: ...

class Binding(_message.Message):
    __slots__ = ("content", "meta")
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    META_FIELD_NUMBER: _ClassVar[int]
    content: BindingContent
    meta: CommonMeta
    def __init__(self, content: _Optional[_Union[BindingContent, _Mapping]] = ..., meta: _Optional[_Union[CommonMeta, _Mapping]] = ...) -> None: ...

class CreateBindingRequest(_message.Message):
    __slots__ = ("operation_params", "content", "idempotency_key")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    content: BindingContent
    idempotency_key: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., content: _Optional[_Union[BindingContent, _Mapping]] = ..., idempotency_key: _Optional[str] = ...) -> None: ...

class CreateBindingResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class CreateBindingResult(_message.Message):
    __slots__ = ("binding_id",)
    BINDING_ID_FIELD_NUMBER: _ClassVar[int]
    binding_id: str
    def __init__(self, binding_id: _Optional[str] = ...) -> None: ...

class ListBindingsRequest(_message.Message):
    __slots__ = ("operation_params", "page_token", "limit", "filter")
    class Filter(_message.Message):
        __slots__ = ("connection_id", "name", "created_by_me", "visibility")
        CONNECTION_ID_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        CREATED_BY_ME_FIELD_NUMBER: _ClassVar[int]
        VISIBILITY_FIELD_NUMBER: _ClassVar[int]
        connection_id: str
        name: str
        created_by_me: bool
        visibility: Acl.Visibility
        def __init__(self, connection_id: _Optional[str] = ..., name: _Optional[str] = ..., created_by_me: bool = ..., visibility: _Optional[_Union[Acl.Visibility, str]] = ...) -> None: ...
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    page_token: str
    limit: int
    filter: ListBindingsRequest.Filter
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., page_token: _Optional[str] = ..., limit: _Optional[int] = ..., filter: _Optional[_Union[ListBindingsRequest.Filter, _Mapping]] = ...) -> None: ...

class ListBindingsResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListBindingsResult(_message.Message):
    __slots__ = ("binding", "next_page_token")
    BINDING_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    binding: _containers.RepeatedCompositeFieldContainer[BriefBinding]
    next_page_token: str
    def __init__(self, binding: _Optional[_Iterable[_Union[BriefBinding, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class DescribeBindingRequest(_message.Message):
    __slots__ = ("operation_params", "binding_id")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    BINDING_ID_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    binding_id: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., binding_id: _Optional[str] = ...) -> None: ...

class DescribeBindingResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeBindingResult(_message.Message):
    __slots__ = ("binding",)
    BINDING_FIELD_NUMBER: _ClassVar[int]
    binding: Binding
    def __init__(self, binding: _Optional[_Union[Binding, _Mapping]] = ...) -> None: ...

class ModifyBindingRequest(_message.Message):
    __slots__ = ("operation_params", "binding_id", "content", "previous_revision", "idempotency_key")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    BINDING_ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_REVISION_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    binding_id: str
    content: BindingContent
    previous_revision: int
    idempotency_key: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., binding_id: _Optional[str] = ..., content: _Optional[_Union[BindingContent, _Mapping]] = ..., previous_revision: _Optional[int] = ..., idempotency_key: _Optional[str] = ...) -> None: ...

class ModifyBindingResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ModifyBindingResult(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DeleteBindingRequest(_message.Message):
    __slots__ = ("operation_params", "binding_id", "previous_revision", "idempotency_key")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    BINDING_ID_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_REVISION_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    binding_id: str
    previous_revision: int
    idempotency_key: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., binding_id: _Optional[str] = ..., previous_revision: _Optional[int] = ..., idempotency_key: _Optional[str] = ...) -> None: ...

class DeleteBindingResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DeleteBindingResult(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
