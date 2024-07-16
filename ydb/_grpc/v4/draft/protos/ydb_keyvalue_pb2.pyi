from protos import ydb_operation_pb2 as _ydb_operation_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AcquireLockRequest(_message.Message):
    __slots__ = ["operation_params", "partition_id", "path"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    partition_id: int
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., partition_id: _Optional[int] = ...) -> None: ...

class AcquireLockResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class AcquireLockResult(_message.Message):
    __slots__ = ["lock_generation", "node_id"]
    LOCK_GENERATION_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    lock_generation: int
    node_id: int
    def __init__(self, lock_generation: _Optional[int] = ..., node_id: _Optional[int] = ...) -> None: ...

class AlterVolumeRequest(_message.Message):
    __slots__ = ["alter_partition_count", "operation_params", "path", "storage_config"]
    ALTER_PARTITION_COUNT_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    STORAGE_CONFIG_FIELD_NUMBER: _ClassVar[int]
    alter_partition_count: int
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    storage_config: StorageConfig
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., alter_partition_count: _Optional[int] = ..., storage_config: _Optional[_Union[StorageConfig, _Mapping]] = ...) -> None: ...

class AlterVolumeResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class AlterVolumeResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class CreateVolumeRequest(_message.Message):
    __slots__ = ["operation_params", "partition_count", "path", "storage_config"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PARTITION_COUNT_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    STORAGE_CONFIG_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    partition_count: int
    path: str
    storage_config: StorageConfig
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., partition_count: _Optional[int] = ..., storage_config: _Optional[_Union[StorageConfig, _Mapping]] = ...) -> None: ...

class CreateVolumeResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class CreateVolumeResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class DescribeVolumeRequest(_message.Message):
    __slots__ = ["operation_params", "path"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ...) -> None: ...

class DescribeVolumeResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeVolumeResult(_message.Message):
    __slots__ = ["partition_count", "path"]
    PARTITION_COUNT_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    partition_count: int
    path: str
    def __init__(self, path: _Optional[str] = ..., partition_count: _Optional[int] = ...) -> None: ...

class DropVolumeRequest(_message.Message):
    __slots__ = ["operation_params", "path"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ...) -> None: ...

class DropVolumeResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DropVolumeResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class ExecuteTransactionRequest(_message.Message):
    __slots__ = ["commands", "lock_generation", "operation_params", "partition_id", "path"]
    class Command(_message.Message):
        __slots__ = ["concat", "copy_range", "delete_range", "rename", "write"]
        class Concat(_message.Message):
            __slots__ = ["input_keys", "keep_inputs", "output_key"]
            INPUT_KEYS_FIELD_NUMBER: _ClassVar[int]
            KEEP_INPUTS_FIELD_NUMBER: _ClassVar[int]
            OUTPUT_KEY_FIELD_NUMBER: _ClassVar[int]
            input_keys: _containers.RepeatedScalarFieldContainer[str]
            keep_inputs: bool
            output_key: str
            def __init__(self, input_keys: _Optional[_Iterable[str]] = ..., output_key: _Optional[str] = ..., keep_inputs: bool = ...) -> None: ...
        class CopyRange(_message.Message):
            __slots__ = ["prefix_to_add", "prefix_to_remove", "range"]
            PREFIX_TO_ADD_FIELD_NUMBER: _ClassVar[int]
            PREFIX_TO_REMOVE_FIELD_NUMBER: _ClassVar[int]
            RANGE_FIELD_NUMBER: _ClassVar[int]
            prefix_to_add: str
            prefix_to_remove: str
            range: KeyRange
            def __init__(self, range: _Optional[_Union[KeyRange, _Mapping]] = ..., prefix_to_remove: _Optional[str] = ..., prefix_to_add: _Optional[str] = ...) -> None: ...
        class DeleteRange(_message.Message):
            __slots__ = ["range"]
            RANGE_FIELD_NUMBER: _ClassVar[int]
            range: KeyRange
            def __init__(self, range: _Optional[_Union[KeyRange, _Mapping]] = ...) -> None: ...
        class Rename(_message.Message):
            __slots__ = ["new_key", "old_key"]
            NEW_KEY_FIELD_NUMBER: _ClassVar[int]
            OLD_KEY_FIELD_NUMBER: _ClassVar[int]
            new_key: str
            old_key: str
            def __init__(self, old_key: _Optional[str] = ..., new_key: _Optional[str] = ...) -> None: ...
        class Write(_message.Message):
            __slots__ = ["key", "priority", "storage_channel", "tactic", "value"]
            class Tactic(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
            KEY_FIELD_NUMBER: _ClassVar[int]
            PRIORITY_FIELD_NUMBER: _ClassVar[int]
            STORAGE_CHANNEL_FIELD_NUMBER: _ClassVar[int]
            TACTIC_FIELD_NUMBER: _ClassVar[int]
            TACTIC_MAX_THROUGHPUT: ExecuteTransactionRequest.Command.Write.Tactic
            TACTIC_MIN_LATENCY: ExecuteTransactionRequest.Command.Write.Tactic
            TACTIC_UNSPECIFIED: ExecuteTransactionRequest.Command.Write.Tactic
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            priority: Priorities.Priority
            storage_channel: int
            tactic: ExecuteTransactionRequest.Command.Write.Tactic
            value: bytes
            def __init__(self, key: _Optional[str] = ..., value: _Optional[bytes] = ..., storage_channel: _Optional[int] = ..., priority: _Optional[_Union[Priorities.Priority, str]] = ..., tactic: _Optional[_Union[ExecuteTransactionRequest.Command.Write.Tactic, str]] = ...) -> None: ...
        CONCAT_FIELD_NUMBER: _ClassVar[int]
        COPY_RANGE_FIELD_NUMBER: _ClassVar[int]
        DELETE_RANGE_FIELD_NUMBER: _ClassVar[int]
        RENAME_FIELD_NUMBER: _ClassVar[int]
        WRITE_FIELD_NUMBER: _ClassVar[int]
        concat: ExecuteTransactionRequest.Command.Concat
        copy_range: ExecuteTransactionRequest.Command.CopyRange
        delete_range: ExecuteTransactionRequest.Command.DeleteRange
        rename: ExecuteTransactionRequest.Command.Rename
        write: ExecuteTransactionRequest.Command.Write
        def __init__(self, delete_range: _Optional[_Union[ExecuteTransactionRequest.Command.DeleteRange, _Mapping]] = ..., rename: _Optional[_Union[ExecuteTransactionRequest.Command.Rename, _Mapping]] = ..., copy_range: _Optional[_Union[ExecuteTransactionRequest.Command.CopyRange, _Mapping]] = ..., concat: _Optional[_Union[ExecuteTransactionRequest.Command.Concat, _Mapping]] = ..., write: _Optional[_Union[ExecuteTransactionRequest.Command.Write, _Mapping]] = ...) -> None: ...
    COMMANDS_FIELD_NUMBER: _ClassVar[int]
    LOCK_GENERATION_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    commands: _containers.RepeatedCompositeFieldContainer[ExecuteTransactionRequest.Command]
    lock_generation: int
    operation_params: _ydb_operation_pb2.OperationParams
    partition_id: int
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., partition_id: _Optional[int] = ..., lock_generation: _Optional[int] = ..., commands: _Optional[_Iterable[_Union[ExecuteTransactionRequest.Command, _Mapping]]] = ...) -> None: ...

class ExecuteTransactionResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ExecuteTransactionResult(_message.Message):
    __slots__ = ["node_id", "storage_channel_info"]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    STORAGE_CHANNEL_INFO_FIELD_NUMBER: _ClassVar[int]
    node_id: int
    storage_channel_info: _containers.RepeatedCompositeFieldContainer[StorageChannelInfo]
    def __init__(self, storage_channel_info: _Optional[_Iterable[_Union[StorageChannelInfo, _Mapping]]] = ..., node_id: _Optional[int] = ...) -> None: ...

class GetStorageChannelStatusRequest(_message.Message):
    __slots__ = ["lock_generation", "operation_params", "partition_id", "path", "storage_channel"]
    LOCK_GENERATION_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    STORAGE_CHANNEL_FIELD_NUMBER: _ClassVar[int]
    lock_generation: int
    operation_params: _ydb_operation_pb2.OperationParams
    partition_id: int
    path: str
    storage_channel: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., partition_id: _Optional[int] = ..., lock_generation: _Optional[int] = ..., storage_channel: _Optional[_Iterable[int]] = ...) -> None: ...

class GetStorageChannelStatusResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class GetStorageChannelStatusResult(_message.Message):
    __slots__ = ["node_id", "storage_channel_info"]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    STORAGE_CHANNEL_INFO_FIELD_NUMBER: _ClassVar[int]
    node_id: int
    storage_channel_info: _containers.RepeatedCompositeFieldContainer[StorageChannelInfo]
    def __init__(self, storage_channel_info: _Optional[_Iterable[_Union[StorageChannelInfo, _Mapping]]] = ..., node_id: _Optional[int] = ...) -> None: ...

class KeyRange(_message.Message):
    __slots__ = ["from_key_exclusive", "from_key_inclusive", "to_key_exclusive", "to_key_inclusive"]
    FROM_KEY_EXCLUSIVE_FIELD_NUMBER: _ClassVar[int]
    FROM_KEY_INCLUSIVE_FIELD_NUMBER: _ClassVar[int]
    TO_KEY_EXCLUSIVE_FIELD_NUMBER: _ClassVar[int]
    TO_KEY_INCLUSIVE_FIELD_NUMBER: _ClassVar[int]
    from_key_exclusive: str
    from_key_inclusive: str
    to_key_exclusive: str
    to_key_inclusive: str
    def __init__(self, from_key_inclusive: _Optional[str] = ..., from_key_exclusive: _Optional[str] = ..., to_key_inclusive: _Optional[str] = ..., to_key_exclusive: _Optional[str] = ...) -> None: ...

class ListLocalPartitionsRequest(_message.Message):
    __slots__ = ["node_id", "operation_params", "path"]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    node_id: int
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., node_id: _Optional[int] = ...) -> None: ...

class ListLocalPartitionsResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListLocalPartitionsResult(_message.Message):
    __slots__ = ["node_id", "partition_ids", "path"]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    PARTITION_IDS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    node_id: int
    partition_ids: _containers.RepeatedScalarFieldContainer[int]
    path: str
    def __init__(self, path: _Optional[str] = ..., node_id: _Optional[int] = ..., partition_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class ListRangeRequest(_message.Message):
    __slots__ = ["limit_bytes", "lock_generation", "operation_params", "partition_id", "path", "range"]
    LIMIT_BYTES_FIELD_NUMBER: _ClassVar[int]
    LOCK_GENERATION_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    RANGE_FIELD_NUMBER: _ClassVar[int]
    limit_bytes: int
    lock_generation: int
    operation_params: _ydb_operation_pb2.OperationParams
    partition_id: int
    path: str
    range: KeyRange
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., partition_id: _Optional[int] = ..., lock_generation: _Optional[int] = ..., range: _Optional[_Union[KeyRange, _Mapping]] = ..., limit_bytes: _Optional[int] = ...) -> None: ...

class ListRangeResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListRangeResult(_message.Message):
    __slots__ = ["is_overrun", "key", "node_id"]
    class KeyInfo(_message.Message):
        __slots__ = ["creation_unix_time", "key", "storage_channel", "value_size"]
        CREATION_UNIX_TIME_FIELD_NUMBER: _ClassVar[int]
        KEY_FIELD_NUMBER: _ClassVar[int]
        STORAGE_CHANNEL_FIELD_NUMBER: _ClassVar[int]
        VALUE_SIZE_FIELD_NUMBER: _ClassVar[int]
        creation_unix_time: int
        key: str
        storage_channel: int
        value_size: int
        def __init__(self, key: _Optional[str] = ..., value_size: _Optional[int] = ..., creation_unix_time: _Optional[int] = ..., storage_channel: _Optional[int] = ...) -> None: ...
    IS_OVERRUN_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    is_overrun: bool
    key: _containers.RepeatedCompositeFieldContainer[ListRangeResult.KeyInfo]
    node_id: int
    def __init__(self, key: _Optional[_Iterable[_Union[ListRangeResult.KeyInfo, _Mapping]]] = ..., is_overrun: bool = ..., node_id: _Optional[int] = ...) -> None: ...

class Priorities(_message.Message):
    __slots__ = []
    class Priority(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    PRIORITY_BACKGROUND: Priorities.Priority
    PRIORITY_REALTIME: Priorities.Priority
    PRIORITY_UNSPECIFIED: Priorities.Priority
    def __init__(self) -> None: ...

class ReadRangeRequest(_message.Message):
    __slots__ = ["limit_bytes", "lock_generation", "operation_params", "partition_id", "path", "priority", "range"]
    LIMIT_BYTES_FIELD_NUMBER: _ClassVar[int]
    LOCK_GENERATION_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    RANGE_FIELD_NUMBER: _ClassVar[int]
    limit_bytes: int
    lock_generation: int
    operation_params: _ydb_operation_pb2.OperationParams
    partition_id: int
    path: str
    priority: Priorities.Priority
    range: KeyRange
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., partition_id: _Optional[int] = ..., lock_generation: _Optional[int] = ..., range: _Optional[_Union[KeyRange, _Mapping]] = ..., limit_bytes: _Optional[int] = ..., priority: _Optional[_Union[Priorities.Priority, str]] = ...) -> None: ...

class ReadRangeResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ReadRangeResult(_message.Message):
    __slots__ = ["is_overrun", "node_id", "pair"]
    class KeyValuePair(_message.Message):
        __slots__ = ["creation_unix_time", "key", "storage_channel", "value"]
        CREATION_UNIX_TIME_FIELD_NUMBER: _ClassVar[int]
        KEY_FIELD_NUMBER: _ClassVar[int]
        STORAGE_CHANNEL_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        creation_unix_time: int
        key: str
        storage_channel: int
        value: bytes
        def __init__(self, key: _Optional[str] = ..., value: _Optional[bytes] = ..., creation_unix_time: _Optional[int] = ..., storage_channel: _Optional[int] = ...) -> None: ...
    IS_OVERRUN_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    PAIR_FIELD_NUMBER: _ClassVar[int]
    is_overrun: bool
    node_id: int
    pair: _containers.RepeatedCompositeFieldContainer[ReadRangeResult.KeyValuePair]
    def __init__(self, pair: _Optional[_Iterable[_Union[ReadRangeResult.KeyValuePair, _Mapping]]] = ..., is_overrun: bool = ..., node_id: _Optional[int] = ...) -> None: ...

class ReadRequest(_message.Message):
    __slots__ = ["key", "limit_bytes", "lock_generation", "offset", "operation_params", "partition_id", "path", "priority", "size"]
    KEY_FIELD_NUMBER: _ClassVar[int]
    LIMIT_BYTES_FIELD_NUMBER: _ClassVar[int]
    LOCK_GENERATION_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    key: str
    limit_bytes: int
    lock_generation: int
    offset: int
    operation_params: _ydb_operation_pb2.OperationParams
    partition_id: int
    path: str
    priority: Priorities.Priority
    size: int
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., partition_id: _Optional[int] = ..., lock_generation: _Optional[int] = ..., key: _Optional[str] = ..., offset: _Optional[int] = ..., size: _Optional[int] = ..., limit_bytes: _Optional[int] = ..., priority: _Optional[_Union[Priorities.Priority, str]] = ...) -> None: ...

class ReadResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ReadResult(_message.Message):
    __slots__ = ["is_overrun", "node_id", "requested_key", "requested_offset", "requested_size", "value"]
    IS_OVERRUN_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    REQUESTED_KEY_FIELD_NUMBER: _ClassVar[int]
    REQUESTED_OFFSET_FIELD_NUMBER: _ClassVar[int]
    REQUESTED_SIZE_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    is_overrun: bool
    node_id: int
    requested_key: str
    requested_offset: int
    requested_size: int
    value: bytes
    def __init__(self, requested_key: _Optional[str] = ..., requested_offset: _Optional[int] = ..., requested_size: _Optional[int] = ..., value: _Optional[bytes] = ..., is_overrun: bool = ..., node_id: _Optional[int] = ...) -> None: ...

class StorageChannelInfo(_message.Message):
    __slots__ = ["status_flag", "storage_channel"]
    class StatusFlag(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    STATUS_FLAG_FIELD_NUMBER: _ClassVar[int]
    STATUS_FLAG_GREEN: StorageChannelInfo.StatusFlag
    STATUS_FLAG_ORANGE_OUT_SPACE: StorageChannelInfo.StatusFlag
    STATUS_FLAG_UNSPECIFIED: StorageChannelInfo.StatusFlag
    STATUS_FLAG_YELLOW_STOP: StorageChannelInfo.StatusFlag
    STORAGE_CHANNEL_FIELD_NUMBER: _ClassVar[int]
    status_flag: StorageChannelInfo.StatusFlag
    storage_channel: int
    def __init__(self, storage_channel: _Optional[int] = ..., status_flag: _Optional[_Union[StorageChannelInfo.StatusFlag, str]] = ...) -> None: ...

class StorageConfig(_message.Message):
    __slots__ = ["channel"]
    class ChannelConfig(_message.Message):
        __slots__ = ["media"]
        MEDIA_FIELD_NUMBER: _ClassVar[int]
        media: str
        def __init__(self, media: _Optional[str] = ...) -> None: ...
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    channel: _containers.RepeatedCompositeFieldContainer[StorageConfig.ChannelConfig]
    def __init__(self, channel: _Optional[_Iterable[_Union[StorageConfig.ChannelConfig, _Mapping]]] = ...) -> None: ...
