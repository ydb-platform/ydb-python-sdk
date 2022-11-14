from protos import ydb_operation_pb2 as _ydb_operation_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AllocatedComputationalUnit(_message.Message):
    __slots__ = ["host", "port", "unit_kind"]
    HOST_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    UNIT_KIND_FIELD_NUMBER: _ClassVar[int]
    host: str
    port: int
    unit_kind: str
    def __init__(self, host: _Optional[str] = ..., port: _Optional[int] = ..., unit_kind: _Optional[str] = ...) -> None: ...

class AlterDatabaseRequest(_message.Message):
    __slots__ = ["alter_attributes", "computational_units_to_add", "computational_units_to_deregister", "computational_units_to_register", "computational_units_to_remove", "database_quotas", "generation", "idempotency_key", "operation_params", "path", "schema_operation_quotas", "storage_units_to_add"]
    class AlterAttributesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ALTER_ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    COMPUTATIONAL_UNITS_TO_ADD_FIELD_NUMBER: _ClassVar[int]
    COMPUTATIONAL_UNITS_TO_DEREGISTER_FIELD_NUMBER: _ClassVar[int]
    COMPUTATIONAL_UNITS_TO_REGISTER_FIELD_NUMBER: _ClassVar[int]
    COMPUTATIONAL_UNITS_TO_REMOVE_FIELD_NUMBER: _ClassVar[int]
    DATABASE_QUOTAS_FIELD_NUMBER: _ClassVar[int]
    GENERATION_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_OPERATION_QUOTAS_FIELD_NUMBER: _ClassVar[int]
    STORAGE_UNITS_TO_ADD_FIELD_NUMBER: _ClassVar[int]
    alter_attributes: _containers.ScalarMap[str, str]
    computational_units_to_add: _containers.RepeatedCompositeFieldContainer[ComputationalUnits]
    computational_units_to_deregister: _containers.RepeatedCompositeFieldContainer[AllocatedComputationalUnit]
    computational_units_to_register: _containers.RepeatedCompositeFieldContainer[AllocatedComputationalUnit]
    computational_units_to_remove: _containers.RepeatedCompositeFieldContainer[ComputationalUnits]
    database_quotas: DatabaseQuotas
    generation: int
    idempotency_key: str
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    schema_operation_quotas: SchemaOperationQuotas
    storage_units_to_add: _containers.RepeatedCompositeFieldContainer[StorageUnits]
    def __init__(self, path: _Optional[str] = ..., computational_units_to_add: _Optional[_Iterable[_Union[ComputationalUnits, _Mapping]]] = ..., computational_units_to_remove: _Optional[_Iterable[_Union[ComputationalUnits, _Mapping]]] = ..., storage_units_to_add: _Optional[_Iterable[_Union[StorageUnits, _Mapping]]] = ..., computational_units_to_register: _Optional[_Iterable[_Union[AllocatedComputationalUnit, _Mapping]]] = ..., computational_units_to_deregister: _Optional[_Iterable[_Union[AllocatedComputationalUnit, _Mapping]]] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., generation: _Optional[int] = ..., schema_operation_quotas: _Optional[_Union[SchemaOperationQuotas, _Mapping]] = ..., idempotency_key: _Optional[str] = ..., database_quotas: _Optional[_Union[DatabaseQuotas, _Mapping]] = ..., alter_attributes: _Optional[_Mapping[str, str]] = ...) -> None: ...

class AlterDatabaseResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class AvailabilityZoneDescription(_message.Message):
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

class ComputationalUnitDescription(_message.Message):
    __slots__ = ["allowed_availability_zones", "kind", "labels"]
    class LabelsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ALLOWED_AVAILABILITY_ZONES_FIELD_NUMBER: _ClassVar[int]
    KIND_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    allowed_availability_zones: _containers.RepeatedScalarFieldContainer[str]
    kind: str
    labels: _containers.ScalarMap[str, str]
    def __init__(self, kind: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ..., allowed_availability_zones: _Optional[_Iterable[str]] = ...) -> None: ...

class ComputationalUnits(_message.Message):
    __slots__ = ["availability_zone", "count", "unit_kind"]
    AVAILABILITY_ZONE_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    UNIT_KIND_FIELD_NUMBER: _ClassVar[int]
    availability_zone: str
    count: int
    unit_kind: str
    def __init__(self, unit_kind: _Optional[str] = ..., availability_zone: _Optional[str] = ..., count: _Optional[int] = ...) -> None: ...

class CreateDatabaseRequest(_message.Message):
    __slots__ = ["attributes", "database_quotas", "idempotency_key", "operation_params", "options", "path", "resources", "schema_operation_quotas", "serverless_resources", "shared_resources"]
    class AttributesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    DATABASE_QUOTAS_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    RESOURCES_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_OPERATION_QUOTAS_FIELD_NUMBER: _ClassVar[int]
    SERVERLESS_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    SHARED_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    attributes: _containers.ScalarMap[str, str]
    database_quotas: DatabaseQuotas
    idempotency_key: str
    operation_params: _ydb_operation_pb2.OperationParams
    options: DatabaseOptions
    path: str
    resources: Resources
    schema_operation_quotas: SchemaOperationQuotas
    serverless_resources: ServerlessResources
    shared_resources: Resources
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., resources: _Optional[_Union[Resources, _Mapping]] = ..., shared_resources: _Optional[_Union[Resources, _Mapping]] = ..., serverless_resources: _Optional[_Union[ServerlessResources, _Mapping]] = ..., options: _Optional[_Union[DatabaseOptions, _Mapping]] = ..., attributes: _Optional[_Mapping[str, str]] = ..., schema_operation_quotas: _Optional[_Union[SchemaOperationQuotas, _Mapping]] = ..., idempotency_key: _Optional[str] = ..., database_quotas: _Optional[_Union[DatabaseQuotas, _Mapping]] = ...) -> None: ...

class CreateDatabaseResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DatabaseOptions(_message.Message):
    __slots__ = ["disable_external_subdomain", "disable_tx_service", "plan_resolution"]
    DISABLE_EXTERNAL_SUBDOMAIN_FIELD_NUMBER: _ClassVar[int]
    DISABLE_TX_SERVICE_FIELD_NUMBER: _ClassVar[int]
    PLAN_RESOLUTION_FIELD_NUMBER: _ClassVar[int]
    disable_external_subdomain: bool
    disable_tx_service: bool
    plan_resolution: int
    def __init__(self, disable_tx_service: bool = ..., disable_external_subdomain: bool = ..., plan_resolution: _Optional[int] = ...) -> None: ...

class DatabaseQuotas(_message.Message):
    __slots__ = ["data_size_hard_quota", "data_size_soft_quota", "data_stream_reserved_storage_quota", "data_stream_shards_quota", "ttl_min_run_internal_seconds"]
    DATA_SIZE_HARD_QUOTA_FIELD_NUMBER: _ClassVar[int]
    DATA_SIZE_SOFT_QUOTA_FIELD_NUMBER: _ClassVar[int]
    DATA_STREAM_RESERVED_STORAGE_QUOTA_FIELD_NUMBER: _ClassVar[int]
    DATA_STREAM_SHARDS_QUOTA_FIELD_NUMBER: _ClassVar[int]
    TTL_MIN_RUN_INTERNAL_SECONDS_FIELD_NUMBER: _ClassVar[int]
    data_size_hard_quota: int
    data_size_soft_quota: int
    data_stream_reserved_storage_quota: int
    data_stream_shards_quota: int
    ttl_min_run_internal_seconds: int
    def __init__(self, data_size_hard_quota: _Optional[int] = ..., data_size_soft_quota: _Optional[int] = ..., data_stream_shards_quota: _Optional[int] = ..., data_stream_reserved_storage_quota: _Optional[int] = ..., ttl_min_run_internal_seconds: _Optional[int] = ...) -> None: ...

class DescribeDatabaseOptionsRequest(_message.Message):
    __slots__ = ["operation_params"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class DescribeDatabaseOptionsResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeDatabaseOptionsResult(_message.Message):
    __slots__ = ["availability_zones", "computational_units", "storage_units"]
    AVAILABILITY_ZONES_FIELD_NUMBER: _ClassVar[int]
    COMPUTATIONAL_UNITS_FIELD_NUMBER: _ClassVar[int]
    STORAGE_UNITS_FIELD_NUMBER: _ClassVar[int]
    availability_zones: _containers.RepeatedCompositeFieldContainer[AvailabilityZoneDescription]
    computational_units: _containers.RepeatedCompositeFieldContainer[ComputationalUnitDescription]
    storage_units: _containers.RepeatedCompositeFieldContainer[StorageUnitDescription]
    def __init__(self, storage_units: _Optional[_Iterable[_Union[StorageUnitDescription, _Mapping]]] = ..., availability_zones: _Optional[_Iterable[_Union[AvailabilityZoneDescription, _Mapping]]] = ..., computational_units: _Optional[_Iterable[_Union[ComputationalUnitDescription, _Mapping]]] = ...) -> None: ...

class GetDatabaseStatusRequest(_message.Message):
    __slots__ = ["operation_params", "path"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, path: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class GetDatabaseStatusResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class GetDatabaseStatusResult(_message.Message):
    __slots__ = ["allocated_resources", "database_quotas", "generation", "path", "registered_resources", "required_resources", "required_shared_resources", "schema_operation_quotas", "serverless_resources", "state"]
    class State(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    ALLOCATED_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    CONFIGURING: GetDatabaseStatusResult.State
    CREATING: GetDatabaseStatusResult.State
    DATABASE_QUOTAS_FIELD_NUMBER: _ClassVar[int]
    GENERATION_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    PENDING_RESOURCES: GetDatabaseStatusResult.State
    REGISTERED_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    REMOVING: GetDatabaseStatusResult.State
    REQUIRED_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    REQUIRED_SHARED_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    RUNNING: GetDatabaseStatusResult.State
    SCHEMA_OPERATION_QUOTAS_FIELD_NUMBER: _ClassVar[int]
    SERVERLESS_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    STATE_UNSPECIFIED: GetDatabaseStatusResult.State
    allocated_resources: Resources
    database_quotas: DatabaseQuotas
    generation: int
    path: str
    registered_resources: _containers.RepeatedCompositeFieldContainer[AllocatedComputationalUnit]
    required_resources: Resources
    required_shared_resources: Resources
    schema_operation_quotas: SchemaOperationQuotas
    serverless_resources: ServerlessResources
    state: GetDatabaseStatusResult.State
    def __init__(self, path: _Optional[str] = ..., state: _Optional[_Union[GetDatabaseStatusResult.State, str]] = ..., required_resources: _Optional[_Union[Resources, _Mapping]] = ..., required_shared_resources: _Optional[_Union[Resources, _Mapping]] = ..., serverless_resources: _Optional[_Union[ServerlessResources, _Mapping]] = ..., allocated_resources: _Optional[_Union[Resources, _Mapping]] = ..., registered_resources: _Optional[_Iterable[_Union[AllocatedComputationalUnit, _Mapping]]] = ..., generation: _Optional[int] = ..., schema_operation_quotas: _Optional[_Union[SchemaOperationQuotas, _Mapping]] = ..., database_quotas: _Optional[_Union[DatabaseQuotas, _Mapping]] = ...) -> None: ...

class ListDatabasesRequest(_message.Message):
    __slots__ = ["operation_params"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class ListDatabasesResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListDatabasesResult(_message.Message):
    __slots__ = ["paths"]
    PATHS_FIELD_NUMBER: _ClassVar[int]
    paths: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, paths: _Optional[_Iterable[str]] = ...) -> None: ...

class RemoveDatabaseRequest(_message.Message):
    __slots__ = ["operation_params", "path"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, path: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class RemoveDatabaseResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class Resources(_message.Message):
    __slots__ = ["computational_units", "storage_units"]
    COMPUTATIONAL_UNITS_FIELD_NUMBER: _ClassVar[int]
    STORAGE_UNITS_FIELD_NUMBER: _ClassVar[int]
    computational_units: _containers.RepeatedCompositeFieldContainer[ComputationalUnits]
    storage_units: _containers.RepeatedCompositeFieldContainer[StorageUnits]
    def __init__(self, storage_units: _Optional[_Iterable[_Union[StorageUnits, _Mapping]]] = ..., computational_units: _Optional[_Iterable[_Union[ComputationalUnits, _Mapping]]] = ...) -> None: ...

class SchemaOperationQuotas(_message.Message):
    __slots__ = ["leaky_bucket_quotas"]
    class LeakyBucket(_message.Message):
        __slots__ = ["bucket_seconds", "bucket_size"]
        BUCKET_SECONDS_FIELD_NUMBER: _ClassVar[int]
        BUCKET_SIZE_FIELD_NUMBER: _ClassVar[int]
        bucket_seconds: int
        bucket_size: float
        def __init__(self, bucket_size: _Optional[float] = ..., bucket_seconds: _Optional[int] = ...) -> None: ...
    LEAKY_BUCKET_QUOTAS_FIELD_NUMBER: _ClassVar[int]
    leaky_bucket_quotas: _containers.RepeatedCompositeFieldContainer[SchemaOperationQuotas.LeakyBucket]
    def __init__(self, leaky_bucket_quotas: _Optional[_Iterable[_Union[SchemaOperationQuotas.LeakyBucket, _Mapping]]] = ...) -> None: ...

class ServerlessResources(_message.Message):
    __slots__ = ["shared_database_path"]
    SHARED_DATABASE_PATH_FIELD_NUMBER: _ClassVar[int]
    shared_database_path: str
    def __init__(self, shared_database_path: _Optional[str] = ...) -> None: ...

class StorageUnitDescription(_message.Message):
    __slots__ = ["kind", "labels"]
    class LabelsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    KIND_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    kind: str
    labels: _containers.ScalarMap[str, str]
    def __init__(self, kind: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ...) -> None: ...

class StorageUnits(_message.Message):
    __slots__ = ["count", "unit_kind"]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    UNIT_KIND_FIELD_NUMBER: _ClassVar[int]
    count: int
    unit_kind: str
    def __init__(self, unit_kind: _Optional[str] = ..., count: _Optional[int] = ...) -> None: ...
