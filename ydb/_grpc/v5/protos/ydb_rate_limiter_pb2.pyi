from protos import ydb_operation_pb2 as _ydb_operation_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AcquireResourceRequest(_message.Message):
    __slots__ = ["coordination_node_path", "operation_params", "required", "resource_path", "used"]
    COORDINATION_NODE_PATH_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    REQUIRED_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
    USED_FIELD_NUMBER: _ClassVar[int]
    coordination_node_path: str
    operation_params: _ydb_operation_pb2.OperationParams
    required: int
    resource_path: str
    used: int
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., coordination_node_path: _Optional[str] = ..., resource_path: _Optional[str] = ..., required: _Optional[int] = ..., used: _Optional[int] = ...) -> None: ...

class AcquireResourceResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class AcquireResourceResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class AlterResourceRequest(_message.Message):
    __slots__ = ["coordination_node_path", "operation_params", "resource"]
    COORDINATION_NODE_PATH_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_FIELD_NUMBER: _ClassVar[int]
    coordination_node_path: str
    operation_params: _ydb_operation_pb2.OperationParams
    resource: Resource
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., coordination_node_path: _Optional[str] = ..., resource: _Optional[_Union[Resource, _Mapping]] = ...) -> None: ...

class AlterResourceResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class AlterResourceResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class CreateResourceRequest(_message.Message):
    __slots__ = ["coordination_node_path", "operation_params", "resource"]
    COORDINATION_NODE_PATH_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_FIELD_NUMBER: _ClassVar[int]
    coordination_node_path: str
    operation_params: _ydb_operation_pb2.OperationParams
    resource: Resource
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., coordination_node_path: _Optional[str] = ..., resource: _Optional[_Union[Resource, _Mapping]] = ...) -> None: ...

class CreateResourceResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class CreateResourceResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class DescribeResourceRequest(_message.Message):
    __slots__ = ["coordination_node_path", "operation_params", "resource_path"]
    COORDINATION_NODE_PATH_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
    coordination_node_path: str
    operation_params: _ydb_operation_pb2.OperationParams
    resource_path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., coordination_node_path: _Optional[str] = ..., resource_path: _Optional[str] = ...) -> None: ...

class DescribeResourceResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeResourceResult(_message.Message):
    __slots__ = ["resource"]
    RESOURCE_FIELD_NUMBER: _ClassVar[int]
    resource: Resource
    def __init__(self, resource: _Optional[_Union[Resource, _Mapping]] = ...) -> None: ...

class DropResourceRequest(_message.Message):
    __slots__ = ["coordination_node_path", "operation_params", "resource_path"]
    COORDINATION_NODE_PATH_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
    coordination_node_path: str
    operation_params: _ydb_operation_pb2.OperationParams
    resource_path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., coordination_node_path: _Optional[str] = ..., resource_path: _Optional[str] = ...) -> None: ...

class DropResourceResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DropResourceResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class HierarchicalDrrSettings(_message.Message):
    __slots__ = ["max_burst_size_coefficient", "max_units_per_second", "prefetch_coefficient", "prefetch_watermark"]
    MAX_BURST_SIZE_COEFFICIENT_FIELD_NUMBER: _ClassVar[int]
    MAX_UNITS_PER_SECOND_FIELD_NUMBER: _ClassVar[int]
    PREFETCH_COEFFICIENT_FIELD_NUMBER: _ClassVar[int]
    PREFETCH_WATERMARK_FIELD_NUMBER: _ClassVar[int]
    max_burst_size_coefficient: float
    max_units_per_second: float
    prefetch_coefficient: float
    prefetch_watermark: float
    def __init__(self, max_units_per_second: _Optional[float] = ..., max_burst_size_coefficient: _Optional[float] = ..., prefetch_coefficient: _Optional[float] = ..., prefetch_watermark: _Optional[float] = ...) -> None: ...

class ListResourcesRequest(_message.Message):
    __slots__ = ["coordination_node_path", "operation_params", "recursive", "resource_path"]
    COORDINATION_NODE_PATH_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    RECURSIVE_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
    coordination_node_path: str
    operation_params: _ydb_operation_pb2.OperationParams
    recursive: bool
    resource_path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., coordination_node_path: _Optional[str] = ..., resource_path: _Optional[str] = ..., recursive: bool = ...) -> None: ...

class ListResourcesResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListResourcesResult(_message.Message):
    __slots__ = ["resource_paths"]
    RESOURCE_PATHS_FIELD_NUMBER: _ClassVar[int]
    resource_paths: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, resource_paths: _Optional[_Iterable[str]] = ...) -> None: ...

class Resource(_message.Message):
    __slots__ = ["hierarchical_drr", "resource_path"]
    HIERARCHICAL_DRR_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
    hierarchical_drr: HierarchicalDrrSettings
    resource_path: str
    def __init__(self, resource_path: _Optional[str] = ..., hierarchical_drr: _Optional[_Union[HierarchicalDrrSettings, _Mapping]] = ...) -> None: ...
