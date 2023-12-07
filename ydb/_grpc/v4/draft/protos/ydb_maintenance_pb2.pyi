from protos.annotations import validation_pb2 as _validation_pb2
from protos import ydb_status_codes_pb2 as _ydb_status_codes_pb2
from protos import ydb_discovery_pb2 as _ydb_discovery_pb2
from protos import ydb_operation_pb2 as _ydb_operation_pb2
from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

AVAILABILITY_MODE_FORCE: AvailabilityMode
AVAILABILITY_MODE_STRONG: AvailabilityMode
AVAILABILITY_MODE_UNSPECIFIED: AvailabilityMode
AVAILABILITY_MODE_WEAK: AvailabilityMode
DESCRIPTOR: _descriptor.FileDescriptor
ITEM_STATE_DOWN: ItemState
ITEM_STATE_MAINTENANCE: ItemState
ITEM_STATE_UNSPECIFIED: ItemState
ITEM_STATE_UP: ItemState

class Action(_message.Message):
    __slots__ = ["lock_action"]
    LOCK_ACTION_FIELD_NUMBER: _ClassVar[int]
    lock_action: LockAction
    def __init__(self, lock_action: _Optional[_Union[LockAction, _Mapping]] = ...) -> None: ...

class ActionGroup(_message.Message):
    __slots__ = ["actions"]
    ACTIONS_FIELD_NUMBER: _ClassVar[int]
    actions: _containers.RepeatedCompositeFieldContainer[Action]
    def __init__(self, actions: _Optional[_Iterable[_Union[Action, _Mapping]]] = ...) -> None: ...

class ActionGroupStates(_message.Message):
    __slots__ = ["action_states"]
    ACTION_STATES_FIELD_NUMBER: _ClassVar[int]
    action_states: _containers.RepeatedCompositeFieldContainer[ActionState]
    def __init__(self, action_states: _Optional[_Iterable[_Union[ActionState, _Mapping]]] = ...) -> None: ...

class ActionScope(_message.Message):
    __slots__ = ["host", "node_id"]
    HOST_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    host: str
    node_id: int
    def __init__(self, node_id: _Optional[int] = ..., host: _Optional[str] = ...) -> None: ...

class ActionState(_message.Message):
    __slots__ = ["action", "action_uid", "deadline", "reason", "status"]
    class ActionReason(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    class ActionStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    ACTION_FIELD_NUMBER: _ClassVar[int]
    ACTION_REASON_DISABLED_NODES_LIMIT_REACHED: ActionState.ActionReason
    ACTION_REASON_OK: ActionState.ActionReason
    ACTION_REASON_SYS_TABLETS_NODE_LIMIT_REACHED: ActionState.ActionReason
    ACTION_REASON_TENANT_DISABLED_NODES_LIMIT_REACHED: ActionState.ActionReason
    ACTION_REASON_TOO_MANY_UNAVAILABLE_STATE_STORAGE_RINGS: ActionState.ActionReason
    ACTION_REASON_TOO_MANY_UNAVAILABLE_VDISKS: ActionState.ActionReason
    ACTION_REASON_UNSPECIFIED: ActionState.ActionReason
    ACTION_REASON_WRONG_REQUEST: ActionState.ActionReason
    ACTION_STATUS_PENDING: ActionState.ActionStatus
    ACTION_STATUS_PERFORMED: ActionState.ActionStatus
    ACTION_STATUS_UNSPECIFIED: ActionState.ActionStatus
    ACTION_UID_FIELD_NUMBER: _ClassVar[int]
    DEADLINE_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    action: Action
    action_uid: ActionUid
    deadline: _timestamp_pb2.Timestamp
    reason: ActionState.ActionReason
    status: ActionState.ActionStatus
    def __init__(self, action: _Optional[_Union[Action, _Mapping]] = ..., action_uid: _Optional[_Union[ActionUid, _Mapping]] = ..., status: _Optional[_Union[ActionState.ActionStatus, str]] = ..., reason: _Optional[_Union[ActionState.ActionReason, str]] = ..., deadline: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ActionUid(_message.Message):
    __slots__ = ["action_id", "group_id", "task_uid"]
    ACTION_ID_FIELD_NUMBER: _ClassVar[int]
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    TASK_UID_FIELD_NUMBER: _ClassVar[int]
    action_id: str
    group_id: str
    task_uid: str
    def __init__(self, task_uid: _Optional[str] = ..., group_id: _Optional[str] = ..., action_id: _Optional[str] = ...) -> None: ...

class CompleteActionRequest(_message.Message):
    __slots__ = ["action_uids", "operation_params"]
    ACTION_UIDS_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    action_uids: _containers.RepeatedCompositeFieldContainer[ActionUid]
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., action_uids: _Optional[_Iterable[_Union[ActionUid, _Mapping]]] = ...) -> None: ...

class CreateMaintenanceTaskRequest(_message.Message):
    __slots__ = ["action_groups", "operation_params", "task_options"]
    ACTION_GROUPS_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    TASK_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    action_groups: _containers.RepeatedCompositeFieldContainer[ActionGroup]
    operation_params: _ydb_operation_pb2.OperationParams
    task_options: MaintenanceTaskOptions
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., task_options: _Optional[_Union[MaintenanceTaskOptions, _Mapping]] = ..., action_groups: _Optional[_Iterable[_Union[ActionGroup, _Mapping]]] = ...) -> None: ...

class DropMaintenanceTaskRequest(_message.Message):
    __slots__ = ["operation_params", "task_uid"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    TASK_UID_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    task_uid: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., task_uid: _Optional[str] = ...) -> None: ...

class GetMaintenanceTaskRequest(_message.Message):
    __slots__ = ["operation_params", "task_uid"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    TASK_UID_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    task_uid: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., task_uid: _Optional[str] = ...) -> None: ...

class GetMaintenanceTaskResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class GetMaintenanceTaskResult(_message.Message):
    __slots__ = ["action_group_states", "task_options"]
    ACTION_GROUP_STATES_FIELD_NUMBER: _ClassVar[int]
    TASK_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    action_group_states: _containers.RepeatedCompositeFieldContainer[ActionGroupStates]
    task_options: MaintenanceTaskOptions
    def __init__(self, task_options: _Optional[_Union[MaintenanceTaskOptions, _Mapping]] = ..., action_group_states: _Optional[_Iterable[_Union[ActionGroupStates, _Mapping]]] = ...) -> None: ...

class ListClusterNodesRequest(_message.Message):
    __slots__ = ["operation_params"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ...) -> None: ...

class ListClusterNodesResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListClusterNodesResult(_message.Message):
    __slots__ = ["nodes"]
    NODES_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[Node]
    def __init__(self, nodes: _Optional[_Iterable[_Union[Node, _Mapping]]] = ...) -> None: ...

class ListMaintenanceTasksRequest(_message.Message):
    __slots__ = ["operation_params", "user"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    user: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., user: _Optional[str] = ...) -> None: ...

class ListMaintenanceTasksResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListMaintenanceTasksResult(_message.Message):
    __slots__ = ["tasks_uids"]
    TASKS_UIDS_FIELD_NUMBER: _ClassVar[int]
    tasks_uids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, tasks_uids: _Optional[_Iterable[str]] = ...) -> None: ...

class LockAction(_message.Message):
    __slots__ = ["duration", "scope"]
    DURATION_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    duration: _duration_pb2.Duration
    scope: ActionScope
    def __init__(self, scope: _Optional[_Union[ActionScope, _Mapping]] = ..., duration: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ...) -> None: ...

class MaintenanceTaskOptions(_message.Message):
    __slots__ = ["availability_mode", "description", "dry_run", "task_uid"]
    AVAILABILITY_MODE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    DRY_RUN_FIELD_NUMBER: _ClassVar[int]
    TASK_UID_FIELD_NUMBER: _ClassVar[int]
    availability_mode: AvailabilityMode
    description: str
    dry_run: bool
    task_uid: str
    def __init__(self, task_uid: _Optional[str] = ..., description: _Optional[str] = ..., availability_mode: _Optional[_Union[AvailabilityMode, str]] = ..., dry_run: bool = ...) -> None: ...

class MaintenanceTaskResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class MaintenanceTaskResult(_message.Message):
    __slots__ = ["action_group_states", "retry_after", "task_uid"]
    ACTION_GROUP_STATES_FIELD_NUMBER: _ClassVar[int]
    RETRY_AFTER_FIELD_NUMBER: _ClassVar[int]
    TASK_UID_FIELD_NUMBER: _ClassVar[int]
    action_group_states: _containers.RepeatedCompositeFieldContainer[ActionGroupStates]
    retry_after: _timestamp_pb2.Timestamp
    task_uid: str
    def __init__(self, task_uid: _Optional[str] = ..., action_group_states: _Optional[_Iterable[_Union[ActionGroupStates, _Mapping]]] = ..., retry_after: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ManageActionResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ManageActionResult(_message.Message):
    __slots__ = ["action_statuses"]
    class Status(_message.Message):
        __slots__ = ["action_uid", "status"]
        ACTION_UID_FIELD_NUMBER: _ClassVar[int]
        STATUS_FIELD_NUMBER: _ClassVar[int]
        action_uid: ActionUid
        status: _ydb_status_codes_pb2.StatusIds.StatusCode
        def __init__(self, action_uid: _Optional[_Union[ActionUid, _Mapping]] = ..., status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ...) -> None: ...
    ACTION_STATUSES_FIELD_NUMBER: _ClassVar[int]
    action_statuses: _containers.RepeatedCompositeFieldContainer[ManageActionResult.Status]
    def __init__(self, action_statuses: _Optional[_Iterable[_Union[ManageActionResult.Status, _Mapping]]] = ...) -> None: ...

class ManageMaintenanceTaskResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class Node(_message.Message):
    __slots__ = ["dynamic", "host", "location", "node_id", "port", "state", "storage"]
    class DynamicNode(_message.Message):
        __slots__ = ["tenant"]
        TENANT_FIELD_NUMBER: _ClassVar[int]
        tenant: str
        def __init__(self, tenant: _Optional[str] = ...) -> None: ...
    class StorageNode(_message.Message):
        __slots__ = []
        def __init__(self) -> None: ...
    DYNAMIC_FIELD_NUMBER: _ClassVar[int]
    HOST_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    STORAGE_FIELD_NUMBER: _ClassVar[int]
    dynamic: Node.DynamicNode
    host: str
    location: _ydb_discovery_pb2.NodeLocation
    node_id: int
    port: int
    state: ItemState
    storage: Node.StorageNode
    def __init__(self, node_id: _Optional[int] = ..., host: _Optional[str] = ..., port: _Optional[int] = ..., location: _Optional[_Union[_ydb_discovery_pb2.NodeLocation, _Mapping]] = ..., state: _Optional[_Union[ItemState, str]] = ..., storage: _Optional[_Union[Node.StorageNode, _Mapping]] = ..., dynamic: _Optional[_Union[Node.DynamicNode, _Mapping]] = ...) -> None: ...

class RefreshMaintenanceTaskRequest(_message.Message):
    __slots__ = ["operation_params", "task_uid"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    TASK_UID_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    task_uid: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., task_uid: _Optional[str] = ...) -> None: ...

class ItemState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class AvailabilityMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
