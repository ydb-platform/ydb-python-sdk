from protos import ydb_operation_pb2 as _ydb_operation_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class StorageUnits(_message.Message):
    __slots__ = ("unit_kind", "count")
    UNIT_KIND_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    unit_kind: str
    count: int
    def __init__(self, unit_kind: _Optional[str] = ..., count: _Optional[int] = ...) -> None: ...

class ComputationalUnits(_message.Message):
    __slots__ = ("unit_kind", "availability_zone", "count")
    UNIT_KIND_FIELD_NUMBER: _ClassVar[int]
    AVAILABILITY_ZONE_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    unit_kind: str
    availability_zone: str
    count: int
    def __init__(self, unit_kind: _Optional[str] = ..., availability_zone: _Optional[str] = ..., count: _Optional[int] = ...) -> None: ...

class AllocatedComputationalUnit(_message.Message):
    __slots__ = ("host", "port", "unit_kind")
    HOST_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    UNIT_KIND_FIELD_NUMBER: _ClassVar[int]
    host: str
    port: int
    unit_kind: str
    def __init__(self, host: _Optional[str] = ..., port: _Optional[int] = ..., unit_kind: _Optional[str] = ...) -> None: ...

class Resources(_message.Message):
    __slots__ = ("storage_units", "computational_units")
    STORAGE_UNITS_FIELD_NUMBER: _ClassVar[int]
    COMPUTATIONAL_UNITS_FIELD_NUMBER: _ClassVar[int]
    storage_units: _containers.RepeatedCompositeFieldContainer[StorageUnits]
    computational_units: _containers.RepeatedCompositeFieldContainer[ComputationalUnits]
    def __init__(self, storage_units: _Optional[_Iterable[_Union[StorageUnits, _Mapping]]] = ..., computational_units: _Optional[_Iterable[_Union[ComputationalUnits, _Mapping]]] = ...) -> None: ...

class ServerlessResources(_message.Message):
    __slots__ = ("shared_database_path",)
    SHARED_DATABASE_PATH_FIELD_NUMBER: _ClassVar[int]
    shared_database_path: str
    def __init__(self, shared_database_path: _Optional[str] = ...) -> None: ...

class DatabaseOptions(_message.Message):
    __slots__ = ("disable_tx_service", "disable_external_subdomain", "plan_resolution")
    DISABLE_TX_SERVICE_FIELD_NUMBER: _ClassVar[int]
    DISABLE_EXTERNAL_SUBDOMAIN_FIELD_NUMBER: _ClassVar[int]
    PLAN_RESOLUTION_FIELD_NUMBER: _ClassVar[int]
    disable_tx_service: bool
    disable_external_subdomain: bool
    plan_resolution: int
    def __init__(self, disable_tx_service: bool = ..., disable_external_subdomain: bool = ..., plan_resolution: _Optional[int] = ...) -> None: ...

class SchemaOperationQuotas(_message.Message):
    __slots__ = ("leaky_bucket_quotas",)
    class LeakyBucket(_message.Message):
        __slots__ = ("bucket_size", "bucket_seconds")
        BUCKET_SIZE_FIELD_NUMBER: _ClassVar[int]
        BUCKET_SECONDS_FIELD_NUMBER: _ClassVar[int]
        bucket_size: float
        bucket_seconds: int
        def __init__(self, bucket_size: _Optional[float] = ..., bucket_seconds: _Optional[int] = ...) -> None: ...
    LEAKY_BUCKET_QUOTAS_FIELD_NUMBER: _ClassVar[int]
    leaky_bucket_quotas: _containers.RepeatedCompositeFieldContainer[SchemaOperationQuotas.LeakyBucket]
    def __init__(self, leaky_bucket_quotas: _Optional[_Iterable[_Union[SchemaOperationQuotas.LeakyBucket, _Mapping]]] = ...) -> None: ...

class DatabaseQuotas(_message.Message):
    __slots__ = ("data_size_hard_quota", "data_size_soft_quota", "data_stream_shards_quota", "data_stream_reserved_storage_quota", "ttl_min_run_internal_seconds")
    DATA_SIZE_HARD_QUOTA_FIELD_NUMBER: _ClassVar[int]
    DATA_SIZE_SOFT_QUOTA_FIELD_NUMBER: _ClassVar[int]
    DATA_STREAM_SHARDS_QUOTA_FIELD_NUMBER: _ClassVar[int]
    DATA_STREAM_RESERVED_STORAGE_QUOTA_FIELD_NUMBER: _ClassVar[int]
    TTL_MIN_RUN_INTERNAL_SECONDS_FIELD_NUMBER: _ClassVar[int]
    data_size_hard_quota: int
    data_size_soft_quota: int
    data_stream_shards_quota: int
    data_stream_reserved_storage_quota: int
    ttl_min_run_internal_seconds: int
    def __init__(self, data_size_hard_quota: _Optional[int] = ..., data_size_soft_quota: _Optional[int] = ..., data_stream_shards_quota: _Optional[int] = ..., data_stream_reserved_storage_quota: _Optional[int] = ..., ttl_min_run_internal_seconds: _Optional[int] = ...) -> None: ...

class CreateDatabaseRequest(_message.Message):
    __slots__ = ("operation_params", "path", "resources", "shared_resources", "serverless_resources", "options", "attributes", "schema_operation_quotas", "idempotency_key", "database_quotas")
    class AttributesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    RESOURCES_FIELD_NUMBER: _ClassVar[int]
    SHARED_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    SERVERLESS_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_OPERATION_QUOTAS_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    DATABASE_QUOTAS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    resources: Resources
    shared_resources: Resources
    serverless_resources: ServerlessResources
    options: DatabaseOptions
    attributes: _containers.ScalarMap[str, str]
    schema_operation_quotas: SchemaOperationQuotas
    idempotency_key: str
    database_quotas: DatabaseQuotas
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., resources: _Optional[_Union[Resources, _Mapping]] = ..., shared_resources: _Optional[_Union[Resources, _Mapping]] = ..., serverless_resources: _Optional[_Union[ServerlessResources, _Mapping]] = ..., options: _Optional[_Union[DatabaseOptions, _Mapping]] = ..., attributes: _Optional[_Mapping[str, str]] = ..., schema_operation_quotas: _Optional[_Union[SchemaOperationQuotas, _Mapping]] = ..., idempotency_key: _Optional[str] = ..., database_quotas: _Optional[_Union[DatabaseQuotas, _Mapping]] = ...) -> None: ...

class CreateDatabaseResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class GetDatabaseStatusRequest(_message.Message):
    __slots__ = ("path", "operation_params")
    PATH_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    path: str
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, path: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class GetDatabaseStatusResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class GetDatabaseStatusResult(_message.Message):
    __slots__ = ("path", "state", "required_resources", "required_shared_resources", "serverless_resources", "allocated_resources", "registered_resources", "generation", "schema_operation_quotas", "database_quotas")
    class State(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        STATE_UNSPECIFIED: _ClassVar[GetDatabaseStatusResult.State]
        CREATING: _ClassVar[GetDatabaseStatusResult.State]
        RUNNING: _ClassVar[GetDatabaseStatusResult.State]
        REMOVING: _ClassVar[GetDatabaseStatusResult.State]
        PENDING_RESOURCES: _ClassVar[GetDatabaseStatusResult.State]
        CONFIGURING: _ClassVar[GetDatabaseStatusResult.State]
    STATE_UNSPECIFIED: GetDatabaseStatusResult.State
    CREATING: GetDatabaseStatusResult.State
    RUNNING: GetDatabaseStatusResult.State
    REMOVING: GetDatabaseStatusResult.State
    PENDING_RESOURCES: GetDatabaseStatusResult.State
    CONFIGURING: GetDatabaseStatusResult.State
    PATH_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    REQUIRED_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    REQUIRED_SHARED_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    SERVERLESS_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    ALLOCATED_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    REGISTERED_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    GENERATION_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_OPERATION_QUOTAS_FIELD_NUMBER: _ClassVar[int]
    DATABASE_QUOTAS_FIELD_NUMBER: _ClassVar[int]
    path: str
    state: GetDatabaseStatusResult.State
    required_resources: Resources
    required_shared_resources: Resources
    serverless_resources: ServerlessResources
    allocated_resources: Resources
    registered_resources: _containers.RepeatedCompositeFieldContainer[AllocatedComputationalUnit]
    generation: int
    schema_operation_quotas: SchemaOperationQuotas
    database_quotas: DatabaseQuotas
    def __init__(self, path: _Optional[str] = ..., state: _Optional[_Union[GetDatabaseStatusResult.State, str]] = ..., required_resources: _Optional[_Union[Resources, _Mapping]] = ..., required_shared_resources: _Optional[_Union[Resources, _Mapping]] = ..., serverless_resources: _Optional[_Union[ServerlessResources, _Mapping]] = ..., allocated_resources: _Optional[_Union[Resources, _Mapping]] = ..., registered_resources: _Optional[_Iterable[_Union[AllocatedComputationalUnit, _Mapping]]] = ..., generation: _Optional[int] = ..., schema_operation_quotas: _Optional[_Union[SchemaOperationQuotas, _Mapping]] = ..., database_quotas: _Optional[_Union[DatabaseQuotas, _Mapping]] = ...) -> None: ...

class AlterDatabaseRequest(_message.Message):
    __slots__ = ("path", "computational_units_to_add", "computational_units_to_remove", "storage_units_to_add", "computational_units_to_register", "computational_units_to_deregister", "operation_params", "generation", "schema_operation_quotas", "idempotency_key", "database_quotas", "alter_attributes")
    class AlterAttributesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    PATH_FIELD_NUMBER: _ClassVar[int]
    COMPUTATIONAL_UNITS_TO_ADD_FIELD_NUMBER: _ClassVar[int]
    COMPUTATIONAL_UNITS_TO_REMOVE_FIELD_NUMBER: _ClassVar[int]
    STORAGE_UNITS_TO_ADD_FIELD_NUMBER: _ClassVar[int]
    COMPUTATIONAL_UNITS_TO_REGISTER_FIELD_NUMBER: _ClassVar[int]
    COMPUTATIONAL_UNITS_TO_DEREGISTER_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    GENERATION_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_OPERATION_QUOTAS_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    DATABASE_QUOTAS_FIELD_NUMBER: _ClassVar[int]
    ALTER_ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    path: str
    computational_units_to_add: _containers.RepeatedCompositeFieldContainer[ComputationalUnits]
    computational_units_to_remove: _containers.RepeatedCompositeFieldContainer[ComputationalUnits]
    storage_units_to_add: _containers.RepeatedCompositeFieldContainer[StorageUnits]
    computational_units_to_register: _containers.RepeatedCompositeFieldContainer[AllocatedComputationalUnit]
    computational_units_to_deregister: _containers.RepeatedCompositeFieldContainer[AllocatedComputationalUnit]
    operation_params: _ydb_operation_pb2.OperationParams
    generation: int
    schema_operation_quotas: SchemaOperationQuotas
    idempotency_key: str
    database_quotas: DatabaseQuotas
    alter_attributes: _containers.ScalarMap[str, str]
    def __init__(self, path: _Optional[str] = ..., computational_units_to_add: _Optional[_Iterable[_Union[ComputationalUnits, _Mapping]]] = ..., computational_units_to_remove: _Optional[_Iterable[_Union[ComputationalUnits, _Mapping]]] = ..., storage_units_to_add: _Optional[_Iterable[_Union[StorageUnits, _Mapping]]] = ..., computational_units_to_register: _Optional[_Iterable[_Union[AllocatedComputationalUnit, _Mapping]]] = ..., computational_units_to_deregister: _Optional[_Iterable[_Union[AllocatedComputationalUnit, _Mapping]]] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., generation: _Optional[int] = ..., schema_operation_quotas: _Optional[_Union[SchemaOperationQuotas, _Mapping]] = ..., idempotency_key: _Optional[str] = ..., database_quotas: _Optional[_Union[DatabaseQuotas, _Mapping]] = ..., alter_attributes: _Optional[_Mapping[str, str]] = ...) -> None: ...

class AlterDatabaseResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListDatabasesRequest(_message.Message):
    __slots__ = ("operation_params",)
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class ListDatabasesResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListDatabasesResult(_message.Message):
    __slots__ = ("paths",)
    PATHS_FIELD_NUMBER: _ClassVar[int]
    paths: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, paths: _Optional[_Iterable[str]] = ...) -> None: ...

class RemoveDatabaseRequest(_message.Message):
    __slots__ = ("path", "operation_params")
    PATH_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    path: str
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, path: _Optional[str] = ..., operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class RemoveDatabaseResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class StorageUnitDescription(_message.Message):
    __slots__ = ("kind", "labels")
    class LabelsEntry(_message.Message):
        __slots__ = ("key", "value")
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

class AvailabilityZoneDescription(_message.Message):
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

class ComputationalUnitDescription(_message.Message):
    __slots__ = ("kind", "labels", "allowed_availability_zones")
    class LabelsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    KIND_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    ALLOWED_AVAILABILITY_ZONES_FIELD_NUMBER: _ClassVar[int]
    kind: str
    labels: _containers.ScalarMap[str, str]
    allowed_availability_zones: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, kind: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ..., allowed_availability_zones: _Optional[_Iterable[str]] = ...) -> None: ...

class DescribeDatabaseOptionsRequest(_message.Message):
    __slots__ = ("operation_params",)
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class DescribeDatabaseOptionsResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeDatabaseOptionsResult(_message.Message):
    __slots__ = ("storage_units", "availability_zones", "computational_units")
    STORAGE_UNITS_FIELD_NUMBER: _ClassVar[int]
    AVAILABILITY_ZONES_FIELD_NUMBER: _ClassVar[int]
    COMPUTATIONAL_UNITS_FIELD_NUMBER: _ClassVar[int]
    storage_units: _containers.RepeatedCompositeFieldContainer[StorageUnitDescription]
    availability_zones: _containers.RepeatedCompositeFieldContainer[AvailabilityZoneDescription]
    computational_units: _containers.RepeatedCompositeFieldContainer[ComputationalUnitDescription]
    def __init__(self, storage_units: _Optional[_Iterable[_Union[StorageUnitDescription, _Mapping]]] = ..., availability_zones: _Optional[_Iterable[_Union[AvailabilityZoneDescription, _Mapping]]] = ..., computational_units: _Optional[_Iterable[_Union[ComputationalUnitDescription, _Mapping]]] = ...) -> None: ...
