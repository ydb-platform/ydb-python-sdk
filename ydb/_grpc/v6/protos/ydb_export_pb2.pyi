import datetime

from protos.annotations import sensitive_pb2 as _sensitive_pb2
from protos.annotations import validation_pb2 as _validation_pb2
from protos import ydb_operation_pb2 as _ydb_operation_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ExportProgress(_message.Message):
    __slots__ = ()
    class Progress(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        PROGRESS_UNSPECIFIED: _ClassVar[ExportProgress.Progress]
        PROGRESS_PREPARING: _ClassVar[ExportProgress.Progress]
        PROGRESS_TRANSFER_DATA: _ClassVar[ExportProgress.Progress]
        PROGRESS_DONE: _ClassVar[ExportProgress.Progress]
        PROGRESS_CANCELLATION: _ClassVar[ExportProgress.Progress]
        PROGRESS_CANCELLED: _ClassVar[ExportProgress.Progress]
    PROGRESS_UNSPECIFIED: ExportProgress.Progress
    PROGRESS_PREPARING: ExportProgress.Progress
    PROGRESS_TRANSFER_DATA: ExportProgress.Progress
    PROGRESS_DONE: ExportProgress.Progress
    PROGRESS_CANCELLATION: ExportProgress.Progress
    PROGRESS_CANCELLED: ExportProgress.Progress
    def __init__(self) -> None: ...

class ExportItemProgress(_message.Message):
    __slots__ = ("parts_total", "parts_completed", "start_time", "end_time")
    PARTS_TOTAL_FIELD_NUMBER: _ClassVar[int]
    PARTS_COMPLETED_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    parts_total: int
    parts_completed: int
    start_time: _timestamp_pb2.Timestamp
    end_time: _timestamp_pb2.Timestamp
    def __init__(self, parts_total: _Optional[int] = ..., parts_completed: _Optional[int] = ..., start_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., end_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ExportToYtSettings(_message.Message):
    __slots__ = ("host", "port", "token", "items", "description", "number_of_retries", "use_type_v3", "exclude_regexps")
    class Item(_message.Message):
        __slots__ = ("source_path", "destination_path")
        SOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
        DESTINATION_PATH_FIELD_NUMBER: _ClassVar[int]
        source_path: str
        destination_path: str
        def __init__(self, source_path: _Optional[str] = ..., destination_path: _Optional[str] = ...) -> None: ...
    HOST_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    NUMBER_OF_RETRIES_FIELD_NUMBER: _ClassVar[int]
    USE_TYPE_V3_FIELD_NUMBER: _ClassVar[int]
    EXCLUDE_REGEXPS_FIELD_NUMBER: _ClassVar[int]
    host: str
    port: int
    token: str
    items: _containers.RepeatedCompositeFieldContainer[ExportToYtSettings.Item]
    description: str
    number_of_retries: int
    use_type_v3: bool
    exclude_regexps: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, host: _Optional[str] = ..., port: _Optional[int] = ..., token: _Optional[str] = ..., items: _Optional[_Iterable[_Union[ExportToYtSettings.Item, _Mapping]]] = ..., description: _Optional[str] = ..., number_of_retries: _Optional[int] = ..., use_type_v3: bool = ..., exclude_regexps: _Optional[_Iterable[str]] = ...) -> None: ...

class ExportToYtResult(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ExportToYtMetadata(_message.Message):
    __slots__ = ("settings", "progress", "items_progress")
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    ITEMS_PROGRESS_FIELD_NUMBER: _ClassVar[int]
    settings: ExportToYtSettings
    progress: ExportProgress.Progress
    items_progress: _containers.RepeatedCompositeFieldContainer[ExportItemProgress]
    def __init__(self, settings: _Optional[_Union[ExportToYtSettings, _Mapping]] = ..., progress: _Optional[_Union[ExportProgress.Progress, str]] = ..., items_progress: _Optional[_Iterable[_Union[ExportItemProgress, _Mapping]]] = ...) -> None: ...

class ExportToYtRequest(_message.Message):
    __slots__ = ("operation_params", "settings")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    settings: ExportToYtSettings
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., settings: _Optional[_Union[ExportToYtSettings, _Mapping]] = ...) -> None: ...

class ExportToYtResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ExportToS3Settings(_message.Message):
    __slots__ = ("endpoint", "scheme", "bucket", "access_key", "secret_key", "items", "description", "number_of_retries", "storage_class", "compression", "region", "disable_virtual_addressing", "source_path", "destination_prefix", "encryption_settings", "materialize_indexes", "exclude_regexps")
    class Scheme(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNSPECIFIED: _ClassVar[ExportToS3Settings.Scheme]
        HTTP: _ClassVar[ExportToS3Settings.Scheme]
        HTTPS: _ClassVar[ExportToS3Settings.Scheme]
    UNSPECIFIED: ExportToS3Settings.Scheme
    HTTP: ExportToS3Settings.Scheme
    HTTPS: ExportToS3Settings.Scheme
    class StorageClass(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        STORAGE_CLASS_UNSPECIFIED: _ClassVar[ExportToS3Settings.StorageClass]
        STANDARD: _ClassVar[ExportToS3Settings.StorageClass]
        REDUCED_REDUNDANCY: _ClassVar[ExportToS3Settings.StorageClass]
        STANDARD_IA: _ClassVar[ExportToS3Settings.StorageClass]
        ONEZONE_IA: _ClassVar[ExportToS3Settings.StorageClass]
        INTELLIGENT_TIERING: _ClassVar[ExportToS3Settings.StorageClass]
        GLACIER: _ClassVar[ExportToS3Settings.StorageClass]
        DEEP_ARCHIVE: _ClassVar[ExportToS3Settings.StorageClass]
        OUTPOSTS: _ClassVar[ExportToS3Settings.StorageClass]
    STORAGE_CLASS_UNSPECIFIED: ExportToS3Settings.StorageClass
    STANDARD: ExportToS3Settings.StorageClass
    REDUCED_REDUNDANCY: ExportToS3Settings.StorageClass
    STANDARD_IA: ExportToS3Settings.StorageClass
    ONEZONE_IA: ExportToS3Settings.StorageClass
    INTELLIGENT_TIERING: ExportToS3Settings.StorageClass
    GLACIER: ExportToS3Settings.StorageClass
    DEEP_ARCHIVE: ExportToS3Settings.StorageClass
    OUTPOSTS: ExportToS3Settings.StorageClass
    class Item(_message.Message):
        __slots__ = ("source_path", "destination_prefix")
        SOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
        DESTINATION_PREFIX_FIELD_NUMBER: _ClassVar[int]
        source_path: str
        destination_prefix: str
        def __init__(self, source_path: _Optional[str] = ..., destination_prefix: _Optional[str] = ...) -> None: ...
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    SCHEME_FIELD_NUMBER: _ClassVar[int]
    BUCKET_FIELD_NUMBER: _ClassVar[int]
    ACCESS_KEY_FIELD_NUMBER: _ClassVar[int]
    SECRET_KEY_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    NUMBER_OF_RETRIES_FIELD_NUMBER: _ClassVar[int]
    STORAGE_CLASS_FIELD_NUMBER: _ClassVar[int]
    COMPRESSION_FIELD_NUMBER: _ClassVar[int]
    REGION_FIELD_NUMBER: _ClassVar[int]
    DISABLE_VIRTUAL_ADDRESSING_FIELD_NUMBER: _ClassVar[int]
    SOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
    DESTINATION_PREFIX_FIELD_NUMBER: _ClassVar[int]
    ENCRYPTION_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    MATERIALIZE_INDEXES_FIELD_NUMBER: _ClassVar[int]
    EXCLUDE_REGEXPS_FIELD_NUMBER: _ClassVar[int]
    endpoint: str
    scheme: ExportToS3Settings.Scheme
    bucket: str
    access_key: str
    secret_key: str
    items: _containers.RepeatedCompositeFieldContainer[ExportToS3Settings.Item]
    description: str
    number_of_retries: int
    storage_class: ExportToS3Settings.StorageClass
    compression: str
    region: str
    disable_virtual_addressing: bool
    source_path: str
    destination_prefix: str
    encryption_settings: EncryptionSettings
    materialize_indexes: bool
    exclude_regexps: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, endpoint: _Optional[str] = ..., scheme: _Optional[_Union[ExportToS3Settings.Scheme, str]] = ..., bucket: _Optional[str] = ..., access_key: _Optional[str] = ..., secret_key: _Optional[str] = ..., items: _Optional[_Iterable[_Union[ExportToS3Settings.Item, _Mapping]]] = ..., description: _Optional[str] = ..., number_of_retries: _Optional[int] = ..., storage_class: _Optional[_Union[ExportToS3Settings.StorageClass, str]] = ..., compression: _Optional[str] = ..., region: _Optional[str] = ..., disable_virtual_addressing: bool = ..., source_path: _Optional[str] = ..., destination_prefix: _Optional[str] = ..., encryption_settings: _Optional[_Union[EncryptionSettings, _Mapping]] = ..., materialize_indexes: bool = ..., exclude_regexps: _Optional[_Iterable[str]] = ...) -> None: ...

class ExportToS3Result(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ExportToS3Metadata(_message.Message):
    __slots__ = ("settings", "progress", "items_progress")
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    ITEMS_PROGRESS_FIELD_NUMBER: _ClassVar[int]
    settings: ExportToS3Settings
    progress: ExportProgress.Progress
    items_progress: _containers.RepeatedCompositeFieldContainer[ExportItemProgress]
    def __init__(self, settings: _Optional[_Union[ExportToS3Settings, _Mapping]] = ..., progress: _Optional[_Union[ExportProgress.Progress, str]] = ..., items_progress: _Optional[_Iterable[_Union[ExportItemProgress, _Mapping]]] = ...) -> None: ...

class ExportToS3Request(_message.Message):
    __slots__ = ("operation_params", "settings")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    settings: ExportToS3Settings
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., settings: _Optional[_Union[ExportToS3Settings, _Mapping]] = ...) -> None: ...

class ExportToS3Response(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class EncryptionSettings(_message.Message):
    __slots__ = ("encryption_algorithm", "symmetric_key")
    class SymmetricKey(_message.Message):
        __slots__ = ("key",)
        KEY_FIELD_NUMBER: _ClassVar[int]
        key: bytes
        def __init__(self, key: _Optional[bytes] = ...) -> None: ...
    ENCRYPTION_ALGORITHM_FIELD_NUMBER: _ClassVar[int]
    SYMMETRIC_KEY_FIELD_NUMBER: _ClassVar[int]
    encryption_algorithm: str
    symmetric_key: EncryptionSettings.SymmetricKey
    def __init__(self, encryption_algorithm: _Optional[str] = ..., symmetric_key: _Optional[_Union[EncryptionSettings.SymmetricKey, _Mapping]] = ...) -> None: ...

class ExportToFsSettings(_message.Message):
    __slots__ = ("base_path", "items", "description", "number_of_retries", "compression", "encryption_settings", "source_path", "exclude_regexps")
    class Item(_message.Message):
        __slots__ = ("source_path", "destination_path")
        SOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
        DESTINATION_PATH_FIELD_NUMBER: _ClassVar[int]
        source_path: str
        destination_path: str
        def __init__(self, source_path: _Optional[str] = ..., destination_path: _Optional[str] = ...) -> None: ...
    BASE_PATH_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    NUMBER_OF_RETRIES_FIELD_NUMBER: _ClassVar[int]
    COMPRESSION_FIELD_NUMBER: _ClassVar[int]
    ENCRYPTION_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    SOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
    EXCLUDE_REGEXPS_FIELD_NUMBER: _ClassVar[int]
    base_path: str
    items: _containers.RepeatedCompositeFieldContainer[ExportToFsSettings.Item]
    description: str
    number_of_retries: int
    compression: str
    encryption_settings: EncryptionSettings
    source_path: str
    exclude_regexps: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, base_path: _Optional[str] = ..., items: _Optional[_Iterable[_Union[ExportToFsSettings.Item, _Mapping]]] = ..., description: _Optional[str] = ..., number_of_retries: _Optional[int] = ..., compression: _Optional[str] = ..., encryption_settings: _Optional[_Union[EncryptionSettings, _Mapping]] = ..., source_path: _Optional[str] = ..., exclude_regexps: _Optional[_Iterable[str]] = ...) -> None: ...

class ExportToFsResult(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ExportToFsMetadata(_message.Message):
    __slots__ = ("settings", "progress", "items_progress")
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    ITEMS_PROGRESS_FIELD_NUMBER: _ClassVar[int]
    settings: ExportToFsSettings
    progress: ExportProgress.Progress
    items_progress: _containers.RepeatedCompositeFieldContainer[ExportItemProgress]
    def __init__(self, settings: _Optional[_Union[ExportToFsSettings, _Mapping]] = ..., progress: _Optional[_Union[ExportProgress.Progress, str]] = ..., items_progress: _Optional[_Iterable[_Union[ExportItemProgress, _Mapping]]] = ...) -> None: ...

class ExportToFsRequest(_message.Message):
    __slots__ = ("operation_params", "settings")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    settings: ExportToFsSettings
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., settings: _Optional[_Union[ExportToFsSettings, _Mapping]] = ...) -> None: ...

class ExportToFsResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...
