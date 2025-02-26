from protos import ydb_operation_pb2 as _ydb_operation_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ComputeNodeStatus(_message.Message):
    __slots__ = ["id", "load", "overall", "pools", "tablets"]
    ID_FIELD_NUMBER: _ClassVar[int]
    LOAD_FIELD_NUMBER: _ClassVar[int]
    OVERALL_FIELD_NUMBER: _ClassVar[int]
    POOLS_FIELD_NUMBER: _ClassVar[int]
    TABLETS_FIELD_NUMBER: _ClassVar[int]
    id: str
    load: LoadAverageStatus
    overall: StatusFlag.Status
    pools: _containers.RepeatedCompositeFieldContainer[ThreadPoolStatus]
    tablets: _containers.RepeatedCompositeFieldContainer[ComputeTabletStatus]
    def __init__(self, id: _Optional[str] = ..., overall: _Optional[_Union[StatusFlag.Status, str]] = ..., tablets: _Optional[_Iterable[_Union[ComputeTabletStatus, _Mapping]]] = ..., pools: _Optional[_Iterable[_Union[ThreadPoolStatus, _Mapping]]] = ..., load: _Optional[_Union[LoadAverageStatus, _Mapping]] = ...) -> None: ...

class ComputeStatus(_message.Message):
    __slots__ = ["nodes", "overall", "tablets"]
    NODES_FIELD_NUMBER: _ClassVar[int]
    OVERALL_FIELD_NUMBER: _ClassVar[int]
    TABLETS_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[ComputeNodeStatus]
    overall: StatusFlag.Status
    tablets: _containers.RepeatedCompositeFieldContainer[ComputeTabletStatus]
    def __init__(self, overall: _Optional[_Union[StatusFlag.Status, str]] = ..., nodes: _Optional[_Iterable[_Union[ComputeNodeStatus, _Mapping]]] = ..., tablets: _Optional[_Iterable[_Union[ComputeTabletStatus, _Mapping]]] = ...) -> None: ...

class ComputeTabletStatus(_message.Message):
    __slots__ = ["count", "id", "overall", "state", "type"]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    OVERALL_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    count: int
    id: _containers.RepeatedScalarFieldContainer[str]
    overall: StatusFlag.Status
    state: str
    type: str
    def __init__(self, overall: _Optional[_Union[StatusFlag.Status, str]] = ..., type: _Optional[str] = ..., state: _Optional[str] = ..., count: _Optional[int] = ..., id: _Optional[_Iterable[str]] = ...) -> None: ...

class DatabaseStatus(_message.Message):
    __slots__ = ["compute", "name", "overall", "storage"]
    COMPUTE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    OVERALL_FIELD_NUMBER: _ClassVar[int]
    STORAGE_FIELD_NUMBER: _ClassVar[int]
    compute: ComputeStatus
    name: str
    overall: StatusFlag.Status
    storage: StorageStatus
    def __init__(self, name: _Optional[str] = ..., overall: _Optional[_Union[StatusFlag.Status, str]] = ..., storage: _Optional[_Union[StorageStatus, _Mapping]] = ..., compute: _Optional[_Union[ComputeStatus, _Mapping]] = ...) -> None: ...

class IssueLog(_message.Message):
    __slots__ = ["count", "id", "level", "listed", "location", "message", "reason", "status", "type"]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    LISTED_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    count: int
    id: str
    level: int
    listed: int
    location: Location
    message: str
    reason: _containers.RepeatedScalarFieldContainer[str]
    status: StatusFlag.Status
    type: str
    def __init__(self, id: _Optional[str] = ..., status: _Optional[_Union[StatusFlag.Status, str]] = ..., message: _Optional[str] = ..., location: _Optional[_Union[Location, _Mapping]] = ..., reason: _Optional[_Iterable[str]] = ..., type: _Optional[str] = ..., level: _Optional[int] = ..., listed: _Optional[int] = ..., count: _Optional[int] = ...) -> None: ...

class LoadAverageStatus(_message.Message):
    __slots__ = ["cores", "load", "overall"]
    CORES_FIELD_NUMBER: _ClassVar[int]
    LOAD_FIELD_NUMBER: _ClassVar[int]
    OVERALL_FIELD_NUMBER: _ClassVar[int]
    cores: int
    load: float
    overall: StatusFlag.Status
    def __init__(self, overall: _Optional[_Union[StatusFlag.Status, str]] = ..., load: _Optional[float] = ..., cores: _Optional[int] = ...) -> None: ...

class Location(_message.Message):
    __slots__ = ["compute", "database", "storage"]
    COMPUTE_FIELD_NUMBER: _ClassVar[int]
    DATABASE_FIELD_NUMBER: _ClassVar[int]
    STORAGE_FIELD_NUMBER: _ClassVar[int]
    compute: LocationCompute
    database: LocationDatabase
    storage: LocationStorage
    def __init__(self, storage: _Optional[_Union[LocationStorage, _Mapping]] = ..., compute: _Optional[_Union[LocationCompute, _Mapping]] = ..., database: _Optional[_Union[LocationDatabase, _Mapping]] = ...) -> None: ...

class LocationCompute(_message.Message):
    __slots__ = ["node", "pool", "tablet"]
    NODE_FIELD_NUMBER: _ClassVar[int]
    POOL_FIELD_NUMBER: _ClassVar[int]
    TABLET_FIELD_NUMBER: _ClassVar[int]
    node: LocationNode
    pool: LocationComputePool
    tablet: LocationComputeTablet
    def __init__(self, node: _Optional[_Union[LocationNode, _Mapping]] = ..., pool: _Optional[_Union[LocationComputePool, _Mapping]] = ..., tablet: _Optional[_Union[LocationComputeTablet, _Mapping]] = ...) -> None: ...

class LocationComputePool(_message.Message):
    __slots__ = ["name"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class LocationComputeTablet(_message.Message):
    __slots__ = ["count", "id", "type"]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    count: int
    id: _containers.RepeatedScalarFieldContainer[str]
    type: str
    def __init__(self, type: _Optional[str] = ..., id: _Optional[_Iterable[str]] = ..., count: _Optional[int] = ...) -> None: ...

class LocationDatabase(_message.Message):
    __slots__ = ["name"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class LocationNode(_message.Message):
    __slots__ = ["host", "id", "port"]
    HOST_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    host: str
    id: int
    port: int
    def __init__(self, id: _Optional[int] = ..., host: _Optional[str] = ..., port: _Optional[int] = ...) -> None: ...

class LocationStorage(_message.Message):
    __slots__ = ["node", "pool"]
    NODE_FIELD_NUMBER: _ClassVar[int]
    POOL_FIELD_NUMBER: _ClassVar[int]
    node: LocationNode
    pool: LocationStoragePool
    def __init__(self, node: _Optional[_Union[LocationNode, _Mapping]] = ..., pool: _Optional[_Union[LocationStoragePool, _Mapping]] = ...) -> None: ...

class LocationStorageGroup(_message.Message):
    __slots__ = ["id", "vdisk"]
    ID_FIELD_NUMBER: _ClassVar[int]
    VDISK_FIELD_NUMBER: _ClassVar[int]
    id: _containers.RepeatedScalarFieldContainer[str]
    vdisk: LocationStorageVDisk
    def __init__(self, id: _Optional[_Iterable[str]] = ..., vdisk: _Optional[_Union[LocationStorageVDisk, _Mapping]] = ...) -> None: ...

class LocationStoragePDisk(_message.Message):
    __slots__ = ["id", "path"]
    ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    id: str
    path: str
    def __init__(self, id: _Optional[str] = ..., path: _Optional[str] = ...) -> None: ...

class LocationStoragePool(_message.Message):
    __slots__ = ["group", "name"]
    GROUP_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    group: LocationStorageGroup
    name: str
    def __init__(self, name: _Optional[str] = ..., group: _Optional[_Union[LocationStorageGroup, _Mapping]] = ...) -> None: ...

class LocationStorageVDisk(_message.Message):
    __slots__ = ["id", "pdisk"]
    ID_FIELD_NUMBER: _ClassVar[int]
    PDISK_FIELD_NUMBER: _ClassVar[int]
    id: _containers.RepeatedScalarFieldContainer[str]
    pdisk: _containers.RepeatedCompositeFieldContainer[LocationStoragePDisk]
    def __init__(self, id: _Optional[_Iterable[str]] = ..., pdisk: _Optional[_Iterable[_Union[LocationStoragePDisk, _Mapping]]] = ...) -> None: ...

class NodeCheckRequest(_message.Message):
    __slots__ = ["operation_params"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class NodeCheckResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class SelfCheck(_message.Message):
    __slots__ = []
    class Result(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    DEGRADED: SelfCheck.Result
    EMERGENCY: SelfCheck.Result
    GOOD: SelfCheck.Result
    MAINTENANCE_REQUIRED: SelfCheck.Result
    UNSPECIFIED: SelfCheck.Result
    def __init__(self) -> None: ...

class SelfCheckRequest(_message.Message):
    __slots__ = ["maximum_level", "minimum_status", "operation_params", "return_verbose_status"]
    MAXIMUM_LEVEL_FIELD_NUMBER: _ClassVar[int]
    MINIMUM_STATUS_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    RETURN_VERBOSE_STATUS_FIELD_NUMBER: _ClassVar[int]
    maximum_level: int
    minimum_status: StatusFlag.Status
    operation_params: _ydb_operation_pb2.OperationParams
    return_verbose_status: bool
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., return_verbose_status: bool = ..., minimum_status: _Optional[_Union[StatusFlag.Status, str]] = ..., maximum_level: _Optional[int] = ...) -> None: ...

class SelfCheckResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class SelfCheckResult(_message.Message):
    __slots__ = ["database_status", "issue_log", "self_check_result"]
    DATABASE_STATUS_FIELD_NUMBER: _ClassVar[int]
    ISSUE_LOG_FIELD_NUMBER: _ClassVar[int]
    SELF_CHECK_RESULT_FIELD_NUMBER: _ClassVar[int]
    database_status: _containers.RepeatedCompositeFieldContainer[DatabaseStatus]
    issue_log: _containers.RepeatedCompositeFieldContainer[IssueLog]
    self_check_result: SelfCheck.Result
    def __init__(self, self_check_result: _Optional[_Union[SelfCheck.Result, str]] = ..., issue_log: _Optional[_Iterable[_Union[IssueLog, _Mapping]]] = ..., database_status: _Optional[_Iterable[_Union[DatabaseStatus, _Mapping]]] = ...) -> None: ...

class StatusFlag(_message.Message):
    __slots__ = []
    class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    BLUE: StatusFlag.Status
    GREEN: StatusFlag.Status
    GREY: StatusFlag.Status
    ORANGE: StatusFlag.Status
    RED: StatusFlag.Status
    UNSPECIFIED: StatusFlag.Status
    YELLOW: StatusFlag.Status
    def __init__(self) -> None: ...

class StorageGroupStatus(_message.Message):
    __slots__ = ["id", "overall", "vdisks"]
    ID_FIELD_NUMBER: _ClassVar[int]
    OVERALL_FIELD_NUMBER: _ClassVar[int]
    VDISKS_FIELD_NUMBER: _ClassVar[int]
    id: str
    overall: StatusFlag.Status
    vdisks: _containers.RepeatedCompositeFieldContainer[StorageVDiskStatus]
    def __init__(self, id: _Optional[str] = ..., overall: _Optional[_Union[StatusFlag.Status, str]] = ..., vdisks: _Optional[_Iterable[_Union[StorageVDiskStatus, _Mapping]]] = ...) -> None: ...

class StoragePDiskStatus(_message.Message):
    __slots__ = ["id", "overall"]
    ID_FIELD_NUMBER: _ClassVar[int]
    OVERALL_FIELD_NUMBER: _ClassVar[int]
    id: str
    overall: StatusFlag.Status
    def __init__(self, id: _Optional[str] = ..., overall: _Optional[_Union[StatusFlag.Status, str]] = ...) -> None: ...

class StoragePoolStatus(_message.Message):
    __slots__ = ["groups", "id", "overall"]
    GROUPS_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    OVERALL_FIELD_NUMBER: _ClassVar[int]
    groups: _containers.RepeatedCompositeFieldContainer[StorageGroupStatus]
    id: str
    overall: StatusFlag.Status
    def __init__(self, id: _Optional[str] = ..., overall: _Optional[_Union[StatusFlag.Status, str]] = ..., groups: _Optional[_Iterable[_Union[StorageGroupStatus, _Mapping]]] = ...) -> None: ...

class StorageStatus(_message.Message):
    __slots__ = ["overall", "pools"]
    OVERALL_FIELD_NUMBER: _ClassVar[int]
    POOLS_FIELD_NUMBER: _ClassVar[int]
    overall: StatusFlag.Status
    pools: _containers.RepeatedCompositeFieldContainer[StoragePoolStatus]
    def __init__(self, overall: _Optional[_Union[StatusFlag.Status, str]] = ..., pools: _Optional[_Iterable[_Union[StoragePoolStatus, _Mapping]]] = ...) -> None: ...

class StorageVDiskStatus(_message.Message):
    __slots__ = ["id", "overall", "pdisk", "vdisk_status"]
    ID_FIELD_NUMBER: _ClassVar[int]
    OVERALL_FIELD_NUMBER: _ClassVar[int]
    PDISK_FIELD_NUMBER: _ClassVar[int]
    VDISK_STATUS_FIELD_NUMBER: _ClassVar[int]
    id: str
    overall: StatusFlag.Status
    pdisk: StoragePDiskStatus
    vdisk_status: StatusFlag.Status
    def __init__(self, id: _Optional[str] = ..., overall: _Optional[_Union[StatusFlag.Status, str]] = ..., vdisk_status: _Optional[_Union[StatusFlag.Status, str]] = ..., pdisk: _Optional[_Union[StoragePDiskStatus, _Mapping]] = ...) -> None: ...

class ThreadPoolStatus(_message.Message):
    __slots__ = ["name", "overall", "usage"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    OVERALL_FIELD_NUMBER: _ClassVar[int]
    USAGE_FIELD_NUMBER: _ClassVar[int]
    name: str
    overall: StatusFlag.Status
    usage: float
    def __init__(self, overall: _Optional[_Union[StatusFlag.Status, str]] = ..., name: _Optional[str] = ..., usage: _Optional[float] = ...) -> None: ...
