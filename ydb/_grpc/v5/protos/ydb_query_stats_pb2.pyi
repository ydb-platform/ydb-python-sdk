from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CompilationStats(_message.Message):
    __slots__ = ["cpu_time_us", "duration_us", "from_cache"]
    CPU_TIME_US_FIELD_NUMBER: _ClassVar[int]
    DURATION_US_FIELD_NUMBER: _ClassVar[int]
    FROM_CACHE_FIELD_NUMBER: _ClassVar[int]
    cpu_time_us: int
    duration_us: int
    from_cache: bool
    def __init__(self, from_cache: bool = ..., duration_us: _Optional[int] = ..., cpu_time_us: _Optional[int] = ...) -> None: ...

class OperationStats(_message.Message):
    __slots__ = ["bytes", "rows"]
    BYTES_FIELD_NUMBER: _ClassVar[int]
    ROWS_FIELD_NUMBER: _ClassVar[int]
    bytes: int
    rows: int
    def __init__(self, rows: _Optional[int] = ..., bytes: _Optional[int] = ...) -> None: ...

class QueryPhaseStats(_message.Message):
    __slots__ = ["affected_shards", "cpu_time_us", "duration_us", "literal_phase", "table_access"]
    AFFECTED_SHARDS_FIELD_NUMBER: _ClassVar[int]
    CPU_TIME_US_FIELD_NUMBER: _ClassVar[int]
    DURATION_US_FIELD_NUMBER: _ClassVar[int]
    LITERAL_PHASE_FIELD_NUMBER: _ClassVar[int]
    TABLE_ACCESS_FIELD_NUMBER: _ClassVar[int]
    affected_shards: int
    cpu_time_us: int
    duration_us: int
    literal_phase: bool
    table_access: _containers.RepeatedCompositeFieldContainer[TableAccessStats]
    def __init__(self, duration_us: _Optional[int] = ..., table_access: _Optional[_Iterable[_Union[TableAccessStats, _Mapping]]] = ..., cpu_time_us: _Optional[int] = ..., affected_shards: _Optional[int] = ..., literal_phase: bool = ...) -> None: ...

class QueryStats(_message.Message):
    __slots__ = ["compilation", "process_cpu_time_us", "query_ast", "query_phases", "query_plan", "total_cpu_time_us", "total_duration_us"]
    COMPILATION_FIELD_NUMBER: _ClassVar[int]
    PROCESS_CPU_TIME_US_FIELD_NUMBER: _ClassVar[int]
    QUERY_AST_FIELD_NUMBER: _ClassVar[int]
    QUERY_PHASES_FIELD_NUMBER: _ClassVar[int]
    QUERY_PLAN_FIELD_NUMBER: _ClassVar[int]
    TOTAL_CPU_TIME_US_FIELD_NUMBER: _ClassVar[int]
    TOTAL_DURATION_US_FIELD_NUMBER: _ClassVar[int]
    compilation: CompilationStats
    process_cpu_time_us: int
    query_ast: str
    query_phases: _containers.RepeatedCompositeFieldContainer[QueryPhaseStats]
    query_plan: str
    total_cpu_time_us: int
    total_duration_us: int
    def __init__(self, query_phases: _Optional[_Iterable[_Union[QueryPhaseStats, _Mapping]]] = ..., compilation: _Optional[_Union[CompilationStats, _Mapping]] = ..., process_cpu_time_us: _Optional[int] = ..., query_plan: _Optional[str] = ..., query_ast: _Optional[str] = ..., total_duration_us: _Optional[int] = ..., total_cpu_time_us: _Optional[int] = ...) -> None: ...

class TableAccessStats(_message.Message):
    __slots__ = ["deletes", "name", "partitions_count", "reads", "updates"]
    DELETES_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PARTITIONS_COUNT_FIELD_NUMBER: _ClassVar[int]
    READS_FIELD_NUMBER: _ClassVar[int]
    UPDATES_FIELD_NUMBER: _ClassVar[int]
    deletes: OperationStats
    name: str
    partitions_count: int
    reads: OperationStats
    updates: OperationStats
    def __init__(self, name: _Optional[str] = ..., reads: _Optional[_Union[OperationStats, _Mapping]] = ..., updates: _Optional[_Union[OperationStats, _Mapping]] = ..., deletes: _Optional[_Union[OperationStats, _Mapping]] = ..., partitions_count: _Optional[int] = ...) -> None: ...
