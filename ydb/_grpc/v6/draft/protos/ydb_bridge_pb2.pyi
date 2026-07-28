from protos.annotations import validation_pb2 as _validation_pb2
from protos import ydb_bridge_common_pb2 as _ydb_bridge_common_pb2
from protos import ydb_operation_pb2 as _ydb_operation_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetClusterStateRequest(_message.Message):
    __slots__ = ("operation_params",)
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class GetClusterStateResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class GetClusterStateResult(_message.Message):
    __slots__ = ("pile_states", "generation")
    PILE_STATES_FIELD_NUMBER: _ClassVar[int]
    GENERATION_FIELD_NUMBER: _ClassVar[int]
    pile_states: _containers.RepeatedCompositeFieldContainer[_ydb_bridge_common_pb2.PileState]
    generation: int
    def __init__(self, pile_states: _Optional[_Iterable[_Union[_ydb_bridge_common_pb2.PileState, _Mapping]]] = ..., generation: _Optional[int] = ...) -> None: ...

class UpdateClusterStateRequest(_message.Message):
    __slots__ = ("operation_params", "updates", "quorum_piles")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    UPDATES_FIELD_NUMBER: _ClassVar[int]
    QUORUM_PILES_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    updates: _containers.RepeatedCompositeFieldContainer[_ydb_bridge_common_pb2.PileState]
    quorum_piles: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., updates: _Optional[_Iterable[_Union[_ydb_bridge_common_pb2.PileState, _Mapping]]] = ..., quorum_piles: _Optional[_Iterable[str]] = ...) -> None: ...

class UpdateClusterStateResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class UpdateClusterStateResult(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class BridgeHistoryEvent(_message.Message):
    __slots__ = ("timestamp", "request_id", "generation_uuid", "primary_pile", "pile_name", "event", "from_state", "to_state", "initiator")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    GENERATION_UUID_FIELD_NUMBER: _ClassVar[int]
    PRIMARY_PILE_FIELD_NUMBER: _ClassVar[int]
    PILE_NAME_FIELD_NUMBER: _ClassVar[int]
    EVENT_FIELD_NUMBER: _ClassVar[int]
    FROM_STATE_FIELD_NUMBER: _ClassVar[int]
    TO_STATE_FIELD_NUMBER: _ClassVar[int]
    INITIATOR_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    request_id: str
    generation_uuid: str
    primary_pile: str
    pile_name: str
    event: str
    from_state: _ydb_bridge_common_pb2.PileState.State
    to_state: _ydb_bridge_common_pb2.PileState.State
    initiator: str
    def __init__(self, timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., request_id: _Optional[str] = ..., generation_uuid: _Optional[str] = ..., primary_pile: _Optional[str] = ..., pile_name: _Optional[str] = ..., event: _Optional[str] = ..., from_state: _Optional[_Union[_ydb_bridge_common_pb2.PileState.State, str]] = ..., to_state: _Optional[_Union[_ydb_bridge_common_pb2.PileState.State, str]] = ..., initiator: _Optional[str] = ...) -> None: ...

class GetClusterHistoryRequest(_message.Message):
    __slots__ = ("operation_params", "limit", "page_token")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    limit: int
    page_token: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., limit: _Optional[int] = ..., page_token: _Optional[str] = ...) -> None: ...

class GetClusterHistoryResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class GetClusterHistoryResult(_message.Message):
    __slots__ = ("events", "next_page_token")
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    events: _containers.RepeatedCompositeFieldContainer[BridgeHistoryEvent]
    next_page_token: str
    def __init__(self, events: _Optional[_Iterable[_Union[BridgeHistoryEvent, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...
