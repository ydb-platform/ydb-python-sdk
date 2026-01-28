from protos import ydb_common_pb2 as _ydb_common_pb2
from protos import ydb_operation_pb2 as _ydb_operation_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class MakeDirectoryRequest(_message.Message):
    __slots__ = ("operation_params", "path")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ...) -> None: ...

class MakeDirectoryResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class RemoveDirectoryRequest(_message.Message):
    __slots__ = ("operation_params", "path")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ...) -> None: ...

class RemoveDirectoryResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListDirectoryRequest(_message.Message):
    __slots__ = ("operation_params", "path")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ...) -> None: ...

class ListDirectoryResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class Permissions(_message.Message):
    __slots__ = ("subject", "permission_names")
    SUBJECT_FIELD_NUMBER: _ClassVar[int]
    PERMISSION_NAMES_FIELD_NUMBER: _ClassVar[int]
    subject: str
    permission_names: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, subject: _Optional[str] = ..., permission_names: _Optional[_Iterable[str]] = ...) -> None: ...

class Entry(_message.Message):
    __slots__ = ("name", "owner", "type", "effective_permissions", "permissions", "size_bytes", "created_at")
    class Type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        TYPE_UNSPECIFIED: _ClassVar[Entry.Type]
        DIRECTORY: _ClassVar[Entry.Type]
        TABLE: _ClassVar[Entry.Type]
        PERS_QUEUE_GROUP: _ClassVar[Entry.Type]
        DATABASE: _ClassVar[Entry.Type]
        RTMR_VOLUME: _ClassVar[Entry.Type]
        BLOCK_STORE_VOLUME: _ClassVar[Entry.Type]
        COORDINATION_NODE: _ClassVar[Entry.Type]
        COLUMN_STORE: _ClassVar[Entry.Type]
        COLUMN_TABLE: _ClassVar[Entry.Type]
        SEQUENCE: _ClassVar[Entry.Type]
        REPLICATION: _ClassVar[Entry.Type]
        TOPIC: _ClassVar[Entry.Type]
        EXTERNAL_TABLE: _ClassVar[Entry.Type]
        EXTERNAL_DATA_SOURCE: _ClassVar[Entry.Type]
        VIEW: _ClassVar[Entry.Type]
        RESOURCE_POOL: _ClassVar[Entry.Type]
        TRANSFER: _ClassVar[Entry.Type]
        SYS_VIEW: _ClassVar[Entry.Type]
    TYPE_UNSPECIFIED: Entry.Type
    DIRECTORY: Entry.Type
    TABLE: Entry.Type
    PERS_QUEUE_GROUP: Entry.Type
    DATABASE: Entry.Type
    RTMR_VOLUME: Entry.Type
    BLOCK_STORE_VOLUME: Entry.Type
    COORDINATION_NODE: Entry.Type
    COLUMN_STORE: Entry.Type
    COLUMN_TABLE: Entry.Type
    SEQUENCE: Entry.Type
    REPLICATION: Entry.Type
    TOPIC: Entry.Type
    EXTERNAL_TABLE: Entry.Type
    EXTERNAL_DATA_SOURCE: Entry.Type
    VIEW: Entry.Type
    RESOURCE_POOL: Entry.Type
    TRANSFER: Entry.Type
    SYS_VIEW: Entry.Type
    NAME_FIELD_NUMBER: _ClassVar[int]
    OWNER_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    EFFECTIVE_PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    SIZE_BYTES_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    name: str
    owner: str
    type: Entry.Type
    effective_permissions: _containers.RepeatedCompositeFieldContainer[Permissions]
    permissions: _containers.RepeatedCompositeFieldContainer[Permissions]
    size_bytes: int
    created_at: _ydb_common_pb2.VirtualTimestamp
    def __init__(self, name: _Optional[str] = ..., owner: _Optional[str] = ..., type: _Optional[_Union[Entry.Type, str]] = ..., effective_permissions: _Optional[_Iterable[_Union[Permissions, _Mapping]]] = ..., permissions: _Optional[_Iterable[_Union[Permissions, _Mapping]]] = ..., size_bytes: _Optional[int] = ..., created_at: _Optional[_Union[_ydb_common_pb2.VirtualTimestamp, _Mapping]] = ...) -> None: ...

class ListDirectoryResult(_message.Message):
    __slots__ = ("self", "children")
    SELF_FIELD_NUMBER: _ClassVar[int]
    CHILDREN_FIELD_NUMBER: _ClassVar[int]
    self: Entry
    children: _containers.RepeatedCompositeFieldContainer[Entry]
    def __init__(self_, self: _Optional[_Union[Entry, _Mapping]] = ..., children: _Optional[_Iterable[_Union[Entry, _Mapping]]] = ...) -> None: ...

class DescribePathRequest(_message.Message):
    __slots__ = ("operation_params", "path")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ...) -> None: ...

class DescribePathResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribePathResult(_message.Message):
    __slots__ = ("self",)
    SELF_FIELD_NUMBER: _ClassVar[int]
    self: Entry
    def __init__(self_, self: _Optional[_Union[Entry, _Mapping]] = ...) -> None: ...

class PermissionsAction(_message.Message):
    __slots__ = ("grant", "revoke", "set", "change_owner")
    GRANT_FIELD_NUMBER: _ClassVar[int]
    REVOKE_FIELD_NUMBER: _ClassVar[int]
    SET_FIELD_NUMBER: _ClassVar[int]
    CHANGE_OWNER_FIELD_NUMBER: _ClassVar[int]
    grant: Permissions
    revoke: Permissions
    set: Permissions
    change_owner: str
    def __init__(self, grant: _Optional[_Union[Permissions, _Mapping]] = ..., revoke: _Optional[_Union[Permissions, _Mapping]] = ..., set: _Optional[_Union[Permissions, _Mapping]] = ..., change_owner: _Optional[str] = ...) -> None: ...

class ModifyPermissionsRequest(_message.Message):
    __slots__ = ("operation_params", "path", "actions", "clear_permissions", "interrupt_inheritance")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    ACTIONS_FIELD_NUMBER: _ClassVar[int]
    CLEAR_PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    INTERRUPT_INHERITANCE_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    actions: _containers.RepeatedCompositeFieldContainer[PermissionsAction]
    clear_permissions: bool
    interrupt_inheritance: bool
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., actions: _Optional[_Iterable[_Union[PermissionsAction, _Mapping]]] = ..., clear_permissions: bool = ..., interrupt_inheritance: bool = ...) -> None: ...

class ModifyPermissionsResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...
