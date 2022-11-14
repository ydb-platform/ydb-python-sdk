from google.protobuf import empty_pb2 as _empty_pb2
from protos import ydb_operation_pb2 as _ydb_operation_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ClusterInfo(_message.Message):
    __slots__ = ["available", "endpoint", "name"]
    AVAILABLE_FIELD_NUMBER: _ClassVar[int]
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    available: bool
    endpoint: str
    name: str
    def __init__(self, endpoint: _Optional[str] = ..., name: _Optional[str] = ..., available: bool = ...) -> None: ...

class DiscoverClustersRequest(_message.Message):
    __slots__ = ["minimal_version", "operation_params", "read_sessions", "write_sessions"]
    MINIMAL_VERSION_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    READ_SESSIONS_FIELD_NUMBER: _ClassVar[int]
    WRITE_SESSIONS_FIELD_NUMBER: _ClassVar[int]
    minimal_version: int
    operation_params: _ydb_operation_pb2.OperationParams
    read_sessions: _containers.RepeatedCompositeFieldContainer[ReadSessionParams]
    write_sessions: _containers.RepeatedCompositeFieldContainer[WriteSessionParams]
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., write_sessions: _Optional[_Iterable[_Union[WriteSessionParams, _Mapping]]] = ..., read_sessions: _Optional[_Iterable[_Union[ReadSessionParams, _Mapping]]] = ..., minimal_version: _Optional[int] = ...) -> None: ...

class DiscoverClustersResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DiscoverClustersResult(_message.Message):
    __slots__ = ["read_sessions_clusters", "version", "write_sessions_clusters"]
    READ_SESSIONS_CLUSTERS_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    WRITE_SESSIONS_CLUSTERS_FIELD_NUMBER: _ClassVar[int]
    read_sessions_clusters: _containers.RepeatedCompositeFieldContainer[ReadSessionClusters]
    version: int
    write_sessions_clusters: _containers.RepeatedCompositeFieldContainer[WriteSessionClusters]
    def __init__(self, write_sessions_clusters: _Optional[_Iterable[_Union[WriteSessionClusters, _Mapping]]] = ..., read_sessions_clusters: _Optional[_Iterable[_Union[ReadSessionClusters, _Mapping]]] = ..., version: _Optional[int] = ...) -> None: ...

class ReadSessionClusters(_message.Message):
    __slots__ = ["clusters"]
    CLUSTERS_FIELD_NUMBER: _ClassVar[int]
    clusters: _containers.RepeatedCompositeFieldContainer[ClusterInfo]
    def __init__(self, clusters: _Optional[_Iterable[_Union[ClusterInfo, _Mapping]]] = ...) -> None: ...

class ReadSessionParams(_message.Message):
    __slots__ = ["all_original", "mirror_to_cluster", "topic"]
    ALL_ORIGINAL_FIELD_NUMBER: _ClassVar[int]
    MIRROR_TO_CLUSTER_FIELD_NUMBER: _ClassVar[int]
    TOPIC_FIELD_NUMBER: _ClassVar[int]
    all_original: _empty_pb2.Empty
    mirror_to_cluster: str
    topic: str
    def __init__(self, topic: _Optional[str] = ..., mirror_to_cluster: _Optional[str] = ..., all_original: _Optional[_Union[_empty_pb2.Empty, _Mapping]] = ...) -> None: ...

class WriteSessionClusters(_message.Message):
    __slots__ = ["clusters", "primary_cluster_selection_reason"]
    class SelectionReason(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    CLIENT_LOCATION: WriteSessionClusters.SelectionReason
    CLIENT_PREFERENCE: WriteSessionClusters.SelectionReason
    CLUSTERS_FIELD_NUMBER: _ClassVar[int]
    CONSISTENT_DISTRIBUTION: WriteSessionClusters.SelectionReason
    PRIMARY_CLUSTER_SELECTION_REASON_FIELD_NUMBER: _ClassVar[int]
    SELECTION_REASON_UNSPECIFIED: WriteSessionClusters.SelectionReason
    clusters: _containers.RepeatedCompositeFieldContainer[ClusterInfo]
    primary_cluster_selection_reason: WriteSessionClusters.SelectionReason
    def __init__(self, clusters: _Optional[_Iterable[_Union[ClusterInfo, _Mapping]]] = ..., primary_cluster_selection_reason: _Optional[_Union[WriteSessionClusters.SelectionReason, str]] = ...) -> None: ...

class WriteSessionParams(_message.Message):
    __slots__ = ["partition_group", "preferred_cluster_name", "source_id", "topic"]
    PARTITION_GROUP_FIELD_NUMBER: _ClassVar[int]
    PREFERRED_CLUSTER_NAME_FIELD_NUMBER: _ClassVar[int]
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    TOPIC_FIELD_NUMBER: _ClassVar[int]
    partition_group: int
    preferred_cluster_name: str
    source_id: bytes
    topic: str
    def __init__(self, topic: _Optional[str] = ..., source_id: _Optional[bytes] = ..., partition_group: _Optional[int] = ..., preferred_cluster_name: _Optional[str] = ...) -> None: ...
