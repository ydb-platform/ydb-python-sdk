from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ArrowBatchSettings(_message.Message):
    __slots__ = ("schema",)
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    schema: bytes
    def __init__(self, schema: _Optional[bytes] = ...) -> None: ...

class CsvSettings(_message.Message):
    __slots__ = ("skip_rows", "delimiter", "null_value", "header", "quoting")
    class Quoting(_message.Message):
        __slots__ = ("disabled", "quote_char", "double_quote_disabled")
        DISABLED_FIELD_NUMBER: _ClassVar[int]
        QUOTE_CHAR_FIELD_NUMBER: _ClassVar[int]
        DOUBLE_QUOTE_DISABLED_FIELD_NUMBER: _ClassVar[int]
        disabled: bool
        quote_char: bytes
        double_quote_disabled: bool
        def __init__(self, disabled: bool = ..., quote_char: _Optional[bytes] = ..., double_quote_disabled: bool = ...) -> None: ...
    SKIP_ROWS_FIELD_NUMBER: _ClassVar[int]
    DELIMITER_FIELD_NUMBER: _ClassVar[int]
    NULL_VALUE_FIELD_NUMBER: _ClassVar[int]
    HEADER_FIELD_NUMBER: _ClassVar[int]
    QUOTING_FIELD_NUMBER: _ClassVar[int]
    skip_rows: int
    delimiter: bytes
    null_value: bytes
    header: bool
    quoting: CsvSettings.Quoting
    def __init__(self, skip_rows: _Optional[int] = ..., delimiter: _Optional[bytes] = ..., null_value: _Optional[bytes] = ..., header: bool = ..., quoting: _Optional[_Union[CsvSettings.Quoting, _Mapping]] = ...) -> None: ...

class ArrowFormatSettings(_message.Message):
    __slots__ = ("compression_codec",)
    class CompressionCodec(_message.Message):
        __slots__ = ("type", "level")
        class Type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            TYPE_UNSPECIFIED: _ClassVar[ArrowFormatSettings.CompressionCodec.Type]
            TYPE_NONE: _ClassVar[ArrowFormatSettings.CompressionCodec.Type]
            TYPE_ZSTD: _ClassVar[ArrowFormatSettings.CompressionCodec.Type]
            TYPE_LZ4_FRAME: _ClassVar[ArrowFormatSettings.CompressionCodec.Type]
        TYPE_UNSPECIFIED: ArrowFormatSettings.CompressionCodec.Type
        TYPE_NONE: ArrowFormatSettings.CompressionCodec.Type
        TYPE_ZSTD: ArrowFormatSettings.CompressionCodec.Type
        TYPE_LZ4_FRAME: ArrowFormatSettings.CompressionCodec.Type
        TYPE_FIELD_NUMBER: _ClassVar[int]
        LEVEL_FIELD_NUMBER: _ClassVar[int]
        type: ArrowFormatSettings.CompressionCodec.Type
        level: int
        def __init__(self, type: _Optional[_Union[ArrowFormatSettings.CompressionCodec.Type, str]] = ..., level: _Optional[int] = ...) -> None: ...
    COMPRESSION_CODEC_FIELD_NUMBER: _ClassVar[int]
    compression_codec: ArrowFormatSettings.CompressionCodec
    def __init__(self, compression_codec: _Optional[_Union[ArrowFormatSettings.CompressionCodec, _Mapping]] = ...) -> None: ...

class ArrowFormatMeta(_message.Message):
    __slots__ = ("schema",)
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    schema: bytes
    def __init__(self, schema: _Optional[bytes] = ...) -> None: ...
