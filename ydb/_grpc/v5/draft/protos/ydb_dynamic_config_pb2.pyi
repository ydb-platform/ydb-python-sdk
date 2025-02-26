from protos import ydb_operation_pb2 as _ydb_operation_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AddVolatileConfigRequest(_message.Message):
    __slots__ = ["config", "operation_params"]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    config: str
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., config: _Optional[str] = ...) -> None: ...

class AddVolatileConfigResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ConfigIdentity(_message.Message):
    __slots__ = ["cluster", "version"]
    CLUSTER_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    cluster: str
    version: int
    def __init__(self, version: _Optional[int] = ..., cluster: _Optional[str] = ...) -> None: ...

class DropConfigRequest(_message.Message):
    __slots__ = ["identity", "operation_params"]
    IDENTITY_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    identity: ConfigIdentity
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., identity: _Optional[_Union[ConfigIdentity, _Mapping]] = ...) -> None: ...

class DropConfigResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class GetConfigRequest(_message.Message):
    __slots__ = ["operation_params"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class GetConfigResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class GetConfigResult(_message.Message):
    __slots__ = ["config", "identity", "volatile_configs"]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    IDENTITY_FIELD_NUMBER: _ClassVar[int]
    VOLATILE_CONFIGS_FIELD_NUMBER: _ClassVar[int]
    config: str
    identity: ConfigIdentity
    volatile_configs: _containers.RepeatedCompositeFieldContainer[VolatileConfig]
    def __init__(self, config: _Optional[str] = ..., volatile_configs: _Optional[_Iterable[_Union[VolatileConfig, _Mapping]]] = ..., identity: _Optional[_Union[ConfigIdentity, _Mapping]] = ...) -> None: ...

class GetMetadataRequest(_message.Message):
    __slots__ = ["operation_params"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class GetMetadataResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class GetMetadataResult(_message.Message):
    __slots__ = ["metadata", "volatile_configs"]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    VOLATILE_CONFIGS_FIELD_NUMBER: _ClassVar[int]
    metadata: str
    volatile_configs: _containers.RepeatedCompositeFieldContainer[VolatileConfigMetadata]
    def __init__(self, metadata: _Optional[str] = ..., volatile_configs: _Optional[_Iterable[_Union[VolatileConfigMetadata, _Mapping]]] = ...) -> None: ...

class GetNodeLabelsRequest(_message.Message):
    __slots__ = ["node_id", "operation_params"]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    node_id: int
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., node_id: _Optional[int] = ...) -> None: ...

class GetNodeLabelsResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class GetNodeLabelsResult(_message.Message):
    __slots__ = ["labels"]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    labels: _containers.RepeatedCompositeFieldContainer[YamlLabel]
    def __init__(self, labels: _Optional[_Iterable[_Union[YamlLabel, _Mapping]]] = ...) -> None: ...

class LabelSet(_message.Message):
    __slots__ = ["labels"]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    labels: _containers.RepeatedCompositeFieldContainer[YamlLabelExt]
    def __init__(self, labels: _Optional[_Iterable[_Union[YamlLabelExt, _Mapping]]] = ...) -> None: ...

class RemoveVolatileConfigRequest(_message.Message):
    __slots__ = ["all", "force", "identity", "ids", "operation_params"]
    class IdsToDelete(_message.Message):
        __slots__ = ["ids"]
        IDS_FIELD_NUMBER: _ClassVar[int]
        ids: _containers.RepeatedScalarFieldContainer[int]
        def __init__(self, ids: _Optional[_Iterable[int]] = ...) -> None: ...
    ALL_FIELD_NUMBER: _ClassVar[int]
    FORCE_FIELD_NUMBER: _ClassVar[int]
    IDENTITY_FIELD_NUMBER: _ClassVar[int]
    IDS_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    all: bool
    force: bool
    identity: ConfigIdentity
    ids: RemoveVolatileConfigRequest.IdsToDelete
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., identity: _Optional[_Union[ConfigIdentity, _Mapping]] = ..., force: bool = ..., ids: _Optional[_Union[RemoveVolatileConfigRequest.IdsToDelete, _Mapping]] = ..., all: bool = ...) -> None: ...

class RemoveVolatileConfigResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ReplaceConfigRequest(_message.Message):
    __slots__ = ["allow_unknown_fields", "config", "dry_run", "operation_params"]
    ALLOW_UNKNOWN_FIELDS_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    DRY_RUN_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    allow_unknown_fields: bool
    config: str
    dry_run: bool
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., config: _Optional[str] = ..., dry_run: bool = ..., allow_unknown_fields: bool = ...) -> None: ...

class ReplaceConfigResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ResolveAllConfigRequest(_message.Message):
    __slots__ = ["config", "operation_params", "verbose_response", "volatile_configs"]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    VERBOSE_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    VOLATILE_CONFIGS_FIELD_NUMBER: _ClassVar[int]
    config: str
    operation_params: _ydb_operation_pb2.OperationParams
    verbose_response: bool
    volatile_configs: _containers.RepeatedCompositeFieldContainer[VolatileConfig]
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., config: _Optional[str] = ..., volatile_configs: _Optional[_Iterable[_Union[VolatileConfig, _Mapping]]] = ..., verbose_response: bool = ...) -> None: ...

class ResolveAllConfigResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ResolveAllConfigResult(_message.Message):
    __slots__ = ["config", "configs"]
    CONFIGS_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    config: str
    configs: _containers.RepeatedCompositeFieldContainer[ResolvedConfig]
    def __init__(self, config: _Optional[str] = ..., configs: _Optional[_Iterable[_Union[ResolvedConfig, _Mapping]]] = ...) -> None: ...

class ResolveConfigRequest(_message.Message):
    __slots__ = ["config", "labels", "operation_params", "volatile_configs"]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    VOLATILE_CONFIGS_FIELD_NUMBER: _ClassVar[int]
    config: str
    labels: _containers.RepeatedCompositeFieldContainer[YamlLabel]
    operation_params: _ydb_operation_pb2.OperationParams
    volatile_configs: _containers.RepeatedCompositeFieldContainer[VolatileConfig]
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., config: _Optional[str] = ..., volatile_configs: _Optional[_Iterable[_Union[VolatileConfig, _Mapping]]] = ..., labels: _Optional[_Iterable[_Union[YamlLabel, _Mapping]]] = ...) -> None: ...

class ResolveConfigResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ResolveConfigResult(_message.Message):
    __slots__ = ["config"]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    config: str
    def __init__(self, config: _Optional[str] = ...) -> None: ...

class ResolvedConfig(_message.Message):
    __slots__ = ["config", "label_sets"]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    LABEL_SETS_FIELD_NUMBER: _ClassVar[int]
    config: str
    label_sets: _containers.RepeatedCompositeFieldContainer[LabelSet]
    def __init__(self, label_sets: _Optional[_Iterable[_Union[LabelSet, _Mapping]]] = ..., config: _Optional[str] = ...) -> None: ...

class SetConfigRequest(_message.Message):
    __slots__ = ["allow_unknown_fields", "config", "dry_run", "operation_params"]
    ALLOW_UNKNOWN_FIELDS_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    DRY_RUN_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    allow_unknown_fields: bool
    config: str
    dry_run: bool
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., config: _Optional[str] = ..., dry_run: bool = ..., allow_unknown_fields: bool = ...) -> None: ...

class SetConfigResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class VolatileConfig(_message.Message):
    __slots__ = ["config", "id"]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    config: str
    id: int
    def __init__(self, id: _Optional[int] = ..., config: _Optional[str] = ...) -> None: ...

class VolatileConfigMetadata(_message.Message):
    __slots__ = ["id", "metadata"]
    ID_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    id: int
    metadata: str
    def __init__(self, id: _Optional[int] = ..., metadata: _Optional[str] = ...) -> None: ...

class YamlLabel(_message.Message):
    __slots__ = ["label", "value"]
    LABEL_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    label: str
    value: str
    def __init__(self, label: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class YamlLabelExt(_message.Message):
    __slots__ = ["label", "type", "value"]
    class LabelType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    COMMON: YamlLabelExt.LabelType
    EMPTY: YamlLabelExt.LabelType
    LABEL_FIELD_NUMBER: _ClassVar[int]
    NOT_SET: YamlLabelExt.LabelType
    TYPE_FIELD_NUMBER: _ClassVar[int]
    UNSPECIFIED: YamlLabelExt.LabelType
    VALUE_FIELD_NUMBER: _ClassVar[int]
    label: str
    type: YamlLabelExt.LabelType
    value: str
    def __init__(self, label: _Optional[str] = ..., type: _Optional[_Union[YamlLabelExt.LabelType, str]] = ..., value: _Optional[str] = ...) -> None: ...
