from google.protobuf import descriptor_pb2 as _descriptor_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor
REQUIRED_FIELD_NUMBER: _ClassVar[int]
required: _descriptor.FieldDescriptor
SIZE_FIELD_NUMBER: _ClassVar[int]
size: _descriptor.FieldDescriptor
LENGTH_FIELD_NUMBER: _ClassVar[int]
length: _descriptor.FieldDescriptor
MAP_KEY_FIELD_NUMBER: _ClassVar[int]
map_key: _descriptor.FieldDescriptor
VALUE_FIELD_NUMBER: _ClassVar[int]
value: _descriptor.FieldDescriptor

class Limit(_message.Message):
    __slots__ = ("range", "lt", "le", "eq", "ge", "gt")
    class Range(_message.Message):
        __slots__ = ("min", "max")
        MIN_FIELD_NUMBER: _ClassVar[int]
        MAX_FIELD_NUMBER: _ClassVar[int]
        min: int
        max: int
        def __init__(self, min: _Optional[int] = ..., max: _Optional[int] = ...) -> None: ...
    RANGE_FIELD_NUMBER: _ClassVar[int]
    LT_FIELD_NUMBER: _ClassVar[int]
    LE_FIELD_NUMBER: _ClassVar[int]
    EQ_FIELD_NUMBER: _ClassVar[int]
    GE_FIELD_NUMBER: _ClassVar[int]
    GT_FIELD_NUMBER: _ClassVar[int]
    range: Limit.Range
    lt: int
    le: int
    eq: int
    ge: int
    gt: int
    def __init__(self, range: _Optional[_Union[Limit.Range, _Mapping]] = ..., lt: _Optional[int] = ..., le: _Optional[int] = ..., eq: _Optional[int] = ..., ge: _Optional[int] = ..., gt: _Optional[int] = ...) -> None: ...

class MapKey(_message.Message):
    __slots__ = ("length", "value")
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    length: Limit
    value: str
    def __init__(self, length: _Optional[_Union[Limit, _Mapping]] = ..., value: _Optional[str] = ...) -> None: ...
