from protos import ydb_status_codes_pb2 as _ydb_status_codes_pb2
from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

AVAILABILITY_MODE_FORCE: AvailabilityMode
AVAILABILITY_MODE_SMART: AvailabilityMode
AVAILABILITY_MODE_STRONG: AvailabilityMode
AVAILABILITY_MODE_UNSPECIFIED: AvailabilityMode
AVAILABILITY_MODE_WEAK: AvailabilityMode
DESCRIPTOR: _descriptor.FileDescriptor
ITEM_STATE_DOWN: ItemState
ITEM_STATE_LOCKED: ItemState
ITEM_STATE_RESTART: ItemState
ITEM_STATE_UNSPECIFIED: ItemState
ITEM_STATE_UP: ItemState

class Action(_message.Message):
    __slots__ = ["lock_action", "set_maintainance_mode_action"]
    LOCK_ACTION_FIELD_NUMBER: _ClassVar[int]
    SET_MAINTAINANCE_MODE_ACTION_FIELD_NUMBER: _ClassVar[int]
    lock_action: LockAction
    set_maintainance_mode_action: SetMaintenanceModeAction
    def __init__(self, lock_action: _Optional[_Union[LockAction, _Mapping]] = ..., set_maintainance_mode_action: _Optional[_Union[SetMaintenanceModeAction, _Mapping]] = ...) -> None: ...

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
    __slots__ = ["host_name", "node_id", "pdisk_id"]
    class PDiskId(_message.Message):
        __slots__ = ["node_id", "pdisk_id"]
        NODE_ID_FIELD_NUMBER: _ClassVar[int]
        PDISK_ID_FIELD_NUMBER: _ClassVar[int]
        node_id: int
        pdisk_id: int
        def __init__(self, node_id: _Optional[int] = ..., pdisk_id: _Optional[int] = ...) -> None: ...
    HOST_NAME_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    PDISK_ID_FIELD_NUMBER: _ClassVar[int]
    host_name: str
    node_id: int
    pdisk_id: ActionScope.PDiskId
    def __init__(self, pdisk_id: _Optional[_Union[ActionScope.PDiskId, _Mapping]] = ..., node_id: _Optional[int] = ..., host_name: _Optional[str] = ...) -> None: ...

class ActionState(_message.Message):
    __slots__ = ["action", "action_uid", "deadline", "reason", "state_timestamp", "status"]
    class ActionReason(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    class ActionStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    ACTION_FIELD_NUMBER: _ClassVar[int]
    ACTION_REASON_DISABLED_NODES_LIMIT_RICHED: ActionState.ActionReason
    ACTION_REASON_OK: ActionState.ActionReason
    ACTION_REASON_STATE_STORAGE_BROKEN: ActionState.ActionReason
    ACTION_REASON_STORAGE_GROUP_BROKEN: ActionState.ActionReason
    ACTION_REASON_TENANT_DISABLED_NODES_LIMIT_RICHED: ActionState.ActionReason
    ACTION_REASON_TOO_MANY_UNAVAILABLE_STATE_STORAGE_RINGS: ActionState.ActionReason
    ACTION_REASON_TOO_MANY_UNAVAILABLE_VDISKS: ActionState.ActionReason
    ACTION_REASON_UNSPECIFIED: ActionState.ActionReason
    ACTION_REASON_WRONG_REQUEST: ActionState.ActionReason
    ACTION_STATUS_CREATED: ActionState.ActionStatus
    ACTION_STATUS_FINISHED_BY_USER: ActionState.ActionStatus
    ACTION_STATUS_PENDING: ActionState.ActionStatus
    ACTION_STATUS_PERMIT_GRANDED: ActionState.ActionStatus
    ACTION_STATUS_TIMEOUT_EXPIRED: ActionState.ActionStatus
    ACTION_STATUS_UNSPECIFIED: ActionState.ActionStatus
    ACTION_STATUS_WAITING: ActionState.ActionStatus
    ACTION_UID_FIELD_NUMBER: _ClassVar[int]
    DEADLINE_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    STATE_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    action: Action
    action_uid: ActionUid
    deadline: _timestamp_pb2.Timestamp
    reason: ActionState.ActionReason
    state_timestamp: _timestamp_pb2.Timestamp
    status: ActionState.ActionStatus
    def __init__(self, action: _Optional[_Union[Action, _Mapping]] = ..., status: _Optional[_Union[ActionState.ActionStatus, str]] = ..., action_uid: _Optional[_Union[ActionUid, _Mapping]] = ..., reason: _Optional[_Union[ActionState.ActionReason, str]] = ..., state_timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., deadline: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ActionUid(_message.Message):
    __slots__ = ["action_id", "group_id", "task_uid"]
    ACTION_ID_FIELD_NUMBER: _ClassVar[int]
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    TASK_UID_FIELD_NUMBER: _ClassVar[int]
    action_id: int
    group_id: int
    task_uid: str
    def __init__(self, task_uid: _Optional[str] = ..., group_id: _Optional[int] = ..., action_id: _Optional[int] = ...) -> None: ...

class CreateMaintenanceTaskRequest(_message.Message):
    __slots__ = ["action_groups", "task_options", "task_timeout"]
    ACTION_GROUPS_FIELD_NUMBER: _ClassVar[int]
    TASK_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TASK_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    action_groups: _containers.RepeatedCompositeFieldContainer[ActionGroup]
    task_options: MaintenanceTaskOptions
    task_timeout: _duration_pb2.Duration
    def __init__(self, task_options: _Optional[_Union[MaintenanceTaskOptions, _Mapping]] = ..., action_groups: _Optional[_Iterable[_Union[ActionGroup, _Mapping]]] = ..., task_timeout: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ...) -> None: ...

class DropMaintenanceTaskRequest(_message.Message):
    __slots__ = ["task_uid"]
    TASK_UID_FIELD_NUMBER: _ClassVar[int]
    task_uid: str
    def __init__(self, task_uid: _Optional[str] = ...) -> None: ...

class GetMaintenanceTaskRequest(_message.Message):
    __slots__ = ["task_uid"]
    TASK_UID_FIELD_NUMBER: _ClassVar[int]
    task_uid: str
    def __init__(self, task_uid: _Optional[str] = ...) -> None: ...

class GetMaintenanceTaskResponse(_message.Message):
    __slots__ = ["actions_group_states", "task_deadline", "task_options"]
    ACTIONS_GROUP_STATES_FIELD_NUMBER: _ClassVar[int]
    TASK_DEADLINE_FIELD_NUMBER: _ClassVar[int]
    TASK_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    actions_group_states: _containers.RepeatedCompositeFieldContainer[ActionGroupStates]
    task_deadline: _timestamp_pb2.Timestamp
    task_options: MaintenanceTaskOptions
    def __init__(self, task_options: _Optional[_Union[MaintenanceTaskOptions, _Mapping]] = ..., actions_group_states: _Optional[_Iterable[_Union[ActionGroupStates, _Mapping]]] = ..., task_deadline: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class GetReadableActionReasonRequest(_message.Message):
    __slots__ = ["action_ids"]
    ACTION_IDS_FIELD_NUMBER: _ClassVar[int]
    action_ids: _containers.RepeatedCompositeFieldContainer[ActionUid]
    def __init__(self, action_ids: _Optional[_Iterable[_Union[ActionUid, _Mapping]]] = ...) -> None: ...

class GetReadableActionReasonResponse(_message.Message):
    __slots__ = ["reasons"]
    class Reason(_message.Message):
        __slots__ = ["Reason", "action_state"]
        ACTION_STATE_FIELD_NUMBER: _ClassVar[int]
        REASON_FIELD_NUMBER: _ClassVar[int]
        Reason: str
        action_state: ActionState
        def __init__(self, action_state: _Optional[_Union[ActionState, _Mapping]] = ..., Reason: _Optional[str] = ...) -> None: ...
    REASONS_FIELD_NUMBER: _ClassVar[int]
    reasons: _containers.RepeatedCompositeFieldContainer[GetReadableActionReasonResponse.Reason]
    def __init__(self, reasons: _Optional[_Iterable[_Union[GetReadableActionReasonResponse.Reason, _Mapping]]] = ...) -> None: ...

class ListClusterNodesRequest(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class ListClusterNodesResponse(_message.Message):
    __slots__ = ["nodes"]
    class Node(_message.Message):
        __slots__ = ["data_center", "fqdn", "interconnect_port", "is_dynamic", "is_storage", "node_id", "rack", "state", "tenant"]
        DATA_CENTER_FIELD_NUMBER: _ClassVar[int]
        FQDN_FIELD_NUMBER: _ClassVar[int]
        INTERCONNECT_PORT_FIELD_NUMBER: _ClassVar[int]
        IS_DYNAMIC_FIELD_NUMBER: _ClassVar[int]
        IS_STORAGE_FIELD_NUMBER: _ClassVar[int]
        NODE_ID_FIELD_NUMBER: _ClassVar[int]
        RACK_FIELD_NUMBER: _ClassVar[int]
        STATE_FIELD_NUMBER: _ClassVar[int]
        TENANT_FIELD_NUMBER: _ClassVar[int]
        data_center: str
        fqdn: str
        interconnect_port: int
        is_dynamic: bool
        is_storage: bool
        node_id: int
        rack: str
        state: ItemState
        tenant: str
        def __init__(self, node_id: _Optional[int] = ..., data_center: _Optional[str] = ..., rack: _Optional[str] = ..., fqdn: _Optional[str] = ..., interconnect_port: _Optional[int] = ..., state: _Optional[_Union[ItemState, str]] = ..., tenant: _Optional[str] = ..., is_storage: bool = ..., is_dynamic: bool = ...) -> None: ...
    NODES_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[ListClusterNodesResponse.Node]
    def __init__(self, nodes: _Optional[_Iterable[_Union[ListClusterNodesResponse.Node, _Mapping]]] = ...) -> None: ...

class ListMaintenanceTasksRequest(_message.Message):
    __slots__ = ["user"]
    USER_FIELD_NUMBER: _ClassVar[int]
    user: str
    def __init__(self, user: _Optional[str] = ...) -> None: ...

class ListMaintenanceTasksResponse(_message.Message):
    __slots__ = ["tasks_uids"]
    TASKS_UIDS_FIELD_NUMBER: _ClassVar[int]
    tasks_uids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, tasks_uids: _Optional[_Iterable[str]] = ...) -> None: ...

class ListNodesDevicesRequest(_message.Message):
    __slots__ = ["node_id"]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    node_id: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, node_id: _Optional[_Iterable[int]] = ...) -> None: ...

class ListNodesDevicesResponse(_message.Message):
    __slots__ = ["nodes_devices"]
    class Device(_message.Message):
        __slots__ = ["name", "state"]
        NAME_FIELD_NUMBER: _ClassVar[int]
        STATE_FIELD_NUMBER: _ClassVar[int]
        name: str
        state: ItemState
        def __init__(self, name: _Optional[str] = ..., state: _Optional[_Union[ItemState, str]] = ...) -> None: ...
    class NodeDevices(_message.Message):
        __slots__ = ["devices", "node_id"]
        DEVICES_FIELD_NUMBER: _ClassVar[int]
        NODE_ID_FIELD_NUMBER: _ClassVar[int]
        devices: _containers.RepeatedCompositeFieldContainer[ListNodesDevicesResponse.Device]
        node_id: int
        def __init__(self, node_id: _Optional[int] = ..., devices: _Optional[_Iterable[_Union[ListNodesDevicesResponse.Device, _Mapping]]] = ...) -> None: ...
    NODES_DEVICES_FIELD_NUMBER: _ClassVar[int]
    nodes_devices: _containers.RepeatedCompositeFieldContainer[ListNodesDevicesResponse.NodeDevices]
    def __init__(self, nodes_devices: _Optional[_Iterable[_Union[ListNodesDevicesResponse.NodeDevices, _Mapping]]] = ...) -> None: ...

class LockAction(_message.Message):
    __slots__ = ["action_scope", "duration"]
    ACTION_SCOPE_FIELD_NUMBER: _ClassVar[int]
    DURATION_FIELD_NUMBER: _ClassVar[int]
    action_scope: ActionScope
    duration: _duration_pb2.Duration
    def __init__(self, action_scope: _Optional[_Union[ActionScope, _Mapping]] = ..., duration: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ...) -> None: ...

class MaintenanceTaskOptions(_message.Message):
    __slots__ = ["availability_mode", "comment", "dry_run", "in_flight", "name", "priority", "task_uid"]
    AVAILABILITY_MODE_FIELD_NUMBER: _ClassVar[int]
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    DRY_RUN_FIELD_NUMBER: _ClassVar[int]
    IN_FLIGHT_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    TASK_UID_FIELD_NUMBER: _ClassVar[int]
    availability_mode: AvailabilityMode
    comment: str
    dry_run: bool
    in_flight: int
    name: str
    priority: int
    task_uid: str
    def __init__(self, in_flight: _Optional[int] = ..., dry_run: bool = ..., name: _Optional[str] = ..., comment: _Optional[str] = ..., availability_mode: _Optional[_Union[AvailabilityMode, str]] = ..., task_uid: _Optional[str] = ..., priority: _Optional[int] = ...) -> None: ...

class MaintenanceTaskResponse(_message.Message):
    __slots__ = ["actions_states", "deadline", "status", "task_uid"]
    ACTIONS_STATES_FIELD_NUMBER: _ClassVar[int]
    DEADLINE_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    TASK_UID_FIELD_NUMBER: _ClassVar[int]
    actions_states: _containers.RepeatedCompositeFieldContainer[ActionGroupStates]
    deadline: _timestamp_pb2.Timestamp
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    task_uid: str
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., task_uid: _Optional[str] = ..., actions_states: _Optional[_Iterable[_Union[ActionGroupStates, _Mapping]]] = ..., deadline: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ManageMaintenanceTaskResponse(_message.Message):
    __slots__ = ["status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ...) -> None: ...

class ManagePermitResponse(_message.Message):
    __slots__ = ["permit_statuses"]
    PERMIT_STATUSES_FIELD_NUMBER: _ClassVar[int]
    permit_statuses: _containers.RepeatedCompositeFieldContainer[PermitStatus]
    def __init__(self, permit_statuses: _Optional[_Iterable[_Union[PermitStatus, _Mapping]]] = ...) -> None: ...

class PermitStatus(_message.Message):
    __slots__ = ["action_uid", "status"]
    ACTION_UID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    action_uid: ActionUid
    status: _ydb_status_codes_pb2.StatusIds.StatusCode
    def __init__(self, action_uid: _Optional[_Union[ActionUid, _Mapping]] = ..., status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ...) -> None: ...

class ProlongateMaintenanceTaskRequest(_message.Message):
    __slots__ = ["new_deadline", "task_uid"]
    NEW_DEADLINE_FIELD_NUMBER: _ClassVar[int]
    TASK_UID_FIELD_NUMBER: _ClassVar[int]
    new_deadline: _timestamp_pb2.Timestamp
    task_uid: str
    def __init__(self, task_uid: _Optional[str] = ..., new_deadline: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ProlongatePermitRequest(_message.Message):
    __slots__ = ["action_durations"]
    class ActionDuration(_message.Message):
        __slots__ = ["action_uid", "new_deadline"]
        ACTION_UID_FIELD_NUMBER: _ClassVar[int]
        NEW_DEADLINE_FIELD_NUMBER: _ClassVar[int]
        action_uid: ActionUid
        new_deadline: _timestamp_pb2.Timestamp
        def __init__(self, action_uid: _Optional[_Union[ActionUid, _Mapping]] = ..., new_deadline: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
    ACTION_DURATIONS_FIELD_NUMBER: _ClassVar[int]
    action_durations: _containers.RepeatedCompositeFieldContainer[ProlongatePermitRequest.ActionDuration]
    def __init__(self, action_durations: _Optional[_Iterable[_Union[ProlongatePermitRequest.ActionDuration, _Mapping]]] = ...) -> None: ...

class RefreshMaintenanceTaskRequest(_message.Message):
    __slots__ = ["task_uid"]
    TASK_UID_FIELD_NUMBER: _ClassVar[int]
    task_uid: str
    def __init__(self, task_uid: _Optional[str] = ...) -> None: ...

class ReleasePermitRequest(_message.Message):
    __slots__ = ["action_uid"]
    ACTION_UID_FIELD_NUMBER: _ClassVar[int]
    action_uid: _containers.RepeatedCompositeFieldContainer[ActionUid]
    def __init__(self, action_uid: _Optional[_Iterable[_Union[ActionUid, _Mapping]]] = ...) -> None: ...

class SetMaintenanceModeAction(_message.Message):
    __slots__ = ["action_scope", "drain_tablets", "duration", "evict_vdisks"]
    ACTION_SCOPE_FIELD_NUMBER: _ClassVar[int]
    DRAIN_TABLETS_FIELD_NUMBER: _ClassVar[int]
    DURATION_FIELD_NUMBER: _ClassVar[int]
    EVICT_VDISKS_FIELD_NUMBER: _ClassVar[int]
    action_scope: ActionScope
    drain_tablets: bool
    duration: _duration_pb2.Duration
    evict_vdisks: bool
    def __init__(self, action_scope: _Optional[_Union[ActionScope, _Mapping]] = ..., drain_tablets: bool = ..., evict_vdisks: bool = ..., duration: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ...) -> None: ...

class AvailabilityMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class ItemState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
