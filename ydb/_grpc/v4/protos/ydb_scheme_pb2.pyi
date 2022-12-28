from protos import ydb_common_pb2 as _ydb_common_pb2
from protos import ydb_operation_pb2 as _ydb_operation_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DescribePathRequest(_message.Message):
    __slots__ = ["operation_params", "path"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ...) -> None: ...

class DescribePathResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribePathResult(_message.Message):
    __slots__ = ["self"]
    SELF_FIELD_NUMBER: _ClassVar[int]
    self: Entry
    def __init__(self, self_: _Optional[_Union[Entry, _Mapping]] = ...) -> None: ...

class Entry(_message.Message):
    __slots__ = ["created_at", "effective_permissions", "name", "owner", "permissions", "size_bytes", "type"]
    class Type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    BLOCK_STORE_VOLUME: Entry.Type
    COLUMN_STORE: Entry.Type
    COLUMN_TABLE: Entry.Type
    COORDINATION_NODE: Entry.Type
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    DATABASE: Entry.Type
    DIRECTORY: Entry.Type
    EFFECTIVE_PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    OWNER_FIELD_NUMBER: _ClassVar[int]
    PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    PERS_QUEUE_GROUP: Entry.Type
    REPLICATION: Entry.Type
    RTMR_VOLUME: Entry.Type
    SEQUENCE: Entry.Type
    SIZE_BYTES_FIELD_NUMBER: _ClassVar[int]
    TABLE: Entry.Type
    TOPIC: Entry.Type
    TYPE_FIELD_NUMBER: _ClassVar[int]
    TYPE_UNSPECIFIED: Entry.Type
    created_at: _ydb_common_pb2.VirtualTimestamp
    effective_permissions: _containers.RepeatedCompositeFieldContainer[Permissions]
    name: str
    owner: str
    permissions: _containers.RepeatedCompositeFieldContainer[Permissions]
    size_bytes: int
    type: Entry.Type
    def __init__(self, name: _Optional[str] = ..., owner: _Optional[str] = ..., type: _Optional[_Union[Entry.Type, str]] = ..., effective_permissions: _Optional[_Iterable[_Union[Permissions, _Mapping]]] = ..., permissions: _Optional[_Iterable[_Union[Permissions, _Mapping]]] = ..., size_bytes: _Optional[int] = ..., created_at: _Optional[_Union[_ydb_common_pb2.VirtualTimestamp, _Mapping]] = ...) -> None: ...

class ListDirectoryRequest(_message.Message):
    __slots__ = ["operation_params", "path"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ...) -> None: ...

class ListDirectoryResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListDirectoryResult(_message.Message):
    __slots__ = ["children", "self"]
    CHILDREN_FIELD_NUMBER: _ClassVar[int]
    SELF_FIELD_NUMBER: _ClassVar[int]
    children: _containers.RepeatedCompositeFieldContainer[Entry]
    self: Entry
    def __init__(self, self_: _Optional[_Union[Entry, _Mapping]] = ..., children: _Optional[_Iterable[_Union[Entry, _Mapping]]] = ...) -> None: ...

class MakeDirectoryRequest(_message.Message):
    __slots__ = ["operation_params", "path"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ...) -> None: ...

class MakeDirectoryResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ModifyPermissionsRequest(_message.Message):
    __slots__ = ["actions", "clear_permissions", "interrupt_inheritance", "operation_params", "path"]
    ACTIONS_FIELD_NUMBER: _ClassVar[int]
    CLEAR_PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    INTERRUPT_INHERITANCE_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    actions: _containers.RepeatedCompositeFieldContainer[PermissionsAction]
    clear_permissions: bool
    interrupt_inheritance: bool
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., actions: _Optional[_Iterable[_Union[PermissionsAction, _Mapping]]] = ..., clear_permissions: bool = ..., interrupt_inheritance: bool = ...) -> None: ...

class ModifyPermissionsResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class Permissions(_message.Message):
    __slots__ = ["permission_names", "subject"]
    PERMISSION_NAMES_FIELD_NUMBER: _ClassVar[int]
    SUBJECT_FIELD_NUMBER: _ClassVar[int]
    permission_names: _containers.RepeatedScalarFieldContainer[str]
    subject: str
    def __init__(self, subject: _Optional[str] = ..., permission_names: _Optional[_Iterable[str]] = ...) -> None: ...

class PermissionsAction(_message.Message):
    __slots__ = ["change_owner", "grant", "revoke", "set"]
    CHANGE_OWNER_FIELD_NUMBER: _ClassVar[int]
    GRANT_FIELD_NUMBER: _ClassVar[int]
    REVOKE_FIELD_NUMBER: _ClassVar[int]
    SET_FIELD_NUMBER: _ClassVar[int]
    change_owner: str
    grant: Permissions
    revoke: Permissions
    set: Permissions
    def __init__(self, grant: _Optional[_Union[Permissions, _Mapping]] = ..., revoke: _Optional[_Union[Permissions, _Mapping]] = ..., set: _Optional[_Union[Permissions, _Mapping]] = ..., change_owner: _Optional[str] = ...) -> None: ...

class RemoveDirectoryRequest(_message.Message):
    __slots__ = ["operation_params", "path"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ...) -> None: ...

class RemoveDirectoryResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...
