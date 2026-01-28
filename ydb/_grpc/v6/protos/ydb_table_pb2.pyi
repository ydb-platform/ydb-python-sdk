import datetime

from protos.annotations import validation_pb2 as _validation_pb2
from protos import ydb_common_pb2 as _ydb_common_pb2
from protos import ydb_issue_message_pb2 as _ydb_issue_message_pb2
from protos import ydb_operation_pb2 as _ydb_operation_pb2
from protos import ydb_query_stats_pb2 as _ydb_query_stats_pb2
from protos import ydb_value_pb2 as _ydb_value_pb2
from protos import ydb_scheme_pb2 as _ydb_scheme_pb2
from protos import ydb_status_codes_pb2 as _ydb_status_codes_pb2
from protos import ydb_topic_pb2 as _ydb_topic_pb2
from protos import ydb_formats_pb2 as _ydb_formats_pb2
from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class StoreType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    STORE_TYPE_UNSPECIFIED: _ClassVar[StoreType]
    STORE_TYPE_ROW: _ClassVar[StoreType]
    STORE_TYPE_COLUMN: _ClassVar[StoreType]
STORE_TYPE_UNSPECIFIED: StoreType
STORE_TYPE_ROW: StoreType
STORE_TYPE_COLUMN: StoreType

class CreateSessionRequest(_message.Message):
    __slots__ = ("operation_params",)
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class CreateSessionResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class CreateSessionResult(_message.Message):
    __slots__ = ("session_id",)
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    def __init__(self, session_id: _Optional[str] = ...) -> None: ...

class DeleteSessionRequest(_message.Message):
    __slots__ = ("session_id", "operation_params")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, session_id: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class DeleteSessionResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class GlobalIndex(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GlobalAsyncIndex(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GlobalUniqueIndex(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class TableIndex(_message.Message):
    __slots__ = ("name", "index_columns", "global_index", "global_async_index", "global_unique_index", "data_columns")
    NAME_FIELD_NUMBER: _ClassVar[int]
    INDEX_COLUMNS_FIELD_NUMBER: _ClassVar[int]
    GLOBAL_INDEX_FIELD_NUMBER: _ClassVar[int]
    GLOBAL_ASYNC_INDEX_FIELD_NUMBER: _ClassVar[int]
    GLOBAL_UNIQUE_INDEX_FIELD_NUMBER: _ClassVar[int]
    DATA_COLUMNS_FIELD_NUMBER: _ClassVar[int]
    name: str
    index_columns: _containers.RepeatedScalarFieldContainer[str]
    global_index: GlobalIndex
    global_async_index: GlobalAsyncIndex
    global_unique_index: GlobalUniqueIndex
    data_columns: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, name: _Optional[str] = ..., index_columns: _Optional[_Iterable[str]] = ..., global_index: _Optional[_Union[GlobalIndex, _Mapping]] = ..., global_async_index: _Optional[_Union[GlobalAsyncIndex, _Mapping]] = ..., global_unique_index: _Optional[_Union[GlobalUniqueIndex, _Mapping]] = ..., data_columns: _Optional[_Iterable[str]] = ...) -> None: ...

class TableIndexDescription(_message.Message):
    __slots__ = ("name", "index_columns", "global_index", "global_async_index", "global_unique_index", "status", "data_columns", "size_bytes")
    class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        STATUS_UNSPECIFIED: _ClassVar[TableIndexDescription.Status]
        STATUS_READY: _ClassVar[TableIndexDescription.Status]
        STATUS_BUILDING: _ClassVar[TableIndexDescription.Status]
    STATUS_UNSPECIFIED: TableIndexDescription.Status
    STATUS_READY: TableIndexDescription.Status
    STATUS_BUILDING: TableIndexDescription.Status
    NAME_FIELD_NUMBER: _ClassVar[int]
    INDEX_COLUMNS_FIELD_NUMBER: _ClassVar[int]
    GLOBAL_INDEX_FIELD_NUMBER: _ClassVar[int]
    GLOBAL_ASYNC_INDEX_FIELD_NUMBER: _ClassVar[int]
    GLOBAL_UNIQUE_INDEX_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    DATA_COLUMNS_FIELD_NUMBER: _ClassVar[int]
    SIZE_BYTES_FIELD_NUMBER: _ClassVar[int]
    name: str
    index_columns: _containers.RepeatedScalarFieldContainer[str]
    global_index: GlobalIndex
    global_async_index: GlobalAsyncIndex
    global_unique_index: GlobalUniqueIndex
    status: TableIndexDescription.Status
    data_columns: _containers.RepeatedScalarFieldContainer[str]
    size_bytes: int
    def __init__(self, name: _Optional[str] = ..., index_columns: _Optional[_Iterable[str]] = ..., global_index: _Optional[_Union[GlobalIndex, _Mapping]] = ..., global_async_index: _Optional[_Union[GlobalAsyncIndex, _Mapping]] = ..., global_unique_index: _Optional[_Union[GlobalUniqueIndex, _Mapping]] = ..., status: _Optional[_Union[TableIndexDescription.Status, str]] = ..., data_columns: _Optional[_Iterable[str]] = ..., size_bytes: _Optional[int] = ...) -> None: ...

class IndexBuildState(_message.Message):
    __slots__ = ()
    class State(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        STATE_UNSPECIFIED: _ClassVar[IndexBuildState.State]
        STATE_PREPARING: _ClassVar[IndexBuildState.State]
        STATE_TRANSFERING_DATA: _ClassVar[IndexBuildState.State]
        STATE_APPLYING: _ClassVar[IndexBuildState.State]
        STATE_DONE: _ClassVar[IndexBuildState.State]
        STATE_CANCELLATION: _ClassVar[IndexBuildState.State]
        STATE_CANCELLED: _ClassVar[IndexBuildState.State]
        STATE_REJECTION: _ClassVar[IndexBuildState.State]
        STATE_REJECTED: _ClassVar[IndexBuildState.State]
    STATE_UNSPECIFIED: IndexBuildState.State
    STATE_PREPARING: IndexBuildState.State
    STATE_TRANSFERING_DATA: IndexBuildState.State
    STATE_APPLYING: IndexBuildState.State
    STATE_DONE: IndexBuildState.State
    STATE_CANCELLATION: IndexBuildState.State
    STATE_CANCELLED: IndexBuildState.State
    STATE_REJECTION: IndexBuildState.State
    STATE_REJECTED: IndexBuildState.State
    def __init__(self) -> None: ...

class IndexBuildDescription(_message.Message):
    __slots__ = ("path", "index")
    PATH_FIELD_NUMBER: _ClassVar[int]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    path: str
    index: TableIndex
    def __init__(self, path: _Optional[str] = ..., index: _Optional[_Union[TableIndex, _Mapping]] = ...) -> None: ...

class IndexBuildMetadata(_message.Message):
    __slots__ = ("description", "state", "progress")
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    description: IndexBuildDescription
    state: IndexBuildState.State
    progress: float
    def __init__(self, description: _Optional[_Union[IndexBuildDescription, _Mapping]] = ..., state: _Optional[_Union[IndexBuildState.State, str]] = ..., progress: _Optional[float] = ...) -> None: ...

class ChangefeedMode(_message.Message):
    __slots__ = ()
    class Mode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        MODE_UNSPECIFIED: _ClassVar[ChangefeedMode.Mode]
        MODE_KEYS_ONLY: _ClassVar[ChangefeedMode.Mode]
        MODE_UPDATES: _ClassVar[ChangefeedMode.Mode]
        MODE_NEW_IMAGE: _ClassVar[ChangefeedMode.Mode]
        MODE_OLD_IMAGE: _ClassVar[ChangefeedMode.Mode]
        MODE_NEW_AND_OLD_IMAGES: _ClassVar[ChangefeedMode.Mode]
    MODE_UNSPECIFIED: ChangefeedMode.Mode
    MODE_KEYS_ONLY: ChangefeedMode.Mode
    MODE_UPDATES: ChangefeedMode.Mode
    MODE_NEW_IMAGE: ChangefeedMode.Mode
    MODE_OLD_IMAGE: ChangefeedMode.Mode
    MODE_NEW_AND_OLD_IMAGES: ChangefeedMode.Mode
    def __init__(self) -> None: ...

class ChangefeedFormat(_message.Message):
    __slots__ = ()
    class Format(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        FORMAT_UNSPECIFIED: _ClassVar[ChangefeedFormat.Format]
        FORMAT_JSON: _ClassVar[ChangefeedFormat.Format]
        FORMAT_DYNAMODB_STREAMS_JSON: _ClassVar[ChangefeedFormat.Format]
        FORMAT_DEBEZIUM_JSON: _ClassVar[ChangefeedFormat.Format]
    FORMAT_UNSPECIFIED: ChangefeedFormat.Format
    FORMAT_JSON: ChangefeedFormat.Format
    FORMAT_DYNAMODB_STREAMS_JSON: ChangefeedFormat.Format
    FORMAT_DEBEZIUM_JSON: ChangefeedFormat.Format
    def __init__(self) -> None: ...

class Changefeed(_message.Message):
    __slots__ = ("name", "mode", "format", "retention_period", "virtual_timestamps", "initial_scan", "attributes", "aws_region", "resolved_timestamps_interval", "topic_partitioning_settings")
    class AttributesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    RETENTION_PERIOD_FIELD_NUMBER: _ClassVar[int]
    VIRTUAL_TIMESTAMPS_FIELD_NUMBER: _ClassVar[int]
    INITIAL_SCAN_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    AWS_REGION_FIELD_NUMBER: _ClassVar[int]
    RESOLVED_TIMESTAMPS_INTERVAL_FIELD_NUMBER: _ClassVar[int]
    TOPIC_PARTITIONING_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    name: str
    mode: ChangefeedMode.Mode
    format: ChangefeedFormat.Format
    retention_period: _duration_pb2.Duration
    virtual_timestamps: bool
    initial_scan: bool
    attributes: _containers.ScalarMap[str, str]
    aws_region: str
    resolved_timestamps_interval: _duration_pb2.Duration
    topic_partitioning_settings: _ydb_topic_pb2.PartitioningSettings
    def __init__(self, name: _Optional[str] = ..., mode: _Optional[_Union[ChangefeedMode.Mode, str]] = ..., format: _Optional[_Union[ChangefeedFormat.Format, str]] = ..., retention_period: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., virtual_timestamps: bool = ..., initial_scan: bool = ..., attributes: _Optional[_Mapping[str, str]] = ..., aws_region: _Optional[str] = ..., resolved_timestamps_interval: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., topic_partitioning_settings: _Optional[_Union[_ydb_topic_pb2.PartitioningSettings, _Mapping]] = ...) -> None: ...

class ChangefeedDescription(_message.Message):
    __slots__ = ("name", "mode", "format", "state", "virtual_timestamps", "attributes", "aws_region", "resolved_timestamps_interval")
    class State(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        STATE_UNSPECIFIED: _ClassVar[ChangefeedDescription.State]
        STATE_ENABLED: _ClassVar[ChangefeedDescription.State]
        STATE_DISABLED: _ClassVar[ChangefeedDescription.State]
        STATE_INITIAL_SCAN: _ClassVar[ChangefeedDescription.State]
    STATE_UNSPECIFIED: ChangefeedDescription.State
    STATE_ENABLED: ChangefeedDescription.State
    STATE_DISABLED: ChangefeedDescription.State
    STATE_INITIAL_SCAN: ChangefeedDescription.State
    class AttributesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    VIRTUAL_TIMESTAMPS_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    AWS_REGION_FIELD_NUMBER: _ClassVar[int]
    RESOLVED_TIMESTAMPS_INTERVAL_FIELD_NUMBER: _ClassVar[int]
    name: str
    mode: ChangefeedMode.Mode
    format: ChangefeedFormat.Format
    state: ChangefeedDescription.State
    virtual_timestamps: bool
    attributes: _containers.ScalarMap[str, str]
    aws_region: str
    resolved_timestamps_interval: _duration_pb2.Duration
    def __init__(self, name: _Optional[str] = ..., mode: _Optional[_Union[ChangefeedMode.Mode, str]] = ..., format: _Optional[_Union[ChangefeedFormat.Format, str]] = ..., state: _Optional[_Union[ChangefeedDescription.State, str]] = ..., virtual_timestamps: bool = ..., attributes: _Optional[_Mapping[str, str]] = ..., aws_region: _Optional[str] = ..., resolved_timestamps_interval: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ...) -> None: ...

class StoragePool(_message.Message):
    __slots__ = ("media",)
    MEDIA_FIELD_NUMBER: _ClassVar[int]
    media: str
    def __init__(self, media: _Optional[str] = ...) -> None: ...

class StoragePolicy(_message.Message):
    __slots__ = ("preset_name", "syslog", "log", "data", "external", "keep_in_memory", "column_families")
    PRESET_NAME_FIELD_NUMBER: _ClassVar[int]
    SYSLOG_FIELD_NUMBER: _ClassVar[int]
    LOG_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_FIELD_NUMBER: _ClassVar[int]
    KEEP_IN_MEMORY_FIELD_NUMBER: _ClassVar[int]
    COLUMN_FAMILIES_FIELD_NUMBER: _ClassVar[int]
    preset_name: str
    syslog: StoragePool
    log: StoragePool
    data: StoragePool
    external: StoragePool
    keep_in_memory: _ydb_common_pb2.FeatureFlag.Status
    column_families: _containers.RepeatedCompositeFieldContainer[ColumnFamilyPolicy]
    def __init__(self, preset_name: _Optional[str] = ..., syslog: _Optional[_Union[StoragePool, _Mapping]] = ..., log: _Optional[_Union[StoragePool, _Mapping]] = ..., data: _Optional[_Union[StoragePool, _Mapping]] = ..., external: _Optional[_Union[StoragePool, _Mapping]] = ..., keep_in_memory: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ..., column_families: _Optional[_Iterable[_Union[ColumnFamilyPolicy, _Mapping]]] = ...) -> None: ...

class ColumnFamilyPolicy(_message.Message):
    __slots__ = ("name", "data", "external", "keep_in_memory", "compression")
    class Compression(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        COMPRESSION_UNSPECIFIED: _ClassVar[ColumnFamilyPolicy.Compression]
        UNCOMPRESSED: _ClassVar[ColumnFamilyPolicy.Compression]
        COMPRESSED: _ClassVar[ColumnFamilyPolicy.Compression]
    COMPRESSION_UNSPECIFIED: ColumnFamilyPolicy.Compression
    UNCOMPRESSED: ColumnFamilyPolicy.Compression
    COMPRESSED: ColumnFamilyPolicy.Compression
    NAME_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_FIELD_NUMBER: _ClassVar[int]
    KEEP_IN_MEMORY_FIELD_NUMBER: _ClassVar[int]
    COMPRESSION_FIELD_NUMBER: _ClassVar[int]
    name: str
    data: StoragePool
    external: StoragePool
    keep_in_memory: _ydb_common_pb2.FeatureFlag.Status
    compression: ColumnFamilyPolicy.Compression
    def __init__(self, name: _Optional[str] = ..., data: _Optional[_Union[StoragePool, _Mapping]] = ..., external: _Optional[_Union[StoragePool, _Mapping]] = ..., keep_in_memory: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ..., compression: _Optional[_Union[ColumnFamilyPolicy.Compression, str]] = ...) -> None: ...

class CompactionPolicy(_message.Message):
    __slots__ = ("preset_name",)
    PRESET_NAME_FIELD_NUMBER: _ClassVar[int]
    preset_name: str
    def __init__(self, preset_name: _Optional[str] = ...) -> None: ...

class ExplicitPartitions(_message.Message):
    __slots__ = ("split_points",)
    SPLIT_POINTS_FIELD_NUMBER: _ClassVar[int]
    split_points: _containers.RepeatedCompositeFieldContainer[_ydb_value_pb2.TypedValue]
    def __init__(self, split_points: _Optional[_Iterable[_Union[_ydb_value_pb2.TypedValue, _Mapping]]] = ...) -> None: ...

class PartitionStats(_message.Message):
    __slots__ = ("rows_estimate", "store_size", "leader_node_id")
    ROWS_ESTIMATE_FIELD_NUMBER: _ClassVar[int]
    STORE_SIZE_FIELD_NUMBER: _ClassVar[int]
    LEADER_NODE_ID_FIELD_NUMBER: _ClassVar[int]
    rows_estimate: int
    store_size: int
    leader_node_id: int
    def __init__(self, rows_estimate: _Optional[int] = ..., store_size: _Optional[int] = ..., leader_node_id: _Optional[int] = ...) -> None: ...

class TableStats(_message.Message):
    __slots__ = ("partition_stats", "rows_estimate", "store_size", "partitions", "creation_time", "modification_time")
    PARTITION_STATS_FIELD_NUMBER: _ClassVar[int]
    ROWS_ESTIMATE_FIELD_NUMBER: _ClassVar[int]
    STORE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PARTITIONS_FIELD_NUMBER: _ClassVar[int]
    CREATION_TIME_FIELD_NUMBER: _ClassVar[int]
    MODIFICATION_TIME_FIELD_NUMBER: _ClassVar[int]
    partition_stats: _containers.RepeatedCompositeFieldContainer[PartitionStats]
    rows_estimate: int
    store_size: int
    partitions: int
    creation_time: _timestamp_pb2.Timestamp
    modification_time: _timestamp_pb2.Timestamp
    def __init__(self, partition_stats: _Optional[_Iterable[_Union[PartitionStats, _Mapping]]] = ..., rows_estimate: _Optional[int] = ..., store_size: _Optional[int] = ..., partitions: _Optional[int] = ..., creation_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., modification_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class PartitioningPolicy(_message.Message):
    __slots__ = ("preset_name", "auto_partitioning", "uniform_partitions", "explicit_partitions")
    class AutoPartitioningPolicy(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        AUTO_PARTITIONING_POLICY_UNSPECIFIED: _ClassVar[PartitioningPolicy.AutoPartitioningPolicy]
        DISABLED: _ClassVar[PartitioningPolicy.AutoPartitioningPolicy]
        AUTO_SPLIT: _ClassVar[PartitioningPolicy.AutoPartitioningPolicy]
        AUTO_SPLIT_MERGE: _ClassVar[PartitioningPolicy.AutoPartitioningPolicy]
    AUTO_PARTITIONING_POLICY_UNSPECIFIED: PartitioningPolicy.AutoPartitioningPolicy
    DISABLED: PartitioningPolicy.AutoPartitioningPolicy
    AUTO_SPLIT: PartitioningPolicy.AutoPartitioningPolicy
    AUTO_SPLIT_MERGE: PartitioningPolicy.AutoPartitioningPolicy
    PRESET_NAME_FIELD_NUMBER: _ClassVar[int]
    AUTO_PARTITIONING_FIELD_NUMBER: _ClassVar[int]
    UNIFORM_PARTITIONS_FIELD_NUMBER: _ClassVar[int]
    EXPLICIT_PARTITIONS_FIELD_NUMBER: _ClassVar[int]
    preset_name: str
    auto_partitioning: PartitioningPolicy.AutoPartitioningPolicy
    uniform_partitions: int
    explicit_partitions: ExplicitPartitions
    def __init__(self, preset_name: _Optional[str] = ..., auto_partitioning: _Optional[_Union[PartitioningPolicy.AutoPartitioningPolicy, str]] = ..., uniform_partitions: _Optional[int] = ..., explicit_partitions: _Optional[_Union[ExplicitPartitions, _Mapping]] = ...) -> None: ...

class ExecutionPolicy(_message.Message):
    __slots__ = ("preset_name",)
    PRESET_NAME_FIELD_NUMBER: _ClassVar[int]
    preset_name: str
    def __init__(self, preset_name: _Optional[str] = ...) -> None: ...

class ReplicationPolicy(_message.Message):
    __slots__ = ("preset_name", "replicas_count", "create_per_availability_zone", "allow_promotion")
    PRESET_NAME_FIELD_NUMBER: _ClassVar[int]
    REPLICAS_COUNT_FIELD_NUMBER: _ClassVar[int]
    CREATE_PER_AVAILABILITY_ZONE_FIELD_NUMBER: _ClassVar[int]
    ALLOW_PROMOTION_FIELD_NUMBER: _ClassVar[int]
    preset_name: str
    replicas_count: int
    create_per_availability_zone: _ydb_common_pb2.FeatureFlag.Status
    allow_promotion: _ydb_common_pb2.FeatureFlag.Status
    def __init__(self, preset_name: _Optional[str] = ..., replicas_count: _Optional[int] = ..., create_per_availability_zone: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ..., allow_promotion: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ...) -> None: ...

class CachingPolicy(_message.Message):
    __slots__ = ("preset_name",)
    PRESET_NAME_FIELD_NUMBER: _ClassVar[int]
    preset_name: str
    def __init__(self, preset_name: _Optional[str] = ...) -> None: ...

class TableProfile(_message.Message):
    __slots__ = ("preset_name", "storage_policy", "compaction_policy", "partitioning_policy", "execution_policy", "replication_policy", "caching_policy")
    PRESET_NAME_FIELD_NUMBER: _ClassVar[int]
    STORAGE_POLICY_FIELD_NUMBER: _ClassVar[int]
    COMPACTION_POLICY_FIELD_NUMBER: _ClassVar[int]
    PARTITIONING_POLICY_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_POLICY_FIELD_NUMBER: _ClassVar[int]
    REPLICATION_POLICY_FIELD_NUMBER: _ClassVar[int]
    CACHING_POLICY_FIELD_NUMBER: _ClassVar[int]
    preset_name: str
    storage_policy: StoragePolicy
    compaction_policy: CompactionPolicy
    partitioning_policy: PartitioningPolicy
    execution_policy: ExecutionPolicy
    replication_policy: ReplicationPolicy
    caching_policy: CachingPolicy
    def __init__(self, preset_name: _Optional[str] = ..., storage_policy: _Optional[_Union[StoragePolicy, _Mapping]] = ..., compaction_policy: _Optional[_Union[CompactionPolicy, _Mapping]] = ..., partitioning_policy: _Optional[_Union[PartitioningPolicy, _Mapping]] = ..., execution_policy: _Optional[_Union[ExecutionPolicy, _Mapping]] = ..., replication_policy: _Optional[_Union[ReplicationPolicy, _Mapping]] = ..., caching_policy: _Optional[_Union[CachingPolicy, _Mapping]] = ...) -> None: ...

class SequenceDescription(_message.Message):
    __slots__ = ("name", "min_value", "max_value", "start_value", "cache", "increment", "cycle", "set_val")
    class SetVal(_message.Message):
        __slots__ = ("next_value", "next_used")
        NEXT_VALUE_FIELD_NUMBER: _ClassVar[int]
        NEXT_USED_FIELD_NUMBER: _ClassVar[int]
        next_value: int
        next_used: bool
        def __init__(self, next_value: _Optional[int] = ..., next_used: bool = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    MIN_VALUE_FIELD_NUMBER: _ClassVar[int]
    MAX_VALUE_FIELD_NUMBER: _ClassVar[int]
    START_VALUE_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    INCREMENT_FIELD_NUMBER: _ClassVar[int]
    CYCLE_FIELD_NUMBER: _ClassVar[int]
    SET_VAL_FIELD_NUMBER: _ClassVar[int]
    name: str
    min_value: int
    max_value: int
    start_value: int
    cache: int
    increment: int
    cycle: bool
    set_val: SequenceDescription.SetVal
    def __init__(self, name: _Optional[str] = ..., min_value: _Optional[int] = ..., max_value: _Optional[int] = ..., start_value: _Optional[int] = ..., cache: _Optional[int] = ..., increment: _Optional[int] = ..., cycle: bool = ..., set_val: _Optional[_Union[SequenceDescription.SetVal, _Mapping]] = ...) -> None: ...

class ColumnMeta(_message.Message):
    __slots__ = ("name", "type", "family", "not_null", "from_literal", "from_sequence")
    NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    FAMILY_FIELD_NUMBER: _ClassVar[int]
    NOT_NULL_FIELD_NUMBER: _ClassVar[int]
    FROM_LITERAL_FIELD_NUMBER: _ClassVar[int]
    FROM_SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    name: str
    type: _ydb_value_pb2.Type
    family: str
    not_null: bool
    from_literal: _ydb_value_pb2.TypedValue
    from_sequence: SequenceDescription
    def __init__(self, name: _Optional[str] = ..., type: _Optional[_Union[_ydb_value_pb2.Type, _Mapping]] = ..., family: _Optional[str] = ..., not_null: bool = ..., from_literal: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ..., from_sequence: _Optional[_Union[SequenceDescription, _Mapping]] = ...) -> None: ...

class DateTypeColumnModeSettings(_message.Message):
    __slots__ = ("column_name", "expire_after_seconds")
    COLUMN_NAME_FIELD_NUMBER: _ClassVar[int]
    EXPIRE_AFTER_SECONDS_FIELD_NUMBER: _ClassVar[int]
    column_name: str
    expire_after_seconds: int
    def __init__(self, column_name: _Optional[str] = ..., expire_after_seconds: _Optional[int] = ...) -> None: ...

class ValueSinceUnixEpochModeSettings(_message.Message):
    __slots__ = ("column_name", "column_unit", "expire_after_seconds")
    class Unit(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNIT_UNSPECIFIED: _ClassVar[ValueSinceUnixEpochModeSettings.Unit]
        UNIT_SECONDS: _ClassVar[ValueSinceUnixEpochModeSettings.Unit]
        UNIT_MILLISECONDS: _ClassVar[ValueSinceUnixEpochModeSettings.Unit]
        UNIT_MICROSECONDS: _ClassVar[ValueSinceUnixEpochModeSettings.Unit]
        UNIT_NANOSECONDS: _ClassVar[ValueSinceUnixEpochModeSettings.Unit]
    UNIT_UNSPECIFIED: ValueSinceUnixEpochModeSettings.Unit
    UNIT_SECONDS: ValueSinceUnixEpochModeSettings.Unit
    UNIT_MILLISECONDS: ValueSinceUnixEpochModeSettings.Unit
    UNIT_MICROSECONDS: ValueSinceUnixEpochModeSettings.Unit
    UNIT_NANOSECONDS: ValueSinceUnixEpochModeSettings.Unit
    COLUMN_NAME_FIELD_NUMBER: _ClassVar[int]
    COLUMN_UNIT_FIELD_NUMBER: _ClassVar[int]
    EXPIRE_AFTER_SECONDS_FIELD_NUMBER: _ClassVar[int]
    column_name: str
    column_unit: ValueSinceUnixEpochModeSettings.Unit
    expire_after_seconds: int
    def __init__(self, column_name: _Optional[str] = ..., column_unit: _Optional[_Union[ValueSinceUnixEpochModeSettings.Unit, str]] = ..., expire_after_seconds: _Optional[int] = ...) -> None: ...

class TtlSettings(_message.Message):
    __slots__ = ("date_type_column", "value_since_unix_epoch", "run_interval_seconds")
    DATE_TYPE_COLUMN_FIELD_NUMBER: _ClassVar[int]
    VALUE_SINCE_UNIX_EPOCH_FIELD_NUMBER: _ClassVar[int]
    RUN_INTERVAL_SECONDS_FIELD_NUMBER: _ClassVar[int]
    date_type_column: DateTypeColumnModeSettings
    value_since_unix_epoch: ValueSinceUnixEpochModeSettings
    run_interval_seconds: int
    def __init__(self, date_type_column: _Optional[_Union[DateTypeColumnModeSettings, _Mapping]] = ..., value_since_unix_epoch: _Optional[_Union[ValueSinceUnixEpochModeSettings, _Mapping]] = ..., run_interval_seconds: _Optional[int] = ...) -> None: ...

class StorageSettings(_message.Message):
    __slots__ = ("tablet_commit_log0", "tablet_commit_log1", "external", "store_external_blobs")
    TABLET_COMMIT_LOG0_FIELD_NUMBER: _ClassVar[int]
    TABLET_COMMIT_LOG1_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_FIELD_NUMBER: _ClassVar[int]
    STORE_EXTERNAL_BLOBS_FIELD_NUMBER: _ClassVar[int]
    tablet_commit_log0: StoragePool
    tablet_commit_log1: StoragePool
    external: StoragePool
    store_external_blobs: _ydb_common_pb2.FeatureFlag.Status
    def __init__(self, tablet_commit_log0: _Optional[_Union[StoragePool, _Mapping]] = ..., tablet_commit_log1: _Optional[_Union[StoragePool, _Mapping]] = ..., external: _Optional[_Union[StoragePool, _Mapping]] = ..., store_external_blobs: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ...) -> None: ...

class ColumnFamily(_message.Message):
    __slots__ = ("name", "data", "compression", "keep_in_memory")
    class Compression(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        COMPRESSION_UNSPECIFIED: _ClassVar[ColumnFamily.Compression]
        COMPRESSION_NONE: _ClassVar[ColumnFamily.Compression]
        COMPRESSION_LZ4: _ClassVar[ColumnFamily.Compression]
    COMPRESSION_UNSPECIFIED: ColumnFamily.Compression
    COMPRESSION_NONE: ColumnFamily.Compression
    COMPRESSION_LZ4: ColumnFamily.Compression
    NAME_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    COMPRESSION_FIELD_NUMBER: _ClassVar[int]
    KEEP_IN_MEMORY_FIELD_NUMBER: _ClassVar[int]
    name: str
    data: StoragePool
    compression: ColumnFamily.Compression
    keep_in_memory: _ydb_common_pb2.FeatureFlag.Status
    def __init__(self, name: _Optional[str] = ..., data: _Optional[_Union[StoragePool, _Mapping]] = ..., compression: _Optional[_Union[ColumnFamily.Compression, str]] = ..., keep_in_memory: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ...) -> None: ...

class PartitioningSettings(_message.Message):
    __slots__ = ("partition_by", "partitioning_by_size", "partition_size_mb", "partitioning_by_load", "min_partitions_count", "max_partitions_count")
    PARTITION_BY_FIELD_NUMBER: _ClassVar[int]
    PARTITIONING_BY_SIZE_FIELD_NUMBER: _ClassVar[int]
    PARTITION_SIZE_MB_FIELD_NUMBER: _ClassVar[int]
    PARTITIONING_BY_LOAD_FIELD_NUMBER: _ClassVar[int]
    MIN_PARTITIONS_COUNT_FIELD_NUMBER: _ClassVar[int]
    MAX_PARTITIONS_COUNT_FIELD_NUMBER: _ClassVar[int]
    partition_by: _containers.RepeatedScalarFieldContainer[str]
    partitioning_by_size: _ydb_common_pb2.FeatureFlag.Status
    partition_size_mb: int
    partitioning_by_load: _ydb_common_pb2.FeatureFlag.Status
    min_partitions_count: int
    max_partitions_count: int
    def __init__(self, partition_by: _Optional[_Iterable[str]] = ..., partitioning_by_size: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ..., partition_size_mb: _Optional[int] = ..., partitioning_by_load: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ..., min_partitions_count: _Optional[int] = ..., max_partitions_count: _Optional[int] = ...) -> None: ...

class AzReadReplicasSettings(_message.Message):
    __slots__ = ("name", "read_replicas_count")
    NAME_FIELD_NUMBER: _ClassVar[int]
    READ_REPLICAS_COUNT_FIELD_NUMBER: _ClassVar[int]
    name: str
    read_replicas_count: int
    def __init__(self, name: _Optional[str] = ..., read_replicas_count: _Optional[int] = ...) -> None: ...

class ClusterReplicasSettings(_message.Message):
    __slots__ = ("az_read_replicas_settings",)
    AZ_READ_REPLICAS_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    az_read_replicas_settings: _containers.RepeatedCompositeFieldContainer[AzReadReplicasSettings]
    def __init__(self, az_read_replicas_settings: _Optional[_Iterable[_Union[AzReadReplicasSettings, _Mapping]]] = ...) -> None: ...

class ReadReplicasSettings(_message.Message):
    __slots__ = ("per_az_read_replicas_count", "any_az_read_replicas_count")
    PER_AZ_READ_REPLICAS_COUNT_FIELD_NUMBER: _ClassVar[int]
    ANY_AZ_READ_REPLICAS_COUNT_FIELD_NUMBER: _ClassVar[int]
    per_az_read_replicas_count: int
    any_az_read_replicas_count: int
    def __init__(self, per_az_read_replicas_count: _Optional[int] = ..., any_az_read_replicas_count: _Optional[int] = ...) -> None: ...

class CreateTableRequest(_message.Message):
    __slots__ = ("session_id", "path", "columns", "primary_key", "profile", "operation_params", "indexes", "ttl_settings", "storage_settings", "column_families", "attributes", "compaction_policy", "uniform_partitions", "partition_at_keys", "partitioning_settings", "key_bloom_filter", "read_replicas_settings", "tiering", "temporary", "store_type")
    class AttributesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    COLUMNS_FIELD_NUMBER: _ClassVar[int]
    PRIMARY_KEY_FIELD_NUMBER: _ClassVar[int]
    PROFILE_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    INDEXES_FIELD_NUMBER: _ClassVar[int]
    TTL_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    STORAGE_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    COLUMN_FAMILIES_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    COMPACTION_POLICY_FIELD_NUMBER: _ClassVar[int]
    UNIFORM_PARTITIONS_FIELD_NUMBER: _ClassVar[int]
    PARTITION_AT_KEYS_FIELD_NUMBER: _ClassVar[int]
    PARTITIONING_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    KEY_BLOOM_FILTER_FIELD_NUMBER: _ClassVar[int]
    READ_REPLICAS_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    TIERING_FIELD_NUMBER: _ClassVar[int]
    TEMPORARY_FIELD_NUMBER: _ClassVar[int]
    STORE_TYPE_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    path: str
    columns: _containers.RepeatedCompositeFieldContainer[ColumnMeta]
    primary_key: _containers.RepeatedScalarFieldContainer[str]
    profile: TableProfile
    operation_params: _ydb_operation_pb2.OperationParams
    indexes: _containers.RepeatedCompositeFieldContainer[TableIndex]
    ttl_settings: TtlSettings
    storage_settings: StorageSettings
    column_families: _containers.RepeatedCompositeFieldContainer[ColumnFamily]
    attributes: _containers.ScalarMap[str, str]
    compaction_policy: str
    uniform_partitions: int
    partition_at_keys: ExplicitPartitions
    partitioning_settings: PartitioningSettings
    key_bloom_filter: _ydb_common_pb2.FeatureFlag.Status
    read_replicas_settings: ReadReplicasSettings
    tiering: str
    temporary: bool
    store_type: StoreType
    def __init__(self, session_id: _Optional[str] = ..., path: _Optional[str] = ..., columns: _Optional[_Iterable[_Union[ColumnMeta, _Mapping]]] = ..., primary_key: _Optional[_Iterable[str]] = ..., profile: _Optional[_Union[TableProfile, _Mapping]] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., indexes: _Optional[_Iterable[_Union[TableIndex, _Mapping]]] = ..., ttl_settings: _Optional[_Union[TtlSettings, _Mapping]] = ..., storage_settings: _Optional[_Union[StorageSettings, _Mapping]] = ..., column_families: _Optional[_Iterable[_Union[ColumnFamily, _Mapping]]] = ..., attributes: _Optional[_Mapping[str, str]] = ..., compaction_policy: _Optional[str] = ..., uniform_partitions: _Optional[int] = ..., partition_at_keys: _Optional[_Union[ExplicitPartitions, _Mapping]] = ..., partitioning_settings: _Optional[_Union[PartitioningSettings, _Mapping]] = ..., key_bloom_filter: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ..., read_replicas_settings: _Optional[_Union[ReadReplicasSettings, _Mapping]] = ..., tiering: _Optional[str] = ..., temporary: bool = ..., store_type: _Optional[_Union[StoreType, str]] = ...) -> None: ...

class CreateTableResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DropTableRequest(_message.Message):
    __slots__ = ("session_id", "path", "operation_params")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    path: str
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, session_id: _Optional[str] = ..., path: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class DropTableResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class RenameIndexItem(_message.Message):
    __slots__ = ("source_name", "destination_name", "replace_destination")
    SOURCE_NAME_FIELD_NUMBER: _ClassVar[int]
    DESTINATION_NAME_FIELD_NUMBER: _ClassVar[int]
    REPLACE_DESTINATION_FIELD_NUMBER: _ClassVar[int]
    source_name: str
    destination_name: str
    replace_destination: bool
    def __init__(self, source_name: _Optional[str] = ..., destination_name: _Optional[str] = ..., replace_destination: bool = ...) -> None: ...

class AlterTableRequest(_message.Message):
    __slots__ = ("session_id", "path", "add_columns", "drop_columns", "operation_params", "alter_columns", "set_ttl_settings", "drop_ttl_settings", "add_indexes", "drop_indexes", "alter_storage_settings", "add_column_families", "alter_column_families", "alter_attributes", "set_compaction_policy", "alter_partitioning_settings", "set_key_bloom_filter", "set_read_replicas_settings", "add_changefeeds", "drop_changefeeds", "rename_indexes", "set_tiering", "drop_tiering")
    class AlterAttributesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    ADD_COLUMNS_FIELD_NUMBER: _ClassVar[int]
    DROP_COLUMNS_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    ALTER_COLUMNS_FIELD_NUMBER: _ClassVar[int]
    SET_TTL_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    DROP_TTL_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    ADD_INDEXES_FIELD_NUMBER: _ClassVar[int]
    DROP_INDEXES_FIELD_NUMBER: _ClassVar[int]
    ALTER_STORAGE_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    ADD_COLUMN_FAMILIES_FIELD_NUMBER: _ClassVar[int]
    ALTER_COLUMN_FAMILIES_FIELD_NUMBER: _ClassVar[int]
    ALTER_ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    SET_COMPACTION_POLICY_FIELD_NUMBER: _ClassVar[int]
    ALTER_PARTITIONING_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    SET_KEY_BLOOM_FILTER_FIELD_NUMBER: _ClassVar[int]
    SET_READ_REPLICAS_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    ADD_CHANGEFEEDS_FIELD_NUMBER: _ClassVar[int]
    DROP_CHANGEFEEDS_FIELD_NUMBER: _ClassVar[int]
    RENAME_INDEXES_FIELD_NUMBER: _ClassVar[int]
    SET_TIERING_FIELD_NUMBER: _ClassVar[int]
    DROP_TIERING_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    path: str
    add_columns: _containers.RepeatedCompositeFieldContainer[ColumnMeta]
    drop_columns: _containers.RepeatedScalarFieldContainer[str]
    operation_params: _ydb_operation_pb2.OperationParams
    alter_columns: _containers.RepeatedCompositeFieldContainer[ColumnMeta]
    set_ttl_settings: TtlSettings
    drop_ttl_settings: _empty_pb2.Empty
    add_indexes: _containers.RepeatedCompositeFieldContainer[TableIndex]
    drop_indexes: _containers.RepeatedScalarFieldContainer[str]
    alter_storage_settings: StorageSettings
    add_column_families: _containers.RepeatedCompositeFieldContainer[ColumnFamily]
    alter_column_families: _containers.RepeatedCompositeFieldContainer[ColumnFamily]
    alter_attributes: _containers.ScalarMap[str, str]
    set_compaction_policy: str
    alter_partitioning_settings: PartitioningSettings
    set_key_bloom_filter: _ydb_common_pb2.FeatureFlag.Status
    set_read_replicas_settings: ReadReplicasSettings
    add_changefeeds: _containers.RepeatedCompositeFieldContainer[Changefeed]
    drop_changefeeds: _containers.RepeatedScalarFieldContainer[str]
    rename_indexes: _containers.RepeatedCompositeFieldContainer[RenameIndexItem]
    set_tiering: str
    drop_tiering: _empty_pb2.Empty
    def __init__(self, session_id: _Optional[str] = ..., path: _Optional[str] = ..., add_columns: _Optional[_Iterable[_Union[ColumnMeta, _Mapping]]] = ..., drop_columns: _Optional[_Iterable[str]] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., alter_columns: _Optional[_Iterable[_Union[ColumnMeta, _Mapping]]] = ..., set_ttl_settings: _Optional[_Union[TtlSettings, _Mapping]] = ..., drop_ttl_settings: _Optional[_Union[_empty_pb2.Empty, _Mapping]] = ..., add_indexes: _Optional[_Iterable[_Union[TableIndex, _Mapping]]] = ..., drop_indexes: _Optional[_Iterable[str]] = ..., alter_storage_settings: _Optional[_Union[StorageSettings, _Mapping]] = ..., add_column_families: _Optional[_Iterable[_Union[ColumnFamily, _Mapping]]] = ..., alter_column_families: _Optional[_Iterable[_Union[ColumnFamily, _Mapping]]] = ..., alter_attributes: _Optional[_Mapping[str, str]] = ..., set_compaction_policy: _Optional[str] = ..., alter_partitioning_settings: _Optional[_Union[PartitioningSettings, _Mapping]] = ..., set_key_bloom_filter: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ..., set_read_replicas_settings: _Optional[_Union[ReadReplicasSettings, _Mapping]] = ..., add_changefeeds: _Optional[_Iterable[_Union[Changefeed, _Mapping]]] = ..., drop_changefeeds: _Optional[_Iterable[str]] = ..., rename_indexes: _Optional[_Iterable[_Union[RenameIndexItem, _Mapping]]] = ..., set_tiering: _Optional[str] = ..., drop_tiering: _Optional[_Union[_empty_pb2.Empty, _Mapping]] = ...) -> None: ...

class AlterTableResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class CopyTableRequest(_message.Message):
    __slots__ = ("session_id", "source_path", "destination_path", "operation_params")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
    DESTINATION_PATH_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    source_path: str
    destination_path: str
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, session_id: _Optional[str] = ..., source_path: _Optional[str] = ..., destination_path: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class CopyTableResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class CopyTableItem(_message.Message):
    __slots__ = ("source_path", "destination_path", "omit_indexes")
    SOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
    DESTINATION_PATH_FIELD_NUMBER: _ClassVar[int]
    OMIT_INDEXES_FIELD_NUMBER: _ClassVar[int]
    source_path: str
    destination_path: str
    omit_indexes: bool
    def __init__(self, source_path: _Optional[str] = ..., destination_path: _Optional[str] = ..., omit_indexes: bool = ...) -> None: ...

class CopyTablesRequest(_message.Message):
    __slots__ = ("operation_params", "session_id", "tables")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TABLES_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    session_id: str
    tables: _containers.RepeatedCompositeFieldContainer[CopyTableItem]
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., session_id: _Optional[str] = ..., tables: _Optional[_Iterable[_Union[CopyTableItem, _Mapping]]] = ...) -> None: ...

class CopyTablesResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class RenameTableItem(_message.Message):
    __slots__ = ("source_path", "destination_path", "replace_destination")
    SOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
    DESTINATION_PATH_FIELD_NUMBER: _ClassVar[int]
    REPLACE_DESTINATION_FIELD_NUMBER: _ClassVar[int]
    source_path: str
    destination_path: str
    replace_destination: bool
    def __init__(self, source_path: _Optional[str] = ..., destination_path: _Optional[str] = ..., replace_destination: bool = ...) -> None: ...

class RenameTablesRequest(_message.Message):
    __slots__ = ("operation_params", "session_id", "tables")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TABLES_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    session_id: str
    tables: _containers.RepeatedCompositeFieldContainer[RenameTableItem]
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., session_id: _Optional[str] = ..., tables: _Optional[_Iterable[_Union[RenameTableItem, _Mapping]]] = ...) -> None: ...

class RenameTablesResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeTableRequest(_message.Message):
    __slots__ = ("session_id", "path", "operation_params", "include_shard_key_bounds", "include_table_stats", "include_partition_stats", "include_shard_nodes_info")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_SHARD_KEY_BOUNDS_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_TABLE_STATS_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_PARTITION_STATS_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_SHARD_NODES_INFO_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    path: str
    operation_params: _ydb_operation_pb2.OperationParams
    include_shard_key_bounds: bool
    include_table_stats: bool
    include_partition_stats: bool
    include_shard_nodes_info: bool
    def __init__(self, session_id: _Optional[str] = ..., path: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., include_shard_key_bounds: bool = ..., include_table_stats: bool = ..., include_partition_stats: bool = ..., include_shard_nodes_info: bool = ...) -> None: ...

class DescribeTableResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeTableResult(_message.Message):
    __slots__ = ("self", "columns", "primary_key", "shard_key_bounds", "indexes", "table_stats", "ttl_settings", "storage_settings", "column_families", "attributes", "partitioning_settings", "key_bloom_filter", "read_replicas_settings", "changefeeds", "tiering", "temporary", "store_type")
    class AttributesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    SELF_FIELD_NUMBER: _ClassVar[int]
    COLUMNS_FIELD_NUMBER: _ClassVar[int]
    PRIMARY_KEY_FIELD_NUMBER: _ClassVar[int]
    SHARD_KEY_BOUNDS_FIELD_NUMBER: _ClassVar[int]
    INDEXES_FIELD_NUMBER: _ClassVar[int]
    TABLE_STATS_FIELD_NUMBER: _ClassVar[int]
    TTL_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    STORAGE_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    COLUMN_FAMILIES_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    PARTITIONING_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    KEY_BLOOM_FILTER_FIELD_NUMBER: _ClassVar[int]
    READ_REPLICAS_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    CHANGEFEEDS_FIELD_NUMBER: _ClassVar[int]
    TIERING_FIELD_NUMBER: _ClassVar[int]
    TEMPORARY_FIELD_NUMBER: _ClassVar[int]
    STORE_TYPE_FIELD_NUMBER: _ClassVar[int]
    self: _ydb_scheme_pb2.Entry
    columns: _containers.RepeatedCompositeFieldContainer[ColumnMeta]
    primary_key: _containers.RepeatedScalarFieldContainer[str]
    shard_key_bounds: _containers.RepeatedCompositeFieldContainer[_ydb_value_pb2.TypedValue]
    indexes: _containers.RepeatedCompositeFieldContainer[TableIndexDescription]
    table_stats: TableStats
    ttl_settings: TtlSettings
    storage_settings: StorageSettings
    column_families: _containers.RepeatedCompositeFieldContainer[ColumnFamily]
    attributes: _containers.ScalarMap[str, str]
    partitioning_settings: PartitioningSettings
    key_bloom_filter: _ydb_common_pb2.FeatureFlag.Status
    read_replicas_settings: ReadReplicasSettings
    changefeeds: _containers.RepeatedCompositeFieldContainer[ChangefeedDescription]
    tiering: str
    temporary: bool
    store_type: StoreType
    def __init__(self_, self: _Optional[_Union[_ydb_scheme_pb2.Entry, _Mapping]] = ..., columns: _Optional[_Iterable[_Union[ColumnMeta, _Mapping]]] = ..., primary_key: _Optional[_Iterable[str]] = ..., shard_key_bounds: _Optional[_Iterable[_Union[_ydb_value_pb2.TypedValue, _Mapping]]] = ..., indexes: _Optional[_Iterable[_Union[TableIndexDescription, _Mapping]]] = ..., table_stats: _Optional[_Union[TableStats, _Mapping]] = ..., ttl_settings: _Optional[_Union[TtlSettings, _Mapping]] = ..., storage_settings: _Optional[_Union[StorageSettings, _Mapping]] = ..., column_families: _Optional[_Iterable[_Union[ColumnFamily, _Mapping]]] = ..., attributes: _Optional[_Mapping[str, str]] = ..., partitioning_settings: _Optional[_Union[PartitioningSettings, _Mapping]] = ..., key_bloom_filter: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ..., read_replicas_settings: _Optional[_Union[ReadReplicasSettings, _Mapping]] = ..., changefeeds: _Optional[_Iterable[_Union[ChangefeedDescription, _Mapping]]] = ..., tiering: _Optional[str] = ..., temporary: bool = ..., store_type: _Optional[_Union[StoreType, str]] = ...) -> None: ...

class Query(_message.Message):
    __slots__ = ("yql_text", "id")
    YQL_TEXT_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    yql_text: str
    id: str
    def __init__(self, yql_text: _Optional[str] = ..., id: _Optional[str] = ...) -> None: ...

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

class QueryCachePolicy(_message.Message):
    __slots__ = ("keep_in_cache",)
    KEEP_IN_CACHE_FIELD_NUMBER: _ClassVar[int]
    keep_in_cache: bool
    def __init__(self, keep_in_cache: bool = ...) -> None: ...

class QueryStatsCollection(_message.Message):
    __slots__ = ()
    class Mode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        STATS_COLLECTION_UNSPECIFIED: _ClassVar[QueryStatsCollection.Mode]
        STATS_COLLECTION_NONE: _ClassVar[QueryStatsCollection.Mode]
        STATS_COLLECTION_BASIC: _ClassVar[QueryStatsCollection.Mode]
        STATS_COLLECTION_FULL: _ClassVar[QueryStatsCollection.Mode]
        STATS_COLLECTION_PROFILE: _ClassVar[QueryStatsCollection.Mode]
    STATS_COLLECTION_UNSPECIFIED: QueryStatsCollection.Mode
    STATS_COLLECTION_NONE: QueryStatsCollection.Mode
    STATS_COLLECTION_BASIC: QueryStatsCollection.Mode
    STATS_COLLECTION_FULL: QueryStatsCollection.Mode
    STATS_COLLECTION_PROFILE: QueryStatsCollection.Mode
    def __init__(self) -> None: ...

class ExecuteDataQueryRequest(_message.Message):
    __slots__ = ("session_id", "tx_control", "query", "parameters", "query_cache_policy", "operation_params", "collect_stats")
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _ydb_value_pb2.TypedValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ...) -> None: ...
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TX_CONTROL_FIELD_NUMBER: _ClassVar[int]
    QUERY_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    QUERY_CACHE_POLICY_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    COLLECT_STATS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    tx_control: TransactionControl
    query: Query
    parameters: _containers.MessageMap[str, _ydb_value_pb2.TypedValue]
    query_cache_policy: QueryCachePolicy
    operation_params: _ydb_operation_pb2.OperationParams
    collect_stats: QueryStatsCollection.Mode
    def __init__(self, session_id: _Optional[str] = ..., tx_control: _Optional[_Union[TransactionControl, _Mapping]] = ..., query: _Optional[_Union[Query, _Mapping]] = ..., parameters: _Optional[_Mapping[str, _ydb_value_pb2.TypedValue]] = ..., query_cache_policy: _Optional[_Union[QueryCachePolicy, _Mapping]] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., collect_stats: _Optional[_Union[QueryStatsCollection.Mode, str]] = ...) -> None: ...

class ExecuteDataQueryResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ExecuteSchemeQueryRequest(_message.Message):
    __slots__ = ("session_id", "yql_text", "operation_params")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    YQL_TEXT_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    yql_text: str
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, session_id: _Optional[str] = ..., yql_text: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class ExecuteSchemeQueryResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class TransactionMeta(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class QueryMeta(_message.Message):
    __slots__ = ("id", "parameters_types")
    class ParametersTypesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _ydb_value_pb2.Type
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_ydb_value_pb2.Type, _Mapping]] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_TYPES_FIELD_NUMBER: _ClassVar[int]
    id: str
    parameters_types: _containers.MessageMap[str, _ydb_value_pb2.Type]
    def __init__(self, id: _Optional[str] = ..., parameters_types: _Optional[_Mapping[str, _ydb_value_pb2.Type]] = ...) -> None: ...

class ExecuteQueryResult(_message.Message):
    __slots__ = ("result_sets", "tx_meta", "query_meta", "query_stats")
    RESULT_SETS_FIELD_NUMBER: _ClassVar[int]
    TX_META_FIELD_NUMBER: _ClassVar[int]
    QUERY_META_FIELD_NUMBER: _ClassVar[int]
    QUERY_STATS_FIELD_NUMBER: _ClassVar[int]
    result_sets: _containers.RepeatedCompositeFieldContainer[_ydb_value_pb2.ResultSet]
    tx_meta: TransactionMeta
    query_meta: QueryMeta
    query_stats: _ydb_query_stats_pb2.QueryStats
    def __init__(self, result_sets: _Optional[_Iterable[_Union[_ydb_value_pb2.ResultSet, _Mapping]]] = ..., tx_meta: _Optional[_Union[TransactionMeta, _Mapping]] = ..., query_meta: _Optional[_Union[QueryMeta, _Mapping]] = ..., query_stats: _Optional[_Union[_ydb_query_stats_pb2.QueryStats, _Mapping]] = ...) -> None: ...

class ExplainDataQueryRequest(_message.Message):
    __slots__ = ("session_id", "yql_text", "operation_params", "collect_full_diagnostics")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    YQL_TEXT_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    COLLECT_FULL_DIAGNOSTICS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    yql_text: str
    operation_params: _ydb_operation_pb2.OperationParams
    collect_full_diagnostics: bool
    def __init__(self, session_id: _Optional[str] = ..., yql_text: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., collect_full_diagnostics: bool = ...) -> None: ...

class ExplainDataQueryResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ExplainQueryResult(_message.Message):
    __slots__ = ("query_ast", "query_plan", "query_full_diagnostics")
    QUERY_AST_FIELD_NUMBER: _ClassVar[int]
    QUERY_PLAN_FIELD_NUMBER: _ClassVar[int]
    QUERY_FULL_DIAGNOSTICS_FIELD_NUMBER: _ClassVar[int]
    query_ast: str
    query_plan: str
    query_full_diagnostics: str
    def __init__(self, query_ast: _Optional[str] = ..., query_plan: _Optional[str] = ..., query_full_diagnostics: _Optional[str] = ...) -> None: ...

class PrepareDataQueryRequest(_message.Message):
    __slots__ = ("session_id", "yql_text", "operation_params")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    YQL_TEXT_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    yql_text: str
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, session_id: _Optional[str] = ..., yql_text: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class PrepareDataQueryResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class PrepareQueryResult(_message.Message):
    __slots__ = ("query_id", "parameters_types")
    class ParametersTypesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _ydb_value_pb2.Type
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_ydb_value_pb2.Type, _Mapping]] = ...) -> None: ...
    QUERY_ID_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_TYPES_FIELD_NUMBER: _ClassVar[int]
    query_id: str
    parameters_types: _containers.MessageMap[str, _ydb_value_pb2.Type]
    def __init__(self, query_id: _Optional[str] = ..., parameters_types: _Optional[_Mapping[str, _ydb_value_pb2.Type]] = ...) -> None: ...

class KeepAliveRequest(_message.Message):
    __slots__ = ("session_id", "operation_params")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, session_id: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class KeepAliveResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class KeepAliveResult(_message.Message):
    __slots__ = ("session_status",)
    class SessionStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        SESSION_STATUS_UNSPECIFIED: _ClassVar[KeepAliveResult.SessionStatus]
        SESSION_STATUS_READY: _ClassVar[KeepAliveResult.SessionStatus]
        SESSION_STATUS_BUSY: _ClassVar[KeepAliveResult.SessionStatus]
    SESSION_STATUS_UNSPECIFIED: KeepAliveResult.SessionStatus
    SESSION_STATUS_READY: KeepAliveResult.SessionStatus
    SESSION_STATUS_BUSY: KeepAliveResult.SessionStatus
    SESSION_STATUS_FIELD_NUMBER: _ClassVar[int]
    session_status: KeepAliveResult.SessionStatus
    def __init__(self, session_status: _Optional[_Union[KeepAliveResult.SessionStatus, str]] = ...) -> None: ...

class BeginTransactionRequest(_message.Message):
    __slots__ = ("session_id", "tx_settings", "operation_params")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TX_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    tx_settings: TransactionSettings
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, session_id: _Optional[str] = ..., tx_settings: _Optional[_Union[TransactionSettings, _Mapping]] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class BeginTransactionResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class BeginTransactionResult(_message.Message):
    __slots__ = ("tx_meta",)
    TX_META_FIELD_NUMBER: _ClassVar[int]
    tx_meta: TransactionMeta
    def __init__(self, tx_meta: _Optional[_Union[TransactionMeta, _Mapping]] = ...) -> None: ...

class CommitTransactionRequest(_message.Message):
    __slots__ = ("session_id", "tx_id", "operation_params", "collect_stats")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TX_ID_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    COLLECT_STATS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    tx_id: str
    operation_params: _ydb_operation_pb2.OperationParams
    collect_stats: QueryStatsCollection.Mode
    def __init__(self, session_id: _Optional[str] = ..., tx_id: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., collect_stats: _Optional[_Union[QueryStatsCollection.Mode, str]] = ...) -> None: ...

class CommitTransactionResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class CommitTransactionResult(_message.Message):
    __slots__ = ("query_stats",)
    QUERY_STATS_FIELD_NUMBER: _ClassVar[int]
    query_stats: _ydb_query_stats_pb2.QueryStats
    def __init__(self, query_stats: _Optional[_Union[_ydb_query_stats_pb2.QueryStats, _Mapping]] = ...) -> None: ...

class RollbackTransactionRequest(_message.Message):
    __slots__ = ("session_id", "tx_id", "operation_params")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TX_ID_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    tx_id: str
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, session_id: _Optional[str] = ..., tx_id: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class RollbackTransactionResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class StoragePolicyDescription(_message.Message):
    __slots__ = ("name", "labels")
    class LabelsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    name: str
    labels: _containers.ScalarMap[str, str]
    def __init__(self, name: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ...) -> None: ...

class CompactionPolicyDescription(_message.Message):
    __slots__ = ("name", "labels")
    class LabelsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    name: str
    labels: _containers.ScalarMap[str, str]
    def __init__(self, name: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ...) -> None: ...

class PartitioningPolicyDescription(_message.Message):
    __slots__ = ("name", "labels")
    class LabelsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    name: str
    labels: _containers.ScalarMap[str, str]
    def __init__(self, name: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ...) -> None: ...

class ExecutionPolicyDescription(_message.Message):
    __slots__ = ("name", "labels")
    class LabelsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    name: str
    labels: _containers.ScalarMap[str, str]
    def __init__(self, name: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ...) -> None: ...

class ReplicationPolicyDescription(_message.Message):
    __slots__ = ("name", "labels")
    class LabelsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    name: str
    labels: _containers.ScalarMap[str, str]
    def __init__(self, name: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ...) -> None: ...

class CachingPolicyDescription(_message.Message):
    __slots__ = ("name", "labels")
    class LabelsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    name: str
    labels: _containers.ScalarMap[str, str]
    def __init__(self, name: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ...) -> None: ...

class TableProfileDescription(_message.Message):
    __slots__ = ("name", "labels", "default_storage_policy", "allowed_storage_policies", "default_compaction_policy", "allowed_compaction_policies", "default_partitioning_policy", "allowed_partitioning_policies", "default_execution_policy", "allowed_execution_policies", "default_replication_policy", "allowed_replication_policies", "default_caching_policy", "allowed_caching_policies")
    class LabelsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_STORAGE_POLICY_FIELD_NUMBER: _ClassVar[int]
    ALLOWED_STORAGE_POLICIES_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_COMPACTION_POLICY_FIELD_NUMBER: _ClassVar[int]
    ALLOWED_COMPACTION_POLICIES_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_PARTITIONING_POLICY_FIELD_NUMBER: _ClassVar[int]
    ALLOWED_PARTITIONING_POLICIES_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_EXECUTION_POLICY_FIELD_NUMBER: _ClassVar[int]
    ALLOWED_EXECUTION_POLICIES_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_REPLICATION_POLICY_FIELD_NUMBER: _ClassVar[int]
    ALLOWED_REPLICATION_POLICIES_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_CACHING_POLICY_FIELD_NUMBER: _ClassVar[int]
    ALLOWED_CACHING_POLICIES_FIELD_NUMBER: _ClassVar[int]
    name: str
    labels: _containers.ScalarMap[str, str]
    default_storage_policy: str
    allowed_storage_policies: _containers.RepeatedScalarFieldContainer[str]
    default_compaction_policy: str
    allowed_compaction_policies: _containers.RepeatedScalarFieldContainer[str]
    default_partitioning_policy: str
    allowed_partitioning_policies: _containers.RepeatedScalarFieldContainer[str]
    default_execution_policy: str
    allowed_execution_policies: _containers.RepeatedScalarFieldContainer[str]
    default_replication_policy: str
    allowed_replication_policies: _containers.RepeatedScalarFieldContainer[str]
    default_caching_policy: str
    allowed_caching_policies: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, name: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ..., default_storage_policy: _Optional[str] = ..., allowed_storage_policies: _Optional[_Iterable[str]] = ..., default_compaction_policy: _Optional[str] = ..., allowed_compaction_policies: _Optional[_Iterable[str]] = ..., default_partitioning_policy: _Optional[str] = ..., allowed_partitioning_policies: _Optional[_Iterable[str]] = ..., default_execution_policy: _Optional[str] = ..., allowed_execution_policies: _Optional[_Iterable[str]] = ..., default_replication_policy: _Optional[str] = ..., allowed_replication_policies: _Optional[_Iterable[str]] = ..., default_caching_policy: _Optional[str] = ..., allowed_caching_policies: _Optional[_Iterable[str]] = ...) -> None: ...

class DescribeTableOptionsRequest(_message.Message):
    __slots__ = ("operation_params",)
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class DescribeTableOptionsResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeTableOptionsResult(_message.Message):
    __slots__ = ("table_profile_presets", "storage_policy_presets", "compaction_policy_presets", "partitioning_policy_presets", "execution_policy_presets", "replication_policy_presets", "caching_policy_presets")
    TABLE_PROFILE_PRESETS_FIELD_NUMBER: _ClassVar[int]
    STORAGE_POLICY_PRESETS_FIELD_NUMBER: _ClassVar[int]
    COMPACTION_POLICY_PRESETS_FIELD_NUMBER: _ClassVar[int]
    PARTITIONING_POLICY_PRESETS_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_POLICY_PRESETS_FIELD_NUMBER: _ClassVar[int]
    REPLICATION_POLICY_PRESETS_FIELD_NUMBER: _ClassVar[int]
    CACHING_POLICY_PRESETS_FIELD_NUMBER: _ClassVar[int]
    table_profile_presets: _containers.RepeatedCompositeFieldContainer[TableProfileDescription]
    storage_policy_presets: _containers.RepeatedCompositeFieldContainer[StoragePolicyDescription]
    compaction_policy_presets: _containers.RepeatedCompositeFieldContainer[CompactionPolicyDescription]
    partitioning_policy_presets: _containers.RepeatedCompositeFieldContainer[PartitioningPolicyDescription]
    execution_policy_presets: _containers.RepeatedCompositeFieldContainer[ExecutionPolicyDescription]
    replication_policy_presets: _containers.RepeatedCompositeFieldContainer[ReplicationPolicyDescription]
    caching_policy_presets: _containers.RepeatedCompositeFieldContainer[CachingPolicyDescription]
    def __init__(self, table_profile_presets: _Optional[_Iterable[_Union[TableProfileDescription, _Mapping]]] = ..., storage_policy_presets: _Optional[_Iterable[_Union[StoragePolicyDescription, _Mapping]]] = ..., compaction_policy_presets: _Optional[_Iterable[_Union[CompactionPolicyDescription, _Mapping]]] = ..., partitioning_policy_presets: _Optional[_Iterable[_Union[PartitioningPolicyDescription, _Mapping]]] = ..., execution_policy_presets: _Optional[_Iterable[_Union[ExecutionPolicyDescription, _Mapping]]] = ..., replication_policy_presets: _Optional[_Iterable[_Union[ReplicationPolicyDescription, _Mapping]]] = ..., caching_policy_presets: _Optional[_Iterable[_Union[CachingPolicyDescription, _Mapping]]] = ...) -> None: ...

class KeyRange(_message.Message):
    __slots__ = ("greater", "greater_or_equal", "less", "less_or_equal")
    GREATER_FIELD_NUMBER: _ClassVar[int]
    GREATER_OR_EQUAL_FIELD_NUMBER: _ClassVar[int]
    LESS_FIELD_NUMBER: _ClassVar[int]
    LESS_OR_EQUAL_FIELD_NUMBER: _ClassVar[int]
    greater: _ydb_value_pb2.TypedValue
    greater_or_equal: _ydb_value_pb2.TypedValue
    less: _ydb_value_pb2.TypedValue
    less_or_equal: _ydb_value_pb2.TypedValue
    def __init__(self, greater: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ..., greater_or_equal: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ..., less: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ..., less_or_equal: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ...) -> None: ...

class ReadTableRequest(_message.Message):
    __slots__ = ("session_id", "path", "key_range", "columns", "ordered", "row_limit", "use_snapshot", "batch_limit_bytes", "batch_limit_rows", "return_not_null_data_as_optional")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    KEY_RANGE_FIELD_NUMBER: _ClassVar[int]
    COLUMNS_FIELD_NUMBER: _ClassVar[int]
    ORDERED_FIELD_NUMBER: _ClassVar[int]
    ROW_LIMIT_FIELD_NUMBER: _ClassVar[int]
    USE_SNAPSHOT_FIELD_NUMBER: _ClassVar[int]
    BATCH_LIMIT_BYTES_FIELD_NUMBER: _ClassVar[int]
    BATCH_LIMIT_ROWS_FIELD_NUMBER: _ClassVar[int]
    RETURN_NOT_NULL_DATA_AS_OPTIONAL_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    path: str
    key_range: KeyRange
    columns: _containers.RepeatedScalarFieldContainer[str]
    ordered: bool
    row_limit: int
    use_snapshot: _ydb_common_pb2.FeatureFlag.Status
    batch_limit_bytes: int
    batch_limit_rows: int
    return_not_null_data_as_optional: _ydb_common_pb2.FeatureFlag.Status
    def __init__(self, session_id: _Optional[str] = ..., path: _Optional[str] = ..., key_range: _Optional[_Union[KeyRange, _Mapping]] = ..., columns: _Optional[_Iterable[str]] = ..., ordered: bool = ..., row_limit: _Optional[int] = ..., use_snapshot: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ..., batch_limit_bytes: _Optional[int] = ..., batch_limit_rows: _Optional[int] = ..., return_not_null_data_as_optional: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ...) -> None: ...

class ReadTableResponse(_message.Message):
    __slots__ = ("status", "issues", "snapshot", "result")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    SNAPSHOT_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    snapshot: _ydb_common_pb2.VirtualTimestamp
    result: ReadTableResult
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., snapshot: _Optional[_Union[_ydb_common_pb2.VirtualTimestamp, _Mapping]] = ..., result: _Optional[_Union[ReadTableResult, _Mapping]] = ...) -> None: ...

class ReadTableResult(_message.Message):
    __slots__ = ("result_set",)
    RESULT_SET_FIELD_NUMBER: _ClassVar[int]
    result_set: _ydb_value_pb2.ResultSet
    def __init__(self, result_set: _Optional[_Union[_ydb_value_pb2.ResultSet, _Mapping]] = ...) -> None: ...

class ReadRowsRequest(_message.Message):
    __slots__ = ("session_id", "path", "keys", "columns")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    KEYS_FIELD_NUMBER: _ClassVar[int]
    COLUMNS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    path: str
    keys: _ydb_value_pb2.TypedValue
    columns: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, session_id: _Optional[str] = ..., path: _Optional[str] = ..., keys: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ..., columns: _Optional[_Iterable[str]] = ...) -> None: ...

class ReadRowsResponse(_message.Message):
    __slots__ = ("status", "issues", "result_set")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_FIELD_NUMBER: _ClassVar[int]
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    result_set: _ydb_value_pb2.ResultSet
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., result_set: _Optional[_Union[_ydb_value_pb2.ResultSet, _Mapping]] = ...) -> None: ...

class BulkUpsertRequest(_message.Message):
    __slots__ = ("table", "rows", "operation_params", "arrow_batch_settings", "csv_settings", "data")
    TABLE_FIELD_NUMBER: _ClassVar[int]
    ROWS_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    ARROW_BATCH_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    CSV_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    table: str
    rows: _ydb_value_pb2.TypedValue
    operation_params: _ydb_operation_pb2.OperationParams
    arrow_batch_settings: _ydb_formats_pb2.ArrowBatchSettings
    csv_settings: _ydb_formats_pb2.CsvSettings
    data: bytes
    def __init__(self, table: _Optional[str] = ..., rows: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., arrow_batch_settings: _Optional[_Union[_ydb_formats_pb2.ArrowBatchSettings, _Mapping]] = ..., csv_settings: _Optional[_Union[_ydb_formats_pb2.CsvSettings, _Mapping]] = ..., data: _Optional[bytes] = ...) -> None: ...

class BulkUpsertResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class BulkUpsertResult(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ExecuteScanQueryRequest(_message.Message):
    __slots__ = ("query", "parameters", "mode", "collect_stats", "collect_full_diagnostics")
    class Mode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        MODE_UNSPECIFIED: _ClassVar[ExecuteScanQueryRequest.Mode]
        MODE_EXPLAIN: _ClassVar[ExecuteScanQueryRequest.Mode]
        MODE_EXEC: _ClassVar[ExecuteScanQueryRequest.Mode]
    MODE_UNSPECIFIED: ExecuteScanQueryRequest.Mode
    MODE_EXPLAIN: ExecuteScanQueryRequest.Mode
    MODE_EXEC: ExecuteScanQueryRequest.Mode
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _ydb_value_pb2.TypedValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ...) -> None: ...
    QUERY_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    COLLECT_STATS_FIELD_NUMBER: _ClassVar[int]
    COLLECT_FULL_DIAGNOSTICS_FIELD_NUMBER: _ClassVar[int]
    query: Query
    parameters: _containers.MessageMap[str, _ydb_value_pb2.TypedValue]
    mode: ExecuteScanQueryRequest.Mode
    collect_stats: QueryStatsCollection.Mode
    collect_full_diagnostics: bool
    def __init__(self, query: _Optional[_Union[Query, _Mapping]] = ..., parameters: _Optional[_Mapping[str, _ydb_value_pb2.TypedValue]] = ..., mode: _Optional[_Union[ExecuteScanQueryRequest.Mode, str]] = ..., collect_stats: _Optional[_Union[QueryStatsCollection.Mode, str]] = ..., collect_full_diagnostics: bool = ...) -> None: ...

class ExecuteScanQueryPartialResponse(_message.Message):
    __slots__ = ("status", "issues", "result")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    result: ExecuteScanQueryPartialResult
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., result: _Optional[_Union[ExecuteScanQueryPartialResult, _Mapping]] = ...) -> None: ...

class ExecuteScanQueryPartialResult(_message.Message):
    __slots__ = ("result_set", "query_stats", "query_full_diagnostics")
    RESULT_SET_FIELD_NUMBER: _ClassVar[int]
    QUERY_STATS_FIELD_NUMBER: _ClassVar[int]
    QUERY_FULL_DIAGNOSTICS_FIELD_NUMBER: _ClassVar[int]
    result_set: _ydb_value_pb2.ResultSet
    query_stats: _ydb_query_stats_pb2.QueryStats
    query_full_diagnostics: str
    def __init__(self, result_set: _Optional[_Union[_ydb_value_pb2.ResultSet, _Mapping]] = ..., query_stats: _Optional[_Union[_ydb_query_stats_pb2.QueryStats, _Mapping]] = ..., query_full_diagnostics: _Optional[str] = ...) -> None: ...
