from protos.annotations import validation_pb2 as _validation_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PileState(_message.Message):
    __slots__ = ("pile_name", "state")
    class State(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNSPECIFIED: _ClassVar[PileState.State]
        PRIMARY: _ClassVar[PileState.State]
        PROMOTED: _ClassVar[PileState.State]
        SYNCHRONIZED: _ClassVar[PileState.State]
        NOT_SYNCHRONIZED: _ClassVar[PileState.State]
        SUSPENDED: _ClassVar[PileState.State]
        DISCONNECTED: _ClassVar[PileState.State]
    UNSPECIFIED: PileState.State
    PRIMARY: PileState.State
    PROMOTED: PileState.State
    SYNCHRONIZED: PileState.State
    NOT_SYNCHRONIZED: PileState.State
    SUSPENDED: PileState.State
    DISCONNECTED: PileState.State
    PILE_NAME_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    pile_name: str
    state: PileState.State
    def __init__(self, pile_name: _Optional[str] = ..., state: _Optional[_Union[PileState.State, str]] = ...) -> None: ...
