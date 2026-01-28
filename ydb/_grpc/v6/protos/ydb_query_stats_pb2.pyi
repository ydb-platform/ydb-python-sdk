from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class OperationStats(_message.Message):
    __slots__ = ("rows", "bytes")
    ROWS_FIELD_NUMBER: _ClassVar[int]
    BYTES_FIELD_NUMBER: _ClassVar[int]
    rows: int
    bytes: int
    def __init__(self, rows: _Optional[int] = ..., bytes: _Optional[int] = ...) -> None: ...

class TableAccessStats(_message.Message):
    __slots__ = ("name", "reads", "updates", "deletes", "partitions_count")
    NAME_FIELD_NUMBER: _ClassVar[int]
    READS_FIELD_NUMBER: _ClassVar[int]
    UPDATES_FIELD_NUMBER: _ClassVar[int]
    DELETES_FIELD_NUMBER: _ClassVar[int]
    PARTITIONS_COUNT_FIELD_NUMBER: _ClassVar[int]
    name: str
    reads: OperationStats
    updates: OperationStats
    deletes: OperationStats
    partitions_count: int
    def __init__(self, name: _Optional[str] = ..., reads: _Optional[_Union[OperationStats, _Mapping]] = ..., updates: _Optional[_Union[OperationStats, _Mapping]] = ..., deletes: _Optional[_Union[OperationStats, _Mapping]] = ..., partitions_count: _Optional[int] = ...) -> None: ...

class QueryPhaseStats(_message.Message):
    __slots__ = ("duration_us", "table_access", "cpu_time_us", "affected_shards", "literal_phase")
    DURATION_US_FIELD_NUMBER: _ClassVar[int]
    TABLE_ACCESS_FIELD_NUMBER: _ClassVar[int]
    CPU_TIME_US_FIELD_NUMBER: _ClassVar[int]
    AFFECTED_SHARDS_FIELD_NUMBER: _ClassVar[int]
    LITERAL_PHASE_FIELD_NUMBER: _ClassVar[int]
    duration_us: int
    table_access: _containers.RepeatedCompositeFieldContainer[TableAccessStats]
    cpu_time_us: int
    affected_shards: int
    literal_phase: bool
    def __init__(self, duration_us: _Optional[int] = ..., table_access: _Optional[_Iterable[_Union[TableAccessStats, _Mapping]]] = ..., cpu_time_us: _Optional[int] = ..., affected_shards: _Optional[int] = ..., literal_phase: bool = ...) -> None: ...

class CompilationStats(_message.Message):
    __slots__ = ("from_cache", "duration_us", "cpu_time_us")
    FROM_CACHE_FIELD_NUMBER: _ClassVar[int]
    DURATION_US_FIELD_NUMBER: _ClassVar[int]
    CPU_TIME_US_FIELD_NUMBER: _ClassVar[int]
    from_cache: bool
    duration_us: int
    cpu_time_us: int
    def __init__(self, from_cache: bool = ..., duration_us: _Optional[int] = ..., cpu_time_us: _Optional[int] = ...) -> None: ...

class QueryStats(_message.Message):
    __slots__ = ("query_phases", "compilation", "process_cpu_time_us", "query_plan", "query_ast", "total_duration_us", "total_cpu_time_us")
    QUERY_PHASES_FIELD_NUMBER: _ClassVar[int]
    COMPILATION_FIELD_NUMBER: _ClassVar[int]
    PROCESS_CPU_TIME_US_FIELD_NUMBER: _ClassVar[int]
    QUERY_PLAN_FIELD_NUMBER: _ClassVar[int]
    QUERY_AST_FIELD_NUMBER: _ClassVar[int]
    TOTAL_DURATION_US_FIELD_NUMBER: _ClassVar[int]
    TOTAL_CPU_TIME_US_FIELD_NUMBER: _ClassVar[int]
    query_phases: _containers.RepeatedCompositeFieldContainer[QueryPhaseStats]
    compilation: CompilationStats
    process_cpu_time_us: int
    query_plan: str
    query_ast: str
    total_duration_us: int
    total_cpu_time_us: int
    def __init__(self, query_phases: _Optional[_Iterable[_Union[QueryPhaseStats, _Mapping]]] = ..., compilation: _Optional[_Union[CompilationStats, _Mapping]] = ..., process_cpu_time_us: _Optional[int] = ..., query_plan: _Optional[str] = ..., query_ast: _Optional[str] = ..., total_duration_us: _Optional[int] = ..., total_cpu_time_us: _Optional[int] = ...) -> None: ...
