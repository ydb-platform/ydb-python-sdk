from protos.annotations import validation_pb2 as _validation_pb2
from protos import ydb_export_pb2 as _ydb_export_pb2
from protos import ydb_operation_pb2 as _ydb_operation_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ImportDataRequest(_message.Message):
    __slots__ = ["data", "operation_params", "path", "ydb_dump"]
    DATA_FIELD_NUMBER: _ClassVar[int]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    YDB_DUMP_FIELD_NUMBER: _ClassVar[int]
    data: bytes
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    ydb_dump: YdbDumpFormat
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., data: _Optional[bytes] = ..., ydb_dump: _Optional[_Union[YdbDumpFormat, _Mapping]] = ...) -> None: ...

class ImportDataResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ImportDataResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class ImportFromFsMetadata(_message.Message):
    __slots__ = ["items_progress", "progress", "settings"]
    ITEMS_PROGRESS_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    items_progress: _containers.RepeatedCompositeFieldContainer[ImportItemProgress]
    progress: ImportProgress.Progress
    settings: ImportFromFsSettings
    def __init__(self, settings: _Optional[_Union[ImportFromFsSettings, _Mapping]] = ..., progress: _Optional[_Union[ImportProgress.Progress, str]] = ..., items_progress: _Optional[_Iterable[_Union[ImportItemProgress, _Mapping]]] = ...) -> None: ...

class ImportFromFsRequest(_message.Message):
    __slots__ = ["operation_params", "settings"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    settings: ImportFromFsSettings
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., settings: _Optional[_Union[ImportFromFsSettings, _Mapping]] = ...) -> None: ...

class ImportFromFsResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ImportFromFsResult(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class ImportFromFsSettings(_message.Message):
    __slots__ = ["base_path", "description", "destination_path", "encryption_settings", "exclude_regexps", "items", "no_acl", "number_of_retries", "skip_checksum_validation"]
    class Item(_message.Message):
        __slots__ = ["destination_path", "source_path"]
        DESTINATION_PATH_FIELD_NUMBER: _ClassVar[int]
        SOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
        destination_path: str
        source_path: str
        def __init__(self, source_path: _Optional[str] = ..., destination_path: _Optional[str] = ...) -> None: ...
    BASE_PATH_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    DESTINATION_PATH_FIELD_NUMBER: _ClassVar[int]
    ENCRYPTION_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    EXCLUDE_REGEXPS_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    NO_ACL_FIELD_NUMBER: _ClassVar[int]
    NUMBER_OF_RETRIES_FIELD_NUMBER: _ClassVar[int]
    SKIP_CHECKSUM_VALIDATION_FIELD_NUMBER: _ClassVar[int]
    base_path: str
    description: str
    destination_path: str
    encryption_settings: _ydb_export_pb2.EncryptionSettings
    exclude_regexps: _containers.RepeatedScalarFieldContainer[str]
    items: _containers.RepeatedCompositeFieldContainer[ImportFromFsSettings.Item]
    no_acl: bool
    number_of_retries: int
    skip_checksum_validation: bool
    def __init__(self, base_path: _Optional[str] = ..., items: _Optional[_Iterable[_Union[ImportFromFsSettings.Item, _Mapping]]] = ..., description: _Optional[str] = ..., number_of_retries: _Optional[int] = ..., no_acl: bool = ..., skip_checksum_validation: bool = ..., destination_path: _Optional[str] = ..., encryption_settings: _Optional[_Union[_ydb_export_pb2.EncryptionSettings, _Mapping]] = ..., exclude_regexps: _Optional[_Iterable[str]] = ...) -> None: ...

class ImportFromS3Metadata(_message.Message):
    __slots__ = ["items_progress", "progress", "settings"]
    ITEMS_PROGRESS_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    items_progress: _containers.RepeatedCompositeFieldContainer[ImportItemProgress]
    progress: ImportProgress.Progress
    settings: ImportFromS3Settings
    def __init__(self, settings: _Optional[_Union[ImportFromS3Settings, _Mapping]] = ..., progress: _Optional[_Union[ImportProgress.Progress, str]] = ..., items_progress: _Optional[_Iterable[_Union[ImportItemProgress, _Mapping]]] = ...) -> None: ...

class ImportFromS3Request(_message.Message):
    __slots__ = ["operation_params", "settings"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    settings: ImportFromS3Settings
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., settings: _Optional[_Union[ImportFromS3Settings, _Mapping]] = ...) -> None: ...

class ImportFromS3Response(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ImportFromS3Result(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class ImportFromS3Settings(_message.Message):
    __slots__ = ["access_key", "bucket", "description", "destination_path", "disable_virtual_addressing", "encryption_settings", "endpoint", "exclude_regexps", "index_filling_mode", "items", "no_acl", "number_of_retries", "region", "scheme", "secret_key", "skip_checksum_validation", "source_prefix"]
    class IndexFillingMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    class Scheme(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    class Item(_message.Message):
        __slots__ = ["destination_path", "source_path", "source_prefix"]
        DESTINATION_PATH_FIELD_NUMBER: _ClassVar[int]
        SOURCE_PATH_FIELD_NUMBER: _ClassVar[int]
        SOURCE_PREFIX_FIELD_NUMBER: _ClassVar[int]
        destination_path: str
        source_path: str
        source_prefix: str
        def __init__(self, source_prefix: _Optional[str] = ..., source_path: _Optional[str] = ..., destination_path: _Optional[str] = ...) -> None: ...
    ACCESS_KEY_FIELD_NUMBER: _ClassVar[int]
    BUCKET_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    DESTINATION_PATH_FIELD_NUMBER: _ClassVar[int]
    DISABLE_VIRTUAL_ADDRESSING_FIELD_NUMBER: _ClassVar[int]
    ENCRYPTION_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    EXCLUDE_REGEXPS_FIELD_NUMBER: _ClassVar[int]
    HTTP: ImportFromS3Settings.Scheme
    HTTPS: ImportFromS3Settings.Scheme
    INDEX_FILLING_MODE_AUTO: ImportFromS3Settings.IndexFillingMode
    INDEX_FILLING_MODE_BUILD: ImportFromS3Settings.IndexFillingMode
    INDEX_FILLING_MODE_FIELD_NUMBER: _ClassVar[int]
    INDEX_FILLING_MODE_IMPORT: ImportFromS3Settings.IndexFillingMode
    INDEX_FILLING_MODE_UNSPECIFIED: ImportFromS3Settings.IndexFillingMode
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    NO_ACL_FIELD_NUMBER: _ClassVar[int]
    NUMBER_OF_RETRIES_FIELD_NUMBER: _ClassVar[int]
    REGION_FIELD_NUMBER: _ClassVar[int]
    SCHEME_FIELD_NUMBER: _ClassVar[int]
    SECRET_KEY_FIELD_NUMBER: _ClassVar[int]
    SKIP_CHECKSUM_VALIDATION_FIELD_NUMBER: _ClassVar[int]
    SOURCE_PREFIX_FIELD_NUMBER: _ClassVar[int]
    UNSPECIFIED: ImportFromS3Settings.Scheme
    access_key: str
    bucket: str
    description: str
    destination_path: str
    disable_virtual_addressing: bool
    encryption_settings: _ydb_export_pb2.EncryptionSettings
    endpoint: str
    exclude_regexps: _containers.RepeatedScalarFieldContainer[str]
    index_filling_mode: ImportFromS3Settings.IndexFillingMode
    items: _containers.RepeatedCompositeFieldContainer[ImportFromS3Settings.Item]
    no_acl: bool
    number_of_retries: int
    region: str
    scheme: ImportFromS3Settings.Scheme
    secret_key: str
    skip_checksum_validation: bool
    source_prefix: str
    def __init__(self, endpoint: _Optional[str] = ..., scheme: _Optional[_Union[ImportFromS3Settings.Scheme, str]] = ..., bucket: _Optional[str] = ..., access_key: _Optional[str] = ..., secret_key: _Optional[str] = ..., items: _Optional[_Iterable[_Union[ImportFromS3Settings.Item, _Mapping]]] = ..., description: _Optional[str] = ..., number_of_retries: _Optional[int] = ..., region: _Optional[str] = ..., disable_virtual_addressing: bool = ..., no_acl: bool = ..., skip_checksum_validation: bool = ..., source_prefix: _Optional[str] = ..., destination_path: _Optional[str] = ..., encryption_settings: _Optional[_Union[_ydb_export_pb2.EncryptionSettings, _Mapping]] = ..., index_filling_mode: _Optional[_Union[ImportFromS3Settings.IndexFillingMode, str]] = ..., exclude_regexps: _Optional[_Iterable[str]] = ...) -> None: ...

class ImportItemProgress(_message.Message):
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

class ImportProgress(_message.Message):
    __slots__ = []
    class Progress(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    PROGRESS_BUILD_INDEXES: ImportProgress.Progress
    PROGRESS_CANCELLATION: ImportProgress.Progress
    PROGRESS_CANCELLED: ImportProgress.Progress
    PROGRESS_CREATE_CHANGEFEEDS: ImportProgress.Progress
    PROGRESS_DONE: ImportProgress.Progress
    PROGRESS_PREPARING: ImportProgress.Progress
    PROGRESS_TRANSFER_DATA: ImportProgress.Progress
    PROGRESS_UNSPECIFIED: ImportProgress.Progress
    def __init__(self) -> None: ...

class ListObjectsInFsExportRequest(_message.Message):
    __slots__ = ["operation_params", "page_size", "page_token", "settings"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    page_size: int
    page_token: str
    settings: ListObjectsInFsExportSettings
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., settings: _Optional[_Union[ListObjectsInFsExportSettings, _Mapping]] = ..., page_size: _Optional[int] = ..., page_token: _Optional[str] = ...) -> None: ...

class ListObjectsInFsExportResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListObjectsInFsExportResult(_message.Message):
    __slots__ = ["items", "next_page_token"]
    class Item(_message.Message):
        __slots__ = ["db_path", "fs_path"]
        DB_PATH_FIELD_NUMBER: _ClassVar[int]
        FS_PATH_FIELD_NUMBER: _ClassVar[int]
        db_path: str
        fs_path: str
        def __init__(self, fs_path: _Optional[str] = ..., db_path: _Optional[str] = ...) -> None: ...
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[ListObjectsInFsExportResult.Item]
    next_page_token: str
    def __init__(self, items: _Optional[_Iterable[_Union[ListObjectsInFsExportResult.Item, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class ListObjectsInFsExportSettings(_message.Message):
    __slots__ = ["base_path", "encryption_settings", "exclude_regexps", "items", "number_of_retries"]
    class Item(_message.Message):
        __slots__ = ["path"]
        PATH_FIELD_NUMBER: _ClassVar[int]
        path: str
        def __init__(self, path: _Optional[str] = ...) -> None: ...
    BASE_PATH_FIELD_NUMBER: _ClassVar[int]
    ENCRYPTION_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    EXCLUDE_REGEXPS_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    NUMBER_OF_RETRIES_FIELD_NUMBER: _ClassVar[int]
    base_path: str
    encryption_settings: _ydb_export_pb2.EncryptionSettings
    exclude_regexps: _containers.RepeatedScalarFieldContainer[str]
    items: _containers.RepeatedCompositeFieldContainer[ListObjectsInFsExportSettings.Item]
    number_of_retries: int
    def __init__(self, base_path: _Optional[str] = ..., items: _Optional[_Iterable[_Union[ListObjectsInFsExportSettings.Item, _Mapping]]] = ..., number_of_retries: _Optional[int] = ..., encryption_settings: _Optional[_Union[_ydb_export_pb2.EncryptionSettings, _Mapping]] = ..., exclude_regexps: _Optional[_Iterable[str]] = ...) -> None: ...

class ListObjectsInS3ExportRequest(_message.Message):
    __slots__ = ["operation_params", "page_size", "page_token", "settings"]
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    SETTINGS_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    page_size: int
    page_token: str
    settings: ListObjectsInS3ExportSettings
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., settings: _Optional[_Union[ListObjectsInS3ExportSettings, _Mapping]] = ..., page_size: _Optional[int] = ..., page_token: _Optional[str] = ...) -> None: ...

class ListObjectsInS3ExportResponse(_message.Message):
    __slots__ = ["operation"]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class ListObjectsInS3ExportResult(_message.Message):
    __slots__ = ["items", "next_page_token"]
    class Item(_message.Message):
        __slots__ = ["path", "prefix"]
        PATH_FIELD_NUMBER: _ClassVar[int]
        PREFIX_FIELD_NUMBER: _ClassVar[int]
        path: str
        prefix: str
        def __init__(self, prefix: _Optional[str] = ..., path: _Optional[str] = ...) -> None: ...
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[ListObjectsInS3ExportResult.Item]
    next_page_token: str
    def __init__(self, items: _Optional[_Iterable[_Union[ListObjectsInS3ExportResult.Item, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class ListObjectsInS3ExportSettings(_message.Message):
    __slots__ = ["access_key", "bucket", "disable_virtual_addressing", "encryption_settings", "endpoint", "exclude_regexps", "items", "number_of_retries", "prefix", "region", "scheme", "secret_key"]
    class Item(_message.Message):
        __slots__ = ["path"]
        PATH_FIELD_NUMBER: _ClassVar[int]
        path: str
        def __init__(self, path: _Optional[str] = ...) -> None: ...
    ACCESS_KEY_FIELD_NUMBER: _ClassVar[int]
    BUCKET_FIELD_NUMBER: _ClassVar[int]
    DISABLE_VIRTUAL_ADDRESSING_FIELD_NUMBER: _ClassVar[int]
    ENCRYPTION_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    EXCLUDE_REGEXPS_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    NUMBER_OF_RETRIES_FIELD_NUMBER: _ClassVar[int]
    PREFIX_FIELD_NUMBER: _ClassVar[int]
    REGION_FIELD_NUMBER: _ClassVar[int]
    SCHEME_FIELD_NUMBER: _ClassVar[int]
    SECRET_KEY_FIELD_NUMBER: _ClassVar[int]
    access_key: str
    bucket: str
    disable_virtual_addressing: bool
    encryption_settings: _ydb_export_pb2.EncryptionSettings
    endpoint: str
    exclude_regexps: _containers.RepeatedScalarFieldContainer[str]
    items: _containers.RepeatedCompositeFieldContainer[ListObjectsInS3ExportSettings.Item]
    number_of_retries: int
    prefix: str
    region: str
    scheme: ImportFromS3Settings.Scheme
    secret_key: str
    def __init__(self, endpoint: _Optional[str] = ..., scheme: _Optional[_Union[ImportFromS3Settings.Scheme, str]] = ..., bucket: _Optional[str] = ..., access_key: _Optional[str] = ..., secret_key: _Optional[str] = ..., items: _Optional[_Iterable[_Union[ListObjectsInS3ExportSettings.Item, _Mapping]]] = ..., number_of_retries: _Optional[int] = ..., region: _Optional[str] = ..., disable_virtual_addressing: bool = ..., prefix: _Optional[str] = ..., encryption_settings: _Optional[_Union[_ydb_export_pb2.EncryptionSettings, _Mapping]] = ..., exclude_regexps: _Optional[_Iterable[str]] = ...) -> None: ...

class YdbDumpFormat(_message.Message):
    __slots__ = ["columns"]
    COLUMNS_FIELD_NUMBER: _ClassVar[int]
    columns: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, columns: _Optional[_Iterable[str]] = ...) -> None: ...
