from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class StatusIds(_message.Message):
    __slots__ = []
    class StatusCode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    ABORTED: StatusIds.StatusCode
    ALREADY_EXISTS: StatusIds.StatusCode
    BAD_REQUEST: StatusIds.StatusCode
    BAD_SESSION: StatusIds.StatusCode
    CANCELLED: StatusIds.StatusCode
    EXTERNAL_ERROR: StatusIds.StatusCode
    GENERIC_ERROR: StatusIds.StatusCode
    INTERNAL_ERROR: StatusIds.StatusCode
    NOT_FOUND: StatusIds.StatusCode
    OVERLOADED: StatusIds.StatusCode
    PRECONDITION_FAILED: StatusIds.StatusCode
    SCHEME_ERROR: StatusIds.StatusCode
    SESSION_BUSY: StatusIds.StatusCode
    SESSION_EXPIRED: StatusIds.StatusCode
    STATUS_CODE_UNSPECIFIED: StatusIds.StatusCode
    SUCCESS: StatusIds.StatusCode
    TIMEOUT: StatusIds.StatusCode
    UNAUTHORIZED: StatusIds.StatusCode
    UNAVAILABLE: StatusIds.StatusCode
    UNDETERMINED: StatusIds.StatusCode
    UNSUPPORTED: StatusIds.StatusCode
    def __init__(self) -> None: ...
