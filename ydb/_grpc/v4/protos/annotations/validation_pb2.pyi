from google.protobuf import descriptor_pb2 as _descriptor_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor
LENGTH_FIELD_NUMBER: _ClassVar[int]
MAP_KEY_FIELD_NUMBER: _ClassVar[int]
REQUIRED_FIELD_NUMBER: _ClassVar[int]
SIZE_FIELD_NUMBER: _ClassVar[int]
VALUE_FIELD_NUMBER: _ClassVar[int]
length: _descriptor.FieldDescriptor
map_key: _descriptor.FieldDescriptor
required: _descriptor.FieldDescriptor
size: _descriptor.FieldDescriptor
value: _descriptor.FieldDescriptor

class Limit(_message.Message):
    __slots__ = ["eq", "ge", "gt", "le", "lt", "range"]
    class Range(_message.Message):
        __slots__ = ["max", "min"]
        MAX_FIELD_NUMBER: _ClassVar[int]
        MIN_FIELD_NUMBER: _ClassVar[int]
        max: int
        min: int
        def __init__(self, min: _Optional[int] = ..., max: _Optional[int] = ...) -> None: ...
    EQ_FIELD_NUMBER: _ClassVar[int]
    GE_FIELD_NUMBER: _ClassVar[int]
    GT_FIELD_NUMBER: _ClassVar[int]
    LE_FIELD_NUMBER: _ClassVar[int]
    LT_FIELD_NUMBER: _ClassVar[int]
    RANGE_FIELD_NUMBER: _ClassVar[int]
    eq: int
    ge: int
    gt: int
    le: int
    lt: int
    range: Limit.Range
    def __init__(self, range: _Optional[_Union[Limit.Range, _Mapping]] = ..., lt: _Optional[int] = ..., le: _Optional[int] = ..., eq: _Optional[int] = ..., ge: _Optional[int] = ..., gt: _Optional[int] = ...) -> None: ...

class MapKey(_message.Message):
    __slots__ = ["length", "value"]
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    length: Limit
    value: str
    def __init__(self, length: _Optional[_Union[Limit, _Mapping]] = ..., value: _Optional[str] = ...) -> None: ...
