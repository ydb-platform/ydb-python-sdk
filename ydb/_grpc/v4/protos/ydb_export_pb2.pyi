from protos.annotations import validation_pb2 as _validation_pb2
from protos import ydb_operation_pb2 as _ydb_operation_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ExportItemProgress(_message.Message):
    __slots__ = ["end_time", "parts_completed", "parts_total", "start_time"]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    PARTS_COMPLETED_FIELD_NUMBER: _ClassVar[int]
    PARTS_TOTAL_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    end_time: _timestamp_pb2.Timestamp
    parts_completed: int
    parts_total: int
    start_time: _timestamp_pb2.Timestamp
    def __init__(self, parts_total: _Optional[int] = ..., parts_completed: _Optional[int] = ..., start_time: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., end_time: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ExportProgress(_message.Message):
    __slots__ = []
    class Progress(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    PROGRESS_CANCELLATION: ExportProgress.Progress
    PROGRESS_CANCELLED: ExportProgress.Progress
    PROGRESS_DONE: ExportProgress.Progress
    PROGRESS_PREPARING: ExportProgress.Progress
    PROGRESS_TRANSFER_DATA: ExportProgress.Progress
    PROGRESS_UNSPECIFIED: ExportProgress.Progress
    def __init__(self) -> None: ...

class ExportToS3Metadata(_message.Message):
    __slots__ = ["items_progress", "progress", "settings"]
    ITEMS_PROGRESS_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    items_progress: _containers.RepeatedCompositeFieldContainer[ExportItemProgress]
    progress: ExportProgress.Progress
    settings: ExportToS3Settings
    def __init__(self, settings: _Optional[_Union[ExportToS3Settings, _Mapping]] = ..., progress: _Optional[_Union[ExportProgress.Progress, str]] = ..., items_progress: _Optional[_Iterable[_Union[ExportItemProgress, _Mapping]]] = ...) -> None: ...

class ExportToS3Request(_message.Message):
    __slots__ = ["operation_params", "settings"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    settings: ExportToS3Settings
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., settings: _Optional[_Union[ExportToS3Settings, _Mapping]] = ...) -> None: ...

class ExportToS3Response(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ExportToS3Result(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class ExportToS3Settings(_message.Message):
    __slots__ = ["access_key", "bucket", "compression", "description", "endpoint", "items", "number_of_retries", "region", "scheme", "secret_key", "storage_class"]
    class Scheme(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    class StorageClass(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    class Item(_message.Message):
        __slots__ = ["destination_prefix", "source_path"]
        DESTINATION_PREFIX_FIELD_NUMBER: _ClassVar[int]
        SOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
        destination_prefix: str
        source_path: str
        def __init__(self, source_path: _Optional[str] = ..., destination_prefix: _Optional[str] = ...) -> None: ...
    ACCESS_KEY_FIELD_NUMBER: _ClassVar[int]
    BUCKET_FIELD_NUMBER: _ClassVar[int]
    COMPRESSION_FIELD_NUMBER: _ClassVar[int]
    DEEP_ARCHIVE: ExportToS3Settings.StorageClass
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    GLACIER: ExportToS3Settings.StorageClass
    HTTP: ExportToS3Settings.Scheme
    HTTPS: ExportToS3Settings.Scheme
    INTELLIGENT_TIERING: ExportToS3Settings.StorageClass
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    NUMBER_OF_RETRIES_FIELD_NUMBER: _ClassVar[int]
    ONEZONE_IA: ExportToS3Settings.StorageClass
    OUTPOSTS: ExportToS3Settings.StorageClass
    REDUCED_REDUNDANCY: ExportToS3Settings.StorageClass
    REGION_FIELD_NUMBER: _ClassVar[int]
    SCHEME_FIELD_NUMBER: _ClassVar[int]
    SECRET_KEY_FIELD_NUMBER: _ClassVar[int]
    STANDARD: ExportToS3Settings.StorageClass
    STANDARD_IA: ExportToS3Settings.StorageClass
    STORAGE_CLASS_FIELD_NUMBER: _ClassVar[int]
    STORAGE_CLASS_UNSPECIFIED: ExportToS3Settings.StorageClass
    UNSPECIFIED: ExportToS3Settings.Scheme
    access_key: str
    bucket: str
    compression: str
    description: str
    endpoint: str
    items: _containers.RepeatedCompositeFieldContainer[ExportToS3Settings.Item]
    number_of_retries: int
    region: str
    scheme: ExportToS3Settings.Scheme
    secret_key: str
    storage_class: ExportToS3Settings.StorageClass
    def __init__(self, endpoint: _Optional[str] = ..., scheme: _Optional[_Union[ExportToS3Settings.Scheme, str]] = ..., bucket: _Optional[str] = ..., access_key: _Optional[str] = ..., secret_key: _Optional[str] = ..., items: _Optional[_Iterable[_Union[ExportToS3Settings.Item, _Mapping]]] = ..., description: _Optional[str] = ..., number_of_retries: _Optional[int] = ..., storage_class: _Optional[_Union[ExportToS3Settings.StorageClass, str]] = ..., compression: _Optional[str] = ..., region: _Optional[str] = ...) -> None: ...

class ExportToYtMetadata(_message.Message):
    __slots__ = ["items_progress", "progress", "settings"]
    ITEMS_PROGRESS_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    items_progress: _containers.RepeatedCompositeFieldContainer[ExportItemProgress]
    progress: ExportProgress.Progress
    settings: ExportToYtSettings
    def __init__(self, settings: _Optional[_Union[ExportToYtSettings, _Mapping]] = ..., progress: _Optional[_Union[ExportProgress.Progress, str]] = ..., items_progress: _Optional[_Iterable[_Union[ExportItemProgress, _Mapping]]] = ...) -> None: ...

class ExportToYtRequest(_message.Message):
    __slots__ = ["operation_params", "settings"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    settings: ExportToYtSettings
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., settings: _Optional[_Union[ExportToYtSettings, _Mapping]] = ...) -> None: ...

class ExportToYtResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ExportToYtResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class ExportToYtSettings(_message.Message):
    __slots__ = ["description", "host", "items", "number_of_retries", "port", "token", "use_type_v3"]
    class Item(_message.Message):
        __slots__ = ["destination_path", "source_path"]
        DESTINATION_PATH_FIELD_NUMBER: _ClassVar[int]
        SOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
        destination_path: str
        source_path: str
        def __init__(self, source_path: _Optional[str] = ..., destination_path: _Optional[str] = ...) -> None: ...
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    HOST_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    NUMBER_OF_RETRIES_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    USE_TYPE_V3_FIELD_NUMBER: _ClassVar[int]
    description: str
    host: str
    items: _containers.RepeatedCompositeFieldContainer[ExportToYtSettings.Item]
    number_of_retries: int
    port: int
    token: str
    use_type_v3: bool
    def __init__(self, host: _Optional[str] = ..., port: _Optional[int] = ..., token: _Optional[str] = ..., items: _Optional[_Iterable[_Union[ExportToYtSettings.Item, _Mapping]]] = ..., description: _Optional[str] = ..., number_of_retries: _Optional[int] = ..., use_type_v3: bool = ...) -> None: ...
