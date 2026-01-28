import datetime

from protos.annotations import validation_pb2 as _validation_pb2
from protos import ydb_export_pb2 as _ydb_export_pb2
from protos import ydb_operation_pb2 as _ydb_operation_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ImportProgress(_message.Message):
    __slots__ = ()
    class Progress(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        PROGRESS_UNSPECIFIED: _ClassVar[ImportProgress.Progress]
        PROGRESS_PREPARING: _ClassVar[ImportProgress.Progress]
        PROGRESS_TRANSFER_DATA: _ClassVar[ImportProgress.Progress]
        PROGRESS_BUILD_INDEXES: _ClassVar[ImportProgress.Progress]
        PROGRESS_DONE: _ClassVar[ImportProgress.Progress]
        PROGRESS_CANCELLATION: _ClassVar[ImportProgress.Progress]
        PROGRESS_CANCELLED: _ClassVar[ImportProgress.Progress]
        PROGRESS_CREATE_CHANGEFEEDS: _ClassVar[ImportProgress.Progress]
    PROGRESS_UNSPECIFIED: ImportProgress.Progress
    PROGRESS_PREPARING: ImportProgress.Progress
    PROGRESS_TRANSFER_DATA: ImportProgress.Progress
    PROGRESS_BUILD_INDEXES: ImportProgress.Progress
    PROGRESS_DONE: ImportProgress.Progress
    PROGRESS_CANCELLATION: ImportProgress.Progress
    PROGRESS_CANCELLED: ImportProgress.Progress
    PROGRESS_CREATE_CHANGEFEEDS: ImportProgress.Progress
    def __init__(self) -> None: ...

class ImportItemProgress(_message.Message):
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

class ImportFromS3Settings(_message.Message):
    __slots__ = ("endpoint", "scheme", "bucket", "access_key", "secret_key", "items", "description", "number_of_retries", "region", "disable_virtual_addressing", "no_acl", "skip_checksum_validation", "source_prefix", "destination_path", "encryption_settings", "index_filling_mode", "exclude_regexps")
    class Scheme(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNSPECIFIED: _ClassVar[ImportFromS3Settings.Scheme]
        HTTP: _ClassVar[ImportFromS3Settings.Scheme]
        HTTPS: _ClassVar[ImportFromS3Settings.Scheme]
    UNSPECIFIED: ImportFromS3Settings.Scheme
    HTTP: ImportFromS3Settings.Scheme
    HTTPS: ImportFromS3Settings.Scheme
    class IndexFillingMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        INDEX_FILLING_MODE_UNSPECIFIED: _ClassVar[ImportFromS3Settings.IndexFillingMode]
        INDEX_FILLING_MODE_BUILD: _ClassVar[ImportFromS3Settings.IndexFillingMode]
        INDEX_FILLING_MODE_IMPORT: _ClassVar[ImportFromS3Settings.IndexFillingMode]
        INDEX_FILLING_MODE_AUTO: _ClassVar[ImportFromS3Settings.IndexFillingMode]
    INDEX_FILLING_MODE_UNSPECIFIED: ImportFromS3Settings.IndexFillingMode
    INDEX_FILLING_MODE_BUILD: ImportFromS3Settings.IndexFillingMode
    INDEX_FILLING_MODE_IMPORT: ImportFromS3Settings.IndexFillingMode
    INDEX_FILLING_MODE_AUTO: ImportFromS3Settings.IndexFillingMode
    class Item(_message.Message):
        __slots__ = ("source_prefix", "source_path", "destination_path")
        SOURCE_PREFIX_FIELD_NUMBER: _ClassVar[int]
        SOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
        DESTINATION_PATH_FIELD_NUMBER: _ClassVar[int]
        source_prefix: str
        source_path: str
        destination_path: str
        def __init__(self, source_prefix: _Optional[str] = ..., source_path: _Optional[str] = ..., destination_path: _Optional[str] = ...) -> None: ...
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    SCHEME_FIELD_NUMBER: _ClassVar[int]
    BUCKET_FIELD_NUMBER: _ClassVar[int]
    ACCESS_KEY_FIELD_NUMBER: _ClassVar[int]
    SECRET_KEY_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    NUMBER_OF_RETRIES_FIELD_NUMBER: _ClassVar[int]
    REGION_FIELD_NUMBER: _ClassVar[int]
    DISABLE_VIRTUAL_ADDRESSING_FIELD_NUMBER: _ClassVar[int]
    NO_ACL_FIELD_NUMBER: _ClassVar[int]
    SKIP_CHECKSUM_VALIDATION_FIELD_NUMBER: _ClassVar[int]
    SOURCE_PREFIX_FIELD_NUMBER: _ClassVar[int]
    DESTINATION_PATH_FIELD_NUMBER: _ClassVar[int]
    ENCRYPTION_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    INDEX_FILLING_MODE_FIELD_NUMBER: _ClassVar[int]
    EXCLUDE_REGEXPS_FIELD_NUMBER: _ClassVar[int]
    endpoint: str
    scheme: ImportFromS3Settings.Scheme
    bucket: str
    access_key: str
    secret_key: str
    items: _containers.RepeatedCompositeFieldContainer[ImportFromS3Settings.Item]
    description: str
    number_of_retries: int
    region: str
    disable_virtual_addressing: bool
    no_acl: bool
    skip_checksum_validation: bool
    source_prefix: str
    destination_path: str
    encryption_settings: _ydb_export_pb2.EncryptionSettings
    index_filling_mode: ImportFromS3Settings.IndexFillingMode
    exclude_regexps: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, endpoint: _Optional[str] = ..., scheme: _Optional[_Union[ImportFromS3Settings.Scheme, str]] = ..., bucket: _Optional[str] = ..., access_key: _Optional[str] = ..., secret_key: _Optional[str] = ..., items: _Optional[_Iterable[_Union[ImportFromS3Settings.Item, _Mapping]]] = ..., description: _Optional[str] = ..., number_of_retries: _Optional[int] = ..., region: _Optional[str] = ..., disable_virtual_addressing: bool = ..., no_acl: bool = ..., skip_checksum_validation: bool = ..., source_prefix: _Optional[str] = ..., destination_path: _Optional[str] = ..., encryption_settings: _Optional[_Union[_ydb_export_pb2.EncryptionSettings, _Mapping]] = ..., index_filling_mode: _Optional[_Union[ImportFromS3Settings.IndexFillingMode, str]] = ..., exclude_regexps: _Optional[_Iterable[str]] = ...) -> None: ...

class ImportFromS3Result(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ImportFromS3Metadata(_message.Message):
    __slots__ = ("settings", "progress", "items_progress")
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    ITEMS_PROGRESS_FIELD_NUMBER: _ClassVar[int]
    settings: ImportFromS3Settings
    progress: ImportProgress.Progress
    items_progress: _containers.RepeatedCompositeFieldContainer[ImportItemProgress]
    def __init__(self, settings: _Optional[_Union[ImportFromS3Settings, _Mapping]] = ..., progress: _Optional[_Union[ImportProgress.Progress, str]] = ..., items_progress: _Optional[_Iterable[_Union[ImportItemProgress, _Mapping]]] = ...) -> None: ...

class ImportFromS3Request(_message.Message):
    __slots__ = ("operation_params", "settings")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    settings: ImportFromS3Settings
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., settings: _Optional[_Union[ImportFromS3Settings, _Mapping]] = ...) -> None: ...

class ImportFromS3Response(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ImportFromFsSettings(_message.Message):
    __slots__ = ("base_path", "items", "description", "number_of_retries", "no_acl", "skip_checksum_validation", "destination_path", "encryption_settings", "exclude_regexps")
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
    NO_ACL_FIELD_NUMBER: _ClassVar[int]
    SKIP_CHECKSUM_VALIDATION_FIELD_NUMBER: _ClassVar[int]
    DESTINATION_PATH_FIELD_NUMBER: _ClassVar[int]
    ENCRYPTION_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    EXCLUDE_REGEXPS_FIELD_NUMBER: _ClassVar[int]
    base_path: str
    items: _containers.RepeatedCompositeFieldContainer[ImportFromFsSettings.Item]
    description: str
    number_of_retries: int
    no_acl: bool
    skip_checksum_validation: bool
    destination_path: str
    encryption_settings: _ydb_export_pb2.EncryptionSettings
    exclude_regexps: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, base_path: _Optional[str] = ..., items: _Optional[_Iterable[_Union[ImportFromFsSettings.Item, _Mapping]]] = ..., description: _Optional[str] = ..., number_of_retries: _Optional[int] = ..., no_acl: bool = ..., skip_checksum_validation: bool = ..., destination_path: _Optional[str] = ..., encryption_settings: _Optional[_Union[_ydb_export_pb2.EncryptionSettings, _Mapping]] = ..., exclude_regexps: _Optional[_Iterable[str]] = ...) -> None: ...

class ImportFromFsResult(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ImportFromFsMetadata(_message.Message):
    __slots__ = ("settings", "progress", "items_progress")
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    ITEMS_PROGRESS_FIELD_NUMBER: _ClassVar[int]
    settings: ImportFromFsSettings
    progress: ImportProgress.Progress
    items_progress: _containers.RepeatedCompositeFieldContainer[ImportItemProgress]
    def __init__(self, settings: _Optional[_Union[ImportFromFsSettings, _Mapping]] = ..., progress: _Optional[_Union[ImportProgress.Progress, str]] = ..., items_progress: _Optional[_Iterable[_Union[ImportItemProgress, _Mapping]]] = ...) -> None: ...

class ImportFromFsRequest(_message.Message):
    __slots__ = ("operation_params", "settings")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    settings: ImportFromFsSettings
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., settings: _Optional[_Union[ImportFromFsSettings, _Mapping]] = ...) -> None: ...

class ImportFromFsResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListObjectsInS3ExportSettings(_message.Message):
    __slots__ = ("endpoint", "scheme", "bucket", "access_key", "secret_key", "items", "number_of_retries", "region", "disable_virtual_addressing", "prefix", "encryption_settings", "exclude_regexps")
    class Item(_message.Message):
        __slots__ = ("path",)
        PATH_FIELD_NUMBER: _ClassVar[int]
        path: str
        def __init__(self, path: _Optional[str] = ...) -> None: ...
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    SCHEME_FIELD_NUMBER: _ClassVar[int]
    BUCKET_FIELD_NUMBER: _ClassVar[int]
    ACCESS_KEY_FIELD_NUMBER: _ClassVar[int]
    SECRET_KEY_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    NUMBER_OF_RETRIES_FIELD_NUMBER: _ClassVar[int]
    REGION_FIELD_NUMBER: _ClassVar[int]
    DISABLE_VIRTUAL_ADDRESSING_FIELD_NUMBER: _ClassVar[int]
    PREFIX_FIELD_NUMBER: _ClassVar[int]
    ENCRYPTION_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    EXCLUDE_REGEXPS_FIELD_NUMBER: _ClassVar[int]
    endpoint: str
    scheme: ImportFromS3Settings.Scheme
    bucket: str
    access_key: str
    secret_key: str
    items: _containers.RepeatedCompositeFieldContainer[ListObjectsInS3ExportSettings.Item]
    number_of_retries: int
    region: str
    disable_virtual_addressing: bool
    prefix: str
    encryption_settings: _ydb_export_pb2.EncryptionSettings
    exclude_regexps: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, endpoint: _Optional[str] = ..., scheme: _Optional[_Union[ImportFromS3Settings.Scheme, str]] = ..., bucket: _Optional[str] = ..., access_key: _Optional[str] = ..., secret_key: _Optional[str] = ..., items: _Optional[_Iterable[_Union[ListObjectsInS3ExportSettings.Item, _Mapping]]] = ..., number_of_retries: _Optional[int] = ..., region: _Optional[str] = ..., disable_virtual_addressing: bool = ..., prefix: _Optional[str] = ..., encryption_settings: _Optional[_Union[_ydb_export_pb2.EncryptionSettings, _Mapping]] = ..., exclude_regexps: _Optional[_Iterable[str]] = ...) -> None: ...

class ListObjectsInS3ExportResult(_message.Message):
    __slots__ = ("items", "next_page_token")
    class Item(_message.Message):
        __slots__ = ("prefix", "path")
        PREFIX_FIELD_NUMBER: _ClassVar[int]
        PATH_FIELD_NUMBER: _ClassVar[int]
        prefix: str
        path: str
        def __init__(self, prefix: _Optional[str] = ..., path: _Optional[str] = ...) -> None: ...
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[ListObjectsInS3ExportResult.Item]
    next_page_token: str
    def __init__(self, items: _Optional[_Iterable[_Union[ListObjectsInS3ExportResult.Item, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class ListObjectsInS3ExportRequest(_message.Message):
    __slots__ = ("operation_params", "settings", "page_size", "page_token")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    settings: ListObjectsInS3ExportSettings
    page_size: int
    page_token: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., settings: _Optional[_Union[ListObjectsInS3ExportSettings, _Mapping]] = ..., page_size: _Optional[int] = ..., page_token: _Optional[str] = ...) -> None: ...

class ListObjectsInS3ExportResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListObjectsInFsExportSettings(_message.Message):
    __slots__ = ("base_path", "items", "number_of_retries", "encryption_settings", "exclude_regexps")
    class Item(_message.Message):
        __slots__ = ("path",)
        PATH_FIELD_NUMBER: _ClassVar[int]
        path: str
        def __init__(self, path: _Optional[str] = ...) -> None: ...
    BASE_PATH_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    NUMBER_OF_RETRIES_FIELD_NUMBER: _ClassVar[int]
    ENCRYPTION_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    EXCLUDE_REGEXPS_FIELD_NUMBER: _ClassVar[int]
    base_path: str
    items: _containers.RepeatedCompositeFieldContainer[ListObjectsInFsExportSettings.Item]
    number_of_retries: int
    encryption_settings: _ydb_export_pb2.EncryptionSettings
    exclude_regexps: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, base_path: _Optional[str] = ..., items: _Optional[_Iterable[_Union[ListObjectsInFsExportSettings.Item, _Mapping]]] = ..., number_of_retries: _Optional[int] = ..., encryption_settings: _Optional[_Union[_ydb_export_pb2.EncryptionSettings, _Mapping]] = ..., exclude_regexps: _Optional[_Iterable[str]] = ...) -> None: ...

class ListObjectsInFsExportResult(_message.Message):
    __slots__ = ("items", "next_page_token")
    class Item(_message.Message):
        __slots__ = ("fs_path", "db_path")
        FS_PATH_FIELD_NUMBER: _ClassVar[int]
        DB_PATH_FIELD_NUMBER: _ClassVar[int]
        fs_path: str
        db_path: str
        def __init__(self, fs_path: _Optional[str] = ..., db_path: _Optional[str] = ...) -> None: ...
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[ListObjectsInFsExportResult.Item]
    next_page_token: str
    def __init__(self, items: _Optional[_Iterable[_Union[ListObjectsInFsExportResult.Item, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class ListObjectsInFsExportRequest(_message.Message):
    __slots__ = ("operation_params", "settings", "page_size", "page_token")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    settings: ListObjectsInFsExportSettings
    page_size: int
    page_token: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., settings: _Optional[_Union[ListObjectsInFsExportSettings, _Mapping]] = ..., page_size: _Optional[int] = ..., page_token: _Optional[str] = ...) -> None: ...

class ListObjectsInFsExportResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class YdbDumpFormat(_message.Message):
    __slots__ = ("columns",)
    COLUMNS_FIELD_NUMBER: _ClassVar[int]
    columns: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, columns: _Optional[_Iterable[str]] = ...) -> None: ...

class ImportDataResult(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ImportDataRequest(_message.Message):
    __slots__ = ("operation_params", "path", "data", "ydb_dump")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    YDB_DUMP_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    data: bytes
    ydb_dump: YdbDumpFormat
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., data: _Optional[bytes] = ..., ydb_dump: _Optional[_Union[YdbDumpFormat, _Mapping]] = ...) -> None: ...

class ImportDataResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...
