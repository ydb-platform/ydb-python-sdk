from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ArrowBatchSettings(_message.Message):
    __slots__ = ["schema"]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    schema: bytes
    def __init__(self, schema: _Optional[bytes] = ...) -> None: ...

class CsvSettings(_message.Message):
    __slots__ = ["delimiter", "header", "null_value", "quoting", "skip_rows"]
    class Quoting(_message.Message):
        __slots__ = ["disabled", "double_quote_disabled", "quote_char"]
        DISABLED_FIELD_NUMBER: _ClassVar[int]
        DOUBLE_QUOTE_DISABLED_FIELD_NUMBER: _ClassVar[int]
        QUOTE_CHAR_FIELD_NUMBER: _ClassVar[int]
        disabled: bool
        double_quote_disabled: bool
        quote_char: bytes
        def __init__(self, disabled: bool = ..., quote_char: _Optional[bytes] = ..., double_quote_disabled: bool = ...) -> None: ...
    DELIMITER_FIELD_NUMBER: _ClassVar[int]
    HEADER_FIELD_NUMBER: _ClassVar[int]
    NULL_VALUE_FIELD_NUMBER: _ClassVar[int]
    QUOTING_FIELD_NUMBER: _ClassVar[int]
    SKIP_ROWS_FIELD_NUMBER: _ClassVar[int]
    delimiter: bytes
    header: bool
    null_value: bytes
    quoting: CsvSettings.Quoting
    skip_rows: int
    def __init__(self, skip_rows: _Optional[int] = ..., delimiter: _Optional[bytes] = ..., null_value: _Optional[bytes] = ..., header: bool = ..., quoting: _Optional[_Union[CsvSettings.Quoting, _Mapping]] = ...) -> None: ...
