from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class ArrowBatchSettings(_message.Message):
    __slots__ = ["schema"]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    schema: bytes
    def __init__(self, schema: _Optional[bytes] = ...) -> None: ...

class CsvSettings(_message.Message):
    __slots__ = ["delimiter", "header", "null_value", "skip_rows"]
    DELIMITER_FIELD_NUMBER: _ClassVar[int]
    HEADER_FIELD_NUMBER: _ClassVar[int]
    NULL_VALUE_FIELD_NUMBER: _ClassVar[int]
    SKIP_ROWS_FIELD_NUMBER: _ClassVar[int]
    delimiter: bytes
    header: bool
    null_value: bytes
    skip_rows: int
    def __init__(self, skip_rows: _Optional[int] = ..., delimiter: _Optional[bytes] = ..., null_value: _Optional[bytes] = ..., header: bool = ...) -> None: ...
