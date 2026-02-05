from google.protobuf import struct_pb2 as _struct_pb2
from protos import ydb_formats_pb2 as _ydb_formats_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DecimalType(_message.Message):
    __slots__ = ("precision", "scale")
    PRECISION_FIELD_NUMBER: _ClassVar[int]
    SCALE_FIELD_NUMBER: _ClassVar[int]
    precision: int
    scale: int
    def __init__(self, precision: _Optional[int] = ..., scale: _Optional[int] = ...) -> None: ...

class OptionalType(_message.Message):
    __slots__ = ("item",)
    ITEM_FIELD_NUMBER: _ClassVar[int]
    item: Type
    def __init__(self, item: _Optional[_Union[Type, _Mapping]] = ...) -> None: ...

class ListType(_message.Message):
    __slots__ = ("item",)
    ITEM_FIELD_NUMBER: _ClassVar[int]
    item: Type
    def __init__(self, item: _Optional[_Union[Type, _Mapping]] = ...) -> None: ...

class VariantType(_message.Message):
    __slots__ = ("tuple_items", "struct_items")
    TUPLE_ITEMS_FIELD_NUMBER: _ClassVar[int]
    STRUCT_ITEMS_FIELD_NUMBER: _ClassVar[int]
    tuple_items: TupleType
    struct_items: StructType
    def __init__(self, tuple_items: _Optional[_Union[TupleType, _Mapping]] = ..., struct_items: _Optional[_Union[StructType, _Mapping]] = ...) -> None: ...

class TupleType(_message.Message):
    __slots__ = ("elements",)
    ELEMENTS_FIELD_NUMBER: _ClassVar[int]
    elements: _containers.RepeatedCompositeFieldContainer[Type]
    def __init__(self, elements: _Optional[_Iterable[_Union[Type, _Mapping]]] = ...) -> None: ...

class StructMember(_message.Message):
    __slots__ = ("name", "type")
    NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    name: str
    type: Type
    def __init__(self, name: _Optional[str] = ..., type: _Optional[_Union[Type, _Mapping]] = ...) -> None: ...

class StructType(_message.Message):
    __slots__ = ("members",)
    MEMBERS_FIELD_NUMBER: _ClassVar[int]
    members: _containers.RepeatedCompositeFieldContainer[StructMember]
    def __init__(self, members: _Optional[_Iterable[_Union[StructMember, _Mapping]]] = ...) -> None: ...

class DictType(_message.Message):
    __slots__ = ("key", "payload")
    KEY_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    key: Type
    payload: Type
    def __init__(self, key: _Optional[_Union[Type, _Mapping]] = ..., payload: _Optional[_Union[Type, _Mapping]] = ...) -> None: ...

class TaggedType(_message.Message):
    __slots__ = ("tag", "type")
    TAG_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    tag: str
    type: Type
    def __init__(self, tag: _Optional[str] = ..., type: _Optional[_Union[Type, _Mapping]] = ...) -> None: ...

class PgType(_message.Message):
    __slots__ = ("type_name", "type_modifier", "oid", "typlen", "typmod")
    TYPE_NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_MODIFIER_FIELD_NUMBER: _ClassVar[int]
    OID_FIELD_NUMBER: _ClassVar[int]
    TYPLEN_FIELD_NUMBER: _ClassVar[int]
    TYPMOD_FIELD_NUMBER: _ClassVar[int]
    type_name: str
    type_modifier: str
    oid: int
    typlen: int
    typmod: int
    def __init__(self, type_name: _Optional[str] = ..., type_modifier: _Optional[str] = ..., oid: _Optional[int] = ..., typlen: _Optional[int] = ..., typmod: _Optional[int] = ...) -> None: ...

class Type(_message.Message):
    __slots__ = ("type_id", "decimal_type", "optional_type", "list_type", "tuple_type", "struct_type", "dict_type", "variant_type", "tagged_type", "void_type", "null_type", "empty_list_type", "empty_dict_type", "pg_type")
    class PrimitiveTypeId(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        PRIMITIVE_TYPE_ID_UNSPECIFIED: _ClassVar[Type.PrimitiveTypeId]
        BOOL: _ClassVar[Type.PrimitiveTypeId]
        INT8: _ClassVar[Type.PrimitiveTypeId]
        UINT8: _ClassVar[Type.PrimitiveTypeId]
        INT16: _ClassVar[Type.PrimitiveTypeId]
        UINT16: _ClassVar[Type.PrimitiveTypeId]
        INT32: _ClassVar[Type.PrimitiveTypeId]
        UINT32: _ClassVar[Type.PrimitiveTypeId]
        INT64: _ClassVar[Type.PrimitiveTypeId]
        UINT64: _ClassVar[Type.PrimitiveTypeId]
        FLOAT: _ClassVar[Type.PrimitiveTypeId]
        DOUBLE: _ClassVar[Type.PrimitiveTypeId]
        DATE: _ClassVar[Type.PrimitiveTypeId]
        DATETIME: _ClassVar[Type.PrimitiveTypeId]
        TIMESTAMP: _ClassVar[Type.PrimitiveTypeId]
        INTERVAL: _ClassVar[Type.PrimitiveTypeId]
        TZ_DATE: _ClassVar[Type.PrimitiveTypeId]
        TZ_DATETIME: _ClassVar[Type.PrimitiveTypeId]
        TZ_TIMESTAMP: _ClassVar[Type.PrimitiveTypeId]
        DATE32: _ClassVar[Type.PrimitiveTypeId]
        DATETIME64: _ClassVar[Type.PrimitiveTypeId]
        TIMESTAMP64: _ClassVar[Type.PrimitiveTypeId]
        INTERVAL64: _ClassVar[Type.PrimitiveTypeId]
        STRING: _ClassVar[Type.PrimitiveTypeId]
        UTF8: _ClassVar[Type.PrimitiveTypeId]
        YSON: _ClassVar[Type.PrimitiveTypeId]
        JSON: _ClassVar[Type.PrimitiveTypeId]
        UUID: _ClassVar[Type.PrimitiveTypeId]
        JSON_DOCUMENT: _ClassVar[Type.PrimitiveTypeId]
        DYNUMBER: _ClassVar[Type.PrimitiveTypeId]
    PRIMITIVE_TYPE_ID_UNSPECIFIED: Type.PrimitiveTypeId
    BOOL: Type.PrimitiveTypeId
    INT8: Type.PrimitiveTypeId
    UINT8: Type.PrimitiveTypeId
    INT16: Type.PrimitiveTypeId
    UINT16: Type.PrimitiveTypeId
    INT32: Type.PrimitiveTypeId
    UINT32: Type.PrimitiveTypeId
    INT64: Type.PrimitiveTypeId
    UINT64: Type.PrimitiveTypeId
    FLOAT: Type.PrimitiveTypeId
    DOUBLE: Type.PrimitiveTypeId
    DATE: Type.PrimitiveTypeId
    DATETIME: Type.PrimitiveTypeId
    TIMESTAMP: Type.PrimitiveTypeId
    INTERVAL: Type.PrimitiveTypeId
    TZ_DATE: Type.PrimitiveTypeId
    TZ_DATETIME: Type.PrimitiveTypeId
    TZ_TIMESTAMP: Type.PrimitiveTypeId
    DATE32: Type.PrimitiveTypeId
    DATETIME64: Type.PrimitiveTypeId
    TIMESTAMP64: Type.PrimitiveTypeId
    INTERVAL64: Type.PrimitiveTypeId
    STRING: Type.PrimitiveTypeId
    UTF8: Type.PrimitiveTypeId
    YSON: Type.PrimitiveTypeId
    JSON: Type.PrimitiveTypeId
    UUID: Type.PrimitiveTypeId
    JSON_DOCUMENT: Type.PrimitiveTypeId
    DYNUMBER: Type.PrimitiveTypeId
    TYPE_ID_FIELD_NUMBER: _ClassVar[int]
    DECIMAL_TYPE_FIELD_NUMBER: _ClassVar[int]
    OPTIONAL_TYPE_FIELD_NUMBER: _ClassVar[int]
    LIST_TYPE_FIELD_NUMBER: _ClassVar[int]
    TUPLE_TYPE_FIELD_NUMBER: _ClassVar[int]
    STRUCT_TYPE_FIELD_NUMBER: _ClassVar[int]
    DICT_TYPE_FIELD_NUMBER: _ClassVar[int]
    VARIANT_TYPE_FIELD_NUMBER: _ClassVar[int]
    TAGGED_TYPE_FIELD_NUMBER: _ClassVar[int]
    VOID_TYPE_FIELD_NUMBER: _ClassVar[int]
    NULL_TYPE_FIELD_NUMBER: _ClassVar[int]
    EMPTY_LIST_TYPE_FIELD_NUMBER: _ClassVar[int]
    EMPTY_DICT_TYPE_FIELD_NUMBER: _ClassVar[int]
    PG_TYPE_FIELD_NUMBER: _ClassVar[int]
    type_id: Type.PrimitiveTypeId
    decimal_type: DecimalType
    optional_type: OptionalType
    list_type: ListType
    tuple_type: TupleType
    struct_type: StructType
    dict_type: DictType
    variant_type: VariantType
    tagged_type: TaggedType
    void_type: _struct_pb2.NullValue
    null_type: _struct_pb2.NullValue
    empty_list_type: _struct_pb2.NullValue
    empty_dict_type: _struct_pb2.NullValue
    pg_type: PgType
    def __init__(self, type_id: _Optional[_Union[Type.PrimitiveTypeId, str]] = ..., decimal_type: _Optional[_Union[DecimalType, _Mapping]] = ..., optional_type: _Optional[_Union[OptionalType, _Mapping]] = ..., list_type: _Optional[_Union[ListType, _Mapping]] = ..., tuple_type: _Optional[_Union[TupleType, _Mapping]] = ..., struct_type: _Optional[_Union[StructType, _Mapping]] = ..., dict_type: _Optional[_Union[DictType, _Mapping]] = ..., variant_type: _Optional[_Union[VariantType, _Mapping]] = ..., tagged_type: _Optional[_Union[TaggedType, _Mapping]] = ..., void_type: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., null_type: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., empty_list_type: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., empty_dict_type: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., pg_type: _Optional[_Union[PgType, _Mapping]] = ...) -> None: ...

class ValuePair(_message.Message):
    __slots__ = ("key", "payload")
    KEY_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    key: Value
    payload: Value
    def __init__(self, key: _Optional[_Union[Value, _Mapping]] = ..., payload: _Optional[_Union[Value, _Mapping]] = ...) -> None: ...

class Value(_message.Message):
    __slots__ = ("bool_value", "int32_value", "uint32_value", "int64_value", "uint64_value", "float_value", "double_value", "bytes_value", "text_value", "null_flag_value", "nested_value", "low_128", "items", "pairs", "variant_index", "high_128")
    BOOL_VALUE_FIELD_NUMBER: _ClassVar[int]
    INT32_VALUE_FIELD_NUMBER: _ClassVar[int]
    UINT32_VALUE_FIELD_NUMBER: _ClassVar[int]
    INT64_VALUE_FIELD_NUMBER: _ClassVar[int]
    UINT64_VALUE_FIELD_NUMBER: _ClassVar[int]
    FLOAT_VALUE_FIELD_NUMBER: _ClassVar[int]
    DOUBLE_VALUE_FIELD_NUMBER: _ClassVar[int]
    BYTES_VALUE_FIELD_NUMBER: _ClassVar[int]
    TEXT_VALUE_FIELD_NUMBER: _ClassVar[int]
    NULL_FLAG_VALUE_FIELD_NUMBER: _ClassVar[int]
    NESTED_VALUE_FIELD_NUMBER: _ClassVar[int]
    LOW_128_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    PAIRS_FIELD_NUMBER: _ClassVar[int]
    VARIANT_INDEX_FIELD_NUMBER: _ClassVar[int]
    HIGH_128_FIELD_NUMBER: _ClassVar[int]
    bool_value: bool
    int32_value: int
    uint32_value: int
    int64_value: int
    uint64_value: int
    float_value: float
    double_value: float
    bytes_value: bytes
    text_value: str
    null_flag_value: _struct_pb2.NullValue
    nested_value: Value
    low_128: int
    items: _containers.RepeatedCompositeFieldContainer[Value]
    pairs: _containers.RepeatedCompositeFieldContainer[ValuePair]
    variant_index: int
    high_128: int
    def __init__(self, bool_value: bool = ..., int32_value: _Optional[int] = ..., uint32_value: _Optional[int] = ..., int64_value: _Optional[int] = ..., uint64_value: _Optional[int] = ..., float_value: _Optional[float] = ..., double_value: _Optional[float] = ..., bytes_value: _Optional[bytes] = ..., text_value: _Optional[str] = ..., null_flag_value: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., nested_value: _Optional[_Union[Value, _Mapping]] = ..., low_128: _Optional[int] = ..., items: _Optional[_Iterable[_Union[Value, _Mapping]]] = ..., pairs: _Optional[_Iterable[_Union[ValuePair, _Mapping]]] = ..., variant_index: _Optional[int] = ..., high_128: _Optional[int] = ...) -> None: ...

class TypedValue(_message.Message):
    __slots__ = ("type", "value")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    type: Type
    value: Value
    def __init__(self, type: _Optional[_Union[Type, _Mapping]] = ..., value: _Optional[_Union[Value, _Mapping]] = ...) -> None: ...

class Column(_message.Message):
    __slots__ = ("name", "type")
    NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    name: str
    type: Type
    def __init__(self, name: _Optional[str] = ..., type: _Optional[_Union[Type, _Mapping]] = ...) -> None: ...

class ResultSet(_message.Message):
    __slots__ = ("columns", "rows", "truncated", "format", "arrow_format_meta", "data")
    class Format(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        FORMAT_UNSPECIFIED: _ClassVar[ResultSet.Format]
        FORMAT_VALUE: _ClassVar[ResultSet.Format]
        FORMAT_ARROW: _ClassVar[ResultSet.Format]
    FORMAT_UNSPECIFIED: ResultSet.Format
    FORMAT_VALUE: ResultSet.Format
    FORMAT_ARROW: ResultSet.Format
    COLUMNS_FIELD_NUMBER: _ClassVar[int]
    ROWS_FIELD_NUMBER: _ClassVar[int]
    TRUNCATED_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    ARROW_FORMAT_META_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    columns: _containers.RepeatedCompositeFieldContainer[Column]
    rows: _containers.RepeatedCompositeFieldContainer[Value]
    truncated: bool
    format: ResultSet.Format
    arrow_format_meta: _ydb_formats_pb2.ArrowFormatMeta
    data: bytes
    def __init__(self, columns: _Optional[_Iterable[_Union[Column, _Mapping]]] = ..., rows: _Optional[_Iterable[_Union[Value, _Mapping]]] = ..., truncated: bool = ..., format: _Optional[_Union[ResultSet.Format, str]] = ..., arrow_format_meta: _Optional[_Union[_ydb_formats_pb2.ArrowFormatMeta, _Mapping]] = ..., data: _Optional[bytes] = ...) -> None: ...
