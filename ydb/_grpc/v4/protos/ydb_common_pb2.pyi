from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class CostInfo(_message.Message):
    __slots__ = ["consumed_units"]
    CONSUMED_UNITS_FIELD_NUMBER: _ClassVar[int]
    consumed_units: float
    def __init__(self, consumed_units: _Optional[float] = ...) -> None: ...

class FeatureFlag(_message.Message):
    __slots__ = []
    class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    DISABLED: FeatureFlag.Status
    ENABLED: FeatureFlag.Status
    STATUS_UNSPECIFIED: FeatureFlag.Status
    def __init__(self) -> None: ...

class QuotaExceeded(_message.Message):
    __slots__ = ["disk"]
    DISK_FIELD_NUMBER: _ClassVar[int]
    disk: bool
    def __init__(self, disk: bool = ...) -> None: ...

class VirtualTimestamp(_message.Message):
    __slots__ = ["plan_step", "tx_id"]
    PLAN_STEP_FIELD_NUMBER: _ClassVar[int]
    TX_ID_FIELD_NUMBER: _ClassVar[int]
    plan_step: int
    tx_id: int
    def __init__(self, plan_step: _Optional[int] = ..., tx_id: _Optional[int] = ...) -> None: ...
