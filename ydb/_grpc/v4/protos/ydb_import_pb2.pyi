from protos.annotations import validation_pb2 as _validation_pb2
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
    __slots__ = ["access_key", "bucket", "description", "endpoint", "items", "number_of_retries", "region", "scheme", "secret_key"]
    class Scheme(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    class Item(_message.Message):
        __slots__ = ["destination_path", "source_prefix"]
        DESTINATION_PATH_FIELD_NUMBER: _ClassVar[int]
        SOURCE_PREFIX_FIELD_NUMBER: _ClassVar[int]
        destination_path: str
        source_prefix: str
        def __init__(self, source_prefix: _Optional[str] = ..., destination_path: _Optional[str] = ...) -> None: ...
    ACCESS_KEY_FIELD_NUMBER: _ClassVar[int]
    BUCKET_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    HTTP: ImportFromS3Settings.Scheme
    HTTPS: ImportFromS3Settings.Scheme
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    NUMBER_OF_RETRIES_FIELD_NUMBER: _ClassVar[int]
    REGION_FIELD_NUMBER: _ClassVar[int]
    SCHEME_FIELD_NUMBER: _ClassVar[int]
    SECRET_KEY_FIELD_NUMBER: _ClassVar[int]
    UNSPECIFIED: ImportFromS3Settings.Scheme
    access_key: str
    bucket: str
    description: str
    endpoint: str
    items: _containers.RepeatedCompositeFieldContainer[ImportFromS3Settings.Item]
    number_of_retries: int
    region: str
    scheme: ImportFromS3Settings.Scheme
    secret_key: str
    def __init__(self, endpoint: _Optional[str] = ..., scheme: _Optional[_Union[ImportFromS3Settings.Scheme, str]] = ..., bucket: _Optional[str] = ..., access_key: _Optional[str] = ..., secret_key: _Optional[str] = ..., items: _Optional[_Iterable[_Union[ImportFromS3Settings.Item, _Mapping]]] = ..., description: _Optional[str] = ..., number_of_retries: _Optional[int] = ..., region: _Optional[str] = ...) -> None: ...

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
    PROGRESS_DONE: ImportProgress.Progress
    PROGRESS_PREPARING: ImportProgress.Progress
    PROGRESS_TRANSFER_DATA: ImportProgress.Progress
    PROGRESS_UNSPECIFIED: ImportProgress.Progress
    def __init__(self) -> None: ...

class YdbDumpFormat(_message.Message):
    __slots__ = ["columns"]
    COLUMNS_FIELD_NUMBER: _ClassVar[int]
    columns: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, columns: _Optional[_Iterable[str]] = ...) -> None: ...
