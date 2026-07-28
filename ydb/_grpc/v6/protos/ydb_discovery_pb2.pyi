from protos import ydb_bridge_common_pb2 as _ydb_bridge_common_pb2
from protos import ydb_operation_pb2 as _ydb_operation_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ListEndpointsRequest(_message.Message):
    __slots__ = ("database", "service")
    DATABASE_FIELD_NUMBER: _ClassVar[int]
    SERVICE_FIELD_NUMBER: _ClassVar[int]
    database: str
    service: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, database: _Optional[str] = ..., service: _Optional[_Iterable[str]] = ...) -> None: ...

class EndpointInfo(_message.Message):
    __slots__ = ("address", "port", "load_factor", "ssl", "service", "location", "node_id", "ip_v4", "ip_v6", "ssl_target_name_override", "bridge_pile_name")
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    LOAD_FACTOR_FIELD_NUMBER: _ClassVar[int]
    SSL_FIELD_NUMBER: _ClassVar[int]
    SERVICE_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    IP_V4_FIELD_NUMBER: _ClassVar[int]
    IP_V6_FIELD_NUMBER: _ClassVar[int]
    SSL_TARGET_NAME_OVERRIDE_FIELD_NUMBER: _ClassVar[int]
    BRIDGE_PILE_NAME_FIELD_NUMBER: _ClassVar[int]
    address: str
    port: int
    load_factor: float
    ssl: bool
    service: _containers.RepeatedScalarFieldContainer[str]
    location: str
    node_id: int
    ip_v4: _containers.RepeatedScalarFieldContainer[str]
    ip_v6: _containers.RepeatedScalarFieldContainer[str]
    ssl_target_name_override: str
    bridge_pile_name: str
    def __init__(self, address: _Optional[str] = ..., port: _Optional[int] = ..., load_factor: _Optional[float] = ..., ssl: bool = ..., service: _Optional[_Iterable[str]] = ..., location: _Optional[str] = ..., node_id: _Optional[int] = ..., ip_v4: _Optional[_Iterable[str]] = ..., ip_v6: _Optional[_Iterable[str]] = ..., ssl_target_name_override: _Optional[str] = ..., bridge_pile_name: _Optional[str] = ...) -> None: ...

class ListEndpointsResult(_message.Message):
    __slots__ = ("endpoints", "self_location", "pile_states")
    ENDPOINTS_FIELD_NUMBER: _ClassVar[int]
    SELF_LOCATION_FIELD_NUMBER: _ClassVar[int]
    PILE_STATES_FIELD_NUMBER: _ClassVar[int]
    endpoints: _containers.RepeatedCompositeFieldContainer[EndpointInfo]
    self_location: str
    pile_states: _containers.RepeatedCompositeFieldContainer[_ydb_bridge_common_pb2.PileState]
    def __init__(self, endpoints: _Optional[_Iterable[_Union[EndpointInfo, _Mapping]]] = ..., self_location: _Optional[str] = ..., pile_states: _Optional[_Iterable[_Union[_ydb_bridge_common_pb2.PileState, _Mapping]]] = ...) -> None: ...

class ListEndpointsResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class WhoAmIRequest(_message.Message):
    __slots__ = ("include_groups",)
    INCLUDE_GROUPS_FIELD_NUMBER: _ClassVar[int]
    include_groups: bool
    def __init__(self, include_groups: bool = ...) -> None: ...

class WhoAmIResult(_message.Message):
    __slots__ = ("user", "groups", "is_administration_allowed", "is_monitoring_allowed", "is_viewer_allowed", "is_database_allowed", "is_register_node_allowed", "is_bootstrap_allowed")
    USER_FIELD_NUMBER: _ClassVar[int]
    GROUPS_FIELD_NUMBER: _ClassVar[int]
    IS_ADMINISTRATION_ALLOWED_FIELD_NUMBER: _ClassVar[int]
    IS_MONITORING_ALLOWED_FIELD_NUMBER: _ClassVar[int]
    IS_VIEWER_ALLOWED_FIELD_NUMBER: _ClassVar[int]
    IS_DATABASE_ALLOWED_FIELD_NUMBER: _ClassVar[int]
    IS_REGISTER_NODE_ALLOWED_FIELD_NUMBER: _ClassVar[int]
    IS_BOOTSTRAP_ALLOWED_FIELD_NUMBER: _ClassVar[int]
    user: str
    groups: _containers.RepeatedScalarFieldContainer[str]
    is_administration_allowed: bool
    is_monitoring_allowed: bool
    is_viewer_allowed: bool
    is_database_allowed: bool
    is_register_node_allowed: bool
    is_bootstrap_allowed: bool
    def __init__(self, user: _Optional[str] = ..., groups: _Optional[_Iterable[str]] = ..., is_administration_allowed: bool = ..., is_monitoring_allowed: bool = ..., is_viewer_allowed: bool = ..., is_database_allowed: bool = ..., is_register_node_allowed: bool = ..., is_bootstrap_allowed: bool = ...) -> None: ...

class WhoAmIResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class NodeLocation(_message.Message):
    __slots__ = ("data_center_num", "room_num", "rack_num", "body_num", "body", "bridge_pile_name", "data_center", "module", "rack", "unit")
    DATA_CENTER_NUM_FIELD_NUMBER: _ClassVar[int]
    ROOM_NUM_FIELD_NUMBER: _ClassVar[int]
    RACK_NUM_FIELD_NUMBER: _ClassVar[int]
    BODY_NUM_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    BRIDGE_PILE_NAME_FIELD_NUMBER: _ClassVar[int]
    DATA_CENTER_FIELD_NUMBER: _ClassVar[int]
    MODULE_FIELD_NUMBER: _ClassVar[int]
    RACK_FIELD_NUMBER: _ClassVar[int]
    UNIT_FIELD_NUMBER: _ClassVar[int]
    data_center_num: int
    room_num: int
    rack_num: int
    body_num: int
    body: int
    bridge_pile_name: str
    data_center: str
    module: str
    rack: str
    unit: str
    def __init__(self, data_center_num: _Optional[int] = ..., room_num: _Optional[int] = ..., rack_num: _Optional[int] = ..., body_num: _Optional[int] = ..., body: _Optional[int] = ..., bridge_pile_name: _Optional[str] = ..., data_center: _Optional[str] = ..., module: _Optional[str] = ..., rack: _Optional[str] = ..., unit: _Optional[str] = ...) -> None: ...

class NodeInfo(_message.Message):
    __slots__ = ("node_id", "host", "port", "resolve_host", "address", "location", "expire")
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    HOST_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    RESOLVE_HOST_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    EXPIRE_FIELD_NUMBER: _ClassVar[int]
    node_id: int
    host: str
    port: int
    resolve_host: str
    address: str
    location: NodeLocation
    expire: int
    def __init__(self, node_id: _Optional[int] = ..., host: _Optional[str] = ..., port: _Optional[int] = ..., resolve_host: _Optional[str] = ..., address: _Optional[str] = ..., location: _Optional[_Union[NodeLocation, _Mapping]] = ..., expire: _Optional[int] = ...) -> None: ...

class NodeRegistrationRequest(_message.Message):
    __slots__ = ("host", "port", "resolve_host", "address", "location", "domain_path", "fixed_node_id", "path")
    HOST_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    RESOLVE_HOST_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    DOMAIN_PATH_FIELD_NUMBER: _ClassVar[int]
    FIXED_NODE_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    host: str
    port: int
    resolve_host: str
    address: str
    location: NodeLocation
    domain_path: str
    fixed_node_id: bool
    path: str
    def __init__(self, host: _Optional[str] = ..., port: _Optional[int] = ..., resolve_host: _Optional[str] = ..., address: _Optional[str] = ..., location: _Optional[_Union[NodeLocation, _Mapping]] = ..., domain_path: _Optional[str] = ..., fixed_node_id: bool = ..., path: _Optional[str] = ...) -> None: ...

class NodeRegistrationResult(_message.Message):
    __slots__ = ("node_id", "domain_path", "expire", "nodes", "scope_tablet_id", "scope_path_id", "node_name")
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    DOMAIN_PATH_FIELD_NUMBER: _ClassVar[int]
    EXPIRE_FIELD_NUMBER: _ClassVar[int]
    NODES_FIELD_NUMBER: _ClassVar[int]
    SCOPE_TABLET_ID_FIELD_NUMBER: _ClassVar[int]
    SCOPE_PATH_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_NAME_FIELD_NUMBER: _ClassVar[int]
    node_id: int
    domain_path: str
    expire: int
    nodes: _containers.RepeatedCompositeFieldContainer[NodeInfo]
    scope_tablet_id: int
    scope_path_id: int
    node_name: str
    def __init__(self, node_id: _Optional[int] = ..., domain_path: _Optional[str] = ..., expire: _Optional[int] = ..., nodes: _Optional[_Iterable[_Union[NodeInfo, _Mapping]]] = ..., scope_tablet_id: _Optional[int] = ..., scope_path_id: _Optional[int] = ..., node_name: _Optional[str] = ...) -> None: ...

class NodeRegistrationResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...
