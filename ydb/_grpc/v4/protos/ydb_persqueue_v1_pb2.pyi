from protos import ydb_operation_pb2 as _ydb_operation_pb2
from protos import ydb_scheme_pb2 as _ydb_scheme_pb2
from protos import ydb_status_codes_pb2 as _ydb_status_codes_pb2
from protos import ydb_issue_message_pb2 as _ydb_issue_message_pb2
from protos.annotations import validation_pb2 as _validation_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

CODEC_GZIP: Codec
CODEC_LZOP: Codec
CODEC_RAW: Codec
CODEC_UNSPECIFIED: Codec
CODEC_ZSTD: Codec
DESCRIPTOR: _descriptor.FileDescriptor

class AddReadRuleRequest(_message.Message):
    __slots__ = ["operation_params", "path", "read_rule"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    READ_RULE_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    read_rule: TopicSettings.ReadRule
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., read_rule: _Optional[_Union[TopicSettings.ReadRule, _Mapping]] = ...) -> None: ...

class AddReadRuleResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class AddReadRuleResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class AlterTopicRequest(_message.Message):
    __slots__ = ["operation_params", "path", "settings"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    settings: TopicSettings
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., settings: _Optional[_Union[TopicSettings, _Mapping]] = ...) -> None: ...

class AlterTopicResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class AlterTopicResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class CommitCookie(_message.Message):
    __slots__ = ["assign_id", "partition_cookie"]
    ASSIGN_ID_FIELD_NUMBER: _ClassVar[int]
    PARTITION_COOKIE_FIELD_NUMBER: _ClassVar[int]
    assign_id: int
    partition_cookie: int
    def __init__(self, assign_id: _Optional[int] = ..., partition_cookie: _Optional[int] = ...) -> None: ...

class CommitOffsetRange(_message.Message):
    __slots__ = ["assign_id", "end_offset", "start_offset"]
    ASSIGN_ID_FIELD_NUMBER: _ClassVar[int]
    END_OFFSET_FIELD_NUMBER: _ClassVar[int]
    START_OFFSET_FIELD_NUMBER: _ClassVar[int]
    assign_id: int
    end_offset: int
    start_offset: int
    def __init__(self, assign_id: _Optional[int] = ..., start_offset: _Optional[int] = ..., end_offset: _Optional[int] = ...) -> None: ...

class CreateTopicRequest(_message.Message):
    __slots__ = ["operation_params", "path", "settings"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    settings: TopicSettings
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., settings: _Optional[_Union[TopicSettings, _Mapping]] = ...) -> None: ...

class CreateTopicResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class CreateTopicResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class Credentials(_message.Message):
    __slots__ = ["iam", "jwt_params", "oauth_token"]
    class Iam(_message.Message):
        __slots__ = ["endpoint", "service_account_key"]
        ENDPOINT_FIELD_NUMBER: _ClassVar[int]
        SERVICE_ACCOUNT_KEY_FIELD_NUMBER: _ClassVar[int]
        endpoint: str
        service_account_key: str
        def __init__(self, endpoint: _Optional[str] = ..., service_account_key: _Optional[str] = ...) -> None: ...
    IAM_FIELD_NUMBER: _ClassVar[int]
    JWT_PARAMS_FIELD_NUMBER: _ClassVar[int]
    OAUTH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    iam: Credentials.Iam
    jwt_params: str
    oauth_token: str
    def __init__(self, oauth_token: _Optional[str] = ..., jwt_params: _Optional[str] = ..., iam: _Optional[_Union[Credentials.Iam, _Mapping]] = ...) -> None: ...

class DescribeTopicRequest(_message.Message):
    __slots__ = ["operation_params", "path"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ...) -> None: ...

class DescribeTopicResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeTopicResult(_message.Message):
    __slots__ = ["self", "settings"]
    SELF_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    self: _ydb_scheme_pb2.Entry
    settings: TopicSettings
    def __init__(self, self_: _Optional[_Union[_ydb_scheme_pb2.Entry, _Mapping]] = ..., settings: _Optional[_Union[TopicSettings, _Mapping]] = ...) -> None: ...

class DropTopicRequest(_message.Message):
    __slots__ = ["operation_params", "path"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ...) -> None: ...

class DropTopicResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DropTopicResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class KeyValue(_message.Message):
    __slots__ = ["key", "value"]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: str
    value: str
    def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class MigrationStreamingReadClientMessage(_message.Message):
    __slots__ = ["commit", "init_request", "read", "released", "start_read", "status", "token"]
    class Commit(_message.Message):
        __slots__ = ["cookies", "offset_ranges"]
        COOKIES_FIELD_NUMBER: _ClassVar[int]
        OFFSET_RANGES_FIELD_NUMBER: _ClassVar[int]
        cookies: _containers.RepeatedCompositeFieldContainer[CommitCookie]
        offset_ranges: _containers.RepeatedCompositeFieldContainer[CommitOffsetRange]
        def __init__(self, cookies: _Optional[_Iterable[_Union[CommitCookie, _Mapping]]] = ..., offset_ranges: _Optional[_Iterable[_Union[CommitOffsetRange, _Mapping]]] = ...) -> None: ...
    class InitRequest(_message.Message):
        __slots__ = ["connection_attempt", "consumer", "idle_timeout_ms", "max_lag_duration_ms", "max_meta_cache_size", "max_supported_block_format_version", "ranges_mode", "read_only_original", "read_params", "session_id", "start_from_written_at_ms", "state", "topics_read_settings"]
        class State(_message.Message):
            __slots__ = ["partition_streams_states"]
            class PartitionStreamState(_message.Message):
                __slots__ = ["offset_ranges", "partition_stream", "read_offset", "status"]
                class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                    __slots__ = []
                CREATING: MigrationStreamingReadClientMessage.InitRequest.State.PartitionStreamState.Status
                DESTROYING: MigrationStreamingReadClientMessage.InitRequest.State.PartitionStreamState.Status
                OFFSET_RANGES_FIELD_NUMBER: _ClassVar[int]
                PARTITION_STREAM_FIELD_NUMBER: _ClassVar[int]
                READING: MigrationStreamingReadClientMessage.InitRequest.State.PartitionStreamState.Status
                READ_OFFSET_FIELD_NUMBER: _ClassVar[int]
                STATUS_FIELD_NUMBER: _ClassVar[int]
                STATUS_UNSPECIFIED: MigrationStreamingReadClientMessage.InitRequest.State.PartitionStreamState.Status
                STOPPED: MigrationStreamingReadClientMessage.InitRequest.State.PartitionStreamState.Status
                offset_ranges: _containers.RepeatedCompositeFieldContainer[OffsetsRange]
                partition_stream: PartitionStream
                read_offset: int
                status: MigrationStreamingReadClientMessage.InitRequest.State.PartitionStreamState.Status
                def __init__(self, partition_stream: _Optional[_Union[PartitionStream, _Mapping]] = ..., read_offset: _Optional[int] = ..., offset_ranges: _Optional[_Iterable[_Union[OffsetsRange, _Mapping]]] = ..., status: _Optional[_Union[MigrationStreamingReadClientMessage.InitRequest.State.PartitionStreamState.Status, str]] = ...) -> None: ...
            PARTITION_STREAMS_STATES_FIELD_NUMBER: _ClassVar[int]
            partition_streams_states: _containers.RepeatedCompositeFieldContainer[MigrationStreamingReadClientMessage.InitRequest.State.PartitionStreamState]
            def __init__(self, partition_streams_states: _Optional[_Iterable[_Union[MigrationStreamingReadClientMessage.InitRequest.State.PartitionStreamState, _Mapping]]] = ...) -> None: ...
        CONNECTION_ATTEMPT_FIELD_NUMBER: _ClassVar[int]
        CONSUMER_FIELD_NUMBER: _ClassVar[int]
        IDLE_TIMEOUT_MS_FIELD_NUMBER: _ClassVar[int]
        MAX_LAG_DURATION_MS_FIELD_NUMBER: _ClassVar[int]
        MAX_META_CACHE_SIZE_FIELD_NUMBER: _ClassVar[int]
        MAX_SUPPORTED_BLOCK_FORMAT_VERSION_FIELD_NUMBER: _ClassVar[int]
        RANGES_MODE_FIELD_NUMBER: _ClassVar[int]
        READ_ONLY_ORIGINAL_FIELD_NUMBER: _ClassVar[int]
        READ_PARAMS_FIELD_NUMBER: _ClassVar[int]
        SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        START_FROM_WRITTEN_AT_MS_FIELD_NUMBER: _ClassVar[int]
        STATE_FIELD_NUMBER: _ClassVar[int]
        TOPICS_READ_SETTINGS_FIELD_NUMBER: _ClassVar[int]
        connection_attempt: int
        consumer: str
        idle_timeout_ms: int
        max_lag_duration_ms: int
        max_meta_cache_size: int
        max_supported_block_format_version: int
        ranges_mode: bool
        read_only_original: bool
        read_params: ReadParams
        session_id: str
        start_from_written_at_ms: int
        state: MigrationStreamingReadClientMessage.InitRequest.State
        topics_read_settings: _containers.RepeatedCompositeFieldContainer[MigrationStreamingReadClientMessage.TopicReadSettings]
        def __init__(self, topics_read_settings: _Optional[_Iterable[_Union[MigrationStreamingReadClientMessage.TopicReadSettings, _Mapping]]] = ..., read_only_original: bool = ..., consumer: _Optional[str] = ..., max_lag_duration_ms: _Optional[int] = ..., start_from_written_at_ms: _Optional[int] = ..., max_supported_block_format_version: _Optional[int] = ..., max_meta_cache_size: _Optional[int] = ..., session_id: _Optional[str] = ..., connection_attempt: _Optional[int] = ..., state: _Optional[_Union[MigrationStreamingReadClientMessage.InitRequest.State, _Mapping]] = ..., idle_timeout_ms: _Optional[int] = ..., read_params: _Optional[_Union[ReadParams, _Mapping]] = ..., ranges_mode: bool = ...) -> None: ...
    class Read(_message.Message):
        __slots__ = []
        def __init__(self) -> None: ...
    class Released(_message.Message):
        __slots__ = ["assign_id", "cluster", "partition", "topic"]
        ASSIGN_ID_FIELD_NUMBER: _ClassVar[int]
        CLUSTER_FIELD_NUMBER: _ClassVar[int]
        PARTITION_FIELD_NUMBER: _ClassVar[int]
        TOPIC_FIELD_NUMBER: _ClassVar[int]
        assign_id: int
        cluster: str
        partition: int
        topic: Path
        def __init__(self, topic: _Optional[_Union[Path, _Mapping]] = ..., cluster: _Optional[str] = ..., partition: _Optional[int] = ..., assign_id: _Optional[int] = ...) -> None: ...
    class StartRead(_message.Message):
        __slots__ = ["assign_id", "cluster", "commit_offset", "partition", "read_offset", "topic", "verify_read_offset"]
        ASSIGN_ID_FIELD_NUMBER: _ClassVar[int]
        CLUSTER_FIELD_NUMBER: _ClassVar[int]
        COMMIT_OFFSET_FIELD_NUMBER: _ClassVar[int]
        PARTITION_FIELD_NUMBER: _ClassVar[int]
        READ_OFFSET_FIELD_NUMBER: _ClassVar[int]
        TOPIC_FIELD_NUMBER: _ClassVar[int]
        VERIFY_READ_OFFSET_FIELD_NUMBER: _ClassVar[int]
        assign_id: int
        cluster: str
        commit_offset: int
        partition: int
        read_offset: int
        topic: Path
        verify_read_offset: bool
        def __init__(self, topic: _Optional[_Union[Path, _Mapping]] = ..., cluster: _Optional[str] = ..., partition: _Optional[int] = ..., assign_id: _Optional[int] = ..., read_offset: _Optional[int] = ..., commit_offset: _Optional[int] = ..., verify_read_offset: bool = ...) -> None: ...
    class Status(_message.Message):
        __slots__ = ["assign_id", "cluster", "partition", "topic"]
        ASSIGN_ID_FIELD_NUMBER: _ClassVar[int]
        CLUSTER_FIELD_NUMBER: _ClassVar[int]
        PARTITION_FIELD_NUMBER: _ClassVar[int]
        TOPIC_FIELD_NUMBER: _ClassVar[int]
        assign_id: int
        cluster: str
        partition: int
        topic: Path
        def __init__(self, topic: _Optional[_Union[Path, _Mapping]] = ..., cluster: _Optional[str] = ..., partition: _Optional[int] = ..., assign_id: _Optional[int] = ...) -> None: ...
    class TopicReadSettings(_message.Message):
        __slots__ = ["partition_group_ids", "start_from_written_at_ms", "topic"]
        PARTITION_GROUP_IDS_FIELD_NUMBER: _ClassVar[int]
        START_FROM_WRITTEN_AT_MS_FIELD_NUMBER: _ClassVar[int]
        TOPIC_FIELD_NUMBER: _ClassVar[int]
        partition_group_ids: _containers.RepeatedScalarFieldContainer[int]
        start_from_written_at_ms: int
        topic: str
        def __init__(self, topic: _Optional[str] = ..., partition_group_ids: _Optional[_Iterable[int]] = ..., start_from_written_at_ms: _Optional[int] = ...) -> None: ...
    COMMIT_FIELD_NUMBER: _ClassVar[int]
    INIT_REQUEST_FIELD_NUMBER: _ClassVar[int]
    READ_FIELD_NUMBER: _ClassVar[int]
    RELEASED_FIELD_NUMBER: _ClassVar[int]
    START_READ_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    commit: MigrationStreamingReadClientMessage.Commit
    init_request: MigrationStreamingReadClientMessage.InitRequest
    read: MigrationStreamingReadClientMessage.Read
    released: MigrationStreamingReadClientMessage.Released
    start_read: MigrationStreamingReadClientMessage.StartRead
    status: MigrationStreamingReadClientMessage.Status
    token: bytes
    def __init__(self, init_request: _Optional[_Union[MigrationStreamingReadClientMessage.InitRequest, _Mapping]] = ..., read: _Optional[_Union[MigrationStreamingReadClientMessage.Read, _Mapping]] = ..., start_read: _Optional[_Union[MigrationStreamingReadClientMessage.StartRead, _Mapping]] = ..., commit: _Optional[_Union[MigrationStreamingReadClientMessage.Commit, _Mapping]] = ..., released: _Optional[_Union[MigrationStreamingReadClientMessage.Released, _Mapping]] = ..., status: _Optional[_Union[MigrationStreamingReadClientMessage.Status, _Mapping]] = ..., token: _Optional[bytes] = ...) -> None: ...

class MigrationStreamingReadServerMessage(_message.Message):
    __slots__ = ["assigned", "committed", "data_batch", "init_response", "issues", "partition_status", "release", "status"]
    class Assigned(_message.Message):
        __slots__ = ["assign_id", "cluster", "end_offset", "partition", "read_offset", "topic"]
        ASSIGN_ID_FIELD_NUMBER: _ClassVar[int]
        CLUSTER_FIELD_NUMBER: _ClassVar[int]
        END_OFFSET_FIELD_NUMBER: _ClassVar[int]
        PARTITION_FIELD_NUMBER: _ClassVar[int]
        READ_OFFSET_FIELD_NUMBER: _ClassVar[int]
        TOPIC_FIELD_NUMBER: _ClassVar[int]
        assign_id: int
        cluster: str
        end_offset: int
        partition: int
        read_offset: int
        topic: Path
        def __init__(self, topic: _Optional[_Union[Path, _Mapping]] = ..., cluster: _Optional[str] = ..., partition: _Optional[int] = ..., assign_id: _Optional[int] = ..., read_offset: _Optional[int] = ..., end_offset: _Optional[int] = ...) -> None: ...
    class Committed(_message.Message):
        __slots__ = ["cookies", "offset_ranges"]
        COOKIES_FIELD_NUMBER: _ClassVar[int]
        OFFSET_RANGES_FIELD_NUMBER: _ClassVar[int]
        cookies: _containers.RepeatedCompositeFieldContainer[CommitCookie]
        offset_ranges: _containers.RepeatedCompositeFieldContainer[CommitOffsetRange]
        def __init__(self, cookies: _Optional[_Iterable[_Union[CommitCookie, _Mapping]]] = ..., offset_ranges: _Optional[_Iterable[_Union[CommitOffsetRange, _Mapping]]] = ...) -> None: ...
    class DataBatch(_message.Message):
        __slots__ = ["partition_data"]
        class Batch(_message.Message):
            __slots__ = ["extra_fields", "ip", "message_data", "source_id", "write_timestamp_ms"]
            EXTRA_FIELDS_FIELD_NUMBER: _ClassVar[int]
            IP_FIELD_NUMBER: _ClassVar[int]
            MESSAGE_DATA_FIELD_NUMBER: _ClassVar[int]
            SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
            WRITE_TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
            extra_fields: _containers.RepeatedCompositeFieldContainer[KeyValue]
            ip: str
            message_data: _containers.RepeatedCompositeFieldContainer[MigrationStreamingReadServerMessage.DataBatch.MessageData]
            source_id: bytes
            write_timestamp_ms: int
            def __init__(self, source_id: _Optional[bytes] = ..., extra_fields: _Optional[_Iterable[_Union[KeyValue, _Mapping]]] = ..., write_timestamp_ms: _Optional[int] = ..., ip: _Optional[str] = ..., message_data: _Optional[_Iterable[_Union[MigrationStreamingReadServerMessage.DataBatch.MessageData, _Mapping]]] = ...) -> None: ...
        class MessageData(_message.Message):
            __slots__ = ["codec", "create_timestamp_ms", "data", "explicit_hash", "offset", "partition_key", "seq_no", "uncompressed_size"]
            CODEC_FIELD_NUMBER: _ClassVar[int]
            CREATE_TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
            DATA_FIELD_NUMBER: _ClassVar[int]
            EXPLICIT_HASH_FIELD_NUMBER: _ClassVar[int]
            OFFSET_FIELD_NUMBER: _ClassVar[int]
            PARTITION_KEY_FIELD_NUMBER: _ClassVar[int]
            SEQ_NO_FIELD_NUMBER: _ClassVar[int]
            UNCOMPRESSED_SIZE_FIELD_NUMBER: _ClassVar[int]
            codec: Codec
            create_timestamp_ms: int
            data: bytes
            explicit_hash: bytes
            offset: int
            partition_key: str
            seq_no: int
            uncompressed_size: int
            def __init__(self, offset: _Optional[int] = ..., seq_no: _Optional[int] = ..., create_timestamp_ms: _Optional[int] = ..., codec: _Optional[_Union[Codec, str]] = ..., data: _Optional[bytes] = ..., uncompressed_size: _Optional[int] = ..., partition_key: _Optional[str] = ..., explicit_hash: _Optional[bytes] = ...) -> None: ...
        class PartitionData(_message.Message):
            __slots__ = ["batches", "cluster", "cookie", "deprecated_topic", "partition", "topic"]
            BATCHES_FIELD_NUMBER: _ClassVar[int]
            CLUSTER_FIELD_NUMBER: _ClassVar[int]
            COOKIE_FIELD_NUMBER: _ClassVar[int]
            DEPRECATED_TOPIC_FIELD_NUMBER: _ClassVar[int]
            PARTITION_FIELD_NUMBER: _ClassVar[int]
            TOPIC_FIELD_NUMBER: _ClassVar[int]
            batches: _containers.RepeatedCompositeFieldContainer[MigrationStreamingReadServerMessage.DataBatch.Batch]
            cluster: str
            cookie: CommitCookie
            deprecated_topic: str
            partition: int
            topic: Path
            def __init__(self, topic: _Optional[_Union[Path, _Mapping]] = ..., cluster: _Optional[str] = ..., partition: _Optional[int] = ..., batches: _Optional[_Iterable[_Union[MigrationStreamingReadServerMessage.DataBatch.Batch, _Mapping]]] = ..., cookie: _Optional[_Union[CommitCookie, _Mapping]] = ..., deprecated_topic: _Optional[str] = ...) -> None: ...
        PARTITION_DATA_FIELD_NUMBER: _ClassVar[int]
        partition_data: _containers.RepeatedCompositeFieldContainer[MigrationStreamingReadServerMessage.DataBatch.PartitionData]
        def __init__(self, partition_data: _Optional[_Iterable[_Union[MigrationStreamingReadServerMessage.DataBatch.PartitionData, _Mapping]]] = ...) -> None: ...
    class InitResponse(_message.Message):
        __slots__ = ["block_format_version_by_topic", "max_meta_cache_size", "session_id"]
        class BlockFormatVersionByTopicEntry(_message.Message):
            __slots__ = ["key", "value"]
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: int
            def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
        BLOCK_FORMAT_VERSION_BY_TOPIC_FIELD_NUMBER: _ClassVar[int]
        MAX_META_CACHE_SIZE_FIELD_NUMBER: _ClassVar[int]
        SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        block_format_version_by_topic: _containers.ScalarMap[str, int]
        max_meta_cache_size: int
        session_id: str
        def __init__(self, session_id: _Optional[str] = ..., block_format_version_by_topic: _Optional[_Mapping[str, int]] = ..., max_meta_cache_size: _Optional[int] = ...) -> None: ...
    class PartitionStatus(_message.Message):
        __slots__ = ["assign_id", "cluster", "committed_offset", "end_offset", "partition", "topic", "write_watermark_ms"]
        ASSIGN_ID_FIELD_NUMBER: _ClassVar[int]
        CLUSTER_FIELD_NUMBER: _ClassVar[int]
        COMMITTED_OFFSET_FIELD_NUMBER: _ClassVar[int]
        END_OFFSET_FIELD_NUMBER: _ClassVar[int]
        PARTITION_FIELD_NUMBER: _ClassVar[int]
        TOPIC_FIELD_NUMBER: _ClassVar[int]
        WRITE_WATERMARK_MS_FIELD_NUMBER: _ClassVar[int]
        assign_id: int
        cluster: str
        committed_offset: int
        end_offset: int
        partition: int
        topic: Path
        write_watermark_ms: int
        def __init__(self, topic: _Optional[_Union[Path, _Mapping]] = ..., cluster: _Optional[str] = ..., partition: _Optional[int] = ..., assign_id: _Optional[int] = ..., committed_offset: _Optional[int] = ..., end_offset: _Optional[int] = ..., write_watermark_ms: _Optional[int] = ...) -> None: ...
    class Release(_message.Message):
        __slots__ = ["assign_id", "cluster", "commit_offset", "forceful_release", "partition", "topic"]
        ASSIGN_ID_FIELD_NUMBER: _ClassVar[int]
        CLUSTER_FIELD_NUMBER: _ClassVar[int]
        COMMIT_OFFSET_FIELD_NUMBER: _ClassVar[int]
        FORCEFUL_RELEASE_FIELD_NUMBER: _ClassVar[int]
        PARTITION_FIELD_NUMBER: _ClassVar[int]
        TOPIC_FIELD_NUMBER: _ClassVar[int]
        assign_id: int
        cluster: str
        commit_offset: int
        forceful_release: bool
        partition: int
        topic: Path
        def __init__(self, topic: _Optional[_Union[Path, _Mapping]] = ..., cluster: _Optional[str] = ..., partition: _Optional[int] = ..., assign_id: _Optional[int] = ..., forceful_release: bool = ..., commit_offset: _Optional[int] = ...) -> None: ...
    ASSIGNED_FIELD_NUMBER: _ClassVar[int]
    COMMITTED_FIELD_NUMBER: _ClassVar[int]
    DATA_BATCH_FIELD_NUMBER: _ClassVar[int]
    INIT_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    PARTITION_STATUS_FIELD_NUMBER: _ClassVar[int]
    RELEASE_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    assigned: MigrationStreamingReadServerMessage.Assigned
    committed: MigrationStreamingReadServerMessage.Committed
    data_batch: MigrationStreamingReadServerMessage.DataBatch
    init_response: MigrationStreamingReadServerMessage.InitResponse
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    partition_status: MigrationStreamingReadServerMessage.PartitionStatus
    release: MigrationStreamingReadServerMessage.Release
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., init_response: _Optional[_Union[MigrationStreamingReadServerMessage.InitResponse, _Mapping]] = ..., data_batch: _Optional[_Union[MigrationStreamingReadServerMessage.DataBatch, _Mapping]] = ..., assigned: _Optional[_Union[MigrationStreamingReadServerMessage.Assigned, _Mapping]] = ..., release: _Optional[_Union[MigrationStreamingReadServerMessage.Release, _Mapping]] = ..., committed: _Optional[_Union[MigrationStreamingReadServerMessage.Committed, _Mapping]] = ..., partition_status: _Optional[_Union[MigrationStreamingReadServerMessage.PartitionStatus, _Mapping]] = ...) -> None: ...

class OffsetsRange(_message.Message):
    __slots__ = ["end_offset", "start_offset"]
    END_OFFSET_FIELD_NUMBER: _ClassVar[int]
    START_OFFSET_FIELD_NUMBER: _ClassVar[int]
    end_offset: int
    start_offset: int
    def __init__(self, start_offset: _Optional[int] = ..., end_offset: _Optional[int] = ...) -> None: ...

class PartitionStream(_message.Message):
    __slots__ = ["cluster", "connection_meta", "partition_group_id", "partition_id", "partition_stream_id", "topic"]
    CLUSTER_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_META_FIELD_NUMBER: _ClassVar[int]
    PARTITION_GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
    PARTITION_STREAM_ID_FIELD_NUMBER: _ClassVar[int]
    TOPIC_FIELD_NUMBER: _ClassVar[int]
    cluster: str
    connection_meta: bytes
    partition_group_id: int
    partition_id: int
    partition_stream_id: int
    topic: str
    def __init__(self, topic: _Optional[str] = ..., cluster: _Optional[str] = ..., partition_id: _Optional[int] = ..., partition_group_id: _Optional[int] = ..., partition_stream_id: _Optional[int] = ..., connection_meta: _Optional[bytes] = ...) -> None: ...

class Path(_message.Message):
    __slots__ = ["path"]
    PATH_FIELD_NUMBER: _ClassVar[int]
    path: str
    def __init__(self, path: _Optional[str] = ...) -> None: ...

class ReadInfoRequest(_message.Message):
    __slots__ = ["consumer", "get_only_original", "operation_params", "topics"]
    CONSUMER_FIELD_NUMBER: _ClassVar[int]
    GET_ONLY_ORIGINAL_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    TOPICS_FIELD_NUMBER: _ClassVar[int]
    consumer: Path
    get_only_original: bool
    operation_params: _ydb_operation_pb2.OperationParams
    topics: _containers.RepeatedCompositeFieldContainer[Path]
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., topics: _Optional[_Iterable[_Union[Path, _Mapping]]] = ..., get_only_original: bool = ..., consumer: _Optional[_Union[Path, _Mapping]] = ...) -> None: ...

class ReadInfoResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ReadInfoResult(_message.Message):
    __slots__ = ["topics"]
    class TopicInfo(_message.Message):
        __slots__ = ["cluster", "issues", "partitions", "status", "topic"]
        class PartitionInfo(_message.Message):
            __slots__ = ["assign_id", "assign_timestamp_ms", "client_node", "commit_offset", "commit_time_lag_ms", "committed_read_cookie", "end_offset", "issues", "last_read_cookie", "out_of_order_read_cookies_to_commit", "partition", "proxy_node", "read_offset", "read_time_lag_ms", "session_id", "start_offset", "status", "tablet_node"]
            ASSIGN_ID_FIELD_NUMBER: _ClassVar[int]
            ASSIGN_TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
            CLIENT_NODE_FIELD_NUMBER: _ClassVar[int]
            COMMITTED_READ_COOKIE_FIELD_NUMBER: _ClassVar[int]
            COMMIT_OFFSET_FIELD_NUMBER: _ClassVar[int]
            COMMIT_TIME_LAG_MS_FIELD_NUMBER: _ClassVar[int]
            END_OFFSET_FIELD_NUMBER: _ClassVar[int]
            ISSUES_FIELD_NUMBER: _ClassVar[int]
            LAST_READ_COOKIE_FIELD_NUMBER: _ClassVar[int]
            OUT_OF_ORDER_READ_COOKIES_TO_COMMIT_FIELD_NUMBER: _ClassVar[int]
            PARTITION_FIELD_NUMBER: _ClassVar[int]
            PROXY_NODE_FIELD_NUMBER: _ClassVar[int]
            READ_OFFSET_FIELD_NUMBER: _ClassVar[int]
            READ_TIME_LAG_MS_FIELD_NUMBER: _ClassVar[int]
            SESSION_ID_FIELD_NUMBER: _ClassVar[int]
            START_OFFSET_FIELD_NUMBER: _ClassVar[int]
            STATUS_FIELD_NUMBER: _ClassVar[int]
            TABLET_NODE_FIELD_NUMBER: _ClassVar[int]
            assign_id: int
            assign_timestamp_ms: int
            client_node: str
            commit_offset: int
            commit_time_lag_ms: int
            committed_read_cookie: int
            end_offset: int
            issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
            last_read_cookie: int
            out_of_order_read_cookies_to_commit: _containers.RepeatedScalarFieldContainer[int]
            partition: int
            proxy_node: str
            read_offset: int
            read_time_lag_ms: int
            session_id: str
            start_offset: int
            status: _ydb_status_codes_pb2.StatusIds.StatusCode
            tablet_node: str
            def __init__(self, partition: _Optional[int] = ..., status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., start_offset: _Optional[int] = ..., end_offset: _Optional[int] = ..., commit_offset: _Optional[int] = ..., commit_time_lag_ms: _Optional[int] = ..., read_offset: _Optional[int] = ..., read_time_lag_ms: _Optional[int] = ..., session_id: _Optional[str] = ..., client_node: _Optional[str] = ..., proxy_node: _Optional[str] = ..., tablet_node: _Optional[str] = ..., assign_id: _Optional[int] = ..., assign_timestamp_ms: _Optional[int] = ..., last_read_cookie: _Optional[int] = ..., committed_read_cookie: _Optional[int] = ..., out_of_order_read_cookies_to_commit: _Optional[_Iterable[int]] = ...) -> None: ...
        CLUSTER_FIELD_NUMBER: _ClassVar[int]
        ISSUES_FIELD_NUMBER: _ClassVar[int]
        PARTITIONS_FIELD_NUMBER: _ClassVar[int]
        STATUS_FIELD_NUMBER: _ClassVar[int]
        TOPIC_FIELD_NUMBER: _ClassVar[int]
        cluster: str
        issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
        partitions: _containers.RepeatedCompositeFieldContainer[ReadInfoResult.TopicInfo.PartitionInfo]
        status: _ydb_status_codes_pb2.StatusIds.StatusCode
        topic: Path
        def __init__(self, topic: _Optional[_Union[Path, _Mapping]] = ..., cluster: _Optional[str] = ..., status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., partitions: _Optional[_Iterable[_Union[ReadInfoResult.TopicInfo.PartitionInfo, _Mapping]]] = ...) -> None: ...
    TOPICS_FIELD_NUMBER: _ClassVar[int]
    topics: _containers.RepeatedCompositeFieldContainer[ReadInfoResult.TopicInfo]
    def __init__(self, topics: _Optional[_Iterable[_Union[ReadInfoResult.TopicInfo, _Mapping]]] = ...) -> None: ...

class ReadParams(_message.Message):
    __slots__ = ["max_read_messages_count", "max_read_size"]
    MAX_READ_MESSAGES_COUNT_FIELD_NUMBER: _ClassVar[int]
    MAX_READ_SIZE_FIELD_NUMBER: _ClassVar[int]
    max_read_messages_count: int
    max_read_size: int
    def __init__(self, max_read_messages_count: _Optional[int] = ..., max_read_size: _Optional[int] = ...) -> None: ...

class RemoveReadRuleRequest(_message.Message):
    __slots__ = ["consumer_name", "operation_params", "path"]
    CONSUMER_NAME_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    consumer_name: str
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., consumer_name: _Optional[str] = ...) -> None: ...

class RemoveReadRuleResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class RemoveReadRuleResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class SessionMetaValue(_message.Message):
    __slots__ = ["value"]
    class ValueEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: _containers.ScalarMap[str, str]
    def __init__(self, value: _Optional[_Mapping[str, str]] = ...) -> None: ...

class StreamingReadClientMessageNew(_message.Message):
    __slots__ = ["add_topic_request", "commit_request", "create_partition_stream_response", "destroy_partition_stream_response", "init_request", "partition_stream_status_request", "read_request", "remove_topic_request", "resume_read_request", "stop_read_request", "token"]
    class AddTopicRequest(_message.Message):
        __slots__ = ["topic_read_settings"]
        TOPIC_READ_SETTINGS_FIELD_NUMBER: _ClassVar[int]
        topic_read_settings: StreamingReadClientMessageNew.TopicReadSettings
        def __init__(self, topic_read_settings: _Optional[_Union[StreamingReadClientMessageNew.TopicReadSettings, _Mapping]] = ...) -> None: ...
    class CommitRequest(_message.Message):
        __slots__ = ["commits"]
        COMMITS_FIELD_NUMBER: _ClassVar[int]
        commits: _containers.RepeatedCompositeFieldContainer[StreamingReadClientMessageNew.PartitionCommit]
        def __init__(self, commits: _Optional[_Iterable[_Union[StreamingReadClientMessageNew.PartitionCommit, _Mapping]]] = ...) -> None: ...
    class CreatePartitionStreamResponse(_message.Message):
        __slots__ = ["commit_offset", "partition_stream_id", "read_offset", "verify_read_offset"]
        COMMIT_OFFSET_FIELD_NUMBER: _ClassVar[int]
        PARTITION_STREAM_ID_FIELD_NUMBER: _ClassVar[int]
        READ_OFFSET_FIELD_NUMBER: _ClassVar[int]
        VERIFY_READ_OFFSET_FIELD_NUMBER: _ClassVar[int]
        commit_offset: int
        partition_stream_id: int
        read_offset: int
        verify_read_offset: bool
        def __init__(self, partition_stream_id: _Optional[int] = ..., read_offset: _Optional[int] = ..., commit_offset: _Optional[int] = ..., verify_read_offset: bool = ...) -> None: ...
    class DestroyPartitionStreamResponse(_message.Message):
        __slots__ = ["partition_stream_id"]
        PARTITION_STREAM_ID_FIELD_NUMBER: _ClassVar[int]
        partition_stream_id: int
        def __init__(self, partition_stream_id: _Optional[int] = ...) -> None: ...
    class InitRequest(_message.Message):
        __slots__ = ["connection_attempt", "consumer", "idle_timeout_ms", "max_lag_duration_ms", "max_meta_cache_size", "max_supported_block_format_version", "read_only_original", "session_id", "start_from_written_at_ms", "state", "topics_read_settings"]
        class State(_message.Message):
            __slots__ = ["partition_streams_states"]
            class PartitionStreamState(_message.Message):
                __slots__ = ["offset_ranges", "partition_stream", "read_offset", "status"]
                class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                    __slots__ = []
                CREATING: StreamingReadClientMessageNew.InitRequest.State.PartitionStreamState.Status
                DESTROYING: StreamingReadClientMessageNew.InitRequest.State.PartitionStreamState.Status
                OFFSET_RANGES_FIELD_NUMBER: _ClassVar[int]
                PARTITION_STREAM_FIELD_NUMBER: _ClassVar[int]
                READING: StreamingReadClientMessageNew.InitRequest.State.PartitionStreamState.Status
                READ_OFFSET_FIELD_NUMBER: _ClassVar[int]
                STATUS_FIELD_NUMBER: _ClassVar[int]
                STATUS_UNSPECIFIED: StreamingReadClientMessageNew.InitRequest.State.PartitionStreamState.Status
                STOPPED: StreamingReadClientMessageNew.InitRequest.State.PartitionStreamState.Status
                offset_ranges: _containers.RepeatedCompositeFieldContainer[OffsetsRange]
                partition_stream: PartitionStream
                read_offset: int
                status: StreamingReadClientMessageNew.InitRequest.State.PartitionStreamState.Status
                def __init__(self, partition_stream: _Optional[_Union[PartitionStream, _Mapping]] = ..., read_offset: _Optional[int] = ..., offset_ranges: _Optional[_Iterable[_Union[OffsetsRange, _Mapping]]] = ..., status: _Optional[_Union[StreamingReadClientMessageNew.InitRequest.State.PartitionStreamState.Status, str]] = ...) -> None: ...
            PARTITION_STREAMS_STATES_FIELD_NUMBER: _ClassVar[int]
            partition_streams_states: _containers.RepeatedCompositeFieldContainer[StreamingReadClientMessageNew.InitRequest.State.PartitionStreamState]
            def __init__(self, partition_streams_states: _Optional[_Iterable[_Union[StreamingReadClientMessageNew.InitRequest.State.PartitionStreamState, _Mapping]]] = ...) -> None: ...
        CONNECTION_ATTEMPT_FIELD_NUMBER: _ClassVar[int]
        CONSUMER_FIELD_NUMBER: _ClassVar[int]
        IDLE_TIMEOUT_MS_FIELD_NUMBER: _ClassVar[int]
        MAX_LAG_DURATION_MS_FIELD_NUMBER: _ClassVar[int]
        MAX_META_CACHE_SIZE_FIELD_NUMBER: _ClassVar[int]
        MAX_SUPPORTED_BLOCK_FORMAT_VERSION_FIELD_NUMBER: _ClassVar[int]
        READ_ONLY_ORIGINAL_FIELD_NUMBER: _ClassVar[int]
        SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        START_FROM_WRITTEN_AT_MS_FIELD_NUMBER: _ClassVar[int]
        STATE_FIELD_NUMBER: _ClassVar[int]
        TOPICS_READ_SETTINGS_FIELD_NUMBER: _ClassVar[int]
        connection_attempt: int
        consumer: str
        idle_timeout_ms: int
        max_lag_duration_ms: int
        max_meta_cache_size: int
        max_supported_block_format_version: int
        read_only_original: bool
        session_id: str
        start_from_written_at_ms: int
        state: StreamingReadClientMessageNew.InitRequest.State
        topics_read_settings: _containers.RepeatedCompositeFieldContainer[StreamingReadClientMessageNew.TopicReadSettings]
        def __init__(self, topics_read_settings: _Optional[_Iterable[_Union[StreamingReadClientMessageNew.TopicReadSettings, _Mapping]]] = ..., read_only_original: bool = ..., consumer: _Optional[str] = ..., max_lag_duration_ms: _Optional[int] = ..., start_from_written_at_ms: _Optional[int] = ..., max_supported_block_format_version: _Optional[int] = ..., max_meta_cache_size: _Optional[int] = ..., session_id: _Optional[str] = ..., connection_attempt: _Optional[int] = ..., state: _Optional[_Union[StreamingReadClientMessageNew.InitRequest.State, _Mapping]] = ..., idle_timeout_ms: _Optional[int] = ...) -> None: ...
    class PartitionCommit(_message.Message):
        __slots__ = ["offsets", "partition_stream_id"]
        OFFSETS_FIELD_NUMBER: _ClassVar[int]
        PARTITION_STREAM_ID_FIELD_NUMBER: _ClassVar[int]
        offsets: _containers.RepeatedCompositeFieldContainer[OffsetsRange]
        partition_stream_id: int
        def __init__(self, partition_stream_id: _Optional[int] = ..., offsets: _Optional[_Iterable[_Union[OffsetsRange, _Mapping]]] = ...) -> None: ...
    class PartitionStreamStatusRequest(_message.Message):
        __slots__ = ["partition_stream_id"]
        PARTITION_STREAM_ID_FIELD_NUMBER: _ClassVar[int]
        partition_stream_id: int
        def __init__(self, partition_stream_id: _Optional[int] = ...) -> None: ...
    class ReadRequest(_message.Message):
        __slots__ = ["request_uncompressed_size"]
        REQUEST_UNCOMPRESSED_SIZE_FIELD_NUMBER: _ClassVar[int]
        request_uncompressed_size: int
        def __init__(self, request_uncompressed_size: _Optional[int] = ...) -> None: ...
    class RemoveTopicRequest(_message.Message):
        __slots__ = ["topic"]
        TOPIC_FIELD_NUMBER: _ClassVar[int]
        topic: str
        def __init__(self, topic: _Optional[str] = ...) -> None: ...
    class ResumeReadRequest(_message.Message):
        __slots__ = ["partition_stream_ids", "read_offsets", "resume_cookies"]
        PARTITION_STREAM_IDS_FIELD_NUMBER: _ClassVar[int]
        READ_OFFSETS_FIELD_NUMBER: _ClassVar[int]
        RESUME_COOKIES_FIELD_NUMBER: _ClassVar[int]
        partition_stream_ids: _containers.RepeatedScalarFieldContainer[int]
        read_offsets: _containers.RepeatedScalarFieldContainer[int]
        resume_cookies: _containers.RepeatedScalarFieldContainer[int]
        def __init__(self, partition_stream_ids: _Optional[_Iterable[int]] = ..., read_offsets: _Optional[_Iterable[int]] = ..., resume_cookies: _Optional[_Iterable[int]] = ...) -> None: ...
    class StopReadRequest(_message.Message):
        __slots__ = ["partition_stream_ids"]
        PARTITION_STREAM_IDS_FIELD_NUMBER: _ClassVar[int]
        partition_stream_ids: _containers.RepeatedScalarFieldContainer[int]
        def __init__(self, partition_stream_ids: _Optional[_Iterable[int]] = ...) -> None: ...
    class TopicReadSettings(_message.Message):
        __slots__ = ["partition_group_ids", "start_from_written_at_ms", "topic"]
        PARTITION_GROUP_IDS_FIELD_NUMBER: _ClassVar[int]
        START_FROM_WRITTEN_AT_MS_FIELD_NUMBER: _ClassVar[int]
        TOPIC_FIELD_NUMBER: _ClassVar[int]
        partition_group_ids: _containers.RepeatedScalarFieldContainer[int]
        start_from_written_at_ms: int
        topic: str
        def __init__(self, topic: _Optional[str] = ..., partition_group_ids: _Optional[_Iterable[int]] = ..., start_from_written_at_ms: _Optional[int] = ...) -> None: ...
    ADD_TOPIC_REQUEST_FIELD_NUMBER: _ClassVar[int]
    COMMIT_REQUEST_FIELD_NUMBER: _ClassVar[int]
    CREATE_PARTITION_STREAM_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    DESTROY_PARTITION_STREAM_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    INIT_REQUEST_FIELD_NUMBER: _ClassVar[int]
    PARTITION_STREAM_STATUS_REQUEST_FIELD_NUMBER: _ClassVar[int]
    READ_REQUEST_FIELD_NUMBER: _ClassVar[int]
    REMOVE_TOPIC_REQUEST_FIELD_NUMBER: _ClassVar[int]
    RESUME_READ_REQUEST_FIELD_NUMBER: _ClassVar[int]
    STOP_READ_REQUEST_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    add_topic_request: StreamingReadClientMessageNew.AddTopicRequest
    commit_request: StreamingReadClientMessageNew.CommitRequest
    create_partition_stream_response: StreamingReadClientMessageNew.CreatePartitionStreamResponse
    destroy_partition_stream_response: StreamingReadClientMessageNew.DestroyPartitionStreamResponse
    init_request: StreamingReadClientMessageNew.InitRequest
    partition_stream_status_request: StreamingReadClientMessageNew.PartitionStreamStatusRequest
    read_request: StreamingReadClientMessageNew.ReadRequest
    remove_topic_request: StreamingReadClientMessageNew.RemoveTopicRequest
    resume_read_request: StreamingReadClientMessageNew.ResumeReadRequest
    stop_read_request: StreamingReadClientMessageNew.StopReadRequest
    token: str
    def __init__(self, init_request: _Optional[_Union[StreamingReadClientMessageNew.InitRequest, _Mapping]] = ..., read_request: _Optional[_Union[StreamingReadClientMessageNew.ReadRequest, _Mapping]] = ..., create_partition_stream_response: _Optional[_Union[StreamingReadClientMessageNew.CreatePartitionStreamResponse, _Mapping]] = ..., commit_request: _Optional[_Union[StreamingReadClientMessageNew.CommitRequest, _Mapping]] = ..., destroy_partition_stream_response: _Optional[_Union[StreamingReadClientMessageNew.DestroyPartitionStreamResponse, _Mapping]] = ..., stop_read_request: _Optional[_Union[StreamingReadClientMessageNew.StopReadRequest, _Mapping]] = ..., resume_read_request: _Optional[_Union[StreamingReadClientMessageNew.ResumeReadRequest, _Mapping]] = ..., partition_stream_status_request: _Optional[_Union[StreamingReadClientMessageNew.PartitionStreamStatusRequest, _Mapping]] = ..., add_topic_request: _Optional[_Union[StreamingReadClientMessageNew.AddTopicRequest, _Mapping]] = ..., remove_topic_request: _Optional[_Union[StreamingReadClientMessageNew.RemoveTopicRequest, _Mapping]] = ..., token: _Optional[str] = ...) -> None: ...

class StreamingReadServerMessageNew(_message.Message):
    __slots__ = ["add_topic_response", "batch_read_response", "commit_response", "create_partition_stream_request", "destroy_partition_stream_request", "init_response", "issues", "partition_stream_status_response", "remove_topic_response", "resume_read_response", "status", "stop_read_response"]
    class AddTopicResponse(_message.Message):
        __slots__ = ["block_format_version"]
        BLOCK_FORMAT_VERSION_FIELD_NUMBER: _ClassVar[int]
        block_format_version: int
        def __init__(self, block_format_version: _Optional[int] = ...) -> None: ...
    class BatchReadResponse(_message.Message):
        __slots__ = ["partitions", "skip_range"]
        class PartitionData(_message.Message):
            __slots__ = ["blocks_data", "blocks_headers", "blocks_message_counts", "blocks_offsets", "blocks_part_numbers", "blocks_uncompressed_sizes", "created_at_ms", "ip_indexes", "ips", "message_group_id_indexes", "message_group_ids", "message_session_meta", "message_session_meta_indexes", "message_sizes", "offsets", "partition_stream_id", "read_statistics", "resume_cookie", "sequence_numbers", "written_at_ms"]
            class ReadStatistics(_message.Message):
                __slots__ = ["blobs_from_cache", "blobs_from_disk", "bytes_from_cache", "bytes_from_disk", "bytes_from_head", "repack_duration_ms"]
                BLOBS_FROM_CACHE_FIELD_NUMBER: _ClassVar[int]
                BLOBS_FROM_DISK_FIELD_NUMBER: _ClassVar[int]
                BYTES_FROM_CACHE_FIELD_NUMBER: _ClassVar[int]
                BYTES_FROM_DISK_FIELD_NUMBER: _ClassVar[int]
                BYTES_FROM_HEAD_FIELD_NUMBER: _ClassVar[int]
                REPACK_DURATION_MS_FIELD_NUMBER: _ClassVar[int]
                blobs_from_cache: int
                blobs_from_disk: int
                bytes_from_cache: int
                bytes_from_disk: int
                bytes_from_head: int
                repack_duration_ms: int
                def __init__(self, blobs_from_cache: _Optional[int] = ..., blobs_from_disk: _Optional[int] = ..., bytes_from_head: _Optional[int] = ..., bytes_from_cache: _Optional[int] = ..., bytes_from_disk: _Optional[int] = ..., repack_duration_ms: _Optional[int] = ...) -> None: ...
            BLOCKS_DATA_FIELD_NUMBER: _ClassVar[int]
            BLOCKS_HEADERS_FIELD_NUMBER: _ClassVar[int]
            BLOCKS_MESSAGE_COUNTS_FIELD_NUMBER: _ClassVar[int]
            BLOCKS_OFFSETS_FIELD_NUMBER: _ClassVar[int]
            BLOCKS_PART_NUMBERS_FIELD_NUMBER: _ClassVar[int]
            BLOCKS_UNCOMPRESSED_SIZES_FIELD_NUMBER: _ClassVar[int]
            CREATED_AT_MS_FIELD_NUMBER: _ClassVar[int]
            IPS_FIELD_NUMBER: _ClassVar[int]
            IP_INDEXES_FIELD_NUMBER: _ClassVar[int]
            MESSAGE_GROUP_IDS_FIELD_NUMBER: _ClassVar[int]
            MESSAGE_GROUP_ID_INDEXES_FIELD_NUMBER: _ClassVar[int]
            MESSAGE_SESSION_META_FIELD_NUMBER: _ClassVar[int]
            MESSAGE_SESSION_META_INDEXES_FIELD_NUMBER: _ClassVar[int]
            MESSAGE_SIZES_FIELD_NUMBER: _ClassVar[int]
            OFFSETS_FIELD_NUMBER: _ClassVar[int]
            PARTITION_STREAM_ID_FIELD_NUMBER: _ClassVar[int]
            READ_STATISTICS_FIELD_NUMBER: _ClassVar[int]
            RESUME_COOKIE_FIELD_NUMBER: _ClassVar[int]
            SEQUENCE_NUMBERS_FIELD_NUMBER: _ClassVar[int]
            WRITTEN_AT_MS_FIELD_NUMBER: _ClassVar[int]
            blocks_data: _containers.RepeatedScalarFieldContainer[bytes]
            blocks_headers: _containers.RepeatedScalarFieldContainer[bytes]
            blocks_message_counts: _containers.RepeatedScalarFieldContainer[int]
            blocks_offsets: _containers.RepeatedScalarFieldContainer[int]
            blocks_part_numbers: _containers.RepeatedScalarFieldContainer[int]
            blocks_uncompressed_sizes: _containers.RepeatedScalarFieldContainer[int]
            created_at_ms: _containers.RepeatedScalarFieldContainer[int]
            ip_indexes: _containers.RepeatedScalarFieldContainer[int]
            ips: _containers.RepeatedScalarFieldContainer[str]
            message_group_id_indexes: _containers.RepeatedScalarFieldContainer[int]
            message_group_ids: _containers.RepeatedScalarFieldContainer[str]
            message_session_meta: _containers.RepeatedCompositeFieldContainer[SessionMetaValue]
            message_session_meta_indexes: _containers.RepeatedScalarFieldContainer[int]
            message_sizes: _containers.RepeatedScalarFieldContainer[int]
            offsets: _containers.RepeatedScalarFieldContainer[int]
            partition_stream_id: int
            read_statistics: StreamingReadServerMessageNew.BatchReadResponse.PartitionData.ReadStatistics
            resume_cookie: int
            sequence_numbers: _containers.RepeatedScalarFieldContainer[int]
            written_at_ms: _containers.RepeatedScalarFieldContainer[int]
            def __init__(self, partition_stream_id: _Optional[int] = ..., offsets: _Optional[_Iterable[int]] = ..., sequence_numbers: _Optional[_Iterable[int]] = ..., created_at_ms: _Optional[_Iterable[int]] = ..., written_at_ms: _Optional[_Iterable[int]] = ..., message_group_ids: _Optional[_Iterable[str]] = ..., message_group_id_indexes: _Optional[_Iterable[int]] = ..., ips: _Optional[_Iterable[str]] = ..., ip_indexes: _Optional[_Iterable[int]] = ..., message_session_meta: _Optional[_Iterable[_Union[SessionMetaValue, _Mapping]]] = ..., message_session_meta_indexes: _Optional[_Iterable[int]] = ..., message_sizes: _Optional[_Iterable[int]] = ..., blocks_offsets: _Optional[_Iterable[int]] = ..., blocks_part_numbers: _Optional[_Iterable[int]] = ..., blocks_message_counts: _Optional[_Iterable[int]] = ..., blocks_uncompressed_sizes: _Optional[_Iterable[int]] = ..., blocks_headers: _Optional[_Iterable[bytes]] = ..., blocks_data: _Optional[_Iterable[bytes]] = ..., resume_cookie: _Optional[int] = ..., read_statistics: _Optional[_Union[StreamingReadServerMessageNew.BatchReadResponse.PartitionData.ReadStatistics, _Mapping]] = ...) -> None: ...
        class SkipRange(_message.Message):
            __slots__ = ["partition_stream_id", "skip_range"]
            PARTITION_STREAM_ID_FIELD_NUMBER: _ClassVar[int]
            SKIP_RANGE_FIELD_NUMBER: _ClassVar[int]
            partition_stream_id: int
            skip_range: OffsetsRange
            def __init__(self, partition_stream_id: _Optional[int] = ..., skip_range: _Optional[_Union[OffsetsRange, _Mapping]] = ...) -> None: ...
        PARTITIONS_FIELD_NUMBER: _ClassVar[int]
        SKIP_RANGE_FIELD_NUMBER: _ClassVar[int]
        partitions: _containers.RepeatedCompositeFieldContainer[StreamingReadServerMessageNew.BatchReadResponse.PartitionData]
        skip_range: _containers.RepeatedCompositeFieldContainer[StreamingReadServerMessageNew.BatchReadResponse.SkipRange]
        def __init__(self, skip_range: _Optional[_Iterable[_Union[StreamingReadServerMessageNew.BatchReadResponse.SkipRange, _Mapping]]] = ..., partitions: _Optional[_Iterable[_Union[StreamingReadServerMessageNew.BatchReadResponse.PartitionData, _Mapping]]] = ...) -> None: ...
    class CommitResponse(_message.Message):
        __slots__ = ["partitions_committed_offsets"]
        class PartitionCommittedOffset(_message.Message):
            __slots__ = ["committed_offset", "partition_stream_id"]
            COMMITTED_OFFSET_FIELD_NUMBER: _ClassVar[int]
            PARTITION_STREAM_ID_FIELD_NUMBER: _ClassVar[int]
            committed_offset: int
            partition_stream_id: int
            def __init__(self, partition_stream_id: _Optional[int] = ..., committed_offset: _Optional[int] = ...) -> None: ...
        PARTITIONS_COMMITTED_OFFSETS_FIELD_NUMBER: _ClassVar[int]
        partitions_committed_offsets: _containers.RepeatedCompositeFieldContainer[StreamingReadServerMessageNew.CommitResponse.PartitionCommittedOffset]
        def __init__(self, partitions_committed_offsets: _Optional[_Iterable[_Union[StreamingReadServerMessageNew.CommitResponse.PartitionCommittedOffset, _Mapping]]] = ...) -> None: ...
    class CreatePartitionStreamRequest(_message.Message):
        __slots__ = ["committed_offset", "end_offset", "partition_stream"]
        COMMITTED_OFFSET_FIELD_NUMBER: _ClassVar[int]
        END_OFFSET_FIELD_NUMBER: _ClassVar[int]
        PARTITION_STREAM_FIELD_NUMBER: _ClassVar[int]
        committed_offset: int
        end_offset: int
        partition_stream: PartitionStream
        def __init__(self, partition_stream: _Optional[_Union[PartitionStream, _Mapping]] = ..., committed_offset: _Optional[int] = ..., end_offset: _Optional[int] = ...) -> None: ...
    class DestroyPartitionStreamRequest(_message.Message):
        __slots__ = ["committed_offset", "graceful", "partition_stream_id"]
        COMMITTED_OFFSET_FIELD_NUMBER: _ClassVar[int]
        GRACEFUL_FIELD_NUMBER: _ClassVar[int]
        PARTITION_STREAM_ID_FIELD_NUMBER: _ClassVar[int]
        committed_offset: int
        graceful: bool
        partition_stream_id: int
        def __init__(self, partition_stream_id: _Optional[int] = ..., graceful: bool = ..., committed_offset: _Optional[int] = ...) -> None: ...
    class InitResponse(_message.Message):
        __slots__ = ["block_format_version_by_topic", "max_meta_cache_size", "session_id"]
        class BlockFormatVersionByTopicEntry(_message.Message):
            __slots__ = ["key", "value"]
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: int
            def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
        BLOCK_FORMAT_VERSION_BY_TOPIC_FIELD_NUMBER: _ClassVar[int]
        MAX_META_CACHE_SIZE_FIELD_NUMBER: _ClassVar[int]
        SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        block_format_version_by_topic: _containers.ScalarMap[str, int]
        max_meta_cache_size: int
        session_id: str
        def __init__(self, session_id: _Optional[str] = ..., block_format_version_by_topic: _Optional[_Mapping[str, int]] = ..., max_meta_cache_size: _Optional[int] = ...) -> None: ...
    class PartitionStreamStatusResponse(_message.Message):
        __slots__ = ["committed_offset", "end_offset", "partition_stream_id", "written_at_watermark_ms"]
        COMMITTED_OFFSET_FIELD_NUMBER: _ClassVar[int]
        END_OFFSET_FIELD_NUMBER: _ClassVar[int]
        PARTITION_STREAM_ID_FIELD_NUMBER: _ClassVar[int]
        WRITTEN_AT_WATERMARK_MS_FIELD_NUMBER: _ClassVar[int]
        committed_offset: int
        end_offset: int
        partition_stream_id: int
        written_at_watermark_ms: int
        def __init__(self, partition_stream_id: _Optional[int] = ..., committed_offset: _Optional[int] = ..., end_offset: _Optional[int] = ..., written_at_watermark_ms: _Optional[int] = ...) -> None: ...
    class RemoveTopicResponse(_message.Message):
        __slots__ = []
        def __init__(self) -> None: ...
    class ResumeReadResponse(_message.Message):
        __slots__ = []
        def __init__(self) -> None: ...
    class StopReadResponse(_message.Message):
        __slots__ = []
        def __init__(self) -> None: ...
    ADD_TOPIC_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    BATCH_READ_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    COMMIT_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    CREATE_PARTITION_STREAM_REQUEST_FIELD_NUMBER: _ClassVar[int]
    DESTROY_PARTITION_STREAM_REQUEST_FIELD_NUMBER: _ClassVar[int]
    INIT_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    PARTITION_STREAM_STATUS_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    REMOVE_TOPIC_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    RESUME_READ_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    STOP_READ_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    add_topic_response: StreamingReadServerMessageNew.AddTopicResponse
    batch_read_response: StreamingReadServerMessageNew.BatchReadResponse
    commit_response: StreamingReadServerMessageNew.CommitResponse
    create_partition_stream_request: StreamingReadServerMessageNew.CreatePartitionStreamRequest
    destroy_partition_stream_request: StreamingReadServerMessageNew.DestroyPartitionStreamRequest
    init_response: StreamingReadServerMessageNew.InitResponse
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    partition_stream_status_response: StreamingReadServerMessageNew.PartitionStreamStatusResponse
    remove_topic_response: StreamingReadServerMessageNew.RemoveTopicResponse
    resume_read_response: StreamingReadServerMessageNew.ResumeReadResponse
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    stop_read_response: StreamingReadServerMessageNew.StopReadResponse
    def __init__(self, init_response: _Optional[_Union[StreamingReadServerMessageNew.InitResponse, _Mapping]] = ..., batch_read_response: _Optional[_Union[StreamingReadServerMessageNew.BatchReadResponse, _Mapping]] = ..., create_partition_stream_request: _Optional[_Union[StreamingReadServerMessageNew.CreatePartitionStreamRequest, _Mapping]] = ..., destroy_partition_stream_request: _Optional[_Union[StreamingReadServerMessageNew.DestroyPartitionStreamRequest, _Mapping]] = ..., commit_response: _Optional[_Union[StreamingReadServerMessageNew.CommitResponse, _Mapping]] = ..., partition_stream_status_response: _Optional[_Union[StreamingReadServerMessageNew.PartitionStreamStatusResponse, _Mapping]] = ..., stop_read_response: _Optional[_Union[StreamingReadServerMessageNew.StopReadResponse, _Mapping]] = ..., resume_read_response: _Optional[_Union[StreamingReadServerMessageNew.ResumeReadResponse, _Mapping]] = ..., add_topic_response: _Optional[_Union[StreamingReadServerMessageNew.AddTopicResponse, _Mapping]] = ..., remove_topic_response: _Optional[_Union[StreamingReadServerMessageNew.RemoveTopicResponse, _Mapping]] = ..., status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ...) -> None: ...

class StreamingWriteClientMessage(_message.Message):
    __slots__ = ["init_request", "update_token_request", "write_request"]
    class InitRequest(_message.Message):
        __slots__ = ["connection_attempt", "connection_meta", "idle_timeout_ms", "max_supported_block_format_version", "message_group_id", "partition_group_id", "preferred_cluster", "session_id", "session_meta", "topic"]
        class SessionMetaEntry(_message.Message):
            __slots__ = ["key", "value"]
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        CONNECTION_ATTEMPT_FIELD_NUMBER: _ClassVar[int]
        CONNECTION_META_FIELD_NUMBER: _ClassVar[int]
        IDLE_TIMEOUT_MS_FIELD_NUMBER: _ClassVar[int]
        MAX_SUPPORTED_BLOCK_FORMAT_VERSION_FIELD_NUMBER: _ClassVar[int]
        MESSAGE_GROUP_ID_FIELD_NUMBER: _ClassVar[int]
        PARTITION_GROUP_ID_FIELD_NUMBER: _ClassVar[int]
        PREFERRED_CLUSTER_FIELD_NUMBER: _ClassVar[int]
        SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        SESSION_META_FIELD_NUMBER: _ClassVar[int]
        TOPIC_FIELD_NUMBER: _ClassVar[int]
        connection_attempt: int
        connection_meta: bytes
        idle_timeout_ms: int
        max_supported_block_format_version: int
        message_group_id: str
        partition_group_id: int
        preferred_cluster: str
        session_id: str
        session_meta: _containers.ScalarMap[str, str]
        topic: str
        def __init__(self, topic: _Optional[str] = ..., message_group_id: _Optional[str] = ..., session_meta: _Optional[_Mapping[str, str]] = ..., partition_group_id: _Optional[int] = ..., max_supported_block_format_version: _Optional[int] = ..., session_id: _Optional[str] = ..., connection_attempt: _Optional[int] = ..., connection_meta: _Optional[bytes] = ..., preferred_cluster: _Optional[str] = ..., idle_timeout_ms: _Optional[int] = ...) -> None: ...
    class UpdateTokenRequest(_message.Message):
        __slots__ = ["token"]
        TOKEN_FIELD_NUMBER: _ClassVar[int]
        token: str
        def __init__(self, token: _Optional[str] = ...) -> None: ...
    class WriteRequest(_message.Message):
        __slots__ = ["blocks_data", "blocks_headers", "blocks_message_counts", "blocks_offsets", "blocks_part_numbers", "blocks_uncompressed_sizes", "created_at_ms", "message_sizes", "sent_at_ms", "sequence_numbers"]
        BLOCKS_DATA_FIELD_NUMBER: _ClassVar[int]
        BLOCKS_HEADERS_FIELD_NUMBER: _ClassVar[int]
        BLOCKS_MESSAGE_COUNTS_FIELD_NUMBER: _ClassVar[int]
        BLOCKS_OFFSETS_FIELD_NUMBER: _ClassVar[int]
        BLOCKS_PART_NUMBERS_FIELD_NUMBER: _ClassVar[int]
        BLOCKS_UNCOMPRESSED_SIZES_FIELD_NUMBER: _ClassVar[int]
        CREATED_AT_MS_FIELD_NUMBER: _ClassVar[int]
        MESSAGE_SIZES_FIELD_NUMBER: _ClassVar[int]
        SENT_AT_MS_FIELD_NUMBER: _ClassVar[int]
        SEQUENCE_NUMBERS_FIELD_NUMBER: _ClassVar[int]
        blocks_data: _containers.RepeatedScalarFieldContainer[bytes]
        blocks_headers: _containers.RepeatedScalarFieldContainer[bytes]
        blocks_message_counts: _containers.RepeatedScalarFieldContainer[int]
        blocks_offsets: _containers.RepeatedScalarFieldContainer[int]
        blocks_part_numbers: _containers.RepeatedScalarFieldContainer[int]
        blocks_uncompressed_sizes: _containers.RepeatedScalarFieldContainer[int]
        created_at_ms: _containers.RepeatedScalarFieldContainer[int]
        message_sizes: _containers.RepeatedScalarFieldContainer[int]
        sent_at_ms: _containers.RepeatedScalarFieldContainer[int]
        sequence_numbers: _containers.RepeatedScalarFieldContainer[int]
        def __init__(self, sequence_numbers: _Optional[_Iterable[int]] = ..., created_at_ms: _Optional[_Iterable[int]] = ..., sent_at_ms: _Optional[_Iterable[int]] = ..., message_sizes: _Optional[_Iterable[int]] = ..., blocks_offsets: _Optional[_Iterable[int]] = ..., blocks_part_numbers: _Optional[_Iterable[int]] = ..., blocks_message_counts: _Optional[_Iterable[int]] = ..., blocks_uncompressed_sizes: _Optional[_Iterable[int]] = ..., blocks_headers: _Optional[_Iterable[bytes]] = ..., blocks_data: _Optional[_Iterable[bytes]] = ...) -> None: ...
    INIT_REQUEST_FIELD_NUMBER: _ClassVar[int]
    UPDATE_TOKEN_REQUEST_FIELD_NUMBER: _ClassVar[int]
    WRITE_REQUEST_FIELD_NUMBER: _ClassVar[int]
    init_request: StreamingWriteClientMessage.InitRequest
    update_token_request: StreamingWriteClientMessage.UpdateTokenRequest
    write_request: StreamingWriteClientMessage.WriteRequest
    def __init__(self, init_request: _Optional[_Union[StreamingWriteClientMessage.InitRequest, _Mapping]] = ..., write_request: _Optional[_Union[StreamingWriteClientMessage.WriteRequest, _Mapping]] = ..., update_token_request: _Optional[_Union[StreamingWriteClientMessage.UpdateTokenRequest, _Mapping]] = ...) -> None: ...

class StreamingWriteServerMessage(_message.Message):
    __slots__ = ["batch_write_response", "init_response", "issues", "status", "update_token_response"]
    class BatchWriteResponse(_message.Message):
        __slots__ = ["already_written", "offsets", "partition_id", "sequence_numbers", "write_statistics"]
        ALREADY_WRITTEN_FIELD_NUMBER: _ClassVar[int]
        OFFSETS_FIELD_NUMBER: _ClassVar[int]
        PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
        SEQUENCE_NUMBERS_FIELD_NUMBER: _ClassVar[int]
        WRITE_STATISTICS_FIELD_NUMBER: _ClassVar[int]
        already_written: _containers.RepeatedScalarFieldContainer[bool]
        offsets: _containers.RepeatedScalarFieldContainer[int]
        partition_id: int
        sequence_numbers: _containers.RepeatedScalarFieldContainer[int]
        write_statistics: StreamingWriteServerMessage.WriteStatistics
        def __init__(self, sequence_numbers: _Optional[_Iterable[int]] = ..., offsets: _Optional[_Iterable[int]] = ..., already_written: _Optional[_Iterable[bool]] = ..., partition_id: _Optional[int] = ..., write_statistics: _Optional[_Union[StreamingWriteServerMessage.WriteStatistics, _Mapping]] = ...) -> None: ...
    class InitResponse(_message.Message):
        __slots__ = ["block_format_version", "cluster", "connection_meta", "last_sequence_number", "max_block_size", "max_flush_window_size", "partition_id", "session_id", "supported_codecs", "topic"]
        BLOCK_FORMAT_VERSION_FIELD_NUMBER: _ClassVar[int]
        CLUSTER_FIELD_NUMBER: _ClassVar[int]
        CONNECTION_META_FIELD_NUMBER: _ClassVar[int]
        LAST_SEQUENCE_NUMBER_FIELD_NUMBER: _ClassVar[int]
        MAX_BLOCK_SIZE_FIELD_NUMBER: _ClassVar[int]
        MAX_FLUSH_WINDOW_SIZE_FIELD_NUMBER: _ClassVar[int]
        PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
        SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        SUPPORTED_CODECS_FIELD_NUMBER: _ClassVar[int]
        TOPIC_FIELD_NUMBER: _ClassVar[int]
        block_format_version: int
        cluster: str
        connection_meta: bytes
        last_sequence_number: int
        max_block_size: int
        max_flush_window_size: int
        partition_id: int
        session_id: str
        supported_codecs: _containers.RepeatedScalarFieldContainer[Codec]
        topic: str
        def __init__(self, last_sequence_number: _Optional[int] = ..., session_id: _Optional[str] = ..., topic: _Optional[str] = ..., cluster: _Optional[str] = ..., partition_id: _Optional[int] = ..., block_format_version: _Optional[int] = ..., supported_codecs: _Optional[_Iterable[_Union[Codec, str]]] = ..., max_flush_window_size: _Optional[int] = ..., max_block_size: _Optional[int] = ..., connection_meta: _Optional[bytes] = ...) -> None: ...
    class UpdateTokenResponse(_message.Message):
        __slots__ = []
        def __init__(self) -> None: ...
    class WriteStatistics(_message.Message):
        __slots__ = ["persist_duration_ms", "queued_in_partition_duration_ms", "throttled_on_partition_duration_ms", "throttled_on_topic_duration_ms"]
        PERSIST_DURATION_MS_FIELD_NUMBER: _ClassVar[int]
        QUEUED_IN_PARTITION_DURATION_MS_FIELD_NUMBER: _ClassVar[int]
        THROTTLED_ON_PARTITION_DURATION_MS_FIELD_NUMBER: _ClassVar[int]
        THROTTLED_ON_TOPIC_DURATION_MS_FIELD_NUMBER: _ClassVar[int]
        persist_duration_ms: int
        queued_in_partition_duration_ms: int
        throttled_on_partition_duration_ms: int
        throttled_on_topic_duration_ms: int
        def __init__(self, persist_duration_ms: _Optional[int] = ..., queued_in_partition_duration_ms: _Optional[int] = ..., throttled_on_partition_duration_ms: _Optional[int] = ..., throttled_on_topic_duration_ms: _Optional[int] = ...) -> None: ...
    BATCH_WRITE_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    INIT_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    UPDATE_TOKEN_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    batch_write_response: StreamingWriteServerMessage.BatchWriteResponse
    init_response: StreamingWriteServerMessage.InitResponse
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    update_token_response: StreamingWriteServerMessage.UpdateTokenResponse
    def __init__(self, init_response: _Optional[_Union[StreamingWriteServerMessage.InitResponse, _Mapping]] = ..., batch_write_response: _Optional[_Union[StreamingWriteServerMessage.BatchWriteResponse, _Mapping]] = ..., update_token_response: _Optional[_Union[StreamingWriteServerMessage.UpdateTokenResponse, _Mapping]] = ..., status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ...) -> None: ...

class TopicSettings(_message.Message):
    __slots__ = ["attributes", "client_write_disabled", "max_partition_message_groups_seqno_stored", "max_partition_storage_size", "max_partition_write_burst", "max_partition_write_speed", "message_group_seqno_retention_period_ms", "partitions_count", "read_rules", "remote_mirror_rule", "retention_period_ms", "supported_codecs", "supported_format"]
    class Format(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    class AttributesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class ReadRule(_message.Message):
        __slots__ = ["consumer_name", "important", "service_type", "starting_message_timestamp_ms", "supported_codecs", "supported_format", "version"]
        CONSUMER_NAME_FIELD_NUMBER: _ClassVar[int]
        IMPORTANT_FIELD_NUMBER: _ClassVar[int]
        SERVICE_TYPE_FIELD_NUMBER: _ClassVar[int]
        STARTING_MESSAGE_TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
        SUPPORTED_CODECS_FIELD_NUMBER: _ClassVar[int]
        SUPPORTED_FORMAT_FIELD_NUMBER: _ClassVar[int]
        VERSION_FIELD_NUMBER: _ClassVar[int]
        consumer_name: str
        important: bool
        service_type: str
        starting_message_timestamp_ms: int
        supported_codecs: _containers.RepeatedScalarFieldContainer[Codec]
        supported_format: TopicSettings.Format
        version: int
        def __init__(self, consumer_name: _Optional[str] = ..., important: bool = ..., starting_message_timestamp_ms: _Optional[int] = ..., supported_format: _Optional[_Union[TopicSettings.Format, str]] = ..., supported_codecs: _Optional[_Iterable[_Union[Codec, str]]] = ..., version: _Optional[int] = ..., service_type: _Optional[str] = ...) -> None: ...
    class RemoteMirrorRule(_message.Message):
        __slots__ = ["consumer_name", "credentials", "database", "endpoint", "starting_message_timestamp_ms", "topic_path"]
        CONSUMER_NAME_FIELD_NUMBER: _ClassVar[int]
        CREDENTIALS_FIELD_NUMBER: _ClassVar[int]
        DATABASE_FIELD_NUMBER: _ClassVar[int]
        ENDPOINT_FIELD_NUMBER: _ClassVar[int]
        STARTING_MESSAGE_TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
        TOPIC_PATH_FIELD_NUMBER: _ClassVar[int]
        consumer_name: str
        credentials: Credentials
        database: str
        endpoint: str
        starting_message_timestamp_ms: int
        topic_path: str
        def __init__(self, endpoint: _Optional[str] = ..., topic_path: _Optional[str] = ..., consumer_name: _Optional[str] = ..., credentials: _Optional[_Union[Credentials, _Mapping]] = ..., starting_message_timestamp_ms: _Optional[int] = ..., database: _Optional[str] = ...) -> None: ...
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    CLIENT_WRITE_DISABLED_FIELD_NUMBER: _ClassVar[int]
    FORMAT_BASE: TopicSettings.Format
    FORMAT_UNSPECIFIED: TopicSettings.Format
    MAX_PARTITION_MESSAGE_GROUPS_SEQNO_STORED_FIELD_NUMBER: _ClassVar[int]
    MAX_PARTITION_STORAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    MAX_PARTITION_WRITE_BURST_FIELD_NUMBER: _ClassVar[int]
    MAX_PARTITION_WRITE_SPEED_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_GROUP_SEQNO_RETENTION_PERIOD_MS_FIELD_NUMBER: _ClassVar[int]
    PARTITIONS_COUNT_FIELD_NUMBER: _ClassVar[int]
    READ_RULES_FIELD_NUMBER: _ClassVar[int]
    REMOTE_MIRROR_RULE_FIELD_NUMBER: _ClassVar[int]
    RETENTION_PERIOD_MS_FIELD_NUMBER: _ClassVar[int]
    SUPPORTED_CODECS_FIELD_NUMBER: _ClassVar[int]
    SUPPORTED_FORMAT_FIELD_NUMBER: _ClassVar[int]
    attributes: _containers.ScalarMap[str, str]
    client_write_disabled: bool
    max_partition_message_groups_seqno_stored: int
    max_partition_storage_size: int
    max_partition_write_burst: int
    max_partition_write_speed: int
    message_group_seqno_retention_period_ms: int
    partitions_count: int
    read_rules: _containers.RepeatedCompositeFieldContainer[TopicSettings.ReadRule]
    remote_mirror_rule: TopicSettings.RemoteMirrorRule
    retention_period_ms: int
    supported_codecs: _containers.RepeatedScalarFieldContainer[Codec]
    supported_format: TopicSettings.Format
    def __init__(self, partitions_count: _Optional[int] = ..., retention_period_ms: _Optional[int] = ..., message_group_seqno_retention_period_ms: _Optional[int] = ..., max_partition_message_groups_seqno_stored: _Optional[int] = ..., supported_format: _Optional[_Union[TopicSettings.Format, str]] = ..., supported_codecs: _Optional[_Iterable[_Union[Codec, str]]] = ..., max_partition_storage_size: _Optional[int] = ..., max_partition_write_speed: _Optional[int] = ..., max_partition_write_burst: _Optional[int] = ..., client_write_disabled: bool = ..., read_rules: _Optional[_Iterable[_Union[TopicSettings.ReadRule, _Mapping]]] = ..., attributes: _Optional[_Mapping[str, str]] = ..., remote_mirror_rule: _Optional[_Union[TopicSettings.RemoteMirrorRule, _Mapping]] = ...) -> None: ...

class Codec(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
