from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Column(_message.Message):
    __slots__ = ["name", "type"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    name: str
    type: Type
    def __init__(self, name: _Optional[str] = ..., type: _Optional[_Union[Type, _Mapping]] = ...) -> None: ...

class DecimalType(_message.Message):
    __slots__ = ["precision", "scale"]
    PRECISION_FIELD_NUMBER: _ClassVar[int]
    SCALE_FIELD_NUMBER: _ClassVar[int]
    precision: int
    scale: int
    def __init__(self, precision: _Optional[int] = ..., scale: _Optional[int] = ...) -> None: ...

class DictType(_message.Message):
    __slots__ = ["key", "payload"]
    KEY_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    key: Type
    payload: Type
    def __init__(self, key: _Optional[_Union[Type, _Mapping]] = ..., payload: _Optional[_Union[Type, _Mapping]] = ...) -> None: ...

class ListType(_message.Message):
    __slots__ = ["item"]
    ITEM_FIELD_NUMBER: _ClassVar[int]
    item: Type
    def __init__(self, item: _Optional[_Union[Type, _Mapping]] = ...) -> None: ...

class OptionalType(_message.Message):
    __slots__ = ["item"]
    ITEM_FIELD_NUMBER: _ClassVar[int]
    item: Type
    def __init__(self, item: _Optional[_Union[Type, _Mapping]] = ...) -> None: ...

class PgType(_message.Message):
    __slots__ = ["oid", "typlen", "typmod"]
    OID_FIELD_NUMBER: _ClassVar[int]
    TYPLEN_FIELD_NUMBER: _ClassVar[int]
    TYPMOD_FIELD_NUMBER: _ClassVar[int]
    oid: int
    typlen: int
    typmod: int
    def __init__(self, oid: _Optional[int] = ..., typlen: _Optional[int] = ..., typmod: _Optional[int] = ...) -> None: ...

class ResultSet(_message.Message):
    __slots__ = ["columns", "rows", "truncated"]
    COLUMNS_FIELD_NUMBER: _ClassVar[int]
    ROWS_FIELD_NUMBER: _ClassVar[int]
    TRUNCATED_FIELD_NUMBER: _ClassVar[int]
    columns: _containers.RepeatedCompositeFieldContainer[Column]
    rows: _containers.RepeatedCompositeFieldContainer[Value]
    truncated: bool
    def __init__(self, columns: _Optional[_Iterable[_Union[Column, _Mapping]]] = ..., rows: _Optional[_Iterable[_Union[Value, _Mapping]]] = ..., truncated: bool = ...) -> None: ...

class StructMember(_message.Message):
    __slots__ = ["name", "type"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    name: str
    type: Type
    def __init__(self, name: _Optional[str] = ..., type: _Optional[_Union[Type, _Mapping]] = ...) -> None: ...

class StructType(_message.Message):
    __slots__ = ["members"]
    MEMBERS_FIELD_NUMBER: _ClassVar[int]
    members: _containers.RepeatedCompositeFieldContainer[StructMember]
    def __init__(self, members: _Optional[_Iterable[_Union[StructMember, _Mapping]]] = ...) -> None: ...

class TaggedType(_message.Message):
    __slots__ = ["tag", "type"]
    TAG_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    tag: str
    type: Type
    def __init__(self, tag: _Optional[str] = ..., type: _Optional[_Union[Type, _Mapping]] = ...) -> None: ...

class TupleType(_message.Message):
    __slots__ = ["elements"]
    ELEMENTS_FIELD_NUMBER: _ClassVar[int]
    elements: _containers.RepeatedCompositeFieldContainer[Type]
    def __init__(self, elements: _Optional[_Iterable[_Union[Type, _Mapping]]] = ...) -> None: ...

class Type(_message.Message):
    __slots__ = ["decimal_type", "dict_type", "empty_dict_type", "empty_list_type", "list_type", "null_type", "optional_type", "pg_type", "struct_type", "tagged_type", "tuple_type", "type_id", "variant_type", "void_type"]
    class PrimitiveTypeId(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    BOOL: Type.PrimitiveTypeId
    DATE: Type.PrimitiveTypeId
    DATETIME: Type.PrimitiveTypeId
    DECIMAL_TYPE_FIELD_NUMBER: _ClassVar[int]
    DICT_TYPE_FIELD_NUMBER: _ClassVar[int]
    DOUBLE: Type.PrimitiveTypeId
    DYNUMBER: Type.PrimitiveTypeId
    EMPTY_DICT_TYPE_FIELD_NUMBER: _ClassVar[int]
    EMPTY_LIST_TYPE_FIELD_NUMBER: _ClassVar[int]
    FLOAT: Type.PrimitiveTypeId
    INT16: Type.PrimitiveTypeId
    INT32: Type.PrimitiveTypeId
    INT64: Type.PrimitiveTypeId
    INT8: Type.PrimitiveTypeId
    INTERVAL: Type.PrimitiveTypeId
    JSON: Type.PrimitiveTypeId
    JSON_DOCUMENT: Type.PrimitiveTypeId
    LIST_TYPE_FIELD_NUMBER: _ClassVar[int]
    NULL_TYPE_FIELD_NUMBER: _ClassVar[int]
    OPTIONAL_TYPE_FIELD_NUMBER: _ClassVar[int]
    PG_TYPE_FIELD_NUMBER: _ClassVar[int]
    PRIMITIVE_TYPE_ID_UNSPECIFIED: Type.PrimitiveTypeId
    STRING: Type.PrimitiveTypeId
    STRUCT_TYPE_FIELD_NUMBER: _ClassVar[int]
    TAGGED_TYPE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP: Type.PrimitiveTypeId
    TUPLE_TYPE_FIELD_NUMBER: _ClassVar[int]
    TYPE_ID_FIELD_NUMBER: _ClassVar[int]
    TZ_DATE: Type.PrimitiveTypeId
    TZ_DATETIME: Type.PrimitiveTypeId
    TZ_TIMESTAMP: Type.PrimitiveTypeId
    UINT16: Type.PrimitiveTypeId
    UINT32: Type.PrimitiveTypeId
    UINT64: Type.PrimitiveTypeId
    UINT8: Type.PrimitiveTypeId
    UTF8: Type.PrimitiveTypeId
    UUID: Type.PrimitiveTypeId
    VARIANT_TYPE_FIELD_NUMBER: _ClassVar[int]
    VOID_TYPE_FIELD_NUMBER: _ClassVar[int]
    YSON: Type.PrimitiveTypeId
    decimal_type: DecimalType
    dict_type: DictType
    empty_dict_type: _struct_pb2.NullValue
    empty_list_type: _struct_pb2.NullValue
    list_type: ListType
    null_type: _struct_pb2.NullValue
    optional_type: OptionalType
    pg_type: PgType
    struct_type: StructType
    tagged_type: TaggedType
    tuple_type: TupleType
    type_id: Type.PrimitiveTypeId
    variant_type: VariantType
    void_type: _struct_pb2.NullValue
    def __init__(self, type_id: _Optional[_Union[Type.PrimitiveTypeId, str]] = ..., decimal_type: _Optional[_Union[DecimalType, _Mapping]] = ..., optional_type: _Optional[_Union[OptionalType, _Mapping]] = ..., list_type: _Optional[_Union[ListType, _Mapping]] = ..., tuple_type: _Optional[_Union[TupleType, _Mapping]] = ..., struct_type: _Optional[_Union[StructType, _Mapping]] = ..., dict_type: _Optional[_Union[DictType, _Mapping]] = ..., variant_type: _Optional[_Union[VariantType, _Mapping]] = ..., tagged_type: _Optional[_Union[TaggedType, _Mapping]] = ..., void_type: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., null_type: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., empty_list_type: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., empty_dict_type: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., pg_type: _Optional[_Union[PgType, _Mapping]] = ...) -> None: ...

class TypedValue(_message.Message):
    __slots__ = ["type", "value"]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    type: Type
    value: Value
    def __init__(self, type: _Optional[_Union[Type, _Mapping]] = ..., value: _Optional[_Union[Value, _Mapping]] = ...) -> None: ...

class Value(_message.Message):
    __slots__ = ["bool_value", "bytes_value", "double_value", "float_value", "high_128", "int32_value", "int64_value", "items", "low_128", "nested_value", "null_flag_value", "pairs", "text_value", "uint32_value", "uint64_value", "variant_index"]
    BOOL_VALUE_FIELD_NUMBER: _ClassVar[int]
    BYTES_VALUE_FIELD_NUMBER: _ClassVar[int]
    DOUBLE_VALUE_FIELD_NUMBER: _ClassVar[int]
    FLOAT_VALUE_FIELD_NUMBER: _ClassVar[int]
    HIGH_128_FIELD_NUMBER: _ClassVar[int]
    INT32_VALUE_FIELD_NUMBER: _ClassVar[int]
    INT64_VALUE_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    LOW_128_FIELD_NUMBER: _ClassVar[int]
    NESTED_VALUE_FIELD_NUMBER: _ClassVar[int]
    NULL_FLAG_VALUE_FIELD_NUMBER: _ClassVar[int]
    PAIRS_FIELD_NUMBER: _ClassVar[int]
    TEXT_VALUE_FIELD_NUMBER: _ClassVar[int]
    UINT32_VALUE_FIELD_NUMBER: _ClassVar[int]
    UINT64_VALUE_FIELD_NUMBER: _ClassVar[int]
    VARIANT_INDEX_FIELD_NUMBER: _ClassVar[int]
    bool_value: bool
    bytes_value: bytes
    double_value: float
    float_value: float
    high_128: int
    int32_value: int
    int64_value: int
    items: _containers.RepeatedCompositeFieldContainer[Value]
    low_128: int
    nested_value: Value
    null_flag_value: _struct_pb2.NullValue
    pairs: _containers.RepeatedCompositeFieldContainer[ValuePair]
    text_value: str
    uint32_value: int
    uint64_value: int
    variant_index: int
    def __init__(self, bool_value: bool = ..., int32_value: _Optional[int] = ..., uint32_value: _Optional[int] = ..., int64_value: _Optional[int] = ..., uint64_value: _Optional[int] = ..., float_value: _Optional[float] = ..., double_value: _Optional[float] = ..., bytes_value: _Optional[bytes] = ..., text_value: _Optional[str] = ..., null_flag_value: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., nested_value: _Optional[_Union[Value, _Mapping]] = ..., low_128: _Optional[int] = ..., items: _Optional[_Iterable[_Union[Value, _Mapping]]] = ..., pairs: _Optional[_Iterable[_Union[ValuePair, _Mapping]]] = ..., variant_index: _Optional[int] = ..., high_128: _Optional[int] = ...) -> None: ...

class ValuePair(_message.Message):
    __slots__ = ["key", "payload"]
    KEY_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    key: Value
    payload: Value
    def __init__(self, key: _Optional[_Union[Value, _Mapping]] = ..., payload: _Optional[_Union[Value, _Mapping]] = ...) -> None: ...

class VariantType(_message.Message):
    __slots__ = ["struct_items", "tuple_items"]
    STRUCT_ITEMS_FIELD_NUMBER: _ClassVar[int]
    TUPLE_ITEMS_FIELD_NUMBER: _ClassVar[int]
    struct_items: StructType
    tuple_items: TupleType
    def __init__(self, tuple_items: _Optional[_Union[TupleType, _Mapping]] = ..., struct_items: _Optional[_Union[StructType, _Mapping]] = ...) -> None: ...
