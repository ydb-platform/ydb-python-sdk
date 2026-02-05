from protos import ydb_operation_pb2 as _ydb_operation_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class StorageChannelInfo(_message.Message):
    __slots__ = ("storage_channel", "status_flag")
    class StatusFlag(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        STATUS_FLAG_UNSPECIFIED: _ClassVar[StorageChannelInfo.StatusFlag]
        STATUS_FLAG_GREEN: _ClassVar[StorageChannelInfo.StatusFlag]
        STATUS_FLAG_YELLOW_STOP: _ClassVar[StorageChannelInfo.StatusFlag]
        STATUS_FLAG_ORANGE_OUT_SPACE: _ClassVar[StorageChannelInfo.StatusFlag]
    STATUS_FLAG_UNSPECIFIED: StorageChannelInfo.StatusFlag
    STATUS_FLAG_GREEN: StorageChannelInfo.StatusFlag
    STATUS_FLAG_YELLOW_STOP: StorageChannelInfo.StatusFlag
    STATUS_FLAG_ORANGE_OUT_SPACE: StorageChannelInfo.StatusFlag
    STORAGE_CHANNEL_FIELD_NUMBER: _ClassVar[int]
    STATUS_FLAG_FIELD_NUMBER: _ClassVar[int]
    storage_channel: int
    status_flag: StorageChannelInfo.StatusFlag
    def __init__(self, storage_channel: _Optional[int] = ..., status_flag: _Optional[_Union[StorageChannelInfo.StatusFlag, str]] = ...) -> None: ...

class Priorities(_message.Message):
    __slots__ = ()
    class Priority(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        PRIORITY_UNSPECIFIED: _ClassVar[Priorities.Priority]
        PRIORITY_REALTIME: _ClassVar[Priorities.Priority]
        PRIORITY_BACKGROUND: _ClassVar[Priorities.Priority]
    PRIORITY_UNSPECIFIED: Priorities.Priority
    PRIORITY_REALTIME: Priorities.Priority
    PRIORITY_BACKGROUND: Priorities.Priority
    def __init__(self) -> None: ...

class StorageConfig(_message.Message):
    __slots__ = ("channel",)
    class ChannelConfig(_message.Message):
        __slots__ = ("media",)
        MEDIA_FIELD_NUMBER: _ClassVar[int]
        media: str
        def __init__(self, media: _Optional[str] = ...) -> None: ...
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    channel: _containers.RepeatedCompositeFieldContainer[StorageConfig.ChannelConfig]
    def __init__(self, channel: _Optional[_Iterable[_Union[StorageConfig.ChannelConfig, _Mapping]]] = ...) -> None: ...

class KeyRange(_message.Message):
    __slots__ = ("from_key_inclusive", "from_key_exclusive", "to_key_inclusive", "to_key_exclusive")
    FROM_KEY_INCLUSIVE_FIELD_NUMBER: _ClassVar[int]
    FROM_KEY_EXCLUSIVE_FIELD_NUMBER: _ClassVar[int]
    TO_KEY_INCLUSIVE_FIELD_NUMBER: _ClassVar[int]
    TO_KEY_EXCLUSIVE_FIELD_NUMBER: _ClassVar[int]
    from_key_inclusive: str
    from_key_exclusive: str
    to_key_inclusive: str
    to_key_exclusive: str
    def __init__(self, from_key_inclusive: _Optional[str] = ..., from_key_exclusive: _Optional[str] = ..., to_key_inclusive: _Optional[str] = ..., to_key_exclusive: _Optional[str] = ...) -> None: ...

class AcquireLockRequest(_message.Message):
    __slots__ = ("operation_params", "path", "partition_id")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    partition_id: int
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., partition_id: _Optional[int] = ...) -> None: ...

class AcquireLockResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class AcquireLockResult(_message.Message):
    __slots__ = ("lock_generation", "node_id")
    LOCK_GENERATION_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    lock_generation: int
    node_id: int
    def __init__(self, lock_generation: _Optional[int] = ..., node_id: _Optional[int] = ...) -> None: ...

class ExecuteTransactionRequest(_message.Message):
    __slots__ = ("operation_params", "path", "partition_id", "lock_generation", "commands")
    class Command(_message.Message):
        __slots__ = ("delete_range", "rename", "copy_range", "concat", "write")
        class Rename(_message.Message):
            __slots__ = ("old_key", "new_key")
            OLD_KEY_FIELD_NUMBER: _ClassVar[int]
            NEW_KEY_FIELD_NUMBER: _ClassVar[int]
            old_key: str
            new_key: str
            def __init__(self, old_key: _Optional[str] = ..., new_key: _Optional[str] = ...) -> None: ...
        class Concat(_message.Message):
            __slots__ = ("input_keys", "output_key", "keep_inputs")
            INPUT_KEYS_FIELD_NUMBER: _ClassVar[int]
            OUTPUT_KEY_FIELD_NUMBER: _ClassVar[int]
            KEEP_INPUTS_FIELD_NUMBER: _ClassVar[int]
            input_keys: _containers.RepeatedScalarFieldContainer[str]
            output_key: str
            keep_inputs: bool
            def __init__(self, input_keys: _Optional[_Iterable[str]] = ..., output_key: _Optional[str] = ..., keep_inputs: bool = ...) -> None: ...
        class CopyRange(_message.Message):
            __slots__ = ("range", "prefix_to_remove", "prefix_to_add")
            RANGE_FIELD_NUMBER: _ClassVar[int]
            PREFIX_TO_REMOVE_FIELD_NUMBER: _ClassVar[int]
            PREFIX_TO_ADD_FIELD_NUMBER: _ClassVar[int]
            range: KeyRange
            prefix_to_remove: str
            prefix_to_add: str
            def __init__(self, range: _Optional[_Union[KeyRange, _Mapping]] = ..., prefix_to_remove: _Optional[str] = ..., prefix_to_add: _Optional[str] = ...) -> None: ...
        class Write(_message.Message):
            __slots__ = ("key", "value", "storage_channel", "priority", "tactic")
            class Tactic(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = ()
                TACTIC_UNSPECIFIED: _ClassVar[ExecuteTransactionRequest.Command.Write.Tactic]
                TACTIC_MAX_THROUGHPUT: _ClassVar[ExecuteTransactionRequest.Command.Write.Tactic]
                TACTIC_MIN_LATENCY: _ClassVar[ExecuteTransactionRequest.Command.Write.Tactic]
            TACTIC_UNSPECIFIED: ExecuteTransactionRequest.Command.Write.Tactic
            TACTIC_MAX_THROUGHPUT: ExecuteTransactionRequest.Command.Write.Tactic
            TACTIC_MIN_LATENCY: ExecuteTransactionRequest.Command.Write.Tactic
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            STORAGE_CHANNEL_FIELD_NUMBER: _ClassVar[int]
            PRIORITY_FIELD_NUMBER: _ClassVar[int]
            TACTIC_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: bytes
            storage_channel: int
            priority: Priorities.Priority
            tactic: ExecuteTransactionRequest.Command.Write.Tactic
            def __init__(self, key: _Optional[str] = ..., value: _Optional[bytes] = ..., storage_channel: _Optional[int] = ..., priority: _Optional[_Union[Priorities.Priority, str]] = ..., tactic: _Optional[_Union[ExecuteTransactionRequest.Command.Write.Tactic, str]] = ...) -> None: ...
        class DeleteRange(_message.Message):
            __slots__ = ("range",)
            RANGE_FIELD_NUMBER: _ClassVar[int]
            range: KeyRange
            def __init__(self, range: _Optional[_Union[KeyRange, _Mapping]] = ...) -> None: ...
        DELETE_RANGE_FIELD_NUMBER: _ClassVar[int]
        RENAME_FIELD_NUMBER: _ClassVar[int]
        COPY_RANGE_FIELD_NUMBER: _ClassVar[int]
        CONCAT_FIELD_NUMBER: _ClassVar[int]
        WRITE_FIELD_NUMBER: _ClassVar[int]
        delete_range: ExecuteTransactionRequest.Command.DeleteRange
        rename: ExecuteTransactionRequest.Command.Rename
        copy_range: ExecuteTransactionRequest.Command.CopyRange
        concat: ExecuteTransactionRequest.Command.Concat
        write: ExecuteTransactionRequest.Command.Write
        def __init__(self, delete_range: _Optional[_Union[ExecuteTransactionRequest.Command.DeleteRange, _Mapping]] = ..., rename: _Optional[_Union[ExecuteTransactionRequest.Command.Rename, _Mapping]] = ..., copy_range: _Optional[_Union[ExecuteTransactionRequest.Command.CopyRange, _Mapping]] = ..., concat: _Optional[_Union[ExecuteTransactionRequest.Command.Concat, _Mapping]] = ..., write: _Optional[_Union[ExecuteTransactionRequest.Command.Write, _Mapping]] = ...) -> None: ...
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
    LOCK_GENERATION_FIELD_NUMBER: _ClassVar[int]
    COMMANDS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    partition_id: int
    lock_generation: int
    commands: _containers.RepeatedCompositeFieldContainer[ExecuteTransactionRequest.Command]
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., partition_id: _Optional[int] = ..., lock_generation: _Optional[int] = ..., commands: _Optional[_Iterable[_Union[ExecuteTransactionRequest.Command, _Mapping]]] = ...) -> None: ...

class ExecuteTransactionResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ExecuteTransactionResult(_message.Message):
    __slots__ = ("storage_channel_info", "node_id")
    STORAGE_CHANNEL_INFO_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    storage_channel_info: _containers.RepeatedCompositeFieldContainer[StorageChannelInfo]
    node_id: int
    def __init__(self, storage_channel_info: _Optional[_Iterable[_Union[StorageChannelInfo, _Mapping]]] = ..., node_id: _Optional[int] = ...) -> None: ...

class ReadRequest(_message.Message):
    __slots__ = ("operation_params", "path", "partition_id", "lock_generation", "key", "offset", "size", "limit_bytes", "priority")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
    LOCK_GENERATION_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    LIMIT_BYTES_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    partition_id: int
    lock_generation: int
    key: str
    offset: int
    size: int
    limit_bytes: int
    priority: Priorities.Priority
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., partition_id: _Optional[int] = ..., lock_generation: _Optional[int] = ..., key: _Optional[str] = ..., offset: _Optional[int] = ..., size: _Optional[int] = ..., limit_bytes: _Optional[int] = ..., priority: _Optional[_Union[Priorities.Priority, str]] = ...) -> None: ...

class ReadResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ReadResult(_message.Message):
    __slots__ = ("requested_key", "requested_offset", "requested_size", "value", "is_overrun", "node_id")
    REQUESTED_KEY_FIELD_NUMBER: _ClassVar[int]
    REQUESTED_OFFSET_FIELD_NUMBER: _ClassVar[int]
    REQUESTED_SIZE_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    IS_OVERRUN_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    requested_key: str
    requested_offset: int
    requested_size: int
    value: bytes
    is_overrun: bool
    node_id: int
    def __init__(self, requested_key: _Optional[str] = ..., requested_offset: _Optional[int] = ..., requested_size: _Optional[int] = ..., value: _Optional[bytes] = ..., is_overrun: bool = ..., node_id: _Optional[int] = ...) -> None: ...

class ReadRangeRequest(_message.Message):
    __slots__ = ("operation_params", "path", "partition_id", "lock_generation", "range", "limit_bytes", "priority")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
    LOCK_GENERATION_FIELD_NUMBER: _ClassVar[int]
    RANGE_FIELD_NUMBER: _ClassVar[int]
    LIMIT_BYTES_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    partition_id: int
    lock_generation: int
    range: KeyRange
    limit_bytes: int
    priority: Priorities.Priority
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., partition_id: _Optional[int] = ..., lock_generation: _Optional[int] = ..., range: _Optional[_Union[KeyRange, _Mapping]] = ..., limit_bytes: _Optional[int] = ..., priority: _Optional[_Union[Priorities.Priority, str]] = ...) -> None: ...

class ReadRangeResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ReadRangeResult(_message.Message):
    __slots__ = ("pair", "is_overrun", "node_id")
    class KeyValuePair(_message.Message):
        __slots__ = ("key", "value", "creation_unix_time", "storage_channel")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        CREATION_UNIX_TIME_FIELD_NUMBER: _ClassVar[int]
        STORAGE_CHANNEL_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: bytes
        creation_unix_time: int
        storage_channel: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[bytes] = ..., creation_unix_time: _Optional[int] = ..., storage_channel: _Optional[int] = ...) -> None: ...
    PAIR_FIELD_NUMBER: _ClassVar[int]
    IS_OVERRUN_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    pair: _containers.RepeatedCompositeFieldContainer[ReadRangeResult.KeyValuePair]
    is_overrun: bool
    node_id: int
    def __init__(self, pair: _Optional[_Iterable[_Union[ReadRangeResult.KeyValuePair, _Mapping]]] = ..., is_overrun: bool = ..., node_id: _Optional[int] = ...) -> None: ...

class ListRangeRequest(_message.Message):
    __slots__ = ("operation_params", "path", "partition_id", "lock_generation", "range", "limit_bytes")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
    LOCK_GENERATION_FIELD_NUMBER: _ClassVar[int]
    RANGE_FIELD_NUMBER: _ClassVar[int]
    LIMIT_BYTES_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    partition_id: int
    lock_generation: int
    range: KeyRange
    limit_bytes: int
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., partition_id: _Optional[int] = ..., lock_generation: _Optional[int] = ..., range: _Optional[_Union[KeyRange, _Mapping]] = ..., limit_bytes: _Optional[int] = ...) -> None: ...

class ListRangeResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListRangeResult(_message.Message):
    __slots__ = ("key", "is_overrun", "node_id")
    class KeyInfo(_message.Message):
        __slots__ = ("key", "value_size", "creation_unix_time", "storage_channel")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_SIZE_FIELD_NUMBER: _ClassVar[int]
        CREATION_UNIX_TIME_FIELD_NUMBER: _ClassVar[int]
        STORAGE_CHANNEL_FIELD_NUMBER: _ClassVar[int]
        key: str
        value_size: int
        creation_unix_time: int
        storage_channel: int
        def __init__(self, key: _Optional[str] = ..., value_size: _Optional[int] = ..., creation_unix_time: _Optional[int] = ..., storage_channel: _Optional[int] = ...) -> None: ...
    KEY_FIELD_NUMBER: _ClassVar[int]
    IS_OVERRUN_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    key: _containers.RepeatedCompositeFieldContainer[ListRangeResult.KeyInfo]
    is_overrun: bool
    node_id: int
    def __init__(self, key: _Optional[_Iterable[_Union[ListRangeResult.KeyInfo, _Mapping]]] = ..., is_overrun: bool = ..., node_id: _Optional[int] = ...) -> None: ...

class GetStorageChannelStatusRequest(_message.Message):
    __slots__ = ("operation_params", "path", "partition_id", "lock_generation", "storage_channel")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
    LOCK_GENERATION_FIELD_NUMBER: _ClassVar[int]
    STORAGE_CHANNEL_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    partition_id: int
    lock_generation: int
    storage_channel: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., partition_id: _Optional[int] = ..., lock_generation: _Optional[int] = ..., storage_channel: _Optional[_Iterable[int]] = ...) -> None: ...

class GetStorageChannelStatusResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class GetStorageChannelStatusResult(_message.Message):
    __slots__ = ("storage_channel_info", "node_id")
    STORAGE_CHANNEL_INFO_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    storage_channel_info: _containers.RepeatedCompositeFieldContainer[StorageChannelInfo]
    node_id: int
    def __init__(self, storage_channel_info: _Optional[_Iterable[_Union[StorageChannelInfo, _Mapping]]] = ..., node_id: _Optional[int] = ...) -> None: ...

class CreateVolumeRequest(_message.Message):
    __slots__ = ("operation_params", "path", "partition_count", "storage_config")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    PARTITION_COUNT_FIELD_NUMBER: _ClassVar[int]
    STORAGE_CONFIG_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    partition_count: int
    storage_config: StorageConfig
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., partition_count: _Optional[int] = ..., storage_config: _Optional[_Union[StorageConfig, _Mapping]] = ...) -> None: ...

class CreateVolumeResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class CreateVolumeResult(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DropVolumeRequest(_message.Message):
    __slots__ = ("operation_params", "path")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ...) -> None: ...

class DropVolumeResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DropVolumeResult(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AlterVolumeRequest(_message.Message):
    __slots__ = ("operation_params", "path", "alter_partition_count", "storage_config")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    ALTER_PARTITION_COUNT_FIELD_NUMBER: _ClassVar[int]
    STORAGE_CONFIG_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    alter_partition_count: int
    storage_config: StorageConfig
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., alter_partition_count: _Optional[int] = ..., storage_config: _Optional[_Union[StorageConfig, _Mapping]] = ...) -> None: ...

class AlterVolumeResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class AlterVolumeResult(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DescribeVolumeRequest(_message.Message):
    __slots__ = ("operation_params", "path")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ...) -> None: ...

class DescribeVolumeResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeVolumeResult(_message.Message):
    __slots__ = ("path", "partition_count")
    PATH_FIELD_NUMBER: _ClassVar[int]
    PARTITION_COUNT_FIELD_NUMBER: _ClassVar[int]
    path: str
    partition_count: int
    def __init__(self, path: _Optional[str] = ..., partition_count: _Optional[int] = ...) -> None: ...

class ListLocalPartitionsRequest(_message.Message):
    __slots__ = ("operation_params", "path", "node_id")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    node_id: int
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., node_id: _Optional[int] = ...) -> None: ...

class ListLocalPartitionsResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListLocalPartitionsResult(_message.Message):
    __slots__ = ("path", "node_id", "partition_ids")
    PATH_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    PARTITION_IDS_FIELD_NUMBER: _ClassVar[int]
    path: str
    node_id: int
    partition_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, path: _Optional[str] = ..., node_id: _Optional[int] = ..., partition_ids: _Optional[_Iterable[int]] = ...) -> None: ...
