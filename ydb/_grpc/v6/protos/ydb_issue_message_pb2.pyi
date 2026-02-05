from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class IssueMessage(_message.Message):
    __slots__ = ("position", "message", "end_position", "issue_code", "severity", "issues")
    class Position(_message.Message):
        __slots__ = ("row", "column", "file")
        ROW_FIELD_NUMBER: _ClassVar[int]
        COLUMN_FIELD_NUMBER: _ClassVar[int]
        FILE_FIELD_NUMBER: _ClassVar[int]
        row: int
        column: int
        file: str
        def __init__(self, row: _Optional[int] = ..., column: _Optional[int] = ..., file: _Optional[str] = ...) -> None: ...
    POSITION_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    END_POSITION_FIELD_NUMBER: _ClassVar[int]
    ISSUE_CODE_FIELD_NUMBER: _ClassVar[int]
    SEVERITY_FIELD_NUMBER: _ClassVar[int]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    position: IssueMessage.Position
    message: str
    end_position: IssueMessage.Position
    issue_code: int
    severity: int
    issues: _containers.RepeatedCompositeFieldContainer[IssueMessage]
    def __init__(self, position: _Optional[_Union[IssueMessage.Position, _Mapping]] = ..., message: _Optional[str] = ..., end_position: _Optional[_Union[IssueMessage.Position, _Mapping]] = ..., issue_code: _Optional[int] = ..., severity: _Optional[int] = ..., issues: _Optional[_Iterable[_Union[IssueMessage, _Mapping]]] = ...) -> None: ...
