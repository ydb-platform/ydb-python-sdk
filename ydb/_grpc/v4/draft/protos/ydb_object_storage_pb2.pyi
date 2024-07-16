from protos import ydb_issue_message_pb2 as _ydb_issue_message_pb2
from protos import ydb_value_pb2 as _ydb_value_pb2
from protos import ydb_status_codes_pb2 as _ydb_status_codes_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ListingRequest(_message.Message):
    __slots__ = ["columns_to_return", "continuation_token", "key_prefix", "matching_filter", "max_keys", "path_column_delimiter", "path_column_prefix", "start_after_key_suffix", "table_name"]
    class EMatchType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    COLUMNS_TO_RETURN_FIELD_NUMBER: _ClassVar[int]
    CONTINUATION_TOKEN_FIELD_NUMBER: _ClassVar[int]
    EQUAL: ListingRequest.EMatchType
    KEY_PREFIX_FIELD_NUMBER: _ClassVar[int]
    MATCHING_FILTER_FIELD_NUMBER: _ClassVar[int]
    MAX_KEYS_FIELD_NUMBER: _ClassVar[int]
    NOT_EQUAL: ListingRequest.EMatchType
    PATH_COLUMN_DELIMITER_FIELD_NUMBER: _ClassVar[int]
    PATH_COLUMN_PREFIX_FIELD_NUMBER: _ClassVar[int]
    START_AFTER_KEY_SUFFIX_FIELD_NUMBER: _ClassVar[int]
    TABLE_NAME_FIELD_NUMBER: _ClassVar[int]
    columns_to_return: _containers.RepeatedScalarFieldContainer[str]
    continuation_token: bytes
    key_prefix: _ydb_value_pb2.TypedValue
    matching_filter: _ydb_value_pb2.TypedValue
    max_keys: int
    path_column_delimiter: str
    path_column_prefix: str
    start_after_key_suffix: _ydb_value_pb2.TypedValue
    table_name: str
    def __init__(self, table_name: _Optional[str] = ..., key_prefix: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ..., path_column_prefix: _Optional[str] = ..., path_column_delimiter: _Optional[str] = ..., continuation_token: _Optional[bytes] = ..., start_after_key_suffix: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ..., max_keys: _Optional[int] = ..., columns_to_return: _Optional[_Iterable[str]] = ..., matching_filter: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ...) -> None: ...

class ListingResponse(_message.Message):
    __slots__ = ["common_prefixes", "contents", "is_truncated", "issues", "next_continuation_token", "status"]
    COMMON_PREFIXES_FIELD_NUMBER: _ClassVar[int]
    CONTENTS_FIELD_NUMBER: _ClassVar[int]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    IS_TRUNCATED_FIELD_NUMBER: _ClassVar[int]
    NEXT_CONTINUATION_TOKEN_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    common_prefixes: _containers.RepeatedScalarFieldContainer[str]
    contents: _ydb_value_pb2.ResultSet
    is_truncated: bool
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    next_continuation_token: bytes
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., common_prefixes: _Optional[_Iterable[str]] = ..., contents: _Optional[_Union[_ydb_value_pb2.ResultSet, _Mapping]] = ..., is_truncated: bool = ..., next_continuation_token: _Optional[bytes] = ...) -> None: ...
