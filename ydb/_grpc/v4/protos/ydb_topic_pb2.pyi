from protos import ydb_operation_pb2 as _ydb_operation_pb2
from protos import ydb_scheme_pb2 as _ydb_scheme_pb2
from protos import ydb_status_codes_pb2 as _ydb_status_codes_pb2
from protos import ydb_issue_message_pb2 as _ydb_issue_message_pb2
from protos import ydb_table_pb2 as _ydb_table_pb2
from protos.annotations import validation_pb2 as _validation_pb2
from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

CODEC_CUSTOM: Codec
CODEC_GZIP: Codec
CODEC_LZOP: Codec
CODEC_RAW: Codec
CODEC_UNSPECIFIED: Codec
CODEC_ZSTD: Codec
DESCRIPTOR: _descriptor.FileDescriptor
METERING_MODE_REQUEST_UNITS: MeteringMode
METERING_MODE_RESERVED_CAPACITY: MeteringMode
METERING_MODE_UNSPECIFIED: MeteringMode

class AddOffsetsToTransactionRequest(_message.Message):
    __slots__ = ["consumer", "operation_params", "session_id", "topics", "tx_control"]
    class TopicOffsets(_message.Message):
        __slots__ = ["partitions", "path"]
        class PartitionOffsets(_message.Message):
            __slots__ = ["partition_id", "partition_offsets"]
            PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
            PARTITION_OFFSETS_FIELD_NUMBER: _ClassVar[int]
            partition_id: int
            partition_offsets: _containers.RepeatedCompositeFieldContainer[OffsetsRange]
            def __init__(self, partition_id: _Optional[int] = ..., partition_offsets: _Optional[_Iterable[_Union[OffsetsRange, _Mapping]]] = ...) -> None: ...
        PARTITIONS_FIELD_NUMBER: _ClassVar[int]
        PATH_FIELD_NUMBER: _ClassVar[int]
        partitions: _containers.RepeatedCompositeFieldContainer[AddOffsetsToTransactionRequest.TopicOffsets.PartitionOffsets]
        path: str
        def __init__(self, path: _Optional[str] = ..., partitions: _Optional[_Iterable[_Union[AddOffsetsToTransactionRequest.TopicOffsets.PartitionOffsets, _Mapping]]] = ...) -> None: ...
    CONSUMER_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TOPICS_FIELD_NUMBER: _ClassVar[int]
    TX_CONTROL_FIELD_NUMBER: _ClassVar[int]
    consumer: str
    operation_params: _ydb_operation_pb2.OperationParams
    session_id: str
    topics: _containers.RepeatedCompositeFieldContainer[AddOffsetsToTransactionRequest.TopicOffsets]
    tx_control: _ydb_table_pb2.TransactionControl
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., session_id: _Optional[str] = ..., tx_control: _Optional[_Union[_ydb_table_pb2.TransactionControl, _Mapping]] = ..., topics: _Optional[_Iterable[_Union[AddOffsetsToTransactionRequest.TopicOffsets, _Mapping]]] = ..., consumer: _Optional[str] = ...) -> None: ...

class AddOffsetsToTransactionResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class AddOffsetsToTransactionResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class AlterConsumer(_message.Message):
    __slots__ = ["alter_attributes", "name", "set_important", "set_read_from", "set_supported_codecs"]
    class AlterAttributesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ALTER_ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    SET_IMPORTANT_FIELD_NUMBER: _ClassVar[int]
    SET_READ_FROM_FIELD_NUMBER: _ClassVar[int]
    SET_SUPPORTED_CODECS_FIELD_NUMBER: _ClassVar[int]
    alter_attributes: _containers.ScalarMap[str, str]
    name: str
    set_important: bool
    set_read_from: _timestamp_pb2.Timestamp
    set_supported_codecs: SupportedCodecs
    def __init__(self, name: _Optional[str] = ..., set_important: bool = ..., set_read_from: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., set_supported_codecs: _Optional[_Union[SupportedCodecs, _Mapping]] = ..., alter_attributes: _Optional[_Mapping[str, str]] = ...) -> None: ...

class AlterPartitioningSettings(_message.Message):
    __slots__ = ["set_min_active_partitions", "set_partition_count_limit"]
    SET_MIN_ACTIVE_PARTITIONS_FIELD_NUMBER: _ClassVar[int]
    SET_PARTITION_COUNT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    set_min_active_partitions: int
    set_partition_count_limit: int
    def __init__(self, set_min_active_partitions: _Optional[int] = ..., set_partition_count_limit: _Optional[int] = ...) -> None: ...

class AlterTopicRequest(_message.Message):
    __slots__ = ["add_consumers", "alter_attributes", "alter_consumers", "alter_partitioning_settings", "drop_consumers", "operation_params", "path", "set_metering_mode", "set_partition_write_burst_bytes", "set_partition_write_speed_bytes_per_second", "set_retention_period", "set_retention_storage_mb", "set_supported_codecs"]
    class AlterAttributesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ADD_CONSUMERS_FIELD_NUMBER: _ClassVar[int]
    ALTER_ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    ALTER_CONSUMERS_FIELD_NUMBER: _ClassVar[int]
    ALTER_PARTITIONING_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    DROP_CONSUMERS_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    SET_METERING_MODE_FIELD_NUMBER: _ClassVar[int]
    SET_PARTITION_WRITE_BURST_BYTES_FIELD_NUMBER: _ClassVar[int]
    SET_PARTITION_WRITE_SPEED_BYTES_PER_SECOND_FIELD_NUMBER: _ClassVar[int]
    SET_RETENTION_PERIOD_FIELD_NUMBER: _ClassVar[int]
    SET_RETENTION_STORAGE_MB_FIELD_NUMBER: _ClassVar[int]
    SET_SUPPORTED_CODECS_FIELD_NUMBER: _ClassVar[int]
    add_consumers: _containers.RepeatedCompositeFieldContainer[Consumer]
    alter_attributes: _containers.ScalarMap[str, str]
    alter_consumers: _containers.RepeatedCompositeFieldContainer[AlterConsumer]
    alter_partitioning_settings: AlterPartitioningSettings
    drop_consumers: _containers.RepeatedScalarFieldContainer[str]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    set_metering_mode: MeteringMode
    set_partition_write_burst_bytes: int
    set_partition_write_speed_bytes_per_second: int
    set_retention_period: _duration_pb2.Duration
    set_retention_storage_mb: int
    set_supported_codecs: SupportedCodecs
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., alter_partitioning_settings: _Optional[_Union[AlterPartitioningSettings, _Mapping]] = ..., set_retention_period: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., set_retention_storage_mb: _Optional[int] = ..., set_supported_codecs: _Optional[_Union[SupportedCodecs, _Mapping]] = ..., set_partition_write_speed_bytes_per_second: _Optional[int] = ..., set_partition_write_burst_bytes: _Optional[int] = ..., alter_attributes: _Optional[_Mapping[str, str]] = ..., add_consumers: _Optional[_Iterable[_Union[Consumer, _Mapping]]] = ..., drop_consumers: _Optional[_Iterable[str]] = ..., alter_consumers: _Optional[_Iterable[_Union[AlterConsumer, _Mapping]]] = ..., set_metering_mode: _Optional[_Union[MeteringMode, str]] = ...) -> None: ...

class AlterTopicResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class AlterTopicResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class CommitOffsetRequest(_message.Message):
    __slots__ = ["consumer", "offset", "operation_params", "partition_id", "path"]
    CONSUMER_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    consumer: str
    offset: int
    operation_params: _ydb_operation_pb2.OperationParams
    partition_id: int
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., partition_id: _Optional[int] = ..., consumer: _Optional[str] = ..., offset: _Optional[int] = ...) -> None: ...

class CommitOffsetResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class CommitOffsetResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class Consumer(_message.Message):
    __slots__ = ["attributes", "consumer_stats", "important", "name", "read_from", "supported_codecs"]
    class AttributesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class ConsumerStats(_message.Message):
        __slots__ = ["bytes_read", "max_read_time_lag", "max_write_time_lag", "min_partitions_last_read_time"]
        BYTES_READ_FIELD_NUMBER: _ClassVar[int]
        MAX_READ_TIME_LAG_FIELD_NUMBER: _ClassVar[int]
        MAX_WRITE_TIME_LAG_FIELD_NUMBER: _ClassVar[int]
        MIN_PARTITIONS_LAST_READ_TIME_FIELD_NUMBER: _ClassVar[int]
        bytes_read: MultipleWindowsStat
        max_read_time_lag: _duration_pb2.Duration
        max_write_time_lag: _duration_pb2.Duration
        min_partitions_last_read_time: _timestamp_pb2.Timestamp
        def __init__(self, min_partitions_last_read_time: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., max_read_time_lag: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., max_write_time_lag: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., bytes_read: _Optional[_Union[MultipleWindowsStat, _Mapping]] = ...) -> None: ...
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    CONSUMER_STATS_FIELD_NUMBER: _ClassVar[int]
    IMPORTANT_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    READ_FROM_FIELD_NUMBER: _ClassVar[int]
    SUPPORTED_CODECS_FIELD_NUMBER: _ClassVar[int]
    attributes: _containers.ScalarMap[str, str]
    consumer_stats: Consumer.ConsumerStats
    important: bool
    name: str
    read_from: _timestamp_pb2.Timestamp
    supported_codecs: SupportedCodecs
    def __init__(self, name: _Optional[str] = ..., important: bool = ..., read_from: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., supported_codecs: _Optional[_Union[SupportedCodecs, _Mapping]] = ..., attributes: _Optional[_Mapping[str, str]] = ..., consumer_stats: _Optional[_Union[Consumer.ConsumerStats, _Mapping]] = ...) -> None: ...

class CreateTopicRequest(_message.Message):
    __slots__ = ["attributes", "consumers", "metering_mode", "operation_params", "partition_write_burst_bytes", "partition_write_speed_bytes_per_second", "partitioning_settings", "path", "retention_period", "retention_storage_mb", "supported_codecs"]
    class AttributesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    CONSUMERS_FIELD_NUMBER: _ClassVar[int]
    METERING_MODE_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PARTITIONING_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    PARTITION_WRITE_BURST_BYTES_FIELD_NUMBER: _ClassVar[int]
    PARTITION_WRITE_SPEED_BYTES_PER_SECOND_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    RETENTION_PERIOD_FIELD_NUMBER: _ClassVar[int]
    RETENTION_STORAGE_MB_FIELD_NUMBER: _ClassVar[int]
    SUPPORTED_CODECS_FIELD_NUMBER: _ClassVar[int]
    attributes: _containers.ScalarMap[str, str]
    consumers: _containers.RepeatedCompositeFieldContainer[Consumer]
    metering_mode: MeteringMode
    operation_params: _ydb_operation_pb2.OperationParams
    partition_write_burst_bytes: int
    partition_write_speed_bytes_per_second: int
    partitioning_settings: PartitioningSettings
    path: str
    retention_period: _duration_pb2.Duration
    retention_storage_mb: int
    supported_codecs: SupportedCodecs
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., partitioning_settings: _Optional[_Union[PartitioningSettings, _Mapping]] = ..., retention_period: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., retention_storage_mb: _Optional[int] = ..., supported_codecs: _Optional[_Union[SupportedCodecs, _Mapping]] = ..., partition_write_speed_bytes_per_second: _Optional[int] = ..., partition_write_burst_bytes: _Optional[int] = ..., attributes: _Optional[_Mapping[str, str]] = ..., consumers: _Optional[_Iterable[_Union[Consumer, _Mapping]]] = ..., metering_mode: _Optional[_Union[MeteringMode, str]] = ...) -> None: ...

class CreateTopicResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class CreateTopicResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class DescribeConsumerRequest(_message.Message):
    __slots__ = ["consumer", "include_stats", "operation_params", "path"]
    CONSUMER_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_STATS_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    consumer: str
    include_stats: bool
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., consumer: _Optional[str] = ..., include_stats: bool = ...) -> None: ...

class DescribeConsumerResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeConsumerResult(_message.Message):
    __slots__ = ["consumer", "partitions", "self"]
    class PartitionConsumerStats(_message.Message):
        __slots__ = ["bytes_read", "committed_offset", "connection_node_id", "last_read_offset", "last_read_time", "max_read_time_lag", "max_write_time_lag", "partition_read_session_create_time", "read_session_id", "reader_name"]
        BYTES_READ_FIELD_NUMBER: _ClassVar[int]
        COMMITTED_OFFSET_FIELD_NUMBER: _ClassVar[int]
        CONNECTION_NODE_ID_FIELD_NUMBER: _ClassVar[int]
        LAST_READ_OFFSET_FIELD_NUMBER: _ClassVar[int]
        LAST_READ_TIME_FIELD_NUMBER: _ClassVar[int]
        MAX_READ_TIME_LAG_FIELD_NUMBER: _ClassVar[int]
        MAX_WRITE_TIME_LAG_FIELD_NUMBER: _ClassVar[int]
        PARTITION_READ_SESSION_CREATE_TIME_FIELD_NUMBER: _ClassVar[int]
        READER_NAME_FIELD_NUMBER: _ClassVar[int]
        READ_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        bytes_read: MultipleWindowsStat
        committed_offset: int
        connection_node_id: int
        last_read_offset: int
        last_read_time: _timestamp_pb2.Timestamp
        max_read_time_lag: _duration_pb2.Duration
        max_write_time_lag: _duration_pb2.Duration
        partition_read_session_create_time: _timestamp_pb2.Timestamp
        read_session_id: str
        reader_name: str
        def __init__(self, last_read_offset: _Optional[int] = ..., committed_offset: _Optional[int] = ..., read_session_id: _Optional[str] = ..., partition_read_session_create_time: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., last_read_time: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., max_read_time_lag: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., max_write_time_lag: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., bytes_read: _Optional[_Union[MultipleWindowsStat, _Mapping]] = ..., reader_name: _Optional[str] = ..., connection_node_id: _Optional[int] = ...) -> None: ...
    class PartitionInfo(_message.Message):
        __slots__ = ["active", "child_partition_ids", "parent_partition_ids", "partition_consumer_stats", "partition_id", "partition_stats"]
        ACTIVE_FIELD_NUMBER: _ClassVar[int]
        CHILD_PARTITION_IDS_FIELD_NUMBER: _ClassVar[int]
        PARENT_PARTITION_IDS_FIELD_NUMBER: _ClassVar[int]
        PARTITION_CONSUMER_STATS_FIELD_NUMBER: _ClassVar[int]
        PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
        PARTITION_STATS_FIELD_NUMBER: _ClassVar[int]
        active: bool
        child_partition_ids: _containers.RepeatedScalarFieldContainer[int]
        parent_partition_ids: _containers.RepeatedScalarFieldContainer[int]
        partition_consumer_stats: DescribeConsumerResult.PartitionConsumerStats
        partition_id: int
        partition_stats: PartitionStats
        def __init__(self, partition_id: _Optional[int] = ..., active: bool = ..., child_partition_ids: _Optional[_Iterable[int]] = ..., parent_partition_ids: _Optional[_Iterable[int]] = ..., partition_stats: _Optional[_Union[PartitionStats, _Mapping]] = ..., partition_consumer_stats: _Optional[_Union[DescribeConsumerResult.PartitionConsumerStats, _Mapping]] = ...) -> None: ...
    CONSUMER_FIELD_NUMBER: _ClassVar[int]
    PARTITIONS_FIELD_NUMBER: _ClassVar[int]
    SELF_FIELD_NUMBER: _ClassVar[int]
    consumer: Consumer
    partitions: _containers.RepeatedCompositeFieldContainer[DescribeConsumerResult.PartitionInfo]
    self: _ydb_scheme_pb2.Entry
    def __init__(self, self_: _Optional[_Union[_ydb_scheme_pb2.Entry, _Mapping]] = ..., consumer: _Optional[_Union[Consumer, _Mapping]] = ..., partitions: _Optional[_Iterable[_Union[DescribeConsumerResult.PartitionInfo, _Mapping]]] = ...) -> None: ...

class DescribeTopicRequest(_message.Message):
    __slots__ = ["include_stats", "operation_params", "path"]
    INCLUDE_STATS_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    include_stats: bool
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., include_stats: bool = ...) -> None: ...

class DescribeTopicResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeTopicResult(_message.Message):
    __slots__ = ["attributes", "consumers", "metering_mode", "partition_write_burst_bytes", "partition_write_speed_bytes_per_second", "partitioning_settings", "partitions", "retention_period", "retention_storage_mb", "self", "supported_codecs", "topic_stats"]
    class AttributesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class PartitionInfo(_message.Message):
        __slots__ = ["active", "child_partition_ids", "parent_partition_ids", "partition_id", "partition_stats"]
        ACTIVE_FIELD_NUMBER: _ClassVar[int]
        CHILD_PARTITION_IDS_FIELD_NUMBER: _ClassVar[int]
        PARENT_PARTITION_IDS_FIELD_NUMBER: _ClassVar[int]
        PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
        PARTITION_STATS_FIELD_NUMBER: _ClassVar[int]
        active: bool
        child_partition_ids: _containers.RepeatedScalarFieldContainer[int]
        parent_partition_ids: _containers.RepeatedScalarFieldContainer[int]
        partition_id: int
        partition_stats: PartitionStats
        def __init__(self, partition_id: _Optional[int] = ..., active: bool = ..., child_partition_ids: _Optional[_Iterable[int]] = ..., parent_partition_ids: _Optional[_Iterable[int]] = ..., partition_stats: _Optional[_Union[PartitionStats, _Mapping]] = ...) -> None: ...
    class TopicStats(_message.Message):
        __slots__ = ["bytes_written", "max_write_time_lag", "min_last_write_time", "store_size_bytes"]
        BYTES_WRITTEN_FIELD_NUMBER: _ClassVar[int]
        MAX_WRITE_TIME_LAG_FIELD_NUMBER: _ClassVar[int]
        MIN_LAST_WRITE_TIME_FIELD_NUMBER: _ClassVar[int]
        STORE_SIZE_BYTES_FIELD_NUMBER: _ClassVar[int]
        bytes_written: MultipleWindowsStat
        max_write_time_lag: _duration_pb2.Duration
        min_last_write_time: _timestamp_pb2.Timestamp
        store_size_bytes: int
        def __init__(self, store_size_bytes: _Optional[int] = ..., min_last_write_time: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., max_write_time_lag: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., bytes_written: _Optional[_Union[MultipleWindowsStat, _Mapping]] = ...) -> None: ...
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    CONSUMERS_FIELD_NUMBER: _ClassVar[int]
    METERING_MODE_FIELD_NUMBER: _ClassVar[int]
    PARTITIONING_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    PARTITIONS_FIELD_NUMBER: _ClassVar[int]
    PARTITION_WRITE_BURST_BYTES_FIELD_NUMBER: _ClassVar[int]
    PARTITION_WRITE_SPEED_BYTES_PER_SECOND_FIELD_NUMBER: _ClassVar[int]
    RETENTION_PERIOD_FIELD_NUMBER: _ClassVar[int]
    RETENTION_STORAGE_MB_FIELD_NUMBER: _ClassVar[int]
    SELF_FIELD_NUMBER: _ClassVar[int]
    SUPPORTED_CODECS_FIELD_NUMBER: _ClassVar[int]
    TOPIC_STATS_FIELD_NUMBER: _ClassVar[int]
    attributes: _containers.ScalarMap[str, str]
    consumers: _containers.RepeatedCompositeFieldContainer[Consumer]
    metering_mode: MeteringMode
    partition_write_burst_bytes: int
    partition_write_speed_bytes_per_second: int
    partitioning_settings: PartitioningSettings
    partitions: _containers.RepeatedCompositeFieldContainer[DescribeTopicResult.PartitionInfo]
    retention_period: _duration_pb2.Duration
    retention_storage_mb: int
    self: _ydb_scheme_pb2.Entry
    supported_codecs: SupportedCodecs
    topic_stats: DescribeTopicResult.TopicStats
    def __init__(self, self_: _Optional[_Union[_ydb_scheme_pb2.Entry, _Mapping]] = ..., partitioning_settings: _Optional[_Union[PartitioningSettings, _Mapping]] = ..., partitions: _Optional[_Iterable[_Union[DescribeTopicResult.PartitionInfo, _Mapping]]] = ..., retention_period: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., retention_storage_mb: _Optional[int] = ..., supported_codecs: _Optional[_Union[SupportedCodecs, _Mapping]] = ..., partition_write_speed_bytes_per_second: _Optional[int] = ..., partition_write_burst_bytes: _Optional[int] = ..., attributes: _Optional[_Mapping[str, str]] = ..., consumers: _Optional[_Iterable[_Union[Consumer, _Mapping]]] = ..., metering_mode: _Optional[_Union[MeteringMode, str]] = ..., topic_stats: _Optional[_Union[DescribeTopicResult.TopicStats, _Mapping]] = ...) -> None: ...

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

class MultipleWindowsStat(_message.Message):
    __slots__ = ["per_day", "per_hour", "per_minute"]
    PER_DAY_FIELD_NUMBER: _ClassVar[int]
    PER_HOUR_FIELD_NUMBER: _ClassVar[int]
    PER_MINUTE_FIELD_NUMBER: _ClassVar[int]
    per_day: int
    per_hour: int
    per_minute: int
    def __init__(self, per_minute: _Optional[int] = ..., per_hour: _Optional[int] = ..., per_day: _Optional[int] = ...) -> None: ...

class OffsetsRange(_message.Message):
    __slots__ = ["end", "start"]
    END_FIELD_NUMBER: _ClassVar[int]
    START_FIELD_NUMBER: _ClassVar[int]
    end: int
    start: int
    def __init__(self, start: _Optional[int] = ..., end: _Optional[int] = ...) -> None: ...

class PartitionStats(_message.Message):
    __slots__ = ["bytes_written", "last_write_time", "max_write_time_lag", "partition_node_id", "partition_offsets", "store_size_bytes"]
    BYTES_WRITTEN_FIELD_NUMBER: _ClassVar[int]
    LAST_WRITE_TIME_FIELD_NUMBER: _ClassVar[int]
    MAX_WRITE_TIME_LAG_FIELD_NUMBER: _ClassVar[int]
    PARTITION_NODE_ID_FIELD_NUMBER: _ClassVar[int]
    PARTITION_OFFSETS_FIELD_NUMBER: _ClassVar[int]
    STORE_SIZE_BYTES_FIELD_NUMBER: _ClassVar[int]
    bytes_written: MultipleWindowsStat
    last_write_time: _timestamp_pb2.Timestamp
    max_write_time_lag: _duration_pb2.Duration
    partition_node_id: int
    partition_offsets: OffsetsRange
    store_size_bytes: int
    def __init__(self, partition_offsets: _Optional[_Union[OffsetsRange, _Mapping]] = ..., store_size_bytes: _Optional[int] = ..., last_write_time: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., max_write_time_lag: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., bytes_written: _Optional[_Union[MultipleWindowsStat, _Mapping]] = ..., partition_node_id: _Optional[int] = ...) -> None: ...

class PartitioningSettings(_message.Message):
    __slots__ = ["min_active_partitions", "partition_count_limit"]
    MIN_ACTIVE_PARTITIONS_FIELD_NUMBER: _ClassVar[int]
    PARTITION_COUNT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    min_active_partitions: int
    partition_count_limit: int
    def __init__(self, min_active_partitions: _Optional[int] = ..., partition_count_limit: _Optional[int] = ...) -> None: ...

class StreamReadMessage(_message.Message):
    __slots__ = []
    class CommitOffsetRequest(_message.Message):
        __slots__ = ["commit_offsets"]
        class PartitionCommitOffset(_message.Message):
            __slots__ = ["offsets", "partition_session_id"]
            OFFSETS_FIELD_NUMBER: _ClassVar[int]
            PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
            offsets: _containers.RepeatedCompositeFieldContainer[OffsetsRange]
            partition_session_id: int
            def __init__(self, partition_session_id: _Optional[int] = ..., offsets: _Optional[_Iterable[_Union[OffsetsRange, _Mapping]]] = ...) -> None: ...
        COMMIT_OFFSETS_FIELD_NUMBER: _ClassVar[int]
        commit_offsets: _containers.RepeatedCompositeFieldContainer[StreamReadMessage.CommitOffsetRequest.PartitionCommitOffset]
        def __init__(self, commit_offsets: _Optional[_Iterable[_Union[StreamReadMessage.CommitOffsetRequest.PartitionCommitOffset, _Mapping]]] = ...) -> None: ...
    class CommitOffsetResponse(_message.Message):
        __slots__ = ["partitions_committed_offsets"]
        class PartitionCommittedOffset(_message.Message):
            __slots__ = ["committed_offset", "partition_session_id"]
            COMMITTED_OFFSET_FIELD_NUMBER: _ClassVar[int]
            PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
            committed_offset: int
            partition_session_id: int
            def __init__(self, partition_session_id: _Optional[int] = ..., committed_offset: _Optional[int] = ...) -> None: ...
        PARTITIONS_COMMITTED_OFFSETS_FIELD_NUMBER: _ClassVar[int]
        partitions_committed_offsets: _containers.RepeatedCompositeFieldContainer[StreamReadMessage.CommitOffsetResponse.PartitionCommittedOffset]
        def __init__(self, partitions_committed_offsets: _Optional[_Iterable[_Union[StreamReadMessage.CommitOffsetResponse.PartitionCommittedOffset, _Mapping]]] = ...) -> None: ...
    class FromClient(_message.Message):
        __slots__ = ["commit_offset_request", "init_request", "partition_session_status_request", "read_request", "start_partition_session_response", "stop_partition_session_response", "update_token_request"]
        COMMIT_OFFSET_REQUEST_FIELD_NUMBER: _ClassVar[int]
        INIT_REQUEST_FIELD_NUMBER: _ClassVar[int]
        PARTITION_SESSION_STATUS_REQUEST_FIELD_NUMBER: _ClassVar[int]
        READ_REQUEST_FIELD_NUMBER: _ClassVar[int]
        START_PARTITION_SESSION_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        STOP_PARTITION_SESSION_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        UPDATE_TOKEN_REQUEST_FIELD_NUMBER: _ClassVar[int]
        commit_offset_request: StreamReadMessage.CommitOffsetRequest
        init_request: StreamReadMessage.InitRequest
        partition_session_status_request: StreamReadMessage.PartitionSessionStatusRequest
        read_request: StreamReadMessage.ReadRequest
        start_partition_session_response: StreamReadMessage.StartPartitionSessionResponse
        stop_partition_session_response: StreamReadMessage.StopPartitionSessionResponse
        update_token_request: UpdateTokenRequest
        def __init__(self, init_request: _Optional[_Union[StreamReadMessage.InitRequest, _Mapping]] = ..., read_request: _Optional[_Union[StreamReadMessage.ReadRequest, _Mapping]] = ..., commit_offset_request: _Optional[_Union[StreamReadMessage.CommitOffsetRequest, _Mapping]] = ..., partition_session_status_request: _Optional[_Union[StreamReadMessage.PartitionSessionStatusRequest, _Mapping]] = ..., update_token_request: _Optional[_Union[UpdateTokenRequest, _Mapping]] = ..., start_partition_session_response: _Optional[_Union[StreamReadMessage.StartPartitionSessionResponse, _Mapping]] = ..., stop_partition_session_response: _Optional[_Union[StreamReadMessage.StopPartitionSessionResponse, _Mapping]] = ...) -> None: ...
    class FromServer(_message.Message):
        __slots__ = ["commit_offset_response", "init_response", "issues", "partition_session_status_response", "read_response", "start_partition_session_request", "status", "stop_partition_session_request", "update_token_response"]
        COMMIT_OFFSET_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        INIT_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        ISSUES_FIELD_NUMBER: _ClassVar[int]
        PARTITION_SESSION_STATUS_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        READ_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        START_PARTITION_SESSION_REQUEST_FIELD_NUMBER: _ClassVar[int]
        STATUS_FIELD_NUMBER: _ClassVar[int]
        STOP_PARTITION_SESSION_REQUEST_FIELD_NUMBER: _ClassVar[int]
        UPDATE_TOKEN_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        commit_offset_response: StreamReadMessage.CommitOffsetResponse
        init_response: StreamReadMessage.InitResponse
        issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
        partition_session_status_response: StreamReadMessage.PartitionSessionStatusResponse
        read_response: StreamReadMessage.ReadResponse
        start_partition_session_request: StreamReadMessage.StartPartitionSessionRequest
        status: _ydb_status_codes_pb2.StatusIds.StatusCode
        stop_partition_session_request: StreamReadMessage.StopPartitionSessionRequest
        update_token_response: UpdateTokenResponse
        def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., init_response: _Optional[_Union[StreamReadMessage.InitResponse, _Mapping]] = ..., read_response: _Optional[_Union[StreamReadMessage.ReadResponse, _Mapping]] = ..., commit_offset_response: _Optional[_Union[StreamReadMessage.CommitOffsetResponse, _Mapping]] = ..., partition_session_status_response: _Optional[_Union[StreamReadMessage.PartitionSessionStatusResponse, _Mapping]] = ..., update_token_response: _Optional[_Union[UpdateTokenResponse, _Mapping]] = ..., start_partition_session_request: _Optional[_Union[StreamReadMessage.StartPartitionSessionRequest, _Mapping]] = ..., stop_partition_session_request: _Optional[_Union[StreamReadMessage.StopPartitionSessionRequest, _Mapping]] = ...) -> None: ...
    class InitRequest(_message.Message):
        __slots__ = ["consumer", "reader_name", "topics_read_settings"]
        class TopicReadSettings(_message.Message):
            __slots__ = ["max_lag", "partition_ids", "path", "read_from"]
            MAX_LAG_FIELD_NUMBER: _ClassVar[int]
            PARTITION_IDS_FIELD_NUMBER: _ClassVar[int]
            PATH_FIELD_NUMBER: _ClassVar[int]
            READ_FROM_FIELD_NUMBER: _ClassVar[int]
            max_lag: _duration_pb2.Duration
            partition_ids: _containers.RepeatedScalarFieldContainer[int]
            path: str
            read_from: _timestamp_pb2.Timestamp
            def __init__(self, path: _Optional[str] = ..., partition_ids: _Optional[_Iterable[int]] = ..., max_lag: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., read_from: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
        CONSUMER_FIELD_NUMBER: _ClassVar[int]
        READER_NAME_FIELD_NUMBER: _ClassVar[int]
        TOPICS_READ_SETTINGS_FIELD_NUMBER: _ClassVar[int]
        consumer: str
        reader_name: str
        topics_read_settings: _containers.RepeatedCompositeFieldContainer[StreamReadMessage.InitRequest.TopicReadSettings]
        def __init__(self, topics_read_settings: _Optional[_Iterable[_Union[StreamReadMessage.InitRequest.TopicReadSettings, _Mapping]]] = ..., consumer: _Optional[str] = ..., reader_name: _Optional[str] = ...) -> None: ...
    class InitResponse(_message.Message):
        __slots__ = ["session_id"]
        SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        session_id: str
        def __init__(self, session_id: _Optional[str] = ...) -> None: ...
    class PartitionSession(_message.Message):
        __slots__ = ["partition_id", "partition_session_id", "path"]
        PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
        PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        PATH_FIELD_NUMBER: _ClassVar[int]
        partition_id: int
        partition_session_id: int
        path: str
        def __init__(self, partition_session_id: _Optional[int] = ..., path: _Optional[str] = ..., partition_id: _Optional[int] = ...) -> None: ...
    class PartitionSessionStatusRequest(_message.Message):
        __slots__ = ["partition_session_id"]
        PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        partition_session_id: int
        def __init__(self, partition_session_id: _Optional[int] = ...) -> None: ...
    class PartitionSessionStatusResponse(_message.Message):
        __slots__ = ["committed_offset", "partition_offsets", "partition_session_id", "write_time_high_watermark"]
        COMMITTED_OFFSET_FIELD_NUMBER: _ClassVar[int]
        PARTITION_OFFSETS_FIELD_NUMBER: _ClassVar[int]
        PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        WRITE_TIME_HIGH_WATERMARK_FIELD_NUMBER: _ClassVar[int]
        committed_offset: int
        partition_offsets: OffsetsRange
        partition_session_id: int
        write_time_high_watermark: _timestamp_pb2.Timestamp
        def __init__(self, partition_session_id: _Optional[int] = ..., partition_offsets: _Optional[_Union[OffsetsRange, _Mapping]] = ..., committed_offset: _Optional[int] = ..., write_time_high_watermark: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
    class ReadRequest(_message.Message):
        __slots__ = ["bytes_size"]
        BYTES_SIZE_FIELD_NUMBER: _ClassVar[int]
        bytes_size: int
        def __init__(self, bytes_size: _Optional[int] = ...) -> None: ...
    class ReadResponse(_message.Message):
        __slots__ = ["bytes_size", "partition_data"]
        class Batch(_message.Message):
            __slots__ = ["codec", "message_data", "producer_id", "write_session_meta", "written_at"]
            class WriteSessionMetaEntry(_message.Message):
                __slots__ = ["key", "value"]
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            CODEC_FIELD_NUMBER: _ClassVar[int]
            MESSAGE_DATA_FIELD_NUMBER: _ClassVar[int]
            PRODUCER_ID_FIELD_NUMBER: _ClassVar[int]
            WRITE_SESSION_META_FIELD_NUMBER: _ClassVar[int]
            WRITTEN_AT_FIELD_NUMBER: _ClassVar[int]
            codec: int
            message_data: _containers.RepeatedCompositeFieldContainer[StreamReadMessage.ReadResponse.MessageData]
            producer_id: str
            write_session_meta: _containers.ScalarMap[str, str]
            written_at: _timestamp_pb2.Timestamp
            def __init__(self, message_data: _Optional[_Iterable[_Union[StreamReadMessage.ReadResponse.MessageData, _Mapping]]] = ..., producer_id: _Optional[str] = ..., write_session_meta: _Optional[_Mapping[str, str]] = ..., codec: _Optional[int] = ..., written_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
        class MessageData(_message.Message):
            __slots__ = ["created_at", "data", "message_group_id", "offset", "seq_no", "uncompressed_size"]
            CREATED_AT_FIELD_NUMBER: _ClassVar[int]
            DATA_FIELD_NUMBER: _ClassVar[int]
            MESSAGE_GROUP_ID_FIELD_NUMBER: _ClassVar[int]
            OFFSET_FIELD_NUMBER: _ClassVar[int]
            SEQ_NO_FIELD_NUMBER: _ClassVar[int]
            UNCOMPRESSED_SIZE_FIELD_NUMBER: _ClassVar[int]
            created_at: _timestamp_pb2.Timestamp
            data: bytes
            message_group_id: str
            offset: int
            seq_no: int
            uncompressed_size: int
            def __init__(self, offset: _Optional[int] = ..., seq_no: _Optional[int] = ..., created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., data: _Optional[bytes] = ..., uncompressed_size: _Optional[int] = ..., message_group_id: _Optional[str] = ...) -> None: ...
        class PartitionData(_message.Message):
            __slots__ = ["batches", "partition_session_id"]
            BATCHES_FIELD_NUMBER: _ClassVar[int]
            PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
            batches: _containers.RepeatedCompositeFieldContainer[StreamReadMessage.ReadResponse.Batch]
            partition_session_id: int
            def __init__(self, partition_session_id: _Optional[int] = ..., batches: _Optional[_Iterable[_Union[StreamReadMessage.ReadResponse.Batch, _Mapping]]] = ...) -> None: ...
        BYTES_SIZE_FIELD_NUMBER: _ClassVar[int]
        PARTITION_DATA_FIELD_NUMBER: _ClassVar[int]
        bytes_size: int
        partition_data: _containers.RepeatedCompositeFieldContainer[StreamReadMessage.ReadResponse.PartitionData]
        def __init__(self, partition_data: _Optional[_Iterable[_Union[StreamReadMessage.ReadResponse.PartitionData, _Mapping]]] = ..., bytes_size: _Optional[int] = ...) -> None: ...
    class StartPartitionSessionRequest(_message.Message):
        __slots__ = ["committed_offset", "partition_offsets", "partition_session"]
        COMMITTED_OFFSET_FIELD_NUMBER: _ClassVar[int]
        PARTITION_OFFSETS_FIELD_NUMBER: _ClassVar[int]
        PARTITION_SESSION_FIELD_NUMBER: _ClassVar[int]
        committed_offset: int
        partition_offsets: OffsetsRange
        partition_session: StreamReadMessage.PartitionSession
        def __init__(self, partition_session: _Optional[_Union[StreamReadMessage.PartitionSession, _Mapping]] = ..., committed_offset: _Optional[int] = ..., partition_offsets: _Optional[_Union[OffsetsRange, _Mapping]] = ...) -> None: ...
    class StartPartitionSessionResponse(_message.Message):
        __slots__ = ["commit_offset", "partition_session_id", "read_offset"]
        COMMIT_OFFSET_FIELD_NUMBER: _ClassVar[int]
        PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        READ_OFFSET_FIELD_NUMBER: _ClassVar[int]
        commit_offset: int
        partition_session_id: int
        read_offset: int
        def __init__(self, partition_session_id: _Optional[int] = ..., read_offset: _Optional[int] = ..., commit_offset: _Optional[int] = ...) -> None: ...
    class StopPartitionSessionRequest(_message.Message):
        __slots__ = ["committed_offset", "graceful", "partition_session_id"]
        COMMITTED_OFFSET_FIELD_NUMBER: _ClassVar[int]
        GRACEFUL_FIELD_NUMBER: _ClassVar[int]
        PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        committed_offset: int
        graceful: bool
        partition_session_id: int
        def __init__(self, partition_session_id: _Optional[int] = ..., graceful: bool = ..., committed_offset: _Optional[int] = ...) -> None: ...
    class StopPartitionSessionResponse(_message.Message):
        __slots__ = ["partition_session_id"]
        PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        partition_session_id: int
        def __init__(self, partition_session_id: _Optional[int] = ...) -> None: ...
    def __init__(self) -> None: ...

class StreamWriteMessage(_message.Message):
    __slots__ = []
    class FromClient(_message.Message):
        __slots__ = ["init_request", "update_token_request", "write_request"]
        INIT_REQUEST_FIELD_NUMBER: _ClassVar[int]
        UPDATE_TOKEN_REQUEST_FIELD_NUMBER: _ClassVar[int]
        WRITE_REQUEST_FIELD_NUMBER: _ClassVar[int]
        init_request: StreamWriteMessage.InitRequest
        update_token_request: UpdateTokenRequest
        write_request: StreamWriteMessage.WriteRequest
        def __init__(self, init_request: _Optional[_Union[StreamWriteMessage.InitRequest, _Mapping]] = ..., write_request: _Optional[_Union[StreamWriteMessage.WriteRequest, _Mapping]] = ..., update_token_request: _Optional[_Union[UpdateTokenRequest, _Mapping]] = ...) -> None: ...
    class FromServer(_message.Message):
        __slots__ = ["init_response", "issues", "status", "update_token_response", "write_response"]
        INIT_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        ISSUES_FIELD_NUMBER: _ClassVar[int]
        STATUS_FIELD_NUMBER: _ClassVar[int]
        UPDATE_TOKEN_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        WRITE_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        init_response: StreamWriteMessage.InitResponse
        issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
        status: _ydb_status_codes_pb2.StatusIds.StatusCode
        update_token_response: UpdateTokenResponse
        write_response: StreamWriteMessage.WriteResponse
        def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., init_response: _Optional[_Union[StreamWriteMessage.InitResponse, _Mapping]] = ..., write_response: _Optional[_Union[StreamWriteMessage.WriteResponse, _Mapping]] = ..., update_token_response: _Optional[_Union[UpdateTokenResponse, _Mapping]] = ...) -> None: ...
    class InitRequest(_message.Message):
        __slots__ = ["get_last_seq_no", "message_group_id", "partition_id", "path", "producer_id", "write_session_meta"]
        class WriteSessionMetaEntry(_message.Message):
            __slots__ = ["key", "value"]
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        GET_LAST_SEQ_NO_FIELD_NUMBER: _ClassVar[int]
        MESSAGE_GROUP_ID_FIELD_NUMBER: _ClassVar[int]
        PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
        PATH_FIELD_NUMBER: _ClassVar[int]
        PRODUCER_ID_FIELD_NUMBER: _ClassVar[int]
        WRITE_SESSION_META_FIELD_NUMBER: _ClassVar[int]
        get_last_seq_no: bool
        message_group_id: str
        partition_id: int
        path: str
        producer_id: str
        write_session_meta: _containers.ScalarMap[str, str]
        def __init__(self, path: _Optional[str] = ..., producer_id: _Optional[str] = ..., write_session_meta: _Optional[_Mapping[str, str]] = ..., message_group_id: _Optional[str] = ..., partition_id: _Optional[int] = ..., get_last_seq_no: bool = ...) -> None: ...
    class InitResponse(_message.Message):
        __slots__ = ["last_seq_no", "partition_id", "session_id", "supported_codecs"]
        LAST_SEQ_NO_FIELD_NUMBER: _ClassVar[int]
        PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
        SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        SUPPORTED_CODECS_FIELD_NUMBER: _ClassVar[int]
        last_seq_no: int
        partition_id: int
        session_id: str
        supported_codecs: SupportedCodecs
        def __init__(self, last_seq_no: _Optional[int] = ..., session_id: _Optional[str] = ..., partition_id: _Optional[int] = ..., supported_codecs: _Optional[_Union[SupportedCodecs, _Mapping]] = ...) -> None: ...
    class WriteRequest(_message.Message):
        __slots__ = ["codec", "messages"]
        class MessageData(_message.Message):
            __slots__ = ["created_at", "data", "message_group_id", "partition_id", "seq_no", "uncompressed_size"]
            CREATED_AT_FIELD_NUMBER: _ClassVar[int]
            DATA_FIELD_NUMBER: _ClassVar[int]
            MESSAGE_GROUP_ID_FIELD_NUMBER: _ClassVar[int]
            PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
            SEQ_NO_FIELD_NUMBER: _ClassVar[int]
            UNCOMPRESSED_SIZE_FIELD_NUMBER: _ClassVar[int]
            created_at: _timestamp_pb2.Timestamp
            data: bytes
            message_group_id: str
            partition_id: int
            seq_no: int
            uncompressed_size: int
            def __init__(self, seq_no: _Optional[int] = ..., created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., data: _Optional[bytes] = ..., uncompressed_size: _Optional[int] = ..., message_group_id: _Optional[str] = ..., partition_id: _Optional[int] = ...) -> None: ...
        CODEC_FIELD_NUMBER: _ClassVar[int]
        MESSAGES_FIELD_NUMBER: _ClassVar[int]
        codec: int
        messages: _containers.RepeatedCompositeFieldContainer[StreamWriteMessage.WriteRequest.MessageData]
        def __init__(self, messages: _Optional[_Iterable[_Union[StreamWriteMessage.WriteRequest.MessageData, _Mapping]]] = ..., codec: _Optional[int] = ...) -> None: ...
    class WriteResponse(_message.Message):
        __slots__ = ["acks", "partition_id", "write_statistics"]
        class WriteAck(_message.Message):
            __slots__ = ["seq_no", "skipped", "written"]
            class Skipped(_message.Message):
                __slots__ = ["reason"]
                class Reason(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                    __slots__ = []
                REASON_ALREADY_WRITTEN: StreamWriteMessage.WriteResponse.WriteAck.Skipped.Reason
                REASON_FIELD_NUMBER: _ClassVar[int]
                REASON_UNSPECIFIED: StreamWriteMessage.WriteResponse.WriteAck.Skipped.Reason
                reason: StreamWriteMessage.WriteResponse.WriteAck.Skipped.Reason
                def __init__(self, reason: _Optional[_Union[StreamWriteMessage.WriteResponse.WriteAck.Skipped.Reason, str]] = ...) -> None: ...
            class Written(_message.Message):
                __slots__ = ["offset"]
                OFFSET_FIELD_NUMBER: _ClassVar[int]
                offset: int
                def __init__(self, offset: _Optional[int] = ...) -> None: ...
            SEQ_NO_FIELD_NUMBER: _ClassVar[int]
            SKIPPED_FIELD_NUMBER: _ClassVar[int]
            WRITTEN_FIELD_NUMBER: _ClassVar[int]
            seq_no: int
            skipped: StreamWriteMessage.WriteResponse.WriteAck.Skipped
            written: StreamWriteMessage.WriteResponse.WriteAck.Written
            def __init__(self, seq_no: _Optional[int] = ..., written: _Optional[_Union[StreamWriteMessage.WriteResponse.WriteAck.Written, _Mapping]] = ..., skipped: _Optional[_Union[StreamWriteMessage.WriteResponse.WriteAck.Skipped, _Mapping]] = ...) -> None: ...
        class WriteStatistics(_message.Message):
            __slots__ = ["max_queue_wait_time", "min_queue_wait_time", "partition_quota_wait_time", "persisting_time", "topic_quota_wait_time"]
            MAX_QUEUE_WAIT_TIME_FIELD_NUMBER: _ClassVar[int]
            MIN_QUEUE_WAIT_TIME_FIELD_NUMBER: _ClassVar[int]
            PARTITION_QUOTA_WAIT_TIME_FIELD_NUMBER: _ClassVar[int]
            PERSISTING_TIME_FIELD_NUMBER: _ClassVar[int]
            TOPIC_QUOTA_WAIT_TIME_FIELD_NUMBER: _ClassVar[int]
            max_queue_wait_time: _duration_pb2.Duration
            min_queue_wait_time: _duration_pb2.Duration
            partition_quota_wait_time: _duration_pb2.Duration
            persisting_time: _duration_pb2.Duration
            topic_quota_wait_time: _duration_pb2.Duration
            def __init__(self, persisting_time: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., min_queue_wait_time: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., max_queue_wait_time: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., partition_quota_wait_time: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., topic_quota_wait_time: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ...) -> None: ...
        ACKS_FIELD_NUMBER: _ClassVar[int]
        PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
        WRITE_STATISTICS_FIELD_NUMBER: _ClassVar[int]
        acks: _containers.RepeatedCompositeFieldContainer[StreamWriteMessage.WriteResponse.WriteAck]
        partition_id: int
        write_statistics: StreamWriteMessage.WriteResponse.WriteStatistics
        def __init__(self, acks: _Optional[_Iterable[_Union[StreamWriteMessage.WriteResponse.WriteAck, _Mapping]]] = ..., partition_id: _Optional[int] = ..., write_statistics: _Optional[_Union[StreamWriteMessage.WriteResponse.WriteStatistics, _Mapping]] = ...) -> None: ...
    def __init__(self) -> None: ...

class SupportedCodecs(_message.Message):
    __slots__ = ["codecs"]
    CODECS_FIELD_NUMBER: _ClassVar[int]
    codecs: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, codecs: _Optional[_Iterable[int]] = ...) -> None: ...

class UpdateTokenRequest(_message.Message):
    __slots__ = ["token"]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    token: str
    def __init__(self, token: _Optional[str] = ...) -> None: ...

class UpdateTokenResponse(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class Codec(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class MeteringMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
