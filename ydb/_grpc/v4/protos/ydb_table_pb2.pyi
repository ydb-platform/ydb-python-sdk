from protos.annotations import validation_pb2 as _validation_pb2
from protos import ydb_common_pb2 as _ydb_common_pb2
from protos import ydb_issue_message_pb2 as _ydb_issue_message_pb2
from protos import ydb_operation_pb2 as _ydb_operation_pb2
from protos import ydb_query_stats_pb2 as _ydb_query_stats_pb2
from protos import ydb_value_pb2 as _ydb_value_pb2
from protos import ydb_scheme_pb2 as _ydb_scheme_pb2
from protos import ydb_status_codes_pb2 as _ydb_status_codes_pb2
from protos import ydb_formats_pb2 as _ydb_formats_pb2
from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AlterTableRequest(_message.Message):
    __slots__ = ["add_changefeeds", "add_column_families", "add_columns", "add_indexes", "alter_attributes", "alter_column_families", "alter_columns", "alter_partitioning_settings", "alter_storage_settings", "drop_changefeeds", "drop_columns", "drop_indexes", "drop_tiering", "drop_ttl_settings", "operation_params", "path", "rename_indexes", "session_id", "set_compaction_policy", "set_key_bloom_filter", "set_read_replicas_settings", "set_tiering", "set_ttl_settings"]
    class AlterAttributesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ADD_CHANGEFEEDS_FIELD_NUMBER: _ClassVar[int]
    ADD_COLUMNS_FIELD_NUMBER: _ClassVar[int]
    ADD_COLUMN_FAMILIES_FIELD_NUMBER: _ClassVar[int]
    ADD_INDEXES_FIELD_NUMBER: _ClassVar[int]
    ALTER_ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    ALTER_COLUMNS_FIELD_NUMBER: _ClassVar[int]
    ALTER_COLUMN_FAMILIES_FIELD_NUMBER: _ClassVar[int]
    ALTER_PARTITIONING_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    ALTER_STORAGE_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    DROP_CHANGEFEEDS_FIELD_NUMBER: _ClassVar[int]
    DROP_COLUMNS_FIELD_NUMBER: _ClassVar[int]
    DROP_INDEXES_FIELD_NUMBER: _ClassVar[int]
    DROP_TIERING_FIELD_NUMBER: _ClassVar[int]
    DROP_TTL_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    RENAME_INDEXES_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    SET_COMPACTION_POLICY_FIELD_NUMBER: _ClassVar[int]
    SET_KEY_BLOOM_FILTER_FIELD_NUMBER: _ClassVar[int]
    SET_READ_REPLICAS_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    SET_TIERING_FIELD_NUMBER: _ClassVar[int]
    SET_TTL_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    add_changefeeds: _containers.RepeatedCompositeFieldContainer[Changefeed]
    add_column_families: _containers.RepeatedCompositeFieldContainer[ColumnFamily]
    add_columns: _containers.RepeatedCompositeFieldContainer[ColumnMeta]
    add_indexes: _containers.RepeatedCompositeFieldContainer[TableIndex]
    alter_attributes: _containers.ScalarMap[str, str]
    alter_column_families: _containers.RepeatedCompositeFieldContainer[ColumnFamily]
    alter_columns: _containers.RepeatedCompositeFieldContainer[ColumnMeta]
    alter_partitioning_settings: PartitioningSettings
    alter_storage_settings: StorageSettings
    drop_changefeeds: _containers.RepeatedScalarFieldContainer[str]
    drop_columns: _containers.RepeatedScalarFieldContainer[str]
    drop_indexes: _containers.RepeatedScalarFieldContainer[str]
    drop_tiering: _empty_pb2.Empty
    drop_ttl_settings: _empty_pb2.Empty
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    rename_indexes: _containers.RepeatedCompositeFieldContainer[RenameIndexItem]
    session_id: str
    set_compaction_policy: str
    set_key_bloom_filter: _ydb_common_pb2.FeatureFlag.Status
    set_read_replicas_settings: ReadReplicasSettings
    set_tiering: str
    set_ttl_settings: TtlSettings
    def __init__(self, session_id: _Optional[str] = ..., path: _Optional[str] = ..., add_columns: _Optional[_Iterable[_Union[ColumnMeta, _Mapping]]] = ..., drop_columns: _Optional[_Iterable[str]] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., alter_columns: _Optional[_Iterable[_Union[ColumnMeta, _Mapping]]] = ..., set_ttl_settings: _Optional[_Union[TtlSettings, _Mapping]] = ..., drop_ttl_settings: _Optional[_Union[_empty_pb2.Empty, _Mapping]] = ..., add_indexes: _Optional[_Iterable[_Union[TableIndex, _Mapping]]] = ..., drop_indexes: _Optional[_Iterable[str]] = ..., alter_storage_settings: _Optional[_Union[StorageSettings, _Mapping]] = ..., add_column_families: _Optional[_Iterable[_Union[ColumnFamily, _Mapping]]] = ..., alter_column_families: _Optional[_Iterable[_Union[ColumnFamily, _Mapping]]] = ..., alter_attributes: _Optional[_Mapping[str, str]] = ..., set_compaction_policy: _Optional[str] = ..., alter_partitioning_settings: _Optional[_Union[PartitioningSettings, _Mapping]] = ..., set_key_bloom_filter: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ..., set_read_replicas_settings: _Optional[_Union[ReadReplicasSettings, _Mapping]] = ..., add_changefeeds: _Optional[_Iterable[_Union[Changefeed, _Mapping]]] = ..., drop_changefeeds: _Optional[_Iterable[str]] = ..., rename_indexes: _Optional[_Iterable[_Union[RenameIndexItem, _Mapping]]] = ..., set_tiering: _Optional[str] = ..., drop_tiering: _Optional[_Union[_empty_pb2.Empty, _Mapping]] = ...) -> None: ...

class AlterTableResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class AzReadReplicasSettings(_message.Message):
    __slots__ = ["name", "read_replicas_count"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    READ_REPLICAS_COUNT_FIELD_NUMBER: _ClassVar[int]
    name: str
    read_replicas_count: int
    def __init__(self, name: _Optional[str] = ..., read_replicas_count: _Optional[int] = ...) -> None: ...

class BeginTransactionRequest(_message.Message):
    __slots__ = ["operation_params", "session_id", "tx_settings"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TX_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    session_id: str
    tx_settings: TransactionSettings
    def __init__(self, session_id: _Optional[str] = ..., tx_settings: _Optional[_Union[TransactionSettings, _Mapping]] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class BeginTransactionResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class BeginTransactionResult(_message.Message):
    __slots__ = ["tx_meta"]
    TX_META_FIELD_NUMBER: _ClassVar[int]
    tx_meta: TransactionMeta
    def __init__(self, tx_meta: _Optional[_Union[TransactionMeta, _Mapping]] = ...) -> None: ...

class BulkUpsertRequest(_message.Message):
    __slots__ = ["arrow_batch_settings", "csv_settings", "data", "operation_params", "rows", "table"]
    ARROW_BATCH_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    CSV_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    ROWS_FIELD_NUMBER: _ClassVar[int]
    TABLE_FIELD_NUMBER: _ClassVar[int]
    arrow_batch_settings: _ydb_formats_pb2.ArrowBatchSettings
    csv_settings: _ydb_formats_pb2.CsvSettings
    data: bytes
    operation_params: _ydb_operation_pb2.OperationParams
    rows: _ydb_value_pb2.TypedValue
    table: str
    def __init__(self, table: _Optional[str] = ..., rows: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., arrow_batch_settings: _Optional[_Union[_ydb_formats_pb2.ArrowBatchSettings, _Mapping]] = ..., csv_settings: _Optional[_Union[_ydb_formats_pb2.CsvSettings, _Mapping]] = ..., data: _Optional[bytes] = ...) -> None: ...

class BulkUpsertResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class BulkUpsertResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class CachingPolicy(_message.Message):
    __slots__ = ["preset_name"]
    PRESET_NAME_FIELD_NUMBER: _ClassVar[int]
    preset_name: str
    def __init__(self, preset_name: _Optional[str] = ...) -> None: ...

class CachingPolicyDescription(_message.Message):
    __slots__ = ["labels", "name"]
    class LabelsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    LABELS_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    labels: _containers.ScalarMap[str, str]
    name: str
    def __init__(self, name: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ...) -> None: ...

class Changefeed(_message.Message):
    __slots__ = ["attributes", "format", "initial_scan", "mode", "name", "retention_period", "virtual_timestamps"]
    class AttributesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    INITIAL_SCAN_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    RETENTION_PERIOD_FIELD_NUMBER: _ClassVar[int]
    VIRTUAL_TIMESTAMPS_FIELD_NUMBER: _ClassVar[int]
    attributes: _containers.ScalarMap[str, str]
    format: ChangefeedFormat.Format
    initial_scan: bool
    mode: ChangefeedMode.Mode
    name: str
    retention_period: _duration_pb2.Duration
    virtual_timestamps: bool
    def __init__(self, name: _Optional[str] = ..., mode: _Optional[_Union[ChangefeedMode.Mode, str]] = ..., format: _Optional[_Union[ChangefeedFormat.Format, str]] = ..., retention_period: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., virtual_timestamps: bool = ..., initial_scan: bool = ..., attributes: _Optional[_Mapping[str, str]] = ...) -> None: ...

class ChangefeedDescription(_message.Message):
    __slots__ = ["attributes", "format", "mode", "name", "state", "virtual_timestamps"]
    class State(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    class AttributesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    STATE_DISABLED: ChangefeedDescription.State
    STATE_ENABLED: ChangefeedDescription.State
    STATE_FIELD_NUMBER: _ClassVar[int]
    STATE_INITIAL_SCAN: ChangefeedDescription.State
    STATE_UNSPECIFIED: ChangefeedDescription.State
    VIRTUAL_TIMESTAMPS_FIELD_NUMBER: _ClassVar[int]
    attributes: _containers.ScalarMap[str, str]
    format: ChangefeedFormat.Format
    mode: ChangefeedMode.Mode
    name: str
    state: ChangefeedDescription.State
    virtual_timestamps: bool
    def __init__(self, name: _Optional[str] = ..., mode: _Optional[_Union[ChangefeedMode.Mode, str]] = ..., format: _Optional[_Union[ChangefeedFormat.Format, str]] = ..., state: _Optional[_Union[ChangefeedDescription.State, str]] = ..., virtual_timestamps: bool = ..., attributes: _Optional[_Mapping[str, str]] = ...) -> None: ...

class ChangefeedFormat(_message.Message):
    __slots__ = []
    class Format(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    FORMAT_DYNAMODB_STREAMS_JSON: ChangefeedFormat.Format
    FORMAT_JSON: ChangefeedFormat.Format
    FORMAT_UNSPECIFIED: ChangefeedFormat.Format
    def __init__(self) -> None: ...

class ChangefeedMode(_message.Message):
    __slots__ = []
    class Mode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    MODE_KEYS_ONLY: ChangefeedMode.Mode
    MODE_NEW_AND_OLD_IMAGES: ChangefeedMode.Mode
    MODE_NEW_IMAGE: ChangefeedMode.Mode
    MODE_OLD_IMAGE: ChangefeedMode.Mode
    MODE_UNSPECIFIED: ChangefeedMode.Mode
    MODE_UPDATES: ChangefeedMode.Mode
    def __init__(self) -> None: ...

class ClusterReplicasSettings(_message.Message):
    __slots__ = ["az_read_replicas_settings"]
    AZ_READ_REPLICAS_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    az_read_replicas_settings: _containers.RepeatedCompositeFieldContainer[AzReadReplicasSettings]
    def __init__(self, az_read_replicas_settings: _Optional[_Iterable[_Union[AzReadReplicasSettings, _Mapping]]] = ...) -> None: ...

class ColumnFamily(_message.Message):
    __slots__ = ["compression", "data", "keep_in_memory", "name"]
    class Compression(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    COMPRESSION_FIELD_NUMBER: _ClassVar[int]
    COMPRESSION_LZ4: ColumnFamily.Compression
    COMPRESSION_NONE: ColumnFamily.Compression
    COMPRESSION_UNSPECIFIED: ColumnFamily.Compression
    DATA_FIELD_NUMBER: _ClassVar[int]
    KEEP_IN_MEMORY_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    compression: ColumnFamily.Compression
    data: StoragePool
    keep_in_memory: _ydb_common_pb2.FeatureFlag.Status
    name: str
    def __init__(self, name: _Optional[str] = ..., data: _Optional[_Union[StoragePool, _Mapping]] = ..., compression: _Optional[_Union[ColumnFamily.Compression, str]] = ..., keep_in_memory: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ...) -> None: ...

class ColumnFamilyPolicy(_message.Message):
    __slots__ = ["compression", "data", "external", "keep_in_memory", "name"]
    class Compression(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    COMPRESSED: ColumnFamilyPolicy.Compression
    COMPRESSION_FIELD_NUMBER: _ClassVar[int]
    COMPRESSION_UNSPECIFIED: ColumnFamilyPolicy.Compression
    DATA_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_FIELD_NUMBER: _ClassVar[int]
    KEEP_IN_MEMORY_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    UNCOMPRESSED: ColumnFamilyPolicy.Compression
    compression: ColumnFamilyPolicy.Compression
    data: StoragePool
    external: StoragePool
    keep_in_memory: _ydb_common_pb2.FeatureFlag.Status
    name: str
    def __init__(self, name: _Optional[str] = ..., data: _Optional[_Union[StoragePool, _Mapping]] = ..., external: _Optional[_Union[StoragePool, _Mapping]] = ..., keep_in_memory: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ..., compression: _Optional[_Union[ColumnFamilyPolicy.Compression, str]] = ...) -> None: ...

class ColumnMeta(_message.Message):
    __slots__ = ["family", "name", "type"]
    FAMILY_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    family: str
    name: str
    type: _ydb_value_pb2.Type
    def __init__(self, name: _Optional[str] = ..., type: _Optional[_Union[_ydb_value_pb2.Type, _Mapping]] = ..., family: _Optional[str] = ...) -> None: ...

class CommitTransactionRequest(_message.Message):
    __slots__ = ["collect_stats", "operation_params", "session_id", "tx_id"]
    COLLECT_STATS_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TX_ID_FIELD_NUMBER: _ClassVar[int]
    collect_stats: QueryStatsCollection.Mode
    operation_params: _ydb_operation_pb2.OperationParams
    session_id: str
    tx_id: str
    def __init__(self, session_id: _Optional[str] = ..., tx_id: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., collect_stats: _Optional[_Union[QueryStatsCollection.Mode, str]] = ...) -> None: ...

class CommitTransactionResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class CommitTransactionResult(_message.Message):
    __slots__ = ["query_stats"]
    QUERY_STATS_FIELD_NUMBER: _ClassVar[int]
    query_stats: _ydb_query_stats_pb2.QueryStats
    def __init__(self, query_stats: _Optional[_Union[_ydb_query_stats_pb2.QueryStats, _Mapping]] = ...) -> None: ...

class CompactionPolicy(_message.Message):
    __slots__ = ["preset_name"]
    PRESET_NAME_FIELD_NUMBER: _ClassVar[int]
    preset_name: str
    def __init__(self, preset_name: _Optional[str] = ...) -> None: ...

class CompactionPolicyDescription(_message.Message):
    __slots__ = ["labels", "name"]
    class LabelsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    LABELS_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    labels: _containers.ScalarMap[str, str]
    name: str
    def __init__(self, name: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ...) -> None: ...

class CopyTableItem(_message.Message):
    __slots__ = ["destination_path", "omit_indexes", "source_path"]
    DESTINATION_PATH_FIELD_NUMBER: _ClassVar[int]
    OMIT_INDEXES_FIELD_NUMBER: _ClassVar[int]
    SOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
    destination_path: str
    omit_indexes: bool
    source_path: str
    def __init__(self, source_path: _Optional[str] = ..., destination_path: _Optional[str] = ..., omit_indexes: bool = ...) -> None: ...

class CopyTableRequest(_message.Message):
    __slots__ = ["destination_path", "operation_params", "session_id", "source_path"]
    DESTINATION_PATH_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
    destination_path: str
    operation_params: _ydb_operation_pb2.OperationParams
    session_id: str
    source_path: str
    def __init__(self, session_id: _Optional[str] = ..., source_path: _Optional[str] = ..., destination_path: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class CopyTableResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class CopyTablesRequest(_message.Message):
    __slots__ = ["operation_params", "session_id", "tables"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TABLES_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    session_id: str
    tables: _containers.RepeatedCompositeFieldContainer[CopyTableItem]
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., session_id: _Optional[str] = ..., tables: _Optional[_Iterable[_Union[CopyTableItem, _Mapping]]] = ...) -> None: ...

class CopyTablesResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class CreateSessionRequest(_message.Message):
    __slots__ = ["operation_params"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class CreateSessionResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class CreateSessionResult(_message.Message):
    __slots__ = ["session_id"]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    def __init__(self, session_id: _Optional[str] = ...) -> None: ...

class CreateTableRequest(_message.Message):
    __slots__ = ["attributes", "column_families", "columns", "compaction_policy", "indexes", "key_bloom_filter", "operation_params", "partition_at_keys", "partitioning_settings", "path", "primary_key", "profile", "read_replicas_settings", "session_id", "storage_settings", "tiering", "ttl_settings", "uniform_partitions"]
    class AttributesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    COLUMNS_FIELD_NUMBER: _ClassVar[int]
    COLUMN_FAMILIES_FIELD_NUMBER: _ClassVar[int]
    COMPACTION_POLICY_FIELD_NUMBER: _ClassVar[int]
    INDEXES_FIELD_NUMBER: _ClassVar[int]
    KEY_BLOOM_FILTER_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PARTITIONING_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    PARTITION_AT_KEYS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    PRIMARY_KEY_FIELD_NUMBER: _ClassVar[int]
    PROFILE_FIELD_NUMBER: _ClassVar[int]
    READ_REPLICAS_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    STORAGE_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    TIERING_FIELD_NUMBER: _ClassVar[int]
    TTL_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    UNIFORM_PARTITIONS_FIELD_NUMBER: _ClassVar[int]
    attributes: _containers.ScalarMap[str, str]
    column_families: _containers.RepeatedCompositeFieldContainer[ColumnFamily]
    columns: _containers.RepeatedCompositeFieldContainer[ColumnMeta]
    compaction_policy: str
    indexes: _containers.RepeatedCompositeFieldContainer[TableIndex]
    key_bloom_filter: _ydb_common_pb2.FeatureFlag.Status
    operation_params: _ydb_operation_pb2.OperationParams
    partition_at_keys: ExplicitPartitions
    partitioning_settings: PartitioningSettings
    path: str
    primary_key: _containers.RepeatedScalarFieldContainer[str]
    profile: TableProfile
    read_replicas_settings: ReadReplicasSettings
    session_id: str
    storage_settings: StorageSettings
    tiering: str
    ttl_settings: TtlSettings
    uniform_partitions: int
    def __init__(self, session_id: _Optional[str] = ..., path: _Optional[str] = ..., columns: _Optional[_Iterable[_Union[ColumnMeta, _Mapping]]] = ..., primary_key: _Optional[_Iterable[str]] = ..., profile: _Optional[_Union[TableProfile, _Mapping]] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., indexes: _Optional[_Iterable[_Union[TableIndex, _Mapping]]] = ..., ttl_settings: _Optional[_Union[TtlSettings, _Mapping]] = ..., storage_settings: _Optional[_Union[StorageSettings, _Mapping]] = ..., column_families: _Optional[_Iterable[_Union[ColumnFamily, _Mapping]]] = ..., attributes: _Optional[_Mapping[str, str]] = ..., compaction_policy: _Optional[str] = ..., uniform_partitions: _Optional[int] = ..., partition_at_keys: _Optional[_Union[ExplicitPartitions, _Mapping]] = ..., partitioning_settings: _Optional[_Union[PartitioningSettings, _Mapping]] = ..., key_bloom_filter: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ..., read_replicas_settings: _Optional[_Union[ReadReplicasSettings, _Mapping]] = ..., tiering: _Optional[str] = ...) -> None: ...

class CreateTableResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DateTypeColumnModeSettings(_message.Message):
    __slots__ = ["column_name", "expire_after_seconds"]
    COLUMN_NAME_FIELD_NUMBER: _ClassVar[int]
    EXPIRE_AFTER_SECONDS_FIELD_NUMBER: _ClassVar[int]
    column_name: str
    expire_after_seconds: int
    def __init__(self, column_name: _Optional[str] = ..., expire_after_seconds: _Optional[int] = ...) -> None: ...

class DeleteSessionRequest(_message.Message):
    __slots__ = ["operation_params", "session_id"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    session_id: str
    def __init__(self, session_id: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class DeleteSessionResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeTableOptionsRequest(_message.Message):
    __slots__ = ["operation_params"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class DescribeTableOptionsResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeTableOptionsResult(_message.Message):
    __slots__ = ["caching_policy_presets", "compaction_policy_presets", "execution_policy_presets", "partitioning_policy_presets", "replication_policy_presets", "storage_policy_presets", "table_profile_presets"]
    CACHING_POLICY_PRESETS_FIELD_NUMBER: _ClassVar[int]
    COMPACTION_POLICY_PRESETS_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_POLICY_PRESETS_FIELD_NUMBER: _ClassVar[int]
    PARTITIONING_POLICY_PRESETS_FIELD_NUMBER: _ClassVar[int]
    REPLICATION_POLICY_PRESETS_FIELD_NUMBER: _ClassVar[int]
    STORAGE_POLICY_PRESETS_FIELD_NUMBER: _ClassVar[int]
    TABLE_PROFILE_PRESETS_FIELD_NUMBER: _ClassVar[int]
    caching_policy_presets: _containers.RepeatedCompositeFieldContainer[CachingPolicyDescription]
    compaction_policy_presets: _containers.RepeatedCompositeFieldContainer[CompactionPolicyDescription]
    execution_policy_presets: _containers.RepeatedCompositeFieldContainer[ExecutionPolicyDescription]
    partitioning_policy_presets: _containers.RepeatedCompositeFieldContainer[PartitioningPolicyDescription]
    replication_policy_presets: _containers.RepeatedCompositeFieldContainer[ReplicationPolicyDescription]
    storage_policy_presets: _containers.RepeatedCompositeFieldContainer[StoragePolicyDescription]
    table_profile_presets: _containers.RepeatedCompositeFieldContainer[TableProfileDescription]
    def __init__(self, table_profile_presets: _Optional[_Iterable[_Union[TableProfileDescription, _Mapping]]] = ..., storage_policy_presets: _Optional[_Iterable[_Union[StoragePolicyDescription, _Mapping]]] = ..., compaction_policy_presets: _Optional[_Iterable[_Union[CompactionPolicyDescription, _Mapping]]] = ..., partitioning_policy_presets: _Optional[_Iterable[_Union[PartitioningPolicyDescription, _Mapping]]] = ..., execution_policy_presets: _Optional[_Iterable[_Union[ExecutionPolicyDescription, _Mapping]]] = ..., replication_policy_presets: _Optional[_Iterable[_Union[ReplicationPolicyDescription, _Mapping]]] = ..., caching_policy_presets: _Optional[_Iterable[_Union[CachingPolicyDescription, _Mapping]]] = ...) -> None: ...

class DescribeTableRequest(_message.Message):
    __slots__ = ["include_partition_stats", "include_shard_key_bounds", "include_table_stats", "operation_params", "path", "session_id"]
    INCLUDE_PARTITION_STATS_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_SHARD_KEY_BOUNDS_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_TABLE_STATS_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    include_partition_stats: bool
    include_shard_key_bounds: bool
    include_table_stats: bool
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    session_id: str
    def __init__(self, session_id: _Optional[str] = ..., path: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., include_shard_key_bounds: bool = ..., include_table_stats: bool = ..., include_partition_stats: bool = ...) -> None: ...

class DescribeTableResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeTableResult(_message.Message):
    __slots__ = ["attributes", "changefeeds", "column_families", "columns", "indexes", "key_bloom_filter", "partitioning_settings", "primary_key", "read_replicas_settings", "self", "shard_key_bounds", "storage_settings", "table_stats", "tiering", "ttl_settings"]
    class AttributesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    CHANGEFEEDS_FIELD_NUMBER: _ClassVar[int]
    COLUMNS_FIELD_NUMBER: _ClassVar[int]
    COLUMN_FAMILIES_FIELD_NUMBER: _ClassVar[int]
    INDEXES_FIELD_NUMBER: _ClassVar[int]
    KEY_BLOOM_FILTER_FIELD_NUMBER: _ClassVar[int]
    PARTITIONING_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    PRIMARY_KEY_FIELD_NUMBER: _ClassVar[int]
    READ_REPLICAS_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    SELF_FIELD_NUMBER: _ClassVar[int]
    SHARD_KEY_BOUNDS_FIELD_NUMBER: _ClassVar[int]
    STORAGE_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    TABLE_STATS_FIELD_NUMBER: _ClassVar[int]
    TIERING_FIELD_NUMBER: _ClassVar[int]
    TTL_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    attributes: _containers.ScalarMap[str, str]
    changefeeds: _containers.RepeatedCompositeFieldContainer[ChangefeedDescription]
    column_families: _containers.RepeatedCompositeFieldContainer[ColumnFamily]
    columns: _containers.RepeatedCompositeFieldContainer[ColumnMeta]
    indexes: _containers.RepeatedCompositeFieldContainer[TableIndexDescription]
    key_bloom_filter: _ydb_common_pb2.FeatureFlag.Status
    partitioning_settings: PartitioningSettings
    primary_key: _containers.RepeatedScalarFieldContainer[str]
    read_replicas_settings: ReadReplicasSettings
    self: _ydb_scheme_pb2.Entry
    shard_key_bounds: _containers.RepeatedCompositeFieldContainer[_ydb_value_pb2.TypedValue]
    storage_settings: StorageSettings
    table_stats: TableStats
    tiering: str
    ttl_settings: TtlSettings
    def __init__(self, self_: _Optional[_Union[_ydb_scheme_pb2.Entry, _Mapping]] = ..., columns: _Optional[_Iterable[_Union[ColumnMeta, _Mapping]]] = ..., primary_key: _Optional[_Iterable[str]] = ..., shard_key_bounds: _Optional[_Iterable[_Union[_ydb_value_pb2.TypedValue, _Mapping]]] = ..., indexes: _Optional[_Iterable[_Union[TableIndexDescription, _Mapping]]] = ..., table_stats: _Optional[_Union[TableStats, _Mapping]] = ..., ttl_settings: _Optional[_Union[TtlSettings, _Mapping]] = ..., storage_settings: _Optional[_Union[StorageSettings, _Mapping]] = ..., column_families: _Optional[_Iterable[_Union[ColumnFamily, _Mapping]]] = ..., attributes: _Optional[_Mapping[str, str]] = ..., partitioning_settings: _Optional[_Union[PartitioningSettings, _Mapping]] = ..., key_bloom_filter: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ..., read_replicas_settings: _Optional[_Union[ReadReplicasSettings, _Mapping]] = ..., changefeeds: _Optional[_Iterable[_Union[ChangefeedDescription, _Mapping]]] = ..., tiering: _Optional[str] = ...) -> None: ...

class DropTableRequest(_message.Message):
    __slots__ = ["operation_params", "path", "session_id"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    session_id: str
    def __init__(self, session_id: _Optional[str] = ..., path: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class DropTableResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ExecuteDataQueryRequest(_message.Message):
    __slots__ = ["collect_stats", "operation_params", "parameters", "query", "query_cache_policy", "session_id", "tx_control"]
    class ParametersEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _ydb_value_pb2.TypedValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ...) -> None: ...
    COLLECT_STATS_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    QUERY_CACHE_POLICY_FIELD_NUMBER: _ClassVar[int]
    QUERY_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TX_CONTROL_FIELD_NUMBER: _ClassVar[int]
    collect_stats: QueryStatsCollection.Mode
    operation_params: _ydb_operation_pb2.OperationParams
    parameters: _containers.MessageMap[str, _ydb_value_pb2.TypedValue]
    query: Query
    query_cache_policy: QueryCachePolicy
    session_id: str
    tx_control: TransactionControl
    def __init__(self, session_id: _Optional[str] = ..., tx_control: _Optional[_Union[TransactionControl, _Mapping]] = ..., query: _Optional[_Union[Query, _Mapping]] = ..., parameters: _Optional[_Mapping[str, _ydb_value_pb2.TypedValue]] = ..., query_cache_policy: _Optional[_Union[QueryCachePolicy, _Mapping]] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., collect_stats: _Optional[_Union[QueryStatsCollection.Mode, str]] = ...) -> None: ...

class ExecuteDataQueryResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ExecuteQueryResult(_message.Message):
    __slots__ = ["query_meta", "query_stats", "result_sets", "tx_meta"]
    QUERY_META_FIELD_NUMBER: _ClassVar[int]
    QUERY_STATS_FIELD_NUMBER: _ClassVar[int]
    RESULT_SETS_FIELD_NUMBER: _ClassVar[int]
    TX_META_FIELD_NUMBER: _ClassVar[int]
    query_meta: QueryMeta
    query_stats: _ydb_query_stats_pb2.QueryStats
    result_sets: _containers.RepeatedCompositeFieldContainer[_ydb_value_pb2.ResultSet]
    tx_meta: TransactionMeta
    def __init__(self, result_sets: _Optional[_Iterable[_Union[_ydb_value_pb2.ResultSet, _Mapping]]] = ..., tx_meta: _Optional[_Union[TransactionMeta, _Mapping]] = ..., query_meta: _Optional[_Union[QueryMeta, _Mapping]] = ..., query_stats: _Optional[_Union[_ydb_query_stats_pb2.QueryStats, _Mapping]] = ...) -> None: ...

class ExecuteScanQueryPartialResponse(_message.Message):
    __slots__ = ["issues", "result", "status"]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    result: ExecuteScanQueryPartialResult
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., result: _Optional[_Union[ExecuteScanQueryPartialResult, _Mapping]] = ...) -> None: ...

class ExecuteScanQueryPartialResult(_message.Message):
    __slots__ = ["query_stats", "result_set"]
    QUERY_STATS_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_FIELD_NUMBER: _ClassVar[int]
    query_stats: _ydb_query_stats_pb2.QueryStats
    result_set: _ydb_value_pb2.ResultSet
    def __init__(self, result_set: _Optional[_Union[_ydb_value_pb2.ResultSet, _Mapping]] = ..., query_stats: _Optional[_Union[_ydb_query_stats_pb2.QueryStats, _Mapping]] = ...) -> None: ...

class ExecuteScanQueryRequest(_message.Message):
    __slots__ = ["collect_stats", "mode", "parameters", "query"]
    class Mode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    class ParametersEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _ydb_value_pb2.TypedValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ...) -> None: ...
    COLLECT_STATS_FIELD_NUMBER: _ClassVar[int]
    MODE_EXEC: ExecuteScanQueryRequest.Mode
    MODE_EXPLAIN: ExecuteScanQueryRequest.Mode
    MODE_FIELD_NUMBER: _ClassVar[int]
    MODE_UNSPECIFIED: ExecuteScanQueryRequest.Mode
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    QUERY_FIELD_NUMBER: _ClassVar[int]
    collect_stats: QueryStatsCollection.Mode
    mode: ExecuteScanQueryRequest.Mode
    parameters: _containers.MessageMap[str, _ydb_value_pb2.TypedValue]
    query: Query
    def __init__(self, query: _Optional[_Union[Query, _Mapping]] = ..., parameters: _Optional[_Mapping[str, _ydb_value_pb2.TypedValue]] = ..., mode: _Optional[_Union[ExecuteScanQueryRequest.Mode, str]] = ..., collect_stats: _Optional[_Union[QueryStatsCollection.Mode, str]] = ...) -> None: ...

class ExecuteSchemeQueryRequest(_message.Message):
    __slots__ = ["operation_params", "session_id", "yql_text"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    YQL_TEXT_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    session_id: str
    yql_text: str
    def __init__(self, session_id: _Optional[str] = ..., yql_text: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class ExecuteSchemeQueryResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ExecutionPolicy(_message.Message):
    __slots__ = ["preset_name"]
    PRESET_NAME_FIELD_NUMBER: _ClassVar[int]
    preset_name: str
    def __init__(self, preset_name: _Optional[str] = ...) -> None: ...

class ExecutionPolicyDescription(_message.Message):
    __slots__ = ["labels", "name"]
    class LabelsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    LABELS_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    labels: _containers.ScalarMap[str, str]
    name: str
    def __init__(self, name: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ...) -> None: ...

class ExplainDataQueryRequest(_message.Message):
    __slots__ = ["operation_params", "session_id", "yql_text"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    YQL_TEXT_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    session_id: str
    yql_text: str
    def __init__(self, session_id: _Optional[str] = ..., yql_text: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class ExplainDataQueryResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ExplainQueryResult(_message.Message):
    __slots__ = ["query_ast", "query_plan"]
    QUERY_AST_FIELD_NUMBER: _ClassVar[int]
    QUERY_PLAN_FIELD_NUMBER: _ClassVar[int]
    query_ast: str
    query_plan: str
    def __init__(self, query_ast: _Optional[str] = ..., query_plan: _Optional[str] = ...) -> None: ...

class ExplicitPartitions(_message.Message):
    __slots__ = ["split_points"]
    SPLIT_POINTS_FIELD_NUMBER: _ClassVar[int]
    split_points: _containers.RepeatedCompositeFieldContainer[_ydb_value_pb2.TypedValue]
    def __init__(self, split_points: _Optional[_Iterable[_Union[_ydb_value_pb2.TypedValue, _Mapping]]] = ...) -> None: ...

class GlobalAsyncIndex(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class GlobalIndex(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class IndexBuildDescription(_message.Message):
    __slots__ = ["index", "path"]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    index: TableIndex
    path: str
    def __init__(self, path: _Optional[str] = ..., index: _Optional[_Union[TableIndex, _Mapping]] = ...) -> None: ...

class IndexBuildMetadata(_message.Message):
    __slots__ = ["description", "progress", "state"]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    description: IndexBuildDescription
    progress: float
    state: IndexBuildState.State
    def __init__(self, description: _Optional[_Union[IndexBuildDescription, _Mapping]] = ..., state: _Optional[_Union[IndexBuildState.State, str]] = ..., progress: _Optional[float] = ...) -> None: ...

class IndexBuildState(_message.Message):
    __slots__ = []
    class State(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    STATE_APPLYING: IndexBuildState.State
    STATE_CANCELLATION: IndexBuildState.State
    STATE_CANCELLED: IndexBuildState.State
    STATE_DONE: IndexBuildState.State
    STATE_PREPARING: IndexBuildState.State
    STATE_REJECTED: IndexBuildState.State
    STATE_REJECTION: IndexBuildState.State
    STATE_TRANSFERING_DATA: IndexBuildState.State
    STATE_UNSPECIFIED: IndexBuildState.State
    def __init__(self) -> None: ...

class KeepAliveRequest(_message.Message):
    __slots__ = ["operation_params", "session_id"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    session_id: str
    def __init__(self, session_id: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class KeepAliveResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class KeepAliveResult(_message.Message):
    __slots__ = ["session_status"]
    class SessionStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    SESSION_STATUS_BUSY: KeepAliveResult.SessionStatus
    SESSION_STATUS_FIELD_NUMBER: _ClassVar[int]
    SESSION_STATUS_READY: KeepAliveResult.SessionStatus
    SESSION_STATUS_UNSPECIFIED: KeepAliveResult.SessionStatus
    session_status: KeepAliveResult.SessionStatus
    def __init__(self, session_status: _Optional[_Union[KeepAliveResult.SessionStatus, str]] = ...) -> None: ...

class KeyRange(_message.Message):
    __slots__ = ["greater", "greater_or_equal", "less", "less_or_equal"]
    GREATER_FIELD_NUMBER: _ClassVar[int]
    GREATER_OR_EQUAL_FIELD_NUMBER: _ClassVar[int]
    LESS_FIELD_NUMBER: _ClassVar[int]
    LESS_OR_EQUAL_FIELD_NUMBER: _ClassVar[int]
    greater: _ydb_value_pb2.TypedValue
    greater_or_equal: _ydb_value_pb2.TypedValue
    less: _ydb_value_pb2.TypedValue
    less_or_equal: _ydb_value_pb2.TypedValue
    def __init__(self, greater: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ..., greater_or_equal: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ..., less: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ..., less_or_equal: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ...) -> None: ...

class OnlineModeSettings(_message.Message):
    __slots__ = ["allow_inconsistent_reads"]
    ALLOW_INCONSISTENT_READS_FIELD_NUMBER: _ClassVar[int]
    allow_inconsistent_reads: bool
    def __init__(self, allow_inconsistent_reads: bool = ...) -> None: ...

class PartitionStats(_message.Message):
    __slots__ = ["rows_estimate", "store_size"]
    ROWS_ESTIMATE_FIELD_NUMBER: _ClassVar[int]
    STORE_SIZE_FIELD_NUMBER: _ClassVar[int]
    rows_estimate: int
    store_size: int
    def __init__(self, rows_estimate: _Optional[int] = ..., store_size: _Optional[int] = ...) -> None: ...

class PartitioningPolicy(_message.Message):
    __slots__ = ["auto_partitioning", "explicit_partitions", "preset_name", "uniform_partitions"]
    class AutoPartitioningPolicy(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    AUTO_PARTITIONING_FIELD_NUMBER: _ClassVar[int]
    AUTO_PARTITIONING_POLICY_UNSPECIFIED: PartitioningPolicy.AutoPartitioningPolicy
    AUTO_SPLIT: PartitioningPolicy.AutoPartitioningPolicy
    AUTO_SPLIT_MERGE: PartitioningPolicy.AutoPartitioningPolicy
    DISABLED: PartitioningPolicy.AutoPartitioningPolicy
    EXPLICIT_PARTITIONS_FIELD_NUMBER: _ClassVar[int]
    PRESET_NAME_FIELD_NUMBER: _ClassVar[int]
    UNIFORM_PARTITIONS_FIELD_NUMBER: _ClassVar[int]
    auto_partitioning: PartitioningPolicy.AutoPartitioningPolicy
    explicit_partitions: ExplicitPartitions
    preset_name: str
    uniform_partitions: int
    def __init__(self, preset_name: _Optional[str] = ..., auto_partitioning: _Optional[_Union[PartitioningPolicy.AutoPartitioningPolicy, str]] = ..., uniform_partitions: _Optional[int] = ..., explicit_partitions: _Optional[_Union[ExplicitPartitions, _Mapping]] = ...) -> None: ...

class PartitioningPolicyDescription(_message.Message):
    __slots__ = ["labels", "name"]
    class LabelsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    LABELS_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    labels: _containers.ScalarMap[str, str]
    name: str
    def __init__(self, name: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ...) -> None: ...

class PartitioningSettings(_message.Message):
    __slots__ = ["max_partitions_count", "min_partitions_count", "partition_by", "partition_size_mb", "partitioning_by_load", "partitioning_by_size"]
    MAX_PARTITIONS_COUNT_FIELD_NUMBER: _ClassVar[int]
    MIN_PARTITIONS_COUNT_FIELD_NUMBER: _ClassVar[int]
    PARTITIONING_BY_LOAD_FIELD_NUMBER: _ClassVar[int]
    PARTITIONING_BY_SIZE_FIELD_NUMBER: _ClassVar[int]
    PARTITION_BY_FIELD_NUMBER: _ClassVar[int]
    PARTITION_SIZE_MB_FIELD_NUMBER: _ClassVar[int]
    max_partitions_count: int
    min_partitions_count: int
    partition_by: _containers.RepeatedScalarFieldContainer[str]
    partition_size_mb: int
    partitioning_by_load: _ydb_common_pb2.FeatureFlag.Status
    partitioning_by_size: _ydb_common_pb2.FeatureFlag.Status
    def __init__(self, partition_by: _Optional[_Iterable[str]] = ..., partitioning_by_size: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ..., partition_size_mb: _Optional[int] = ..., partitioning_by_load: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ..., min_partitions_count: _Optional[int] = ..., max_partitions_count: _Optional[int] = ...) -> None: ...

class PrepareDataQueryRequest(_message.Message):
    __slots__ = ["operation_params", "session_id", "yql_text"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    YQL_TEXT_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    session_id: str
    yql_text: str
    def __init__(self, session_id: _Optional[str] = ..., yql_text: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class PrepareDataQueryResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class PrepareQueryResult(_message.Message):
    __slots__ = ["parameters_types", "query_id"]
    class ParametersTypesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _ydb_value_pb2.Type
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_ydb_value_pb2.Type, _Mapping]] = ...) -> None: ...
    PARAMETERS_TYPES_FIELD_NUMBER: _ClassVar[int]
    QUERY_ID_FIELD_NUMBER: _ClassVar[int]
    parameters_types: _containers.MessageMap[str, _ydb_value_pb2.Type]
    query_id: str
    def __init__(self, query_id: _Optional[str] = ..., parameters_types: _Optional[_Mapping[str, _ydb_value_pb2.Type]] = ...) -> None: ...

class Query(_message.Message):
    __slots__ = ["id", "yql_text"]
    ID_FIELD_NUMBER: _ClassVar[int]
    YQL_TEXT_FIELD_NUMBER: _ClassVar[int]
    id: str
    yql_text: str
    def __init__(self, yql_text: _Optional[str] = ..., id: _Optional[str] = ...) -> None: ...

class QueryCachePolicy(_message.Message):
    __slots__ = ["keep_in_cache"]
    KEEP_IN_CACHE_FIELD_NUMBER: _ClassVar[int]
    keep_in_cache: bool
    def __init__(self, keep_in_cache: bool = ...) -> None: ...

class QueryMeta(_message.Message):
    __slots__ = ["id", "parameters_types"]
    class ParametersTypesEntry(_message.Message):
        __slots__ = ["key", "value"]
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

class QueryStatsCollection(_message.Message):
    __slots__ = []
    class Mode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    STATS_COLLECTION_BASIC: QueryStatsCollection.Mode
    STATS_COLLECTION_FULL: QueryStatsCollection.Mode
    STATS_COLLECTION_NONE: QueryStatsCollection.Mode
    STATS_COLLECTION_PROFILE: QueryStatsCollection.Mode
    STATS_COLLECTION_UNSPECIFIED: QueryStatsCollection.Mode
    def __init__(self) -> None: ...

class ReadReplicasSettings(_message.Message):
    __slots__ = ["any_az_read_replicas_count", "per_az_read_replicas_count"]
    ANY_AZ_READ_REPLICAS_COUNT_FIELD_NUMBER: _ClassVar[int]
    PER_AZ_READ_REPLICAS_COUNT_FIELD_NUMBER: _ClassVar[int]
    any_az_read_replicas_count: int
    per_az_read_replicas_count: int
    def __init__(self, per_az_read_replicas_count: _Optional[int] = ..., any_az_read_replicas_count: _Optional[int] = ...) -> None: ...

class ReadRowsRequest(_message.Message):
    __slots__ = ["columns", "keys", "path", "session_id"]
    COLUMNS_FIELD_NUMBER: _ClassVar[int]
    KEYS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    columns: _containers.RepeatedScalarFieldContainer[str]
    keys: _ydb_value_pb2.TypedValue
    path: str
    session_id: str
    def __init__(self, session_id: _Optional[str] = ..., path: _Optional[str] = ..., keys: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ..., columns: _Optional[_Iterable[str]] = ...) -> None: ...

class ReadRowsResponse(_message.Message):
    __slots__ = ["issues", "result_set", "status"]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    RESULT_SET_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    result_set: _ydb_value_pb2.ResultSet
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., result_set: _Optional[_Union[_ydb_value_pb2.ResultSet, _Mapping]] = ...) -> None: ...

class ReadTableRequest(_message.Message):
    __slots__ = ["columns", "key_range", "ordered", "path", "row_limit", "session_id", "use_snapshot"]
    COLUMNS_FIELD_NUMBER: _ClassVar[int]
    KEY_RANGE_FIELD_NUMBER: _ClassVar[int]
    ORDERED_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    ROW_LIMIT_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    USE_SNAPSHOT_FIELD_NUMBER: _ClassVar[int]
    columns: _containers.RepeatedScalarFieldContainer[str]
    key_range: KeyRange
    ordered: bool
    path: str
    row_limit: int
    session_id: str
    use_snapshot: _ydb_common_pb2.FeatureFlag.Status
    def __init__(self, session_id: _Optional[str] = ..., path: _Optional[str] = ..., key_range: _Optional[_Union[KeyRange, _Mapping]] = ..., columns: _Optional[_Iterable[str]] = ..., ordered: bool = ..., row_limit: _Optional[int] = ..., use_snapshot: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ...) -> None: ...

class ReadTableResponse(_message.Message):
    __slots__ = ["issues", "result", "snapshot", "status"]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    SNAPSHOT_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    result: ReadTableResult
    snapshot: _ydb_common_pb2.VirtualTimestamp
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., snapshot: _Optional[_Union[_ydb_common_pb2.VirtualTimestamp, _Mapping]] = ..., result: _Optional[_Union[ReadTableResult, _Mapping]] = ...) -> None: ...

class ReadTableResult(_message.Message):
    __slots__ = ["result_set"]
    RESULT_SET_FIELD_NUMBER: _ClassVar[int]
    result_set: _ydb_value_pb2.ResultSet
    def __init__(self, result_set: _Optional[_Union[_ydb_value_pb2.ResultSet, _Mapping]] = ...) -> None: ...

class RenameIndexItem(_message.Message):
    __slots__ = ["destination_name", "replace_destination", "source_name"]
    DESTINATION_NAME_FIELD_NUMBER: _ClassVar[int]
    REPLACE_DESTINATION_FIELD_NUMBER: _ClassVar[int]
    SOURCE_NAME_FIELD_NUMBER: _ClassVar[int]
    destination_name: str
    replace_destination: bool
    source_name: str
    def __init__(self, source_name: _Optional[str] = ..., destination_name: _Optional[str] = ..., replace_destination: bool = ...) -> None: ...

class RenameTableItem(_message.Message):
    __slots__ = ["destination_path", "replace_destination", "source_path"]
    DESTINATION_PATH_FIELD_NUMBER: _ClassVar[int]
    REPLACE_DESTINATION_FIELD_NUMBER: _ClassVar[int]
    SOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
    destination_path: str
    replace_destination: bool
    source_path: str
    def __init__(self, source_path: _Optional[str] = ..., destination_path: _Optional[str] = ..., replace_destination: bool = ...) -> None: ...

class RenameTablesRequest(_message.Message):
    __slots__ = ["operation_params", "session_id", "tables"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TABLES_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    session_id: str
    tables: _containers.RepeatedCompositeFieldContainer[RenameTableItem]
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., session_id: _Optional[str] = ..., tables: _Optional[_Iterable[_Union[RenameTableItem, _Mapping]]] = ...) -> None: ...

class RenameTablesResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ReplicationPolicy(_message.Message):
    __slots__ = ["allow_promotion", "create_per_availability_zone", "preset_name", "replicas_count"]
    ALLOW_PROMOTION_FIELD_NUMBER: _ClassVar[int]
    CREATE_PER_AVAILABILITY_ZONE_FIELD_NUMBER: _ClassVar[int]
    PRESET_NAME_FIELD_NUMBER: _ClassVar[int]
    REPLICAS_COUNT_FIELD_NUMBER: _ClassVar[int]
    allow_promotion: _ydb_common_pb2.FeatureFlag.Status
    create_per_availability_zone: _ydb_common_pb2.FeatureFlag.Status
    preset_name: str
    replicas_count: int
    def __init__(self, preset_name: _Optional[str] = ..., replicas_count: _Optional[int] = ..., create_per_availability_zone: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ..., allow_promotion: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ...) -> None: ...

class ReplicationPolicyDescription(_message.Message):
    __slots__ = ["labels", "name"]
    class LabelsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    LABELS_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    labels: _containers.ScalarMap[str, str]
    name: str
    def __init__(self, name: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ...) -> None: ...

class RollbackTransactionRequest(_message.Message):
    __slots__ = ["operation_params", "session_id", "tx_id"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TX_ID_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    session_id: str
    tx_id: str
    def __init__(self, session_id: _Optional[str] = ..., tx_id: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class RollbackTransactionResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class SerializableModeSettings(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class SnapshotModeSettings(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class StaleModeSettings(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class StoragePolicy(_message.Message):
    __slots__ = ["column_families", "data", "external", "keep_in_memory", "log", "preset_name", "syslog"]
    COLUMN_FAMILIES_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_FIELD_NUMBER: _ClassVar[int]
    KEEP_IN_MEMORY_FIELD_NUMBER: _ClassVar[int]
    LOG_FIELD_NUMBER: _ClassVar[int]
    PRESET_NAME_FIELD_NUMBER: _ClassVar[int]
    SYSLOG_FIELD_NUMBER: _ClassVar[int]
    column_families: _containers.RepeatedCompositeFieldContainer[ColumnFamilyPolicy]
    data: StoragePool
    external: StoragePool
    keep_in_memory: _ydb_common_pb2.FeatureFlag.Status
    log: StoragePool
    preset_name: str
    syslog: StoragePool
    def __init__(self, preset_name: _Optional[str] = ..., syslog: _Optional[_Union[StoragePool, _Mapping]] = ..., log: _Optional[_Union[StoragePool, _Mapping]] = ..., data: _Optional[_Union[StoragePool, _Mapping]] = ..., external: _Optional[_Union[StoragePool, _Mapping]] = ..., keep_in_memory: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ..., column_families: _Optional[_Iterable[_Union[ColumnFamilyPolicy, _Mapping]]] = ...) -> None: ...

class StoragePolicyDescription(_message.Message):
    __slots__ = ["labels", "name"]
    class LabelsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    LABELS_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    labels: _containers.ScalarMap[str, str]
    name: str
    def __init__(self, name: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ...) -> None: ...

class StoragePool(_message.Message):
    __slots__ = ["media"]
    MEDIA_FIELD_NUMBER: _ClassVar[int]
    media: str
    def __init__(self, media: _Optional[str] = ...) -> None: ...

class StorageSettings(_message.Message):
    __slots__ = ["external", "store_external_blobs", "tablet_commit_log0", "tablet_commit_log1"]
    EXTERNAL_FIELD_NUMBER: _ClassVar[int]
    STORE_EXTERNAL_BLOBS_FIELD_NUMBER: _ClassVar[int]
    TABLET_COMMIT_LOG0_FIELD_NUMBER: _ClassVar[int]
    TABLET_COMMIT_LOG1_FIELD_NUMBER: _ClassVar[int]
    external: StoragePool
    store_external_blobs: _ydb_common_pb2.FeatureFlag.Status
    tablet_commit_log0: StoragePool
    tablet_commit_log1: StoragePool
    def __init__(self, tablet_commit_log0: _Optional[_Union[StoragePool, _Mapping]] = ..., tablet_commit_log1: _Optional[_Union[StoragePool, _Mapping]] = ..., external: _Optional[_Union[StoragePool, _Mapping]] = ..., store_external_blobs: _Optional[_Union[_ydb_common_pb2.FeatureFlag.Status, str]] = ...) -> None: ...

class TableIndex(_message.Message):
    __slots__ = ["data_columns", "global_async_index", "global_index", "index_columns", "name"]
    DATA_COLUMNS_FIELD_NUMBER: _ClassVar[int]
    GLOBAL_ASYNC_INDEX_FIELD_NUMBER: _ClassVar[int]
    GLOBAL_INDEX_FIELD_NUMBER: _ClassVar[int]
    INDEX_COLUMNS_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    data_columns: _containers.RepeatedScalarFieldContainer[str]
    global_async_index: GlobalAsyncIndex
    global_index: GlobalIndex
    index_columns: _containers.RepeatedScalarFieldContainer[str]
    name: str
    def __init__(self, name: _Optional[str] = ..., index_columns: _Optional[_Iterable[str]] = ..., global_index: _Optional[_Union[GlobalIndex, _Mapping]] = ..., global_async_index: _Optional[_Union[GlobalAsyncIndex, _Mapping]] = ..., data_columns: _Optional[_Iterable[str]] = ...) -> None: ...

class TableIndexDescription(_message.Message):
    __slots__ = ["data_columns", "global_async_index", "global_index", "index_columns", "name", "size_bytes", "status"]
    class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    DATA_COLUMNS_FIELD_NUMBER: _ClassVar[int]
    GLOBAL_ASYNC_INDEX_FIELD_NUMBER: _ClassVar[int]
    GLOBAL_INDEX_FIELD_NUMBER: _ClassVar[int]
    INDEX_COLUMNS_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    SIZE_BYTES_FIELD_NUMBER: _ClassVar[int]
    STATUS_BUILDING: TableIndexDescription.Status
    STATUS_FIELD_NUMBER: _ClassVar[int]
    STATUS_READY: TableIndexDescription.Status
    STATUS_UNSPECIFIED: TableIndexDescription.Status
    data_columns: _containers.RepeatedScalarFieldContainer[str]
    global_async_index: GlobalAsyncIndex
    global_index: GlobalIndex
    index_columns: _containers.RepeatedScalarFieldContainer[str]
    name: str
    size_bytes: int
    status: TableIndexDescription.Status
    def __init__(self, name: _Optional[str] = ..., index_columns: _Optional[_Iterable[str]] = ..., global_index: _Optional[_Union[GlobalIndex, _Mapping]] = ..., global_async_index: _Optional[_Union[GlobalAsyncIndex, _Mapping]] = ..., status: _Optional[_Union[TableIndexDescription.Status, str]] = ..., data_columns: _Optional[_Iterable[str]] = ..., size_bytes: _Optional[int] = ...) -> None: ...

class TableProfile(_message.Message):
    __slots__ = ["caching_policy", "compaction_policy", "execution_policy", "partitioning_policy", "preset_name", "replication_policy", "storage_policy"]
    CACHING_POLICY_FIELD_NUMBER: _ClassVar[int]
    COMPACTION_POLICY_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_POLICY_FIELD_NUMBER: _ClassVar[int]
    PARTITIONING_POLICY_FIELD_NUMBER: _ClassVar[int]
    PRESET_NAME_FIELD_NUMBER: _ClassVar[int]
    REPLICATION_POLICY_FIELD_NUMBER: _ClassVar[int]
    STORAGE_POLICY_FIELD_NUMBER: _ClassVar[int]
    caching_policy: CachingPolicy
    compaction_policy: CompactionPolicy
    execution_policy: ExecutionPolicy
    partitioning_policy: PartitioningPolicy
    preset_name: str
    replication_policy: ReplicationPolicy
    storage_policy: StoragePolicy
    def __init__(self, preset_name: _Optional[str] = ..., storage_policy: _Optional[_Union[StoragePolicy, _Mapping]] = ..., compaction_policy: _Optional[_Union[CompactionPolicy, _Mapping]] = ..., partitioning_policy: _Optional[_Union[PartitioningPolicy, _Mapping]] = ..., execution_policy: _Optional[_Union[ExecutionPolicy, _Mapping]] = ..., replication_policy: _Optional[_Union[ReplicationPolicy, _Mapping]] = ..., caching_policy: _Optional[_Union[CachingPolicy, _Mapping]] = ...) -> None: ...

class TableProfileDescription(_message.Message):
    __slots__ = ["allowed_caching_policies", "allowed_compaction_policies", "allowed_execution_policies", "allowed_partitioning_policies", "allowed_replication_policies", "allowed_storage_policies", "default_caching_policy", "default_compaction_policy", "default_execution_policy", "default_partitioning_policy", "default_replication_policy", "default_storage_policy", "labels", "name"]
    class LabelsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ALLOWED_CACHING_POLICIES_FIELD_NUMBER: _ClassVar[int]
    ALLOWED_COMPACTION_POLICIES_FIELD_NUMBER: _ClassVar[int]
    ALLOWED_EXECUTION_POLICIES_FIELD_NUMBER: _ClassVar[int]
    ALLOWED_PARTITIONING_POLICIES_FIELD_NUMBER: _ClassVar[int]
    ALLOWED_REPLICATION_POLICIES_FIELD_NUMBER: _ClassVar[int]
    ALLOWED_STORAGE_POLICIES_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_CACHING_POLICY_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_COMPACTION_POLICY_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_EXECUTION_POLICY_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_PARTITIONING_POLICY_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_REPLICATION_POLICY_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_STORAGE_POLICY_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    allowed_caching_policies: _containers.RepeatedScalarFieldContainer[str]
    allowed_compaction_policies: _containers.RepeatedScalarFieldContainer[str]
    allowed_execution_policies: _containers.RepeatedScalarFieldContainer[str]
    allowed_partitioning_policies: _containers.RepeatedScalarFieldContainer[str]
    allowed_replication_policies: _containers.RepeatedScalarFieldContainer[str]
    allowed_storage_policies: _containers.RepeatedScalarFieldContainer[str]
    default_caching_policy: str
    default_compaction_policy: str
    default_execution_policy: str
    default_partitioning_policy: str
    default_replication_policy: str
    default_storage_policy: str
    labels: _containers.ScalarMap[str, str]
    name: str
    def __init__(self, name: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ..., default_storage_policy: _Optional[str] = ..., allowed_storage_policies: _Optional[_Iterable[str]] = ..., default_compaction_policy: _Optional[str] = ..., allowed_compaction_policies: _Optional[_Iterable[str]] = ..., default_partitioning_policy: _Optional[str] = ..., allowed_partitioning_policies: _Optional[_Iterable[str]] = ..., default_execution_policy: _Optional[str] = ..., allowed_execution_policies: _Optional[_Iterable[str]] = ..., default_replication_policy: _Optional[str] = ..., allowed_replication_policies: _Optional[_Iterable[str]] = ..., default_caching_policy: _Optional[str] = ..., allowed_caching_policies: _Optional[_Iterable[str]] = ...) -> None: ...

class TableStats(_message.Message):
    __slots__ = ["creation_time", "modification_time", "partition_stats", "partitions", "rows_estimate", "store_size"]
    CREATION_TIME_FIELD_NUMBER: _ClassVar[int]
    MODIFICATION_TIME_FIELD_NUMBER: _ClassVar[int]
    PARTITIONS_FIELD_NUMBER: _ClassVar[int]
    PARTITION_STATS_FIELD_NUMBER: _ClassVar[int]
    ROWS_ESTIMATE_FIELD_NUMBER: _ClassVar[int]
    STORE_SIZE_FIELD_NUMBER: _ClassVar[int]
    creation_time: _timestamp_pb2.Timestamp
    modification_time: _timestamp_pb2.Timestamp
    partition_stats: _containers.RepeatedCompositeFieldContainer[PartitionStats]
    partitions: int
    rows_estimate: int
    store_size: int
    def __init__(self, partition_stats: _Optional[_Iterable[_Union[PartitionStats, _Mapping]]] = ..., rows_estimate: _Optional[int] = ..., store_size: _Optional[int] = ..., partitions: _Optional[int] = ..., creation_time: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., modification_time: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

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

class TtlSettings(_message.Message):
    __slots__ = ["date_type_column", "run_interval_seconds", "value_since_unix_epoch"]
    DATE_TYPE_COLUMN_FIELD_NUMBER: _ClassVar[int]
    RUN_INTERVAL_SECONDS_FIELD_NUMBER: _ClassVar[int]
    VALUE_SINCE_UNIX_EPOCH_FIELD_NUMBER: _ClassVar[int]
    date_type_column: DateTypeColumnModeSettings
    run_interval_seconds: int
    value_since_unix_epoch: ValueSinceUnixEpochModeSettings
    def __init__(self, date_type_column: _Optional[_Union[DateTypeColumnModeSettings, _Mapping]] = ..., value_since_unix_epoch: _Optional[_Union[ValueSinceUnixEpochModeSettings, _Mapping]] = ..., run_interval_seconds: _Optional[int] = ...) -> None: ...

class ValueSinceUnixEpochModeSettings(_message.Message):
    __slots__ = ["column_name", "column_unit", "expire_after_seconds"]
    class Unit(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    COLUMN_NAME_FIELD_NUMBER: _ClassVar[int]
    COLUMN_UNIT_FIELD_NUMBER: _ClassVar[int]
    EXPIRE_AFTER_SECONDS_FIELD_NUMBER: _ClassVar[int]
    UNIT_MICROSECONDS: ValueSinceUnixEpochModeSettings.Unit
    UNIT_MILLISECONDS: ValueSinceUnixEpochModeSettings.Unit
    UNIT_NANOSECONDS: ValueSinceUnixEpochModeSettings.Unit
    UNIT_SECONDS: ValueSinceUnixEpochModeSettings.Unit
    UNIT_UNSPECIFIED: ValueSinceUnixEpochModeSettings.Unit
    column_name: str
    column_unit: ValueSinceUnixEpochModeSettings.Unit
    expire_after_seconds: int
    def __init__(self, column_name: _Optional[str] = ..., column_unit: _Optional[_Union[ValueSinceUnixEpochModeSettings.Unit, str]] = ..., expire_after_seconds: _Optional[int] = ...) -> None: ...
