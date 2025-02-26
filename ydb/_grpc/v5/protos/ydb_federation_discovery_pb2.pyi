from protos import ydb_operation_pb2 as _ydb_operation_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DatabaseInfo(_message.Message):
    __slots__ = ["endpoint", "id", "location", "name", "path", "status", "weight"]
    class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    AVAILABLE: DatabaseInfo.Status
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    READ_ONLY: DatabaseInfo.Status
    STATUS_FIELD_NUMBER: _ClassVar[int]
    STATUS_UNSPECIFIED: DatabaseInfo.Status
    UNAVAILABLE: DatabaseInfo.Status
    WEIGHT_FIELD_NUMBER: _ClassVar[int]
    endpoint: str
    id: str
    location: str
    name: str
    path: str
    status: DatabaseInfo.Status
    weight: int
    def __init__(self, name: _Optional[str] = ..., path: _Optional[str] = ..., id: _Optional[str] = ..., endpoint: _Optional[str] = ..., location: _Optional[str] = ..., status: _Optional[_Union[DatabaseInfo.Status, str]] = ..., weight: _Optional[int] = ...) -> None: ...

class ListFederationDatabasesRequest(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class ListFederationDatabasesResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListFederationDatabasesResult(_message.Message):
    __slots__ = ["control_plane_endpoint", "federation_databases", "self_location"]
    CONTROL_PLANE_ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    FEDERATION_DATABASES_FIELD_NUMBER: _ClassVar[int]
    SELF_LOCATION_FIELD_NUMBER: _ClassVar[int]
    control_plane_endpoint: str
    federation_databases: _containers.RepeatedCompositeFieldContainer[DatabaseInfo]
    self_location: str
    def __init__(self, control_plane_endpoint: _Optional[str] = ..., federation_databases: _Optional[_Iterable[_Union[DatabaseInfo, _Mapping]]] = ..., self_location: _Optional[str] = ...) -> None: ...
