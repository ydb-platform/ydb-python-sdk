from protos import ydb_operation_pb2 as _ydb_operation_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ConfigIdentity(_message.Message):
    __slots__ = ("version", "cluster")
    VERSION_FIELD_NUMBER: _ClassVar[int]
    CLUSTER_FIELD_NUMBER: _ClassVar[int]
    version: int
    cluster: str
    def __init__(self, version: _Optional[int] = ..., cluster: _Optional[str] = ...) -> None: ...

class SetConfigRequest(_message.Message):
    __slots__ = ("operation_params", "config", "dry_run", "allow_unknown_fields")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    DRY_RUN_FIELD_NUMBER: _ClassVar[int]
    ALLOW_UNKNOWN_FIELDS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    config: str
    dry_run: bool
    allow_unknown_fields: bool
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., config: _Optional[str] = ..., dry_run: bool = ..., allow_unknown_fields: bool = ...) -> None: ...

class SetConfigResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ReplaceConfigRequest(_message.Message):
    __slots__ = ("operation_params", "config", "dry_run", "allow_unknown_fields")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    DRY_RUN_FIELD_NUMBER: _ClassVar[int]
    ALLOW_UNKNOWN_FIELDS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    config: str
    dry_run: bool
    allow_unknown_fields: bool
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., config: _Optional[str] = ..., dry_run: bool = ..., allow_unknown_fields: bool = ...) -> None: ...

class ReplaceConfigResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DropConfigRequest(_message.Message):
    __slots__ = ("operation_params", "identity")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    IDENTITY_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    identity: ConfigIdentity
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., identity: _Optional[_Union[ConfigIdentity, _Mapping]] = ...) -> None: ...

class DropConfigResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class AddVolatileConfigRequest(_message.Message):
    __slots__ = ("operation_params", "config")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    config: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., config: _Optional[str] = ...) -> None: ...

class AddVolatileConfigResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class VolatileConfig(_message.Message):
    __slots__ = ("id", "config")
    ID_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    id: int
    config: str
    def __init__(self, id: _Optional[int] = ..., config: _Optional[str] = ...) -> None: ...

class GetConfigRequest(_message.Message):
    __slots__ = ("operation_params",)
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class GetConfigResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class GetConfigResult(_message.Message):
    __slots__ = ("config", "volatile_configs", "identity")
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    VOLATILE_CONFIGS_FIELD_NUMBER: _ClassVar[int]
    IDENTITY_FIELD_NUMBER: _ClassVar[int]
    config: str
    volatile_configs: _containers.RepeatedCompositeFieldContainer[VolatileConfig]
    identity: ConfigIdentity
    def __init__(self, config: _Optional[str] = ..., volatile_configs: _Optional[_Iterable[_Union[VolatileConfig, _Mapping]]] = ..., identity: _Optional[_Union[ConfigIdentity, _Mapping]] = ...) -> None: ...

class VolatileConfigMetadata(_message.Message):
    __slots__ = ("id", "metadata")
    ID_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    id: int
    metadata: str
    def __init__(self, id: _Optional[int] = ..., metadata: _Optional[str] = ...) -> None: ...

class GetMetadataRequest(_message.Message):
    __slots__ = ("operation_params",)
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class GetMetadataResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class GetMetadataResult(_message.Message):
    __slots__ = ("metadata", "volatile_configs")
    METADATA_FIELD_NUMBER: _ClassVar[int]
    VOLATILE_CONFIGS_FIELD_NUMBER: _ClassVar[int]
    metadata: str
    volatile_configs: _containers.RepeatedCompositeFieldContainer[VolatileConfigMetadata]
    def __init__(self, metadata: _Optional[str] = ..., volatile_configs: _Optional[_Iterable[_Union[VolatileConfigMetadata, _Mapping]]] = ...) -> None: ...

class RemoveVolatileConfigRequest(_message.Message):
    __slots__ = ("operation_params", "identity", "force", "ids", "all")
    class IdsToDelete(_message.Message):
        __slots__ = ("ids",)
        IDS_FIELD_NUMBER: _ClassVar[int]
        ids: _containers.RepeatedScalarFieldContainer[int]
        def __init__(self, ids: _Optional[_Iterable[int]] = ...) -> None: ...
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    IDENTITY_FIELD_NUMBER: _ClassVar[int]
    FORCE_FIELD_NUMBER: _ClassVar[int]
    IDS_FIELD_NUMBER: _ClassVar[int]
    ALL_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    identity: ConfigIdentity
    force: bool
    ids: RemoveVolatileConfigRequest.IdsToDelete
    all: bool
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., identity: _Optional[_Union[ConfigIdentity, _Mapping]] = ..., force: bool = ..., ids: _Optional[_Union[RemoveVolatileConfigRequest.IdsToDelete, _Mapping]] = ..., all: bool = ...) -> None: ...

class RemoveVolatileConfigResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class GetNodeLabelsRequest(_message.Message):
    __slots__ = ("operation_params", "node_id")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    node_id: int
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., node_id: _Optional[int] = ...) -> None: ...

class YamlLabel(_message.Message):
    __slots__ = ("label", "value")
    LABEL_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    label: str
    value: str
    def __init__(self, label: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class GetNodeLabelsResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class GetNodeLabelsResult(_message.Message):
    __slots__ = ("labels",)
    LABELS_FIELD_NUMBER: _ClassVar[int]
    labels: _containers.RepeatedCompositeFieldContainer[YamlLabel]
    def __init__(self, labels: _Optional[_Iterable[_Union[YamlLabel, _Mapping]]] = ...) -> None: ...

class ResolveConfigRequest(_message.Message):
    __slots__ = ("operation_params", "config", "volatile_configs", "labels")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    VOLATILE_CONFIGS_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    config: str
    volatile_configs: _containers.RepeatedCompositeFieldContainer[VolatileConfig]
    labels: _containers.RepeatedCompositeFieldContainer[YamlLabel]
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., config: _Optional[str] = ..., volatile_configs: _Optional[_Iterable[_Union[VolatileConfig, _Mapping]]] = ..., labels: _Optional[_Iterable[_Union[YamlLabel, _Mapping]]] = ...) -> None: ...

class ResolveConfigResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ResolveConfigResult(_message.Message):
    __slots__ = ("config",)
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    config: str
    def __init__(self, config: _Optional[str] = ...) -> None: ...

class ResolveAllConfigRequest(_message.Message):
    __slots__ = ("operation_params", "config", "volatile_configs", "verbose_response")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    VOLATILE_CONFIGS_FIELD_NUMBER: _ClassVar[int]
    VERBOSE_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    config: str
    volatile_configs: _containers.RepeatedCompositeFieldContainer[VolatileConfig]
    verbose_response: bool
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., config: _Optional[str] = ..., volatile_configs: _Optional[_Iterable[_Union[VolatileConfig, _Mapping]]] = ..., verbose_response: bool = ...) -> None: ...

class YamlLabelExt(_message.Message):
    __slots__ = ("label", "type", "value")
    class LabelType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNSPECIFIED: _ClassVar[YamlLabelExt.LabelType]
        COMMON: _ClassVar[YamlLabelExt.LabelType]
        NOT_SET: _ClassVar[YamlLabelExt.LabelType]
        EMPTY: _ClassVar[YamlLabelExt.LabelType]
    UNSPECIFIED: YamlLabelExt.LabelType
    COMMON: YamlLabelExt.LabelType
    NOT_SET: YamlLabelExt.LabelType
    EMPTY: YamlLabelExt.LabelType
    LABEL_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    label: str
    type: YamlLabelExt.LabelType
    value: str
    def __init__(self, label: _Optional[str] = ..., type: _Optional[_Union[YamlLabelExt.LabelType, str]] = ..., value: _Optional[str] = ...) -> None: ...

class LabelSet(_message.Message):
    __slots__ = ("labels",)
    LABELS_FIELD_NUMBER: _ClassVar[int]
    labels: _containers.RepeatedCompositeFieldContainer[YamlLabelExt]
    def __init__(self, labels: _Optional[_Iterable[_Union[YamlLabelExt, _Mapping]]] = ...) -> None: ...

class ResolvedConfig(_message.Message):
    __slots__ = ("label_sets", "config")
    LABEL_SETS_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    label_sets: _containers.RepeatedCompositeFieldContainer[LabelSet]
    config: str
    def __init__(self, label_sets: _Optional[_Iterable[_Union[LabelSet, _Mapping]]] = ..., config: _Optional[str] = ...) -> None: ...

class ResolveAllConfigResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ResolveAllConfigResult(_message.Message):
    __slots__ = ("config", "configs")
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    CONFIGS_FIELD_NUMBER: _ClassVar[int]
    config: str
    configs: _containers.RepeatedCompositeFieldContainer[ResolvedConfig]
    def __init__(self, config: _Optional[str] = ..., configs: _Optional[_Iterable[_Union[ResolvedConfig, _Mapping]]] = ...) -> None: ...
