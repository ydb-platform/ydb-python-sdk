from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class StatusIds(_message.Message):
    __slots__ = ()
    class StatusCode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        STATUS_CODE_UNSPECIFIED: _ClassVar[StatusIds.StatusCode]
        SUCCESS: _ClassVar[StatusIds.StatusCode]
        BAD_REQUEST: _ClassVar[StatusIds.StatusCode]
        UNAUTHORIZED: _ClassVar[StatusIds.StatusCode]
        INTERNAL_ERROR: _ClassVar[StatusIds.StatusCode]
        ABORTED: _ClassVar[StatusIds.StatusCode]
        UNAVAILABLE: _ClassVar[StatusIds.StatusCode]
        OVERLOADED: _ClassVar[StatusIds.StatusCode]
        SCHEME_ERROR: _ClassVar[StatusIds.StatusCode]
        GENERIC_ERROR: _ClassVar[StatusIds.StatusCode]
        TIMEOUT: _ClassVar[StatusIds.StatusCode]
        BAD_SESSION: _ClassVar[StatusIds.StatusCode]
        PRECONDITION_FAILED: _ClassVar[StatusIds.StatusCode]
        ALREADY_EXISTS: _ClassVar[StatusIds.StatusCode]
        NOT_FOUND: _ClassVar[StatusIds.StatusCode]
        SESSION_EXPIRED: _ClassVar[StatusIds.StatusCode]
        CANCELLED: _ClassVar[StatusIds.StatusCode]
        UNDETERMINED: _ClassVar[StatusIds.StatusCode]
        UNSUPPORTED: _ClassVar[StatusIds.StatusCode]
        SESSION_BUSY: _ClassVar[StatusIds.StatusCode]
        EXTERNAL_ERROR: _ClassVar[StatusIds.StatusCode]
    STATUS_CODE_UNSPECIFIED: StatusIds.StatusCode
    SUCCESS: StatusIds.StatusCode
    BAD_REQUEST: StatusIds.StatusCode
    UNAUTHORIZED: StatusIds.StatusCode
    INTERNAL_ERROR: StatusIds.StatusCode
    ABORTED: StatusIds.StatusCode
    UNAVAILABLE: StatusIds.StatusCode
    OVERLOADED: StatusIds.StatusCode
    SCHEME_ERROR: StatusIds.StatusCode
    GENERIC_ERROR: StatusIds.StatusCode
    TIMEOUT: StatusIds.StatusCode
    BAD_SESSION: StatusIds.StatusCode
    PRECONDITION_FAILED: StatusIds.StatusCode
    ALREADY_EXISTS: StatusIds.StatusCode
    NOT_FOUND: StatusIds.StatusCode
    SESSION_EXPIRED: StatusIds.StatusCode
    CANCELLED: StatusIds.StatusCode
    UNDETERMINED: StatusIds.StatusCode
    UNSUPPORTED: StatusIds.StatusCode
    SESSION_BUSY: StatusIds.StatusCode
    EXTERNAL_ERROR: StatusIds.StatusCode
    def __init__(self) -> None: ...
