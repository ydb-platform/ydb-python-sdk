from protos.annotations import validation_pb2 as _validation_pb2
from protos import ydb_bridge_common_pb2 as _ydb_bridge_common_pb2
from protos import ydb_operation_pb2 as _ydb_operation_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class BridgeHistoryEvent(_message.Message):
    __slots__ = ["event", "from_state", "generation_uuid", "initiator", "pile_name", "primary_pile", "request_id", "timestamp", "to_state"]
    EVENT_FIELD_NUMBER: _ClassVar[int]
    FROM_STATE_FIELD_NUMBER: _ClassVar[int]
    GENERATION_UUID_FIELD_NUMBER: _ClassVar[int]
    INITIATOR_FIELD_NUMBER: _ClassVar[int]
    PILE_NAME_FIELD_NUMBER: _ClassVar[int]
    PRIMARY_PILE_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TO_STATE_FIELD_NUMBER: _ClassVar[int]
    event: str
    from_state: _ydb_bridge_common_pb2.PileState.State
    generation_uuid: str
    initiator: str
    pile_name: str
    primary_pile: str
    request_id: str
    timestamp: _timestamp_pb2.Timestamp
    to_state: _ydb_bridge_common_pb2.PileState.State
    def __init__(self, timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., request_id: _Optional[str] = ..., generation_uuid: _Optional[str] = ..., primary_pile: _Optional[str] = ..., pile_name: _Optional[str] = ..., event: _Optional[str] = ..., from_state: _Optional[_Union[_ydb_bridge_common_pb2.PileState.State, str]] = ..., to_state: _Optional[_Union[_ydb_bridge_common_pb2.PileState.State, str]] = ..., initiator: _Optional[str] = ...) -> None: ...

class GetClusterHistoryRequest(_message.Message):
    __slots__ = ["limit", "operation_params", "page_token"]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    limit: int
    operation_params: _ydb_operation_pb2.OperationParams
    page_token: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., limit: _Optional[int] = ..., page_token: _Optional[str] = ...) -> None: ...

class GetClusterHistoryResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class GetClusterHistoryResult(_message.Message):
    __slots__ = ["events", "next_page_token"]
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    events: _containers.RepeatedCompositeFieldContainer[BridgeHistoryEvent]
    next_page_token: str
    def __init__(self, events: _Optional[_Iterable[_Union[BridgeHistoryEvent, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class GetClusterStateRequest(_message.Message):
    __slots__ = ["operation_params"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class GetClusterStateResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class GetClusterStateResult(_message.Message):
    __slots__ = ["generation", "pile_states"]
    GENERATION_FIELD_NUMBER: _ClassVar[int]
    PILE_STATES_FIELD_NUMBER: _ClassVar[int]
    generation: int
    pile_states: _containers.RepeatedCompositeFieldContainer[_ydb_bridge_common_pb2.PileState]
    def __init__(self, pile_states: _Optional[_Iterable[_Union[_ydb_bridge_common_pb2.PileState, _Mapping]]] = ..., generation: _Optional[int] = ...) -> None: ...

class UpdateClusterStateRequest(_message.Message):
    __slots__ = ["operation_params", "quorum_piles", "updates"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    QUORUM_PILES_FIELD_NUMBER: _ClassVar[int]
    UPDATES_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    quorum_piles: _containers.RepeatedScalarFieldContainer[str]
    updates: _containers.RepeatedCompositeFieldContainer[_ydb_bridge_common_pb2.PileState]
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., updates: _Optional[_Iterable[_Union[_ydb_bridge_common_pb2.PileState, _Mapping]]] = ..., quorum_piles: _Optional[_Iterable[str]] = ...) -> None: ...

class UpdateClusterStateResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class UpdateClusterStateResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...
