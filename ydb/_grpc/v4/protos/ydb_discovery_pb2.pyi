from protos import ydb_operation_pb2 as _ydb_operation_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EndpointInfo(_message.Message):
    __slots__ = ["address", "ip_v4", "ip_v6", "load_factor", "location", "node_id", "port", "service", "ssl", "ssl_target_name_override"]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    IP_V4_FIELD_NUMBER: _ClassVar[int]
    IP_V6_FIELD_NUMBER: _ClassVar[int]
    LOAD_FACTOR_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    SERVICE_FIELD_NUMBER: _ClassVar[int]
    SSL_FIELD_NUMBER: _ClassVar[int]
    SSL_TARGET_NAME_OVERRIDE_FIELD_NUMBER: _ClassVar[int]
    address: str
    ip_v4: _containers.RepeatedScalarFieldContainer[str]
    ip_v6: _containers.RepeatedScalarFieldContainer[str]
    load_factor: float
    location: str
    node_id: int
    port: int
    service: _containers.RepeatedScalarFieldContainer[str]
    ssl: bool
    ssl_target_name_override: str
    def __init__(self, address: _Optional[str] = ..., port: _Optional[int] = ..., load_factor: _Optional[float] = ..., ssl: bool = ..., service: _Optional[_Iterable[str]] = ..., location: _Optional[str] = ..., node_id: _Optional[int] = ..., ip_v4: _Optional[_Iterable[str]] = ..., ip_v6: _Optional[_Iterable[str]] = ..., ssl_target_name_override: _Optional[str] = ...) -> None: ...

class ListEndpointsRequest(_message.Message):
    __slots__ = ["database", "service"]
    DATABASE_FIELD_NUMBER: _ClassVar[int]
    SERVICE_FIELD_NUMBER: _ClassVar[int]
    database: str
    service: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, database: _Optional[str] = ..., service: _Optional[_Iterable[str]] = ...) -> None: ...

class ListEndpointsResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListEndpointsResult(_message.Message):
    __slots__ = ["endpoints", "self_location"]
    ENDPOINTS_FIELD_NUMBER: _ClassVar[int]
    SELF_LOCATION_FIELD_NUMBER: _ClassVar[int]
    endpoints: _containers.RepeatedCompositeFieldContainer[EndpointInfo]
    self_location: str
    def __init__(self, endpoints: _Optional[_Iterable[_Union[EndpointInfo, _Mapping]]] = ..., self_location: _Optional[str] = ...) -> None: ...

class WhoAmIRequest(_message.Message):
    __slots__ = ["include_groups"]
    INCLUDE_GROUPS_FIELD_NUMBER: _ClassVar[int]
    include_groups: bool
    def __init__(self, include_groups: bool = ...) -> None: ...

class WhoAmIResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class WhoAmIResult(_message.Message):
    __slots__ = ["groups", "user"]
    GROUPS_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    groups: _containers.RepeatedScalarFieldContainer[str]
    user: str
    def __init__(self, user: _Optional[str] = ..., groups: _Optional[_Iterable[str]] = ...) -> None: ...
