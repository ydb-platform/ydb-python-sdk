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
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

ABORT: QueryAction
ABORT_GRACEFULLY: QueryAction
AUTOMATIC: AutomaticType
AUTOMATIC_TYPE_UNSPECIFIED: AutomaticType
COMPILE: ExecuteMode
DESCRIPTOR: _descriptor.FileDescriptor
EMPTY: StateLoadMode
EXECUTE_MODE_UNSPECIFIED: ExecuteMode
EXPLAIN: ExecuteMode
FROM_LAST_CHECKPOINT: StateLoadMode
NOT_AUTOMATIC: AutomaticType
PARSE: ExecuteMode
PAUSE: QueryAction
PAUSE_GRACEFULLY: QueryAction
QUERY_ACTION_UNSPECIFIED: QueryAction
RESUME: QueryAction
RUN: ExecuteMode
SAVE: ExecuteMode
STATE_LOAD_MODE_UNSPECIFIED: StateLoadMode
VALIDATE: ExecuteMode

class Acl(_message.Message):
    __slots__ = ["visibility"]
    class Visibility(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    PRIVATE: Acl.Visibility
    SCOPE: Acl.Visibility
    VISIBILITY_FIELD_NUMBER: _ClassVar[int]
    VISIBILITY_UNSPECIFIED: Acl.Visibility
    visibility: Acl.Visibility
    def __init__(self, visibility: _Optional[_Union[Acl.Visibility, str]] = ...) -> None: ...

class Binding(_message.Message):
    __slots__ = ["content", "meta"]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    META_FIELD_NUMBER: _ClassVar[int]
    content: BindingContent
    meta: CommonMeta
    def __init__(self, content: _Optional[_Union[BindingContent, _Mapping]] = ..., meta: _Optional[_Union[CommonMeta, _Mapping]] = ...) -> None: ...

class BindingContent(_message.Message):
    __slots__ = ["acl", "connection_id", "description", "name", "setting"]
    ACL_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_ID_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    SETTING_FIELD_NUMBER: _ClassVar[int]
    acl: Acl
    connection_id: str
    description: str
    name: str
    setting: BindingSetting
    def __init__(self, name: _Optional[str] = ..., connection_id: _Optional[str] = ..., setting: _Optional[_Union[BindingSetting, _Mapping]] = ..., acl: _Optional[_Union[Acl, _Mapping]] = ..., description: _Optional[str] = ...) -> None: ...

class BindingSetting(_message.Message):
    __slots__ = ["data_streams", "object_storage"]
    class BindingType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    BINDING_TYPE_UNSPECIFIED: BindingSetting.BindingType
    DATA_STREAMS: BindingSetting.BindingType
    DATA_STREAMS_FIELD_NUMBER: _ClassVar[int]
    OBJECT_STORAGE: BindingSetting.BindingType
    OBJECT_STORAGE_FIELD_NUMBER: _ClassVar[int]
    data_streams: DataStreamsBinding
    object_storage: ObjectStorageBinding
    def __init__(self, data_streams: _Optional[_Union[DataStreamsBinding, _Mapping]] = ..., object_storage: _Optional[_Union[ObjectStorageBinding, _Mapping]] = ...) -> None: ...

class BriefBinding(_message.Message):
    __slots__ = ["connection_id", "meta", "name", "type", "visibility"]
    CONNECTION_ID_FIELD_NUMBER: _ClassVar[int]
    META_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    VISIBILITY_FIELD_NUMBER: _ClassVar[int]
    connection_id: str
    meta: CommonMeta
    name: str
    type: BindingSetting.BindingType
    visibility: Acl.Visibility
    def __init__(self, name: _Optional[str] = ..., connection_id: _Optional[str] = ..., meta: _Optional[_Union[CommonMeta, _Mapping]] = ..., type: _Optional[_Union[BindingSetting.BindingType, str]] = ..., visibility: _Optional[_Union[Acl.Visibility, str]] = ...) -> None: ...

class BriefJob(_message.Message):
    __slots__ = ["automatic", "expire_at", "meta", "query_meta", "query_name", "visibility"]
    AUTOMATIC_FIELD_NUMBER: _ClassVar[int]
    EXPIRE_AT_FIELD_NUMBER: _ClassVar[int]
    META_FIELD_NUMBER: _ClassVar[int]
    QUERY_META_FIELD_NUMBER: _ClassVar[int]
    QUERY_NAME_FIELD_NUMBER: _ClassVar[int]
    VISIBILITY_FIELD_NUMBER: _ClassVar[int]
    automatic: bool
    expire_at: _timestamp_pb2.Timestamp
    meta: CommonMeta
    query_meta: QueryMeta
    query_name: str
    visibility: Acl.Visibility
    def __init__(self, meta: _Optional[_Union[CommonMeta, _Mapping]] = ..., query_meta: _Optional[_Union[QueryMeta, _Mapping]] = ..., query_name: _Optional[str] = ..., visibility: _Optional[_Union[Acl.Visibility, str]] = ..., automatic: bool = ..., expire_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class BriefQuery(_message.Message):
    __slots__ = ["automatic", "meta", "name", "type", "visibility"]
    AUTOMATIC_FIELD_NUMBER: _ClassVar[int]
    META_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    VISIBILITY_FIELD_NUMBER: _ClassVar[int]
    automatic: bool
    meta: QueryMeta
    name: str
    type: QueryContent.QueryType
    visibility: Acl.Visibility
    def __init__(self, type: _Optional[_Union[QueryContent.QueryType, str]] = ..., name: _Optional[str] = ..., meta: _Optional[_Union[QueryMeta, _Mapping]] = ..., visibility: _Optional[_Union[Acl.Visibility, str]] = ..., automatic: bool = ...) -> None: ...

class ClickHouseCluster(_message.Message):
    __slots__ = ["auth", "database_id", "database_name", "host", "login", "password", "port", "secure"]
    AUTH_FIELD_NUMBER: _ClassVar[int]
    DATABASE_ID_FIELD_NUMBER: _ClassVar[int]
    DATABASE_NAME_FIELD_NUMBER: _ClassVar[int]
    HOST_FIELD_NUMBER: _ClassVar[int]
    LOGIN_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    SECURE_FIELD_NUMBER: _ClassVar[int]
    auth: IamAuth
    database_id: str
    database_name: str
    host: str
    login: str
    password: str
    port: int
    secure: bool
    def __init__(self, database_id: _Optional[str] = ..., database_name: _Optional[str] = ..., login: _Optional[str] = ..., password: _Optional[str] = ..., auth: _Optional[_Union[IamAuth, _Mapping]] = ..., host: _Optional[str] = ..., port: _Optional[int] = ..., secure: bool = ...) -> None: ...

class CommonMeta(_message.Message):
    __slots__ = ["created_at", "created_by", "id", "modified_at", "modified_by", "revision"]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    CREATED_BY_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    MODIFIED_AT_FIELD_NUMBER: _ClassVar[int]
    MODIFIED_BY_FIELD_NUMBER: _ClassVar[int]
    REVISION_FIELD_NUMBER: _ClassVar[int]
    created_at: _timestamp_pb2.Timestamp
    created_by: str
    id: str
    modified_at: _timestamp_pb2.Timestamp
    modified_by: str
    revision: int
    def __init__(self, id: _Optional[str] = ..., created_by: _Optional[str] = ..., modified_by: _Optional[str] = ..., created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., modified_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., revision: _Optional[int] = ...) -> None: ...

class Connection(_message.Message):
    __slots__ = ["content", "meta"]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    META_FIELD_NUMBER: _ClassVar[int]
    content: ConnectionContent
    meta: CommonMeta
    def __init__(self, content: _Optional[_Union[ConnectionContent, _Mapping]] = ..., meta: _Optional[_Union[CommonMeta, _Mapping]] = ...) -> None: ...

class ConnectionContent(_message.Message):
    __slots__ = ["acl", "description", "name", "setting"]
    ACL_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    SETTING_FIELD_NUMBER: _ClassVar[int]
    acl: Acl
    description: str
    name: str
    setting: ConnectionSetting
    def __init__(self, name: _Optional[str] = ..., setting: _Optional[_Union[ConnectionSetting, _Mapping]] = ..., acl: _Optional[_Union[Acl, _Mapping]] = ..., description: _Optional[str] = ...) -> None: ...

class ConnectionSetting(_message.Message):
    __slots__ = ["clickhouse_cluster", "data_streams", "monitoring", "object_storage", "postgresql_cluster", "ydb_database"]
    class ConnectionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    CLICKHOUSE_CLUSTER: ConnectionSetting.ConnectionType
    CLICKHOUSE_CLUSTER_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_TYPE_UNSPECIFIED: ConnectionSetting.ConnectionType
    DATA_STREAMS: ConnectionSetting.ConnectionType
    DATA_STREAMS_FIELD_NUMBER: _ClassVar[int]
    MONITORING: ConnectionSetting.ConnectionType
    MONITORING_FIELD_NUMBER: _ClassVar[int]
    OBJECT_STORAGE: ConnectionSetting.ConnectionType
    OBJECT_STORAGE_FIELD_NUMBER: _ClassVar[int]
    POSTGRESQL_CLUSTER: ConnectionSetting.ConnectionType
    POSTGRESQL_CLUSTER_FIELD_NUMBER: _ClassVar[int]
    YDB_DATABASE: ConnectionSetting.ConnectionType
    YDB_DATABASE_FIELD_NUMBER: _ClassVar[int]
    clickhouse_cluster: ClickHouseCluster
    data_streams: DataStreams
    monitoring: Monitoring
    object_storage: ObjectStorageConnection
    postgresql_cluster: PostgreSQLCluster
    ydb_database: YdbDatabase
    def __init__(self, ydb_database: _Optional[_Union[YdbDatabase, _Mapping]] = ..., clickhouse_cluster: _Optional[_Union[ClickHouseCluster, _Mapping]] = ..., data_streams: _Optional[_Union[DataStreams, _Mapping]] = ..., object_storage: _Optional[_Union[ObjectStorageConnection, _Mapping]] = ..., monitoring: _Optional[_Union[Monitoring, _Mapping]] = ..., postgresql_cluster: _Optional[_Union[PostgreSQLCluster, _Mapping]] = ...) -> None: ...

class ControlQueryRequest(_message.Message):
    __slots__ = ["action", "idempotency_key", "operation_params", "previous_revision", "query_id"]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_REVISION_FIELD_NUMBER: _ClassVar[int]
    QUERY_ID_FIELD_NUMBER: _ClassVar[int]
    action: QueryAction
    idempotency_key: str
    operation_params: _ydb_operation_pb2.OperationParams
    previous_revision: int
    query_id: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., query_id: _Optional[str] = ..., action: _Optional[_Union[QueryAction, str]] = ..., previous_revision: _Optional[int] = ..., idempotency_key: _Optional[str] = ...) -> None: ...

class ControlQueryResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ControlQueryResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class CreateBindingRequest(_message.Message):
    __slots__ = ["content", "idempotency_key", "operation_params"]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    content: BindingContent
    idempotency_key: str
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., content: _Optional[_Union[BindingContent, _Mapping]] = ..., idempotency_key: _Optional[str] = ...) -> None: ...

class CreateBindingResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class CreateBindingResult(_message.Message):
    __slots__ = ["binding_id"]
    BINDING_ID_FIELD_NUMBER: _ClassVar[int]
    binding_id: str
    def __init__(self, binding_id: _Optional[str] = ...) -> None: ...

class CreateConnectionRequest(_message.Message):
    __slots__ = ["content", "idempotency_key", "operation_params"]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    content: ConnectionContent
    idempotency_key: str
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., content: _Optional[_Union[ConnectionContent, _Mapping]] = ..., idempotency_key: _Optional[str] = ...) -> None: ...

class CreateConnectionResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class CreateConnectionResult(_message.Message):
    __slots__ = ["connection_id"]
    CONNECTION_ID_FIELD_NUMBER: _ClassVar[int]
    connection_id: str
    def __init__(self, connection_id: _Optional[str] = ...) -> None: ...

class CreateQueryRequest(_message.Message):
    __slots__ = ["content", "disposition", "execute_mode", "idempotency_key", "operation_params"]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    DISPOSITION_FIELD_NUMBER: _ClassVar[int]
    EXECUTE_MODE_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    content: QueryContent
    disposition: StreamingDisposition
    execute_mode: ExecuteMode
    idempotency_key: str
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., content: _Optional[_Union[QueryContent, _Mapping]] = ..., execute_mode: _Optional[_Union[ExecuteMode, str]] = ..., disposition: _Optional[_Union[StreamingDisposition, _Mapping]] = ..., idempotency_key: _Optional[str] = ...) -> None: ...

class CreateQueryResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class CreateQueryResult(_message.Message):
    __slots__ = ["query_id"]
    QUERY_ID_FIELD_NUMBER: _ClassVar[int]
    query_id: str
    def __init__(self, query_id: _Optional[str] = ...) -> None: ...

class CurrentIAMTokenAuth(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class DataStreams(_message.Message):
    __slots__ = ["auth", "database", "database_id", "endpoint", "secure"]
    AUTH_FIELD_NUMBER: _ClassVar[int]
    DATABASE_FIELD_NUMBER: _ClassVar[int]
    DATABASE_ID_FIELD_NUMBER: _ClassVar[int]
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    SECURE_FIELD_NUMBER: _ClassVar[int]
    auth: IamAuth
    database: str
    database_id: str
    endpoint: str
    secure: bool
    def __init__(self, database_id: _Optional[str] = ..., auth: _Optional[_Union[IamAuth, _Mapping]] = ..., endpoint: _Optional[str] = ..., database: _Optional[str] = ..., secure: bool = ...) -> None: ...

class DataStreamsBinding(_message.Message):
    __slots__ = ["compression", "format", "format_setting", "schema", "stream_name"]
    class FormatSettingEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    COMPRESSION_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    FORMAT_SETTING_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    STREAM_NAME_FIELD_NUMBER: _ClassVar[int]
    compression: str
    format: str
    format_setting: _containers.ScalarMap[str, str]
    schema: Schema
    stream_name: str
    def __init__(self, stream_name: _Optional[str] = ..., format: _Optional[str] = ..., compression: _Optional[str] = ..., schema: _Optional[_Union[Schema, _Mapping]] = ..., format_setting: _Optional[_Mapping[str, str]] = ...) -> None: ...

class DeleteBindingRequest(_message.Message):
    __slots__ = ["binding_id", "idempotency_key", "operation_params", "previous_revision"]
    BINDING_ID_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_REVISION_FIELD_NUMBER: _ClassVar[int]
    binding_id: str
    idempotency_key: str
    operation_params: _ydb_operation_pb2.OperationParams
    previous_revision: int
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., binding_id: _Optional[str] = ..., previous_revision: _Optional[int] = ..., idempotency_key: _Optional[str] = ...) -> None: ...

class DeleteBindingResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DeleteBindingResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class DeleteConnectionRequest(_message.Message):
    __slots__ = ["connection_id", "idempotency_key", "operation_params", "previous_revision"]
    CONNECTION_ID_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_REVISION_FIELD_NUMBER: _ClassVar[int]
    connection_id: str
    idempotency_key: str
    operation_params: _ydb_operation_pb2.OperationParams
    previous_revision: int
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., connection_id: _Optional[str] = ..., previous_revision: _Optional[int] = ..., idempotency_key: _Optional[str] = ...) -> None: ...

class DeleteConnectionResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DeleteConnectionResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class DeleteQueryRequest(_message.Message):
    __slots__ = ["idempotency_key", "operation_params", "previous_revision", "query_id"]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_REVISION_FIELD_NUMBER: _ClassVar[int]
    QUERY_ID_FIELD_NUMBER: _ClassVar[int]
    idempotency_key: str
    operation_params: _ydb_operation_pb2.OperationParams
    previous_revision: int
    query_id: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., query_id: _Optional[str] = ..., previous_revision: _Optional[int] = ..., idempotency_key: _Optional[str] = ...) -> None: ...

class DeleteQueryResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DeleteQueryResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class DescribeBindingRequest(_message.Message):
    __slots__ = ["binding_id", "operation_params"]
    BINDING_ID_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    binding_id: str
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., binding_id: _Optional[str] = ...) -> None: ...

class DescribeBindingResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeBindingResult(_message.Message):
    __slots__ = ["binding"]
    BINDING_FIELD_NUMBER: _ClassVar[int]
    binding: Binding
    def __init__(self, binding: _Optional[_Union[Binding, _Mapping]] = ...) -> None: ...

class DescribeConnectionRequest(_message.Message):
    __slots__ = ["connection_id", "operation_params"]
    CONNECTION_ID_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    connection_id: str
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., connection_id: _Optional[str] = ...) -> None: ...

class DescribeConnectionResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeConnectionResult(_message.Message):
    __slots__ = ["connection"]
    CONNECTION_FIELD_NUMBER: _ClassVar[int]
    connection: Connection
    def __init__(self, connection: _Optional[_Union[Connection, _Mapping]] = ...) -> None: ...

class DescribeJobRequest(_message.Message):
    __slots__ = ["job_id", "operation_params"]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., job_id: _Optional[str] = ...) -> None: ...

class DescribeJobResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeJobResult(_message.Message):
    __slots__ = ["job"]
    JOB_FIELD_NUMBER: _ClassVar[int]
    job: Job
    def __init__(self, job: _Optional[_Union[Job, _Mapping]] = ...) -> None: ...

class DescribeQueryRequest(_message.Message):
    __slots__ = ["operation_params", "query_id"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    QUERY_ID_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    query_id: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., query_id: _Optional[str] = ...) -> None: ...

class DescribeQueryResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeQueryResult(_message.Message):
    __slots__ = ["query"]
    QUERY_FIELD_NUMBER: _ClassVar[int]
    query: Query
    def __init__(self, query: _Optional[_Union[Query, _Mapping]] = ...) -> None: ...

class GetQueryStatusRequest(_message.Message):
    __slots__ = ["operation_params", "query_id"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    QUERY_ID_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    query_id: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., query_id: _Optional[str] = ...) -> None: ...

class GetQueryStatusResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class GetQueryStatusResult(_message.Message):
    __slots__ = ["meta_revision", "status"]
    META_REVISION_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    meta_revision: int
    status: QueryMeta.ComputeStatus
    def __init__(self, status: _Optional[_Union[QueryMeta.ComputeStatus, str]] = ..., meta_revision: _Optional[int] = ...) -> None: ...

class GetResultDataRequest(_message.Message):
    __slots__ = ["limit", "offset", "operation_params", "query_id", "result_set_index"]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    QUERY_ID_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_INDEX_FIELD_NUMBER: _ClassVar[int]
    limit: int
    offset: int
    operation_params: _ydb_operation_pb2.OperationParams
    query_id: str
    result_set_index: int
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., query_id: _Optional[str] = ..., result_set_index: _Optional[int] = ..., offset: _Optional[int] = ..., limit: _Optional[int] = ...) -> None: ...

class GetResultDataResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class GetResultDataResult(_message.Message):
    __slots__ = ["result_set"]
    RESULT_SET_FIELD_NUMBER: _ClassVar[int]
    result_set: _ydb_value_pb2.ResultSet
    def __init__(self, result_set: _Optional[_Union[_ydb_value_pb2.ResultSet, _Mapping]] = ...) -> None: ...

class IamAuth(_message.Message):
    __slots__ = ["current_iam", "none", "service_account"]
    CURRENT_IAM_FIELD_NUMBER: _ClassVar[int]
    NONE_FIELD_NUMBER: _ClassVar[int]
    SERVICE_ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    current_iam: CurrentIAMTokenAuth
    none: NoneAuth
    service_account: ServiceAccountAuth
    def __init__(self, current_iam: _Optional[_Union[CurrentIAMTokenAuth, _Mapping]] = ..., service_account: _Optional[_Union[ServiceAccountAuth, _Mapping]] = ..., none: _Optional[_Union[NoneAuth, _Mapping]] = ...) -> None: ...

class Job(_message.Message):
    __slots__ = ["acl", "ast", "automatic", "expire_at", "issue", "meta", "plan", "query_meta", "query_name", "result_set_meta", "statistics", "syntax", "text"]
    ACL_FIELD_NUMBER: _ClassVar[int]
    AST_FIELD_NUMBER: _ClassVar[int]
    AUTOMATIC_FIELD_NUMBER: _ClassVar[int]
    EXPIRE_AT_FIELD_NUMBER: _ClassVar[int]
    ISSUE_FIELD_NUMBER: _ClassVar[int]
    META_FIELD_NUMBER: _ClassVar[int]
    PLAN_FIELD_NUMBER: _ClassVar[int]
    QUERY_META_FIELD_NUMBER: _ClassVar[int]
    QUERY_NAME_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_META_FIELD_NUMBER: _ClassVar[int]
    STATISTICS_FIELD_NUMBER: _ClassVar[int]
    SYNTAX_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    acl: Acl
    ast: QueryAst
    automatic: bool
    expire_at: _timestamp_pb2.Timestamp
    issue: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    meta: CommonMeta
    plan: QueryPlan
    query_meta: QueryMeta
    query_name: str
    result_set_meta: _containers.RepeatedCompositeFieldContainer[ResultSetMeta]
    statistics: QueryStatistics
    syntax: QueryContent.QuerySyntax
    text: str
    def __init__(self, meta: _Optional[_Union[CommonMeta, _Mapping]] = ..., text: _Optional[str] = ..., query_meta: _Optional[_Union[QueryMeta, _Mapping]] = ..., plan: _Optional[_Union[QueryPlan, _Mapping]] = ..., issue: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., statistics: _Optional[_Union[QueryStatistics, _Mapping]] = ..., result_set_meta: _Optional[_Iterable[_Union[ResultSetMeta, _Mapping]]] = ..., ast: _Optional[_Union[QueryAst, _Mapping]] = ..., query_name: _Optional[str] = ..., acl: _Optional[_Union[Acl, _Mapping]] = ..., automatic: bool = ..., expire_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., syntax: _Optional[_Union[QueryContent.QuerySyntax, str]] = ...) -> None: ...

class Limits(_message.Message):
    __slots__ = ["execution_deadline", "execution_timeout", "flow_rate_limit", "max_result_rows", "max_result_size", "memory_limit", "result_ttl", "vcpu_rate_limit", "vcpu_time_limit"]
    EXECUTION_DEADLINE_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    FLOW_RATE_LIMIT_FIELD_NUMBER: _ClassVar[int]
    MAX_RESULT_ROWS_FIELD_NUMBER: _ClassVar[int]
    MAX_RESULT_SIZE_FIELD_NUMBER: _ClassVar[int]
    MEMORY_LIMIT_FIELD_NUMBER: _ClassVar[int]
    RESULT_TTL_FIELD_NUMBER: _ClassVar[int]
    VCPU_RATE_LIMIT_FIELD_NUMBER: _ClassVar[int]
    VCPU_TIME_LIMIT_FIELD_NUMBER: _ClassVar[int]
    execution_deadline: _timestamp_pb2.Timestamp
    execution_timeout: _duration_pb2.Duration
    flow_rate_limit: int
    max_result_rows: int
    max_result_size: int
    memory_limit: int
    result_ttl: _duration_pb2.Duration
    vcpu_rate_limit: int
    vcpu_time_limit: int
    def __init__(self, vcpu_rate_limit: _Optional[int] = ..., flow_rate_limit: _Optional[int] = ..., vcpu_time_limit: _Optional[int] = ..., max_result_size: _Optional[int] = ..., max_result_rows: _Optional[int] = ..., memory_limit: _Optional[int] = ..., result_ttl: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., execution_timeout: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., execution_deadline: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ListBindingsRequest(_message.Message):
    __slots__ = ["filter", "limit", "operation_params", "page_token"]
    class Filter(_message.Message):
        __slots__ = ["connection_id", "created_by_me", "name", "visibility"]
        CONNECTION_ID_FIELD_NUMBER: _ClassVar[int]
        CREATED_BY_ME_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        VISIBILITY_FIELD_NUMBER: _ClassVar[int]
        connection_id: str
        created_by_me: bool
        name: str
        visibility: Acl.Visibility
        def __init__(self, connection_id: _Optional[str] = ..., name: _Optional[str] = ..., created_by_me: bool = ..., visibility: _Optional[_Union[Acl.Visibility, str]] = ...) -> None: ...
    FILTER_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    filter: ListBindingsRequest.Filter
    limit: int
    operation_params: _ydb_operation_pb2.OperationParams
    page_token: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., page_token: _Optional[str] = ..., limit: _Optional[int] = ..., filter: _Optional[_Union[ListBindingsRequest.Filter, _Mapping]] = ...) -> None: ...

class ListBindingsResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListBindingsResult(_message.Message):
    __slots__ = ["binding", "next_page_token"]
    BINDING_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    binding: _containers.RepeatedCompositeFieldContainer[BriefBinding]
    next_page_token: str
    def __init__(self, binding: _Optional[_Iterable[_Union[BriefBinding, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class ListConnectionsRequest(_message.Message):
    __slots__ = ["filter", "limit", "operation_params", "page_token"]
    class Filter(_message.Message):
        __slots__ = ["connection_type", "created_by_me", "name", "visibility"]
        CONNECTION_TYPE_FIELD_NUMBER: _ClassVar[int]
        CREATED_BY_ME_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        VISIBILITY_FIELD_NUMBER: _ClassVar[int]
        connection_type: ConnectionSetting.ConnectionType
        created_by_me: bool
        name: str
        visibility: Acl.Visibility
        def __init__(self, name: _Optional[str] = ..., created_by_me: bool = ..., connection_type: _Optional[_Union[ConnectionSetting.ConnectionType, str]] = ..., visibility: _Optional[_Union[Acl.Visibility, str]] = ...) -> None: ...
    FILTER_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    filter: ListConnectionsRequest.Filter
    limit: int
    operation_params: _ydb_operation_pb2.OperationParams
    page_token: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., page_token: _Optional[str] = ..., limit: _Optional[int] = ..., filter: _Optional[_Union[ListConnectionsRequest.Filter, _Mapping]] = ...) -> None: ...

class ListConnectionsResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListConnectionsResult(_message.Message):
    __slots__ = ["connection", "next_page_token"]
    CONNECTION_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    connection: _containers.RepeatedCompositeFieldContainer[Connection]
    next_page_token: str
    def __init__(self, connection: _Optional[_Iterable[_Union[Connection, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class ListJobsRequest(_message.Message):
    __slots__ = ["filter", "limit", "operation_params", "page_token", "query_id"]
    class Filter(_message.Message):
        __slots__ = ["created_by_me", "query_id"]
        CREATED_BY_ME_FIELD_NUMBER: _ClassVar[int]
        QUERY_ID_FIELD_NUMBER: _ClassVar[int]
        created_by_me: bool
        query_id: str
        def __init__(self, query_id: _Optional[str] = ..., created_by_me: bool = ...) -> None: ...
    FILTER_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    QUERY_ID_FIELD_NUMBER: _ClassVar[int]
    filter: ListJobsRequest.Filter
    limit: int
    operation_params: _ydb_operation_pb2.OperationParams
    page_token: str
    query_id: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., page_token: _Optional[str] = ..., limit: _Optional[int] = ..., query_id: _Optional[str] = ..., filter: _Optional[_Union[ListJobsRequest.Filter, _Mapping]] = ...) -> None: ...

class ListJobsResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListJobsResult(_message.Message):
    __slots__ = ["job", "next_page_token"]
    JOB_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    job: _containers.RepeatedCompositeFieldContainer[BriefJob]
    next_page_token: str
    def __init__(self, job: _Optional[_Iterable[_Union[BriefJob, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class ListQueriesRequest(_message.Message):
    __slots__ = ["filter", "limit", "operation_params", "page_token"]
    class Filter(_message.Message):
        __slots__ = ["automatic", "created_by_me", "mode", "name", "query_type", "status", "visibility"]
        AUTOMATIC_FIELD_NUMBER: _ClassVar[int]
        CREATED_BY_ME_FIELD_NUMBER: _ClassVar[int]
        MODE_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        QUERY_TYPE_FIELD_NUMBER: _ClassVar[int]
        STATUS_FIELD_NUMBER: _ClassVar[int]
        VISIBILITY_FIELD_NUMBER: _ClassVar[int]
        automatic: AutomaticType
        created_by_me: bool
        mode: _containers.RepeatedScalarFieldContainer[ExecuteMode]
        name: str
        query_type: QueryContent.QueryType
        status: _containers.RepeatedScalarFieldContainer[QueryMeta.ComputeStatus]
        visibility: Acl.Visibility
        def __init__(self, query_type: _Optional[_Union[QueryContent.QueryType, str]] = ..., status: _Optional[_Iterable[_Union[QueryMeta.ComputeStatus, str]]] = ..., mode: _Optional[_Iterable[_Union[ExecuteMode, str]]] = ..., name: _Optional[str] = ..., created_by_me: bool = ..., visibility: _Optional[_Union[Acl.Visibility, str]] = ..., automatic: _Optional[_Union[AutomaticType, str]] = ...) -> None: ...
    FILTER_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    filter: ListQueriesRequest.Filter
    limit: int
    operation_params: _ydb_operation_pb2.OperationParams
    page_token: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., page_token: _Optional[str] = ..., limit: _Optional[int] = ..., filter: _Optional[_Union[ListQueriesRequest.Filter, _Mapping]] = ...) -> None: ...

class ListQueriesResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListQueriesResult(_message.Message):
    __slots__ = ["next_page_token", "query"]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    QUERY_FIELD_NUMBER: _ClassVar[int]
    next_page_token: str
    query: _containers.RepeatedCompositeFieldContainer[BriefQuery]
    def __init__(self, query: _Optional[_Iterable[_Union[BriefQuery, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class ModifyBindingRequest(_message.Message):
    __slots__ = ["binding_id", "content", "idempotency_key", "operation_params", "previous_revision"]
    BINDING_ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_REVISION_FIELD_NUMBER: _ClassVar[int]
    binding_id: str
    content: BindingContent
    idempotency_key: str
    operation_params: _ydb_operation_pb2.OperationParams
    previous_revision: int
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., binding_id: _Optional[str] = ..., content: _Optional[_Union[BindingContent, _Mapping]] = ..., previous_revision: _Optional[int] = ..., idempotency_key: _Optional[str] = ...) -> None: ...

class ModifyBindingResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ModifyBindingResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class ModifyConnectionRequest(_message.Message):
    __slots__ = ["connection_id", "content", "idempotency_key", "operation_params", "previous_revision"]
    CONNECTION_ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_REVISION_FIELD_NUMBER: _ClassVar[int]
    connection_id: str
    content: ConnectionContent
    idempotency_key: str
    operation_params: _ydb_operation_pb2.OperationParams
    previous_revision: int
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., connection_id: _Optional[str] = ..., content: _Optional[_Union[ConnectionContent, _Mapping]] = ..., previous_revision: _Optional[int] = ..., idempotency_key: _Optional[str] = ...) -> None: ...

class ModifyConnectionResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ModifyConnectionResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class ModifyQueryRequest(_message.Message):
    __slots__ = ["content", "disposition", "execute_mode", "idempotency_key", "operation_params", "previous_revision", "query_id", "state_load_mode"]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    DISPOSITION_FIELD_NUMBER: _ClassVar[int]
    EXECUTE_MODE_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_REVISION_FIELD_NUMBER: _ClassVar[int]
    QUERY_ID_FIELD_NUMBER: _ClassVar[int]
    STATE_LOAD_MODE_FIELD_NUMBER: _ClassVar[int]
    content: QueryContent
    disposition: StreamingDisposition
    execute_mode: ExecuteMode
    idempotency_key: str
    operation_params: _ydb_operation_pb2.OperationParams
    previous_revision: int
    query_id: str
    state_load_mode: StateLoadMode
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., query_id: _Optional[str] = ..., content: _Optional[_Union[QueryContent, _Mapping]] = ..., execute_mode: _Optional[_Union[ExecuteMode, str]] = ..., disposition: _Optional[_Union[StreamingDisposition, _Mapping]] = ..., state_load_mode: _Optional[_Union[StateLoadMode, str]] = ..., previous_revision: _Optional[int] = ..., idempotency_key: _Optional[str] = ...) -> None: ...

class ModifyQueryResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ModifyQueryResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class Monitoring(_message.Message):
    __slots__ = ["auth", "cluster", "project"]
    AUTH_FIELD_NUMBER: _ClassVar[int]
    CLUSTER_FIELD_NUMBER: _ClassVar[int]
    PROJECT_FIELD_NUMBER: _ClassVar[int]
    auth: IamAuth
    cluster: str
    project: str
    def __init__(self, project: _Optional[str] = ..., cluster: _Optional[str] = ..., auth: _Optional[_Union[IamAuth, _Mapping]] = ...) -> None: ...

class NoneAuth(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class ObjectStorageBinding(_message.Message):
    __slots__ = ["subset"]
    class Subset(_message.Message):
        __slots__ = ["compression", "format", "format_setting", "partitioned_by", "path_pattern", "projection", "schema"]
        class FormatSettingEntry(_message.Message):
            __slots__ = ["key", "value"]
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        class ProjectionEntry(_message.Message):
            __slots__ = ["key", "value"]
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        COMPRESSION_FIELD_NUMBER: _ClassVar[int]
        FORMAT_FIELD_NUMBER: _ClassVar[int]
        FORMAT_SETTING_FIELD_NUMBER: _ClassVar[int]
        PARTITIONED_BY_FIELD_NUMBER: _ClassVar[int]
        PATH_PATTERN_FIELD_NUMBER: _ClassVar[int]
        PROJECTION_FIELD_NUMBER: _ClassVar[int]
        SCHEMA_FIELD_NUMBER: _ClassVar[int]
        compression: str
        format: str
        format_setting: _containers.ScalarMap[str, str]
        partitioned_by: _containers.RepeatedScalarFieldContainer[str]
        path_pattern: str
        projection: _containers.ScalarMap[str, str]
        schema: Schema
        def __init__(self, path_pattern: _Optional[str] = ..., format: _Optional[str] = ..., format_setting: _Optional[_Mapping[str, str]] = ..., compression: _Optional[str] = ..., schema: _Optional[_Union[Schema, _Mapping]] = ..., projection: _Optional[_Mapping[str, str]] = ..., partitioned_by: _Optional[_Iterable[str]] = ...) -> None: ...
    SUBSET_FIELD_NUMBER: _ClassVar[int]
    subset: _containers.RepeatedCompositeFieldContainer[ObjectStorageBinding.Subset]
    def __init__(self, subset: _Optional[_Iterable[_Union[ObjectStorageBinding.Subset, _Mapping]]] = ...) -> None: ...

class ObjectStorageConnection(_message.Message):
    __slots__ = ["auth", "bucket"]
    AUTH_FIELD_NUMBER: _ClassVar[int]
    BUCKET_FIELD_NUMBER: _ClassVar[int]
    auth: IamAuth
    bucket: str
    def __init__(self, bucket: _Optional[str] = ..., auth: _Optional[_Union[IamAuth, _Mapping]] = ...) -> None: ...

class PostgreSQLCluster(_message.Message):
    __slots__ = ["auth", "database_id", "database_name", "host", "login", "password", "port", "schema", "secure"]
    AUTH_FIELD_NUMBER: _ClassVar[int]
    DATABASE_ID_FIELD_NUMBER: _ClassVar[int]
    DATABASE_NAME_FIELD_NUMBER: _ClassVar[int]
    HOST_FIELD_NUMBER: _ClassVar[int]
    LOGIN_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    SECURE_FIELD_NUMBER: _ClassVar[int]
    auth: IamAuth
    database_id: str
    database_name: str
    host: str
    login: str
    password: str
    port: int
    schema: str
    secure: bool
    def __init__(self, database_id: _Optional[str] = ..., database_name: _Optional[str] = ..., login: _Optional[str] = ..., password: _Optional[str] = ..., schema: _Optional[str] = ..., auth: _Optional[_Union[IamAuth, _Mapping]] = ..., host: _Optional[str] = ..., port: _Optional[int] = ..., secure: bool = ...) -> None: ...

class Query(_message.Message):
    __slots__ = ["ast", "content", "issue", "meta", "plan", "result_set_meta", "statistics", "transient_issue"]
    AST_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    ISSUE_FIELD_NUMBER: _ClassVar[int]
    META_FIELD_NUMBER: _ClassVar[int]
    PLAN_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_META_FIELD_NUMBER: _ClassVar[int]
    STATISTICS_FIELD_NUMBER: _ClassVar[int]
    TRANSIENT_ISSUE_FIELD_NUMBER: _ClassVar[int]
    ast: QueryAst
    content: QueryContent
    issue: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    meta: QueryMeta
    plan: QueryPlan
    result_set_meta: _containers.RepeatedCompositeFieldContainer[ResultSetMeta]
    statistics: QueryStatistics
    transient_issue: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    def __init__(self, meta: _Optional[_Union[QueryMeta, _Mapping]] = ..., content: _Optional[_Union[QueryContent, _Mapping]] = ..., plan: _Optional[_Union[QueryPlan, _Mapping]] = ..., issue: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., transient_issue: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., statistics: _Optional[_Union[QueryStatistics, _Mapping]] = ..., result_set_meta: _Optional[_Iterable[_Union[ResultSetMeta, _Mapping]]] = ..., ast: _Optional[_Union[QueryAst, _Mapping]] = ...) -> None: ...

class QueryAst(_message.Message):
    __slots__ = ["data"]
    DATA_FIELD_NUMBER: _ClassVar[int]
    data: str
    def __init__(self, data: _Optional[str] = ...) -> None: ...

class QueryContent(_message.Message):
    __slots__ = ["acl", "automatic", "description", "execution_settings", "limits", "name", "syntax", "text", "type"]
    class QuerySyntax(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    class QueryType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    class ExecutionSettingsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ACL_FIELD_NUMBER: _ClassVar[int]
    ANALYTICS: QueryContent.QueryType
    AUTOMATIC_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    LIMITS_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PG: QueryContent.QuerySyntax
    QUERY_SYNTAX_UNSPECIFIED: QueryContent.QuerySyntax
    QUERY_TYPE_UNSPECIFIED: QueryContent.QueryType
    STREAMING: QueryContent.QueryType
    SYNTAX_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    YQL_V1: QueryContent.QuerySyntax
    acl: Acl
    automatic: bool
    description: str
    execution_settings: _containers.ScalarMap[str, str]
    limits: Limits
    name: str
    syntax: QueryContent.QuerySyntax
    text: str
    type: QueryContent.QueryType
    def __init__(self, type: _Optional[_Union[QueryContent.QueryType, str]] = ..., name: _Optional[str] = ..., acl: _Optional[_Union[Acl, _Mapping]] = ..., limits: _Optional[_Union[Limits, _Mapping]] = ..., text: _Optional[str] = ..., automatic: bool = ..., description: _Optional[str] = ..., execution_settings: _Optional[_Mapping[str, str]] = ..., syntax: _Optional[_Union[QueryContent.QuerySyntax, str]] = ...) -> None: ...

class QueryMeta(_message.Message):
    __slots__ = ["aborted_by", "common", "execute_mode", "expire_at", "finished_at", "has_saved_checkpoints", "last_job_id", "last_job_query_revision", "paused_by", "result_expire_at", "started_at", "started_by", "status", "submitted_at"]
    class ComputeStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    ABORTED_BY_FIELD_NUMBER: _ClassVar[int]
    ABORTED_BY_SYSTEM: QueryMeta.ComputeStatus
    ABORTED_BY_USER: QueryMeta.ComputeStatus
    ABORTING_BY_SYSTEM: QueryMeta.ComputeStatus
    ABORTING_BY_USER: QueryMeta.ComputeStatus
    COMMON_FIELD_NUMBER: _ClassVar[int]
    COMPLETED: QueryMeta.ComputeStatus
    COMPLETING: QueryMeta.ComputeStatus
    COMPUTE_STATUS_UNSPECIFIED: QueryMeta.ComputeStatus
    EXECUTE_MODE_FIELD_NUMBER: _ClassVar[int]
    EXPIRE_AT_FIELD_NUMBER: _ClassVar[int]
    FAILED: QueryMeta.ComputeStatus
    FAILING: QueryMeta.ComputeStatus
    FINISHED_AT_FIELD_NUMBER: _ClassVar[int]
    HAS_SAVED_CHECKPOINTS_FIELD_NUMBER: _ClassVar[int]
    LAST_JOB_ID_FIELD_NUMBER: _ClassVar[int]
    LAST_JOB_QUERY_REVISION_FIELD_NUMBER: _ClassVar[int]
    PAUSED: QueryMeta.ComputeStatus
    PAUSED_BY_FIELD_NUMBER: _ClassVar[int]
    PAUSING: QueryMeta.ComputeStatus
    RESULT_EXPIRE_AT_FIELD_NUMBER: _ClassVar[int]
    RESUMING: QueryMeta.ComputeStatus
    RUNNING: QueryMeta.ComputeStatus
    STARTED_AT_FIELD_NUMBER: _ClassVar[int]
    STARTED_BY_FIELD_NUMBER: _ClassVar[int]
    STARTING: QueryMeta.ComputeStatus
    STATUS_FIELD_NUMBER: _ClassVar[int]
    SUBMITTED_AT_FIELD_NUMBER: _ClassVar[int]
    aborted_by: str
    common: CommonMeta
    execute_mode: ExecuteMode
    expire_at: _timestamp_pb2.Timestamp
    finished_at: _timestamp_pb2.Timestamp
    has_saved_checkpoints: bool
    last_job_id: str
    last_job_query_revision: int
    paused_by: str
    result_expire_at: _timestamp_pb2.Timestamp
    started_at: _timestamp_pb2.Timestamp
    started_by: str
    status: QueryMeta.ComputeStatus
    submitted_at: _timestamp_pb2.Timestamp
    def __init__(self, common: _Optional[_Union[CommonMeta, _Mapping]] = ..., submitted_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., started_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., finished_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., execute_mode: _Optional[_Union[ExecuteMode, str]] = ..., status: _Optional[_Union[QueryMeta.ComputeStatus, str]] = ..., last_job_query_revision: _Optional[int] = ..., last_job_id: _Optional[str] = ..., expire_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., result_expire_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., started_by: _Optional[str] = ..., aborted_by: _Optional[str] = ..., paused_by: _Optional[str] = ..., has_saved_checkpoints: bool = ...) -> None: ...

class QueryPlan(_message.Message):
    __slots__ = ["json"]
    JSON_FIELD_NUMBER: _ClassVar[int]
    json: str
    def __init__(self, json: _Optional[str] = ...) -> None: ...

class QueryStatistics(_message.Message):
    __slots__ = ["json"]
    JSON_FIELD_NUMBER: _ClassVar[int]
    json: str
    def __init__(self, json: _Optional[str] = ...) -> None: ...

class ResultSetMeta(_message.Message):
    __slots__ = ["column", "rows_count", "truncated"]
    COLUMN_FIELD_NUMBER: _ClassVar[int]
    ROWS_COUNT_FIELD_NUMBER: _ClassVar[int]
    TRUNCATED_FIELD_NUMBER: _ClassVar[int]
    column: _containers.RepeatedCompositeFieldContainer[_ydb_value_pb2.Column]
    rows_count: int
    truncated: bool
    def __init__(self, column: _Optional[_Iterable[_Union[_ydb_value_pb2.Column, _Mapping]]] = ..., rows_count: _Optional[int] = ..., truncated: bool = ...) -> None: ...

class Schema(_message.Message):
    __slots__ = ["column"]
    COLUMN_FIELD_NUMBER: _ClassVar[int]
    column: _containers.RepeatedCompositeFieldContainer[_ydb_value_pb2.Column]
    def __init__(self, column: _Optional[_Iterable[_Union[_ydb_value_pb2.Column, _Mapping]]] = ...) -> None: ...

class ServiceAccountAuth(_message.Message):
    __slots__ = ["id"]
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class StreamingDisposition(_message.Message):
    __slots__ = ["fresh", "from_last_checkpoint", "from_time", "oldest", "time_ago"]
    class FromLastCheckpoint(_message.Message):
        __slots__ = ["force"]
        FORCE_FIELD_NUMBER: _ClassVar[int]
        force: bool
        def __init__(self, force: bool = ...) -> None: ...
    class FromTime(_message.Message):
        __slots__ = ["timestamp"]
        TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
        timestamp: _timestamp_pb2.Timestamp
        def __init__(self, timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
    class TimeAgo(_message.Message):
        __slots__ = ["duration"]
        DURATION_FIELD_NUMBER: _ClassVar[int]
        duration: _duration_pb2.Duration
        def __init__(self, duration: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ...) -> None: ...
    FRESH_FIELD_NUMBER: _ClassVar[int]
    FROM_LAST_CHECKPOINT_FIELD_NUMBER: _ClassVar[int]
    FROM_TIME_FIELD_NUMBER: _ClassVar[int]
    OLDEST_FIELD_NUMBER: _ClassVar[int]
    TIME_AGO_FIELD_NUMBER: _ClassVar[int]
    fresh: _empty_pb2.Empty
    from_last_checkpoint: StreamingDisposition.FromLastCheckpoint
    from_time: StreamingDisposition.FromTime
    oldest: _empty_pb2.Empty
    time_ago: StreamingDisposition.TimeAgo
    def __init__(self, oldest: _Optional[_Union[_empty_pb2.Empty, _Mapping]] = ..., fresh: _Optional[_Union[_empty_pb2.Empty, _Mapping]] = ..., from_time: _Optional[_Union[StreamingDisposition.FromTime, _Mapping]] = ..., time_ago: _Optional[_Union[StreamingDisposition.TimeAgo, _Mapping]] = ..., from_last_checkpoint: _Optional[_Union[StreamingDisposition.FromLastCheckpoint, _Mapping]] = ...) -> None: ...

class TestConnectionRequest(_message.Message):
    __slots__ = ["operation_params", "setting"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SETTING_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    setting: ConnectionSetting
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., setting: _Optional[_Union[ConnectionSetting, _Mapping]] = ...) -> None: ...

class TestConnectionResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class TestConnectionResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class YdbDatabase(_message.Message):
    __slots__ = ["auth", "database", "database_id", "endpoint", "secure"]
    AUTH_FIELD_NUMBER: _ClassVar[int]
    DATABASE_FIELD_NUMBER: _ClassVar[int]
    DATABASE_ID_FIELD_NUMBER: _ClassVar[int]
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    SECURE_FIELD_NUMBER: _ClassVar[int]
    auth: IamAuth
    database: str
    database_id: str
    endpoint: str
    secure: bool
    def __init__(self, database_id: _Optional[str] = ..., auth: _Optional[_Union[IamAuth, _Mapping]] = ..., endpoint: _Optional[str] = ..., database: _Optional[str] = ..., secure: bool = ...) -> None: ...

class ExecuteMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class QueryAction(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class StateLoadMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class AutomaticType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
