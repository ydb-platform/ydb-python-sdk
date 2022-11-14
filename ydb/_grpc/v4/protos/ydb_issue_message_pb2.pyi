from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class IssueMessage(_message.Message):
    __slots__ = ["end_position", "issue_code", "issues", "message", "position", "severity"]
    class Position(_message.Message):
        __slots__ = ["column", "file", "row"]
        COLUMN_FIELD_NUMBER: _ClassVar[int]
        FILE_FIELD_NUMBER: _ClassVar[int]
        ROW_FIELD_NUMBER: _ClassVar[int]
        column: int
        file: str
        row: int
        def __init__(self, row: _Optional[int] = ..., column: _Optional[int] = ..., file: _Optional[str] = ...) -> None: ...
    END_POSITION_FIELD_NUMBER: _ClassVar[int]
    ISSUES_FIELD_NUMBER: _ClassVar[int]
    ISSUE_CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    SEVERITY_FIELD_NUMBER: _ClassVar[int]
    end_position: IssueMessage.Position
    issue_code: int
    issues: _containers.RepeatedCompositeFieldContainer[IssueMessage]
    message: str
    position: IssueMessage.Position
    severity: int
    def __init__(self, position: _Optional[_Union[IssueMessage.Position, _Mapping]] = ..., message: _Optional[str] = ..., end_position: _Optional[_Union[IssueMessage.Position, _Mapping]] = ..., issue_code: _Optional[int] = ..., severity: _Optional[int] = ..., issues: _Optional[_Iterable[_Union[IssueMessage, _Mapping]]] = ...) -> None: ...
