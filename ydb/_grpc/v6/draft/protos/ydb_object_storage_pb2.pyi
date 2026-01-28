from protos import ydb_issue_message_pb2 as _ydb_issue_message_pb2
from protos import ydb_value_pb2 as _ydb_value_pb2
from protos import ydb_status_codes_pb2 as _ydb_status_codes_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ListingRequest(_message.Message):
    __slots__ = ("table_name", "key_prefix", "path_column_prefix", "path_column_delimiter", "continuation_token", "start_after_key_suffix", "max_keys", "columns_to_return", "matching_filter")
    class EMatchType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        EQUAL: _ClassVar[ListingRequest.EMatchType]
        NOT_EQUAL: _ClassVar[ListingRequest.EMatchType]
    EQUAL: ListingRequest.EMatchType
    NOT_EQUAL: ListingRequest.EMatchType
    TABLE_NAME_FIELD_NUMBER: _ClassVar[int]
    KEY_PREFIX_FIELD_NUMBER: _ClassVar[int]
    PATH_COLUMN_PREFIX_FIELD_NUMBER: _ClassVar[int]
    PATH_COLUMN_DELIMITER_FIELD_NUMBER: _ClassVar[int]
    CONTINUATION_TOKEN_FIELD_NUMBER: _ClassVar[int]
    START_AFTER_KEY_SUFFIX_FIELD_NUMBER: _ClassVar[int]
    MAX_KEYS_FIELD_NUMBER: _ClassVar[int]
    COLUMNS_TO_RETURN_FIELD_NUMBER: _ClassVar[int]
    MATCHING_FILTER_FIELD_NUMBER: _ClassVar[int]
    table_name: str
    key_prefix: _ydb_value_pb2.TypedValue
    path_column_prefix: str
    path_column_delimiter: str
    continuation_token: bytes
    start_after_key_suffix: _ydb_value_pb2.TypedValue
    max_keys: int
    columns_to_return: _containers.RepeatedScalarFieldContainer[str]
    matching_filter: _ydb_value_pb2.TypedValue
    def __init__(self, table_name: _Optional[str] = ..., key_prefix: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ..., path_column_prefix: _Optional[str] = ..., path_column_delimiter: _Optional[str] = ..., continuation_token: _Optional[bytes] = ..., start_after_key_suffix: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ..., max_keys: _Optional[int] = ..., columns_to_return: _Optional[_Iterable[str]] = ..., matching_filter: _Optional[_Union[_ydb_value_pb2.TypedValue, _Mapping]] = ...) -> None: ...

class ListingResponse(_message.Message):
    __slots__ = ("status", "issues", "common_prefixes", "contents", "is_truncated", "next_continuation_token")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    COMMON_PREFIXES_FIELD_NUMBER: _ClassVar[int]
    CONTENTS_FIELD_NUMBER: _ClassVar[int]
    IS_TRUNCATED_FIELD_NUMBER: _ClassVar[int]
    NEXT_CONTINUATION_TOKEN_FIELD_NUMBER: _ClassVar[int]
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
    common_prefixes: _containers.RepeatedScalarFieldContainer[str]
    contents: _ydb_value_pb2.ResultSet
    is_truncated: bool
    next_continuation_token: bytes
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., common_prefixes: _Optional[_Iterable[str]] = ..., contents: _Optional[_Union[_ydb_value_pb2.ResultSet, _Mapping]] = ..., is_truncated: bool = ..., next_continuation_token: _Optional[bytes] = ...) -> None: ...
