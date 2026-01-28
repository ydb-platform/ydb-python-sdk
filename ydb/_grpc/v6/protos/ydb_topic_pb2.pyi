import datetime

from protos import ydb_operation_pb2 as _ydb_operation_pb2
from protos import ydb_scheme_pb2 as _ydb_scheme_pb2
from protos import ydb_status_codes_pb2 as _ydb_status_codes_pb2
from protos import ydb_issue_message_pb2 as _ydb_issue_message_pb2
from protos.annotations import sensitive_pb2 as _sensitive_pb2
from protos.annotations import validation_pb2 as _validation_pb2
from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Codec(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CODEC_UNSPECIFIED: _ClassVar[Codec]
    CODEC_RAW: _ClassVar[Codec]
    CODEC_GZIP: _ClassVar[Codec]
    CODEC_LZOP: _ClassVar[Codec]
    CODEC_ZSTD: _ClassVar[Codec]
    CODEC_CUSTOM: _ClassVar[Codec]

class AutoPartitioningStrategy(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    AUTO_PARTITIONING_STRATEGY_UNSPECIFIED: _ClassVar[AutoPartitioningStrategy]
    AUTO_PARTITIONING_STRATEGY_DISABLED: _ClassVar[AutoPartitioningStrategy]
    AUTO_PARTITIONING_STRATEGY_SCALE_UP: _ClassVar[AutoPartitioningStrategy]
    AUTO_PARTITIONING_STRATEGY_SCALE_UP_AND_DOWN: _ClassVar[AutoPartitioningStrategy]
    AUTO_PARTITIONING_STRATEGY_PAUSED: _ClassVar[AutoPartitioningStrategy]

class MeteringMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    METERING_MODE_UNSPECIFIED: _ClassVar[MeteringMode]
    METERING_MODE_RESERVED_CAPACITY: _ClassVar[MeteringMode]
    METERING_MODE_REQUEST_UNITS: _ClassVar[MeteringMode]
CODEC_UNSPECIFIED: Codec
CODEC_RAW: Codec
CODEC_GZIP: Codec
CODEC_LZOP: Codec
CODEC_ZSTD: Codec
CODEC_CUSTOM: Codec
AUTO_PARTITIONING_STRATEGY_UNSPECIFIED: AutoPartitioningStrategy
AUTO_PARTITIONING_STRATEGY_DISABLED: AutoPartitioningStrategy
AUTO_PARTITIONING_STRATEGY_SCALE_UP: AutoPartitioningStrategy
AUTO_PARTITIONING_STRATEGY_SCALE_UP_AND_DOWN: AutoPartitioningStrategy
AUTO_PARTITIONING_STRATEGY_PAUSED: AutoPartitioningStrategy
METERING_MODE_UNSPECIFIED: MeteringMode
METERING_MODE_RESERVED_CAPACITY: MeteringMode
METERING_MODE_REQUEST_UNITS: MeteringMode

class SupportedCodecs(_message.Message):
    __slots__ = ("codecs",)
    CODECS_FIELD_NUMBER: _ClassVar[int]
    codecs: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, codecs: _Optional[_Iterable[int]] = ...) -> None: ...

class OffsetsRange(_message.Message):
    __slots__ = ("start", "end")
    START_FIELD_NUMBER: _ClassVar[int]
    END_FIELD_NUMBER: _ClassVar[int]
    start: int
    end: int
    def __init__(self, start: _Optional[int] = ..., end: _Optional[int] = ...) -> None: ...

class UpdateTokenRequest(_message.Message):
    __slots__ = ("token",)
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    token: str
    def __init__(self, token: _Optional[str] = ...) -> None: ...

class UpdateTokenResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PartitionWithGeneration(_message.Message):
    __slots__ = ("partition_id", "generation")
    PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
    GENERATION_FIELD_NUMBER: _ClassVar[int]
    partition_id: int
    generation: int
    def __init__(self, partition_id: _Optional[int] = ..., generation: _Optional[int] = ...) -> None: ...

class MetadataItem(_message.Message):
    __slots__ = ("key", "value")
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: str
    value: bytes
    def __init__(self, key: _Optional[str] = ..., value: _Optional[bytes] = ...) -> None: ...

class StreamWriteMessage(_message.Message):
    __slots__ = ()
    class FromClient(_message.Message):
        __slots__ = ("init_request", "write_request", "update_token_request")
        INIT_REQUEST_FIELD_NUMBER: _ClassVar[int]
        WRITE_REQUEST_FIELD_NUMBER: _ClassVar[int]
        UPDATE_TOKEN_REQUEST_FIELD_NUMBER: _ClassVar[int]
        init_request: StreamWriteMessage.InitRequest
        write_request: StreamWriteMessage.WriteRequest
        update_token_request: UpdateTokenRequest
        def __init__(self, init_request: _Optional[_Union[StreamWriteMessage.InitRequest, _Mapping]] = ..., write_request: _Optional[_Union[StreamWriteMessage.WriteRequest, _Mapping]] = ..., update_token_request: _Optional[_Union[UpdateTokenRequest, _Mapping]] = ...) -> None: ...
    class FromServer(_message.Message):
        __slots__ = ("status", "issues", "init_response", "write_response", "update_token_response")
        STATUS_FIELD_NUMBER: _ClassVar[int]
        ISSUES_FIELD_NUMBER: _ClassVar[int]
        INIT_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        WRITE_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        UPDATE_TOKEN_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        status: _ydb_status_codes_pb2.StatusIds.StatusCode
        issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
        init_response: StreamWriteMessage.InitResponse
        write_response: StreamWriteMessage.WriteResponse
        update_token_response: UpdateTokenResponse
        def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., init_response: _Optional[_Union[StreamWriteMessage.InitResponse, _Mapping]] = ..., write_response: _Optional[_Union[StreamWriteMessage.WriteResponse, _Mapping]] = ..., update_token_response: _Optional[_Union[UpdateTokenResponse, _Mapping]] = ...) -> None: ...
    class InitRequest(_message.Message):
        __slots__ = ("path", "producer_id", "write_session_meta", "message_group_id", "partition_id", "partition_with_generation", "get_last_seq_no")
        class WriteSessionMetaEntry(_message.Message):
            __slots__ = ("key", "value")
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        PATH_FIELD_NUMBER: _ClassVar[int]
        PRODUCER_ID_FIELD_NUMBER: _ClassVar[int]
        WRITE_SESSION_META_FIELD_NUMBER: _ClassVar[int]
        MESSAGE_GROUP_ID_FIELD_NUMBER: _ClassVar[int]
        PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
        PARTITION_WITH_GENERATION_FIELD_NUMBER: _ClassVar[int]
        GET_LAST_SEQ_NO_FIELD_NUMBER: _ClassVar[int]
        path: str
        producer_id: str
        write_session_meta: _containers.ScalarMap[str, str]
        message_group_id: str
        partition_id: int
        partition_with_generation: PartitionWithGeneration
        get_last_seq_no: bool
        def __init__(self, path: _Optional[str] = ..., producer_id: _Optional[str] = ..., write_session_meta: _Optional[_Mapping[str, str]] = ..., message_group_id: _Optional[str] = ..., partition_id: _Optional[int] = ..., partition_with_generation: _Optional[_Union[PartitionWithGeneration, _Mapping]] = ..., get_last_seq_no: bool = ...) -> None: ...
    class InitResponse(_message.Message):
        __slots__ = ("last_seq_no", "session_id", "partition_id", "supported_codecs")
        LAST_SEQ_NO_FIELD_NUMBER: _ClassVar[int]
        SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
        SUPPORTED_CODECS_FIELD_NUMBER: _ClassVar[int]
        last_seq_no: int
        session_id: str
        partition_id: int
        supported_codecs: SupportedCodecs
        def __init__(self, last_seq_no: _Optional[int] = ..., session_id: _Optional[str] = ..., partition_id: _Optional[int] = ..., supported_codecs: _Optional[_Union[SupportedCodecs, _Mapping]] = ...) -> None: ...
    class WriteRequest(_message.Message):
        __slots__ = ("messages", "codec", "tx")
        class MessageData(_message.Message):
            __slots__ = ("seq_no", "created_at", "data", "uncompressed_size", "message_group_id", "partition_id", "partition_with_generation", "metadata_items")
            SEQ_NO_FIELD_NUMBER: _ClassVar[int]
            CREATED_AT_FIELD_NUMBER: _ClassVar[int]
            DATA_FIELD_NUMBER: _ClassVar[int]
            UNCOMPRESSED_SIZE_FIELD_NUMBER: _ClassVar[int]
            MESSAGE_GROUP_ID_FIELD_NUMBER: _ClassVar[int]
            PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
            PARTITION_WITH_GENERATION_FIELD_NUMBER: _ClassVar[int]
            METADATA_ITEMS_FIELD_NUMBER: _ClassVar[int]
            seq_no: int
            created_at: _timestamp_pb2.Timestamp
            data: bytes
            uncompressed_size: int
            message_group_id: str
            partition_id: int
            partition_with_generation: PartitionWithGeneration
            metadata_items: _containers.RepeatedCompositeFieldContainer[MetadataItem]
            def __init__(self, seq_no: _Optional[int] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., data: _Optional[bytes] = ..., uncompressed_size: _Optional[int] = ..., message_group_id: _Optional[str] = ..., partition_id: _Optional[int] = ..., partition_with_generation: _Optional[_Union[PartitionWithGeneration, _Mapping]] = ..., metadata_items: _Optional[_Iterable[_Union[MetadataItem, _Mapping]]] = ...) -> None: ...
        MESSAGES_FIELD_NUMBER: _ClassVar[int]
        CODEC_FIELD_NUMBER: _ClassVar[int]
        TX_FIELD_NUMBER: _ClassVar[int]
        messages: _containers.RepeatedCompositeFieldContainer[StreamWriteMessage.WriteRequest.MessageData]
        codec: int
        tx: TransactionIdentity
        def __init__(self, messages: _Optional[_Iterable[_Union[StreamWriteMessage.WriteRequest.MessageData, _Mapping]]] = ..., codec: _Optional[int] = ..., tx: _Optional[_Union[TransactionIdentity, _Mapping]] = ...) -> None: ...
    class WriteResponse(_message.Message):
        __slots__ = ("acks", "partition_id", "write_statistics")
        class WriteAck(_message.Message):
            __slots__ = ("seq_no", "written", "skipped", "written_in_tx")
            class Written(_message.Message):
                __slots__ = ("offset",)
                OFFSET_FIELD_NUMBER: _ClassVar[int]
                offset: int
                def __init__(self, offset: _Optional[int] = ...) -> None: ...
            class Skipped(_message.Message):
                __slots__ = ("reason",)
                class Reason(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                    __slots__ = ()
                    REASON_UNSPECIFIED: _ClassVar[StreamWriteMessage.WriteResponse.WriteAck.Skipped.Reason]
                    REASON_ALREADY_WRITTEN: _ClassVar[StreamWriteMessage.WriteResponse.WriteAck.Skipped.Reason]
                REASON_UNSPECIFIED: StreamWriteMessage.WriteResponse.WriteAck.Skipped.Reason
                REASON_ALREADY_WRITTEN: StreamWriteMessage.WriteResponse.WriteAck.Skipped.Reason
                REASON_FIELD_NUMBER: _ClassVar[int]
                reason: StreamWriteMessage.WriteResponse.WriteAck.Skipped.Reason
                def __init__(self, reason: _Optional[_Union[StreamWriteMessage.WriteResponse.WriteAck.Skipped.Reason, str]] = ...) -> None: ...
            class WrittenInTx(_message.Message):
                __slots__ = ()
                def __init__(self) -> None: ...
            SEQ_NO_FIELD_NUMBER: _ClassVar[int]
            WRITTEN_FIELD_NUMBER: _ClassVar[int]
            SKIPPED_FIELD_NUMBER: _ClassVar[int]
            WRITTEN_IN_TX_FIELD_NUMBER: _ClassVar[int]
            seq_no: int
            written: StreamWriteMessage.WriteResponse.WriteAck.Written
            skipped: StreamWriteMessage.WriteResponse.WriteAck.Skipped
            written_in_tx: StreamWriteMessage.WriteResponse.WriteAck.WrittenInTx
            def __init__(self, seq_no: _Optional[int] = ..., written: _Optional[_Union[StreamWriteMessage.WriteResponse.WriteAck.Written, _Mapping]] = ..., skipped: _Optional[_Union[StreamWriteMessage.WriteResponse.WriteAck.Skipped, _Mapping]] = ..., written_in_tx: _Optional[_Union[StreamWriteMessage.WriteResponse.WriteAck.WrittenInTx, _Mapping]] = ...) -> None: ...
        class WriteStatistics(_message.Message):
            __slots__ = ("persisting_time", "min_queue_wait_time", "max_queue_wait_time", "partition_quota_wait_time", "topic_quota_wait_time")
            PERSISTING_TIME_FIELD_NUMBER: _ClassVar[int]
            MIN_QUEUE_WAIT_TIME_FIELD_NUMBER: _ClassVar[int]
            MAX_QUEUE_WAIT_TIME_FIELD_NUMBER: _ClassVar[int]
            PARTITION_QUOTA_WAIT_TIME_FIELD_NUMBER: _ClassVar[int]
            TOPIC_QUOTA_WAIT_TIME_FIELD_NUMBER: _ClassVar[int]
            persisting_time: _duration_pb2.Duration
            min_queue_wait_time: _duration_pb2.Duration
            max_queue_wait_time: _duration_pb2.Duration
            partition_quota_wait_time: _duration_pb2.Duration
            topic_quota_wait_time: _duration_pb2.Duration
            def __init__(self, persisting_time: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., min_queue_wait_time: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., max_queue_wait_time: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., partition_quota_wait_time: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., topic_quota_wait_time: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ...) -> None: ...
        ACKS_FIELD_NUMBER: _ClassVar[int]
        PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
        WRITE_STATISTICS_FIELD_NUMBER: _ClassVar[int]
        acks: _containers.RepeatedCompositeFieldContainer[StreamWriteMessage.WriteResponse.WriteAck]
        partition_id: int
        write_statistics: StreamWriteMessage.WriteResponse.WriteStatistics
        def __init__(self, acks: _Optional[_Iterable[_Union[StreamWriteMessage.WriteResponse.WriteAck, _Mapping]]] = ..., partition_id: _Optional[int] = ..., write_statistics: _Optional[_Union[StreamWriteMessage.WriteResponse.WriteStatistics, _Mapping]] = ...) -> None: ...
    def __init__(self) -> None: ...

class StreamReadMessage(_message.Message):
    __slots__ = ()
    class PartitionSession(_message.Message):
        __slots__ = ("partition_session_id", "path", "partition_id")
        PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        PATH_FIELD_NUMBER: _ClassVar[int]
        PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
        partition_session_id: int
        path: str
        partition_id: int
        def __init__(self, partition_session_id: _Optional[int] = ..., path: _Optional[str] = ..., partition_id: _Optional[int] = ...) -> None: ...
    class FromClient(_message.Message):
        __slots__ = ("init_request", "read_request", "commit_offset_request", "partition_session_status_request", "update_token_request", "direct_read_ack", "start_partition_session_response", "stop_partition_session_response")
        INIT_REQUEST_FIELD_NUMBER: _ClassVar[int]
        READ_REQUEST_FIELD_NUMBER: _ClassVar[int]
        COMMIT_OFFSET_REQUEST_FIELD_NUMBER: _ClassVar[int]
        PARTITION_SESSION_STATUS_REQUEST_FIELD_NUMBER: _ClassVar[int]
        UPDATE_TOKEN_REQUEST_FIELD_NUMBER: _ClassVar[int]
        DIRECT_READ_ACK_FIELD_NUMBER: _ClassVar[int]
        START_PARTITION_SESSION_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        STOP_PARTITION_SESSION_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        init_request: StreamReadMessage.InitRequest
        read_request: StreamReadMessage.ReadRequest
        commit_offset_request: StreamReadMessage.CommitOffsetRequest
        partition_session_status_request: StreamReadMessage.PartitionSessionStatusRequest
        update_token_request: UpdateTokenRequest
        direct_read_ack: StreamReadMessage.DirectReadAck
        start_partition_session_response: StreamReadMessage.StartPartitionSessionResponse
        stop_partition_session_response: StreamReadMessage.StopPartitionSessionResponse
        def __init__(self, init_request: _Optional[_Union[StreamReadMessage.InitRequest, _Mapping]] = ..., read_request: _Optional[_Union[StreamReadMessage.ReadRequest, _Mapping]] = ..., commit_offset_request: _Optional[_Union[StreamReadMessage.CommitOffsetRequest, _Mapping]] = ..., partition_session_status_request: _Optional[_Union[StreamReadMessage.PartitionSessionStatusRequest, _Mapping]] = ..., update_token_request: _Optional[_Union[UpdateTokenRequest, _Mapping]] = ..., direct_read_ack: _Optional[_Union[StreamReadMessage.DirectReadAck, _Mapping]] = ..., start_partition_session_response: _Optional[_Union[StreamReadMessage.StartPartitionSessionResponse, _Mapping]] = ..., stop_partition_session_response: _Optional[_Union[StreamReadMessage.StopPartitionSessionResponse, _Mapping]] = ...) -> None: ...
    class FromServer(_message.Message):
        __slots__ = ("status", "issues", "init_response", "read_response", "commit_offset_response", "partition_session_status_response", "update_token_response", "start_partition_session_request", "stop_partition_session_request", "update_partition_session", "end_partition_session")
        STATUS_FIELD_NUMBER: _ClassVar[int]
        ISSUES_FIELD_NUMBER: _ClassVar[int]
        INIT_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        READ_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        COMMIT_OFFSET_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        PARTITION_SESSION_STATUS_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        UPDATE_TOKEN_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        START_PARTITION_SESSION_REQUEST_FIELD_NUMBER: _ClassVar[int]
        STOP_PARTITION_SESSION_REQUEST_FIELD_NUMBER: _ClassVar[int]
        UPDATE_PARTITION_SESSION_FIELD_NUMBER: _ClassVar[int]
        END_PARTITION_SESSION_FIELD_NUMBER: _ClassVar[int]
        status: _ydb_status_codes_pb2.StatusIds.StatusCode
        issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
        init_response: StreamReadMessage.InitResponse
        read_response: StreamReadMessage.ReadResponse
        commit_offset_response: StreamReadMessage.CommitOffsetResponse
        partition_session_status_response: StreamReadMessage.PartitionSessionStatusResponse
        update_token_response: UpdateTokenResponse
        start_partition_session_request: StreamReadMessage.StartPartitionSessionRequest
        stop_partition_session_request: StreamReadMessage.StopPartitionSessionRequest
        update_partition_session: StreamReadMessage.UpdatePartitionSession
        end_partition_session: StreamReadMessage.EndPartitionSession
        def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., init_response: _Optional[_Union[StreamReadMessage.InitResponse, _Mapping]] = ..., read_response: _Optional[_Union[StreamReadMessage.ReadResponse, _Mapping]] = ..., commit_offset_response: _Optional[_Union[StreamReadMessage.CommitOffsetResponse, _Mapping]] = ..., partition_session_status_response: _Optional[_Union[StreamReadMessage.PartitionSessionStatusResponse, _Mapping]] = ..., update_token_response: _Optional[_Union[UpdateTokenResponse, _Mapping]] = ..., start_partition_session_request: _Optional[_Union[StreamReadMessage.StartPartitionSessionRequest, _Mapping]] = ..., stop_partition_session_request: _Optional[_Union[StreamReadMessage.StopPartitionSessionRequest, _Mapping]] = ..., update_partition_session: _Optional[_Union[StreamReadMessage.UpdatePartitionSession, _Mapping]] = ..., end_partition_session: _Optional[_Union[StreamReadMessage.EndPartitionSession, _Mapping]] = ...) -> None: ...
    class InitRequest(_message.Message):
        __slots__ = ("topics_read_settings", "consumer", "reader_name", "direct_read", "auto_partitioning_support")
        class TopicReadSettings(_message.Message):
            __slots__ = ("path", "partition_ids", "max_lag", "read_from")
            PATH_FIELD_NUMBER: _ClassVar[int]
            PARTITION_IDS_FIELD_NUMBER: _ClassVar[int]
            MAX_LAG_FIELD_NUMBER: _ClassVar[int]
            READ_FROM_FIELD_NUMBER: _ClassVar[int]
            path: str
            partition_ids: _containers.RepeatedScalarFieldContainer[int]
            max_lag: _duration_pb2.Duration
            read_from: _timestamp_pb2.Timestamp
            def __init__(self, path: _Optional[str] = ..., partition_ids: _Optional[_Iterable[int]] = ..., max_lag: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., read_from: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
        TOPICS_READ_SETTINGS_FIELD_NUMBER: _ClassVar[int]
        CONSUMER_FIELD_NUMBER: _ClassVar[int]
        READER_NAME_FIELD_NUMBER: _ClassVar[int]
        DIRECT_READ_FIELD_NUMBER: _ClassVar[int]
        AUTO_PARTITIONING_SUPPORT_FIELD_NUMBER: _ClassVar[int]
        topics_read_settings: _containers.RepeatedCompositeFieldContainer[StreamReadMessage.InitRequest.TopicReadSettings]
        consumer: str
        reader_name: str
        direct_read: bool
        auto_partitioning_support: bool
        def __init__(self, topics_read_settings: _Optional[_Iterable[_Union[StreamReadMessage.InitRequest.TopicReadSettings, _Mapping]]] = ..., consumer: _Optional[str] = ..., reader_name: _Optional[str] = ..., direct_read: bool = ..., auto_partitioning_support: bool = ...) -> None: ...
    class InitResponse(_message.Message):
        __slots__ = ("session_id",)
        SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        session_id: str
        def __init__(self, session_id: _Optional[str] = ...) -> None: ...
    class ReadRequest(_message.Message):
        __slots__ = ("bytes_size",)
        BYTES_SIZE_FIELD_NUMBER: _ClassVar[int]
        bytes_size: int
        def __init__(self, bytes_size: _Optional[int] = ...) -> None: ...
    class ReadResponse(_message.Message):
        __slots__ = ("partition_data", "bytes_size")
        class MessageData(_message.Message):
            __slots__ = ("offset", "seq_no", "created_at", "data", "uncompressed_size", "message_group_id", "metadata_items")
            OFFSET_FIELD_NUMBER: _ClassVar[int]
            SEQ_NO_FIELD_NUMBER: _ClassVar[int]
            CREATED_AT_FIELD_NUMBER: _ClassVar[int]
            DATA_FIELD_NUMBER: _ClassVar[int]
            UNCOMPRESSED_SIZE_FIELD_NUMBER: _ClassVar[int]
            MESSAGE_GROUP_ID_FIELD_NUMBER: _ClassVar[int]
            METADATA_ITEMS_FIELD_NUMBER: _ClassVar[int]
            offset: int
            seq_no: int
            created_at: _timestamp_pb2.Timestamp
            data: bytes
            uncompressed_size: int
            message_group_id: str
            metadata_items: _containers.RepeatedCompositeFieldContainer[MetadataItem]
            def __init__(self, offset: _Optional[int] = ..., seq_no: _Optional[int] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., data: _Optional[bytes] = ..., uncompressed_size: _Optional[int] = ..., message_group_id: _Optional[str] = ..., metadata_items: _Optional[_Iterable[_Union[MetadataItem, _Mapping]]] = ...) -> None: ...
        class Batch(_message.Message):
            __slots__ = ("message_data", "producer_id", "write_session_meta", "codec", "written_at")
            class WriteSessionMetaEntry(_message.Message):
                __slots__ = ("key", "value")
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            MESSAGE_DATA_FIELD_NUMBER: _ClassVar[int]
            PRODUCER_ID_FIELD_NUMBER: _ClassVar[int]
            WRITE_SESSION_META_FIELD_NUMBER: _ClassVar[int]
            CODEC_FIELD_NUMBER: _ClassVar[int]
            WRITTEN_AT_FIELD_NUMBER: _ClassVar[int]
            message_data: _containers.RepeatedCompositeFieldContainer[StreamReadMessage.ReadResponse.MessageData]
            producer_id: str
            write_session_meta: _containers.ScalarMap[str, str]
            codec: int
            written_at: _timestamp_pb2.Timestamp
            def __init__(self, message_data: _Optional[_Iterable[_Union[StreamReadMessage.ReadResponse.MessageData, _Mapping]]] = ..., producer_id: _Optional[str] = ..., write_session_meta: _Optional[_Mapping[str, str]] = ..., codec: _Optional[int] = ..., written_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
        class PartitionData(_message.Message):
            __slots__ = ("partition_session_id", "batches")
            PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
            BATCHES_FIELD_NUMBER: _ClassVar[int]
            partition_session_id: int
            batches: _containers.RepeatedCompositeFieldContainer[StreamReadMessage.ReadResponse.Batch]
            def __init__(self, partition_session_id: _Optional[int] = ..., batches: _Optional[_Iterable[_Union[StreamReadMessage.ReadResponse.Batch, _Mapping]]] = ...) -> None: ...
        PARTITION_DATA_FIELD_NUMBER: _ClassVar[int]
        BYTES_SIZE_FIELD_NUMBER: _ClassVar[int]
        partition_data: _containers.RepeatedCompositeFieldContainer[StreamReadMessage.ReadResponse.PartitionData]
        bytes_size: int
        def __init__(self, partition_data: _Optional[_Iterable[_Union[StreamReadMessage.ReadResponse.PartitionData, _Mapping]]] = ..., bytes_size: _Optional[int] = ...) -> None: ...
    class CommitOffsetRequest(_message.Message):
        __slots__ = ("commit_offsets",)
        class PartitionCommitOffset(_message.Message):
            __slots__ = ("partition_session_id", "offsets")
            PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
            OFFSETS_FIELD_NUMBER: _ClassVar[int]
            partition_session_id: int
            offsets: _containers.RepeatedCompositeFieldContainer[OffsetsRange]
            def __init__(self, partition_session_id: _Optional[int] = ..., offsets: _Optional[_Iterable[_Union[OffsetsRange, _Mapping]]] = ...) -> None: ...
        COMMIT_OFFSETS_FIELD_NUMBER: _ClassVar[int]
        commit_offsets: _containers.RepeatedCompositeFieldContainer[StreamReadMessage.CommitOffsetRequest.PartitionCommitOffset]
        def __init__(self, commit_offsets: _Optional[_Iterable[_Union[StreamReadMessage.CommitOffsetRequest.PartitionCommitOffset, _Mapping]]] = ...) -> None: ...
    class CommitOffsetResponse(_message.Message):
        __slots__ = ("partitions_committed_offsets",)
        class PartitionCommittedOffset(_message.Message):
            __slots__ = ("partition_session_id", "committed_offset")
            PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
            COMMITTED_OFFSET_FIELD_NUMBER: _ClassVar[int]
            partition_session_id: int
            committed_offset: int
            def __init__(self, partition_session_id: _Optional[int] = ..., committed_offset: _Optional[int] = ...) -> None: ...
        PARTITIONS_COMMITTED_OFFSETS_FIELD_NUMBER: _ClassVar[int]
        partitions_committed_offsets: _containers.RepeatedCompositeFieldContainer[StreamReadMessage.CommitOffsetResponse.PartitionCommittedOffset]
        def __init__(self, partitions_committed_offsets: _Optional[_Iterable[_Union[StreamReadMessage.CommitOffsetResponse.PartitionCommittedOffset, _Mapping]]] = ...) -> None: ...
    class PartitionSessionStatusRequest(_message.Message):
        __slots__ = ("partition_session_id",)
        PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        partition_session_id: int
        def __init__(self, partition_session_id: _Optional[int] = ...) -> None: ...
    class PartitionSessionStatusResponse(_message.Message):
        __slots__ = ("partition_session_id", "partition_offsets", "committed_offset", "write_time_high_watermark")
        PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        PARTITION_OFFSETS_FIELD_NUMBER: _ClassVar[int]
        COMMITTED_OFFSET_FIELD_NUMBER: _ClassVar[int]
        WRITE_TIME_HIGH_WATERMARK_FIELD_NUMBER: _ClassVar[int]
        partition_session_id: int
        partition_offsets: OffsetsRange
        committed_offset: int
        write_time_high_watermark: _timestamp_pb2.Timestamp
        def __init__(self, partition_session_id: _Optional[int] = ..., partition_offsets: _Optional[_Union[OffsetsRange, _Mapping]] = ..., committed_offset: _Optional[int] = ..., write_time_high_watermark: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
    class StartPartitionSessionRequest(_message.Message):
        __slots__ = ("partition_session", "committed_offset", "partition_offsets", "partition_location")
        PARTITION_SESSION_FIELD_NUMBER: _ClassVar[int]
        COMMITTED_OFFSET_FIELD_NUMBER: _ClassVar[int]
        PARTITION_OFFSETS_FIELD_NUMBER: _ClassVar[int]
        PARTITION_LOCATION_FIELD_NUMBER: _ClassVar[int]
        partition_session: StreamReadMessage.PartitionSession
        committed_offset: int
        partition_offsets: OffsetsRange
        partition_location: PartitionLocation
        def __init__(self, partition_session: _Optional[_Union[StreamReadMessage.PartitionSession, _Mapping]] = ..., committed_offset: _Optional[int] = ..., partition_offsets: _Optional[_Union[OffsetsRange, _Mapping]] = ..., partition_location: _Optional[_Union[PartitionLocation, _Mapping]] = ...) -> None: ...
    class StartPartitionSessionResponse(_message.Message):
        __slots__ = ("partition_session_id", "read_offset", "commit_offset")
        PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        READ_OFFSET_FIELD_NUMBER: _ClassVar[int]
        COMMIT_OFFSET_FIELD_NUMBER: _ClassVar[int]
        partition_session_id: int
        read_offset: int
        commit_offset: int
        def __init__(self, partition_session_id: _Optional[int] = ..., read_offset: _Optional[int] = ..., commit_offset: _Optional[int] = ...) -> None: ...
    class StopPartitionSessionRequest(_message.Message):
        __slots__ = ("partition_session_id", "graceful", "committed_offset", "last_direct_read_id")
        PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        GRACEFUL_FIELD_NUMBER: _ClassVar[int]
        COMMITTED_OFFSET_FIELD_NUMBER: _ClassVar[int]
        LAST_DIRECT_READ_ID_FIELD_NUMBER: _ClassVar[int]
        partition_session_id: int
        graceful: bool
        committed_offset: int
        last_direct_read_id: int
        def __init__(self, partition_session_id: _Optional[int] = ..., graceful: bool = ..., committed_offset: _Optional[int] = ..., last_direct_read_id: _Optional[int] = ...) -> None: ...
    class StopPartitionSessionResponse(_message.Message):
        __slots__ = ("partition_session_id", "graceful")
        PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        GRACEFUL_FIELD_NUMBER: _ClassVar[int]
        partition_session_id: int
        graceful: bool
        def __init__(self, partition_session_id: _Optional[int] = ..., graceful: bool = ...) -> None: ...
    class UpdatePartitionSession(_message.Message):
        __slots__ = ("partition_session_id", "partition_location")
        PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        PARTITION_LOCATION_FIELD_NUMBER: _ClassVar[int]
        partition_session_id: int
        partition_location: PartitionLocation
        def __init__(self, partition_session_id: _Optional[int] = ..., partition_location: _Optional[_Union[PartitionLocation, _Mapping]] = ...) -> None: ...
    class DirectReadAck(_message.Message):
        __slots__ = ("partition_session_id", "direct_read_id")
        PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        DIRECT_READ_ID_FIELD_NUMBER: _ClassVar[int]
        partition_session_id: int
        direct_read_id: int
        def __init__(self, partition_session_id: _Optional[int] = ..., direct_read_id: _Optional[int] = ...) -> None: ...
    class EndPartitionSession(_message.Message):
        __slots__ = ("partition_session_id", "adjacent_partition_ids", "child_partition_ids")
        PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        ADJACENT_PARTITION_IDS_FIELD_NUMBER: _ClassVar[int]
        CHILD_PARTITION_IDS_FIELD_NUMBER: _ClassVar[int]
        partition_session_id: int
        adjacent_partition_ids: _containers.RepeatedScalarFieldContainer[int]
        child_partition_ids: _containers.RepeatedScalarFieldContainer[int]
        def __init__(self, partition_session_id: _Optional[int] = ..., adjacent_partition_ids: _Optional[_Iterable[int]] = ..., child_partition_ids: _Optional[_Iterable[int]] = ...) -> None: ...
    def __init__(self) -> None: ...

class StreamDirectReadMessage(_message.Message):
    __slots__ = ()
    class FromClient(_message.Message):
        __slots__ = ("init_request", "start_direct_read_partition_session_request", "update_token_request")
        INIT_REQUEST_FIELD_NUMBER: _ClassVar[int]
        START_DIRECT_READ_PARTITION_SESSION_REQUEST_FIELD_NUMBER: _ClassVar[int]
        UPDATE_TOKEN_REQUEST_FIELD_NUMBER: _ClassVar[int]
        init_request: StreamDirectReadMessage.InitRequest
        start_direct_read_partition_session_request: StreamDirectReadMessage.StartDirectReadPartitionSessionRequest
        update_token_request: UpdateTokenRequest
        def __init__(self, init_request: _Optional[_Union[StreamDirectReadMessage.InitRequest, _Mapping]] = ..., start_direct_read_partition_session_request: _Optional[_Union[StreamDirectReadMessage.StartDirectReadPartitionSessionRequest, _Mapping]] = ..., update_token_request: _Optional[_Union[UpdateTokenRequest, _Mapping]] = ...) -> None: ...
    class FromServer(_message.Message):
        __slots__ = ("status", "issues", "init_response", "start_direct_read_partition_session_response", "stop_direct_read_partition_session", "direct_read_response", "update_token_response")
        STATUS_FIELD_NUMBER: _ClassVar[int]
        ISSUES_FIELD_NUMBER: _ClassVar[int]
        INIT_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        START_DIRECT_READ_PARTITION_SESSION_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        STOP_DIRECT_READ_PARTITION_SESSION_FIELD_NUMBER: _ClassVar[int]
        DIRECT_READ_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        UPDATE_TOKEN_RESPONSE_FIELD_NUMBER: _ClassVar[int]
        status: _ydb_status_codes_pb2.StatusIds.StatusCode
        issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
        init_response: StreamDirectReadMessage.InitResponse
        start_direct_read_partition_session_response: StreamDirectReadMessage.StartDirectReadPartitionSessionResponse
        stop_direct_read_partition_session: StreamDirectReadMessage.StopDirectReadPartitionSession
        direct_read_response: StreamDirectReadMessage.DirectReadResponse
        update_token_response: UpdateTokenResponse
        def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., init_response: _Optional[_Union[StreamDirectReadMessage.InitResponse, _Mapping]] = ..., start_direct_read_partition_session_response: _Optional[_Union[StreamDirectReadMessage.StartDirectReadPartitionSessionResponse, _Mapping]] = ..., stop_direct_read_partition_session: _Optional[_Union[StreamDirectReadMessage.StopDirectReadPartitionSession, _Mapping]] = ..., direct_read_response: _Optional[_Union[StreamDirectReadMessage.DirectReadResponse, _Mapping]] = ..., update_token_response: _Optional[_Union[UpdateTokenResponse, _Mapping]] = ...) -> None: ...
    class InitRequest(_message.Message):
        __slots__ = ("session_id", "topics_read_settings", "consumer")
        class TopicReadSettings(_message.Message):
            __slots__ = ("path",)
            PATH_FIELD_NUMBER: _ClassVar[int]
            path: str
            def __init__(self, path: _Optional[str] = ...) -> None: ...
        SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        TOPICS_READ_SETTINGS_FIELD_NUMBER: _ClassVar[int]
        CONSUMER_FIELD_NUMBER: _ClassVar[int]
        session_id: str
        topics_read_settings: _containers.RepeatedCompositeFieldContainer[StreamDirectReadMessage.InitRequest.TopicReadSettings]
        consumer: str
        def __init__(self, session_id: _Optional[str] = ..., topics_read_settings: _Optional[_Iterable[_Union[StreamDirectReadMessage.InitRequest.TopicReadSettings, _Mapping]]] = ..., consumer: _Optional[str] = ...) -> None: ...
    class InitResponse(_message.Message):
        __slots__ = ()
        def __init__(self) -> None: ...
    class StartDirectReadPartitionSessionRequest(_message.Message):
        __slots__ = ("partition_session_id", "last_direct_read_id", "generation")
        PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        LAST_DIRECT_READ_ID_FIELD_NUMBER: _ClassVar[int]
        GENERATION_FIELD_NUMBER: _ClassVar[int]
        partition_session_id: int
        last_direct_read_id: int
        generation: int
        def __init__(self, partition_session_id: _Optional[int] = ..., last_direct_read_id: _Optional[int] = ..., generation: _Optional[int] = ...) -> None: ...
    class StartDirectReadPartitionSessionResponse(_message.Message):
        __slots__ = ("partition_session_id", "generation")
        PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        GENERATION_FIELD_NUMBER: _ClassVar[int]
        partition_session_id: int
        generation: int
        def __init__(self, partition_session_id: _Optional[int] = ..., generation: _Optional[int] = ...) -> None: ...
    class StopDirectReadPartitionSession(_message.Message):
        __slots__ = ("status", "issues", "partition_session_id", "generation")
        STATUS_FIELD_NUMBER: _ClassVar[int]
        ISSUES_FIELD_NUMBER: _ClassVar[int]
        PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        GENERATION_FIELD_NUMBER: _ClassVar[int]
        status: _ydb_status_codes_pb2.StatusIds.StatusCode
        issues: _containers.RepeatedCompositeFieldContainer[_ydb_issue_message_pb2.IssueMessage]
        partition_session_id: int
        generation: int
        def __init__(self, status: _Optional[_Union[_ydb_status_codes_pb2.StatusIds.StatusCode, str]] = ..., issues: _Optional[_Iterable[_Union[_ydb_issue_message_pb2.IssueMessage, _Mapping]]] = ..., partition_session_id: _Optional[int] = ..., generation: _Optional[int] = ...) -> None: ...
    class DirectReadResponse(_message.Message):
        __slots__ = ("partition_session_id", "direct_read_id", "partition_data", "bytes_size")
        PARTITION_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        DIRECT_READ_ID_FIELD_NUMBER: _ClassVar[int]
        PARTITION_DATA_FIELD_NUMBER: _ClassVar[int]
        BYTES_SIZE_FIELD_NUMBER: _ClassVar[int]
        partition_session_id: int
        direct_read_id: int
        partition_data: StreamReadMessage.ReadResponse.PartitionData
        bytes_size: int
        def __init__(self, partition_session_id: _Optional[int] = ..., direct_read_id: _Optional[int] = ..., partition_data: _Optional[_Union[StreamReadMessage.ReadResponse.PartitionData, _Mapping]] = ..., bytes_size: _Optional[int] = ...) -> None: ...
    def __init__(self) -> None: ...

class TransactionIdentity(_message.Message):
    __slots__ = ("id", "session")
    ID_FIELD_NUMBER: _ClassVar[int]
    SESSION_FIELD_NUMBER: _ClassVar[int]
    id: str
    session: str
    def __init__(self, id: _Optional[str] = ..., session: _Optional[str] = ...) -> None: ...

class UpdateOffsetsInTransactionRequest(_message.Message):
    __slots__ = ("operation_params", "tx", "topics", "consumer")
    class TopicOffsets(_message.Message):
        __slots__ = ("path", "partitions")
        class PartitionOffsets(_message.Message):
            __slots__ = ("partition_id", "partition_offsets")
            PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
            PARTITION_OFFSETS_FIELD_NUMBER: _ClassVar[int]
            partition_id: int
            partition_offsets: _containers.RepeatedCompositeFieldContainer[OffsetsRange]
            def __init__(self, partition_id: _Optional[int] = ..., partition_offsets: _Optional[_Iterable[_Union[OffsetsRange, _Mapping]]] = ...) -> None: ...
        PATH_FIELD_NUMBER: _ClassVar[int]
        PARTITIONS_FIELD_NUMBER: _ClassVar[int]
        path: str
        partitions: _containers.RepeatedCompositeFieldContainer[UpdateOffsetsInTransactionRequest.TopicOffsets.PartitionOffsets]
        def __init__(self, path: _Optional[str] = ..., partitions: _Optional[_Iterable[_Union[UpdateOffsetsInTransactionRequest.TopicOffsets.PartitionOffsets, _Mapping]]] = ...) -> None: ...
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    TX_FIELD_NUMBER: _ClassVar[int]
    TOPICS_FIELD_NUMBER: _ClassVar[int]
    CONSUMER_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    tx: TransactionIdentity
    topics: _containers.RepeatedCompositeFieldContainer[UpdateOffsetsInTransactionRequest.TopicOffsets]
    consumer: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., tx: _Optional[_Union[TransactionIdentity, _Mapping]] = ..., topics: _Optional[_Iterable[_Union[UpdateOffsetsInTransactionRequest.TopicOffsets, _Mapping]]] = ..., consumer: _Optional[str] = ...) -> None: ...

class UpdateOffsetsInTransactionResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class UpdateOffsetsInTransactionResult(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CommitOffsetRequest(_message.Message):
    __slots__ = ("operation_params", "path", "partition_id", "consumer", "offset", "read_session_id")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
    CONSUMER_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    READ_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    partition_id: int
    consumer: str
    offset: int
    read_session_id: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., partition_id: _Optional[int] = ..., consumer: _Optional[str] = ..., offset: _Optional[int] = ..., read_session_id: _Optional[str] = ...) -> None: ...

class CommitOffsetResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class CommitOffsetResult(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MultipleWindowsStat(_message.Message):
    __slots__ = ("per_minute", "per_hour", "per_day")
    PER_MINUTE_FIELD_NUMBER: _ClassVar[int]
    PER_HOUR_FIELD_NUMBER: _ClassVar[int]
    PER_DAY_FIELD_NUMBER: _ClassVar[int]
    per_minute: int
    per_hour: int
    per_day: int
    def __init__(self, per_minute: _Optional[int] = ..., per_hour: _Optional[int] = ..., per_day: _Optional[int] = ...) -> None: ...

class Consumer(_message.Message):
    __slots__ = ("name", "important", "read_from", "supported_codecs", "attributes", "consumer_stats", "availability_period")
    class AttributesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class ConsumerStats(_message.Message):
        __slots__ = ("min_partitions_last_read_time", "max_read_time_lag", "max_write_time_lag", "max_committed_time_lag", "bytes_read")
        MIN_PARTITIONS_LAST_READ_TIME_FIELD_NUMBER: _ClassVar[int]
        MAX_READ_TIME_LAG_FIELD_NUMBER: _ClassVar[int]
        MAX_WRITE_TIME_LAG_FIELD_NUMBER: _ClassVar[int]
        MAX_COMMITTED_TIME_LAG_FIELD_NUMBER: _ClassVar[int]
        BYTES_READ_FIELD_NUMBER: _ClassVar[int]
        min_partitions_last_read_time: _timestamp_pb2.Timestamp
        max_read_time_lag: _duration_pb2.Duration
        max_write_time_lag: _duration_pb2.Duration
        max_committed_time_lag: _duration_pb2.Duration
        bytes_read: MultipleWindowsStat
        def __init__(self, min_partitions_last_read_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., max_read_time_lag: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., max_write_time_lag: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., max_committed_time_lag: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., bytes_read: _Optional[_Union[MultipleWindowsStat, _Mapping]] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    IMPORTANT_FIELD_NUMBER: _ClassVar[int]
    READ_FROM_FIELD_NUMBER: _ClassVar[int]
    SUPPORTED_CODECS_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    CONSUMER_STATS_FIELD_NUMBER: _ClassVar[int]
    AVAILABILITY_PERIOD_FIELD_NUMBER: _ClassVar[int]
    name: str
    important: bool
    read_from: _timestamp_pb2.Timestamp
    supported_codecs: SupportedCodecs
    attributes: _containers.ScalarMap[str, str]
    consumer_stats: Consumer.ConsumerStats
    availability_period: _duration_pb2.Duration
    def __init__(self, name: _Optional[str] = ..., important: bool = ..., read_from: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., supported_codecs: _Optional[_Union[SupportedCodecs, _Mapping]] = ..., attributes: _Optional[_Mapping[str, str]] = ..., consumer_stats: _Optional[_Union[Consumer.ConsumerStats, _Mapping]] = ..., availability_period: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ...) -> None: ...

class AlterConsumer(_message.Message):
    __slots__ = ("name", "set_important", "set_read_from", "set_supported_codecs", "alter_attributes", "set_availability_period", "reset_availability_period")
    class AlterAttributesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    SET_IMPORTANT_FIELD_NUMBER: _ClassVar[int]
    SET_READ_FROM_FIELD_NUMBER: _ClassVar[int]
    SET_SUPPORTED_CODECS_FIELD_NUMBER: _ClassVar[int]
    ALTER_ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    SET_AVAILABILITY_PERIOD_FIELD_NUMBER: _ClassVar[int]
    RESET_AVAILABILITY_PERIOD_FIELD_NUMBER: _ClassVar[int]
    name: str
    set_important: bool
    set_read_from: _timestamp_pb2.Timestamp
    set_supported_codecs: SupportedCodecs
    alter_attributes: _containers.ScalarMap[str, str]
    set_availability_period: _duration_pb2.Duration
    reset_availability_period: _empty_pb2.Empty
    def __init__(self, name: _Optional[str] = ..., set_important: bool = ..., set_read_from: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., set_supported_codecs: _Optional[_Union[SupportedCodecs, _Mapping]] = ..., alter_attributes: _Optional[_Mapping[str, str]] = ..., set_availability_period: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., reset_availability_period: _Optional[_Union[_empty_pb2.Empty, _Mapping]] = ...) -> None: ...

class PartitioningSettings(_message.Message):
    __slots__ = ("min_active_partitions", "max_active_partitions", "partition_count_limit", "auto_partitioning_settings")
    MIN_ACTIVE_PARTITIONS_FIELD_NUMBER: _ClassVar[int]
    MAX_ACTIVE_PARTITIONS_FIELD_NUMBER: _ClassVar[int]
    PARTITION_COUNT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    AUTO_PARTITIONING_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    min_active_partitions: int
    max_active_partitions: int
    partition_count_limit: int
    auto_partitioning_settings: AutoPartitioningSettings
    def __init__(self, min_active_partitions: _Optional[int] = ..., max_active_partitions: _Optional[int] = ..., partition_count_limit: _Optional[int] = ..., auto_partitioning_settings: _Optional[_Union[AutoPartitioningSettings, _Mapping]] = ...) -> None: ...

class AutoPartitioningSettings(_message.Message):
    __slots__ = ("strategy", "partition_write_speed")
    STRATEGY_FIELD_NUMBER: _ClassVar[int]
    PARTITION_WRITE_SPEED_FIELD_NUMBER: _ClassVar[int]
    strategy: AutoPartitioningStrategy
    partition_write_speed: AutoPartitioningWriteSpeedStrategy
    def __init__(self, strategy: _Optional[_Union[AutoPartitioningStrategy, str]] = ..., partition_write_speed: _Optional[_Union[AutoPartitioningWriteSpeedStrategy, _Mapping]] = ...) -> None: ...

class AutoPartitioningWriteSpeedStrategy(_message.Message):
    __slots__ = ("stabilization_window", "up_utilization_percent", "down_utilization_percent")
    STABILIZATION_WINDOW_FIELD_NUMBER: _ClassVar[int]
    UP_UTILIZATION_PERCENT_FIELD_NUMBER: _ClassVar[int]
    DOWN_UTILIZATION_PERCENT_FIELD_NUMBER: _ClassVar[int]
    stabilization_window: _duration_pb2.Duration
    up_utilization_percent: int
    down_utilization_percent: int
    def __init__(self, stabilization_window: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., up_utilization_percent: _Optional[int] = ..., down_utilization_percent: _Optional[int] = ...) -> None: ...

class AlterPartitioningSettings(_message.Message):
    __slots__ = ("set_min_active_partitions", "set_max_active_partitions", "set_partition_count_limit", "alter_auto_partitioning_settings")
    SET_MIN_ACTIVE_PARTITIONS_FIELD_NUMBER: _ClassVar[int]
    SET_MAX_ACTIVE_PARTITIONS_FIELD_NUMBER: _ClassVar[int]
    SET_PARTITION_COUNT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    ALTER_AUTO_PARTITIONING_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    set_min_active_partitions: int
    set_max_active_partitions: int
    set_partition_count_limit: int
    alter_auto_partitioning_settings: AlterAutoPartitioningSettings
    def __init__(self, set_min_active_partitions: _Optional[int] = ..., set_max_active_partitions: _Optional[int] = ..., set_partition_count_limit: _Optional[int] = ..., alter_auto_partitioning_settings: _Optional[_Union[AlterAutoPartitioningSettings, _Mapping]] = ...) -> None: ...

class AlterAutoPartitioningSettings(_message.Message):
    __slots__ = ("set_strategy", "set_partition_write_speed")
    SET_STRATEGY_FIELD_NUMBER: _ClassVar[int]
    SET_PARTITION_WRITE_SPEED_FIELD_NUMBER: _ClassVar[int]
    set_strategy: AutoPartitioningStrategy
    set_partition_write_speed: AlterAutoPartitioningWriteSpeedStrategy
    def __init__(self, set_strategy: _Optional[_Union[AutoPartitioningStrategy, str]] = ..., set_partition_write_speed: _Optional[_Union[AlterAutoPartitioningWriteSpeedStrategy, _Mapping]] = ...) -> None: ...

class AlterAutoPartitioningWriteSpeedStrategy(_message.Message):
    __slots__ = ("set_stabilization_window", "set_up_utilization_percent", "set_down_utilization_percent")
    SET_STABILIZATION_WINDOW_FIELD_NUMBER: _ClassVar[int]
    SET_UP_UTILIZATION_PERCENT_FIELD_NUMBER: _ClassVar[int]
    SET_DOWN_UTILIZATION_PERCENT_FIELD_NUMBER: _ClassVar[int]
    set_stabilization_window: _duration_pb2.Duration
    set_up_utilization_percent: int
    set_down_utilization_percent: int
    def __init__(self, set_stabilization_window: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., set_up_utilization_percent: _Optional[int] = ..., set_down_utilization_percent: _Optional[int] = ...) -> None: ...

class CreateTopicRequest(_message.Message):
    __slots__ = ("operation_params", "path", "partitioning_settings", "retention_period", "retention_storage_mb", "supported_codecs", "partition_write_speed_bytes_per_second", "partition_write_burst_bytes", "attributes", "consumers", "metering_mode")
    class AttributesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    PARTITIONING_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    RETENTION_PERIOD_FIELD_NUMBER: _ClassVar[int]
    RETENTION_STORAGE_MB_FIELD_NUMBER: _ClassVar[int]
    SUPPORTED_CODECS_FIELD_NUMBER: _ClassVar[int]
    PARTITION_WRITE_SPEED_BYTES_PER_SECOND_FIELD_NUMBER: _ClassVar[int]
    PARTITION_WRITE_BURST_BYTES_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    CONSUMERS_FIELD_NUMBER: _ClassVar[int]
    METERING_MODE_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    partitioning_settings: PartitioningSettings
    retention_period: _duration_pb2.Duration
    retention_storage_mb: int
    supported_codecs: SupportedCodecs
    partition_write_speed_bytes_per_second: int
    partition_write_burst_bytes: int
    attributes: _containers.ScalarMap[str, str]
    consumers: _containers.RepeatedCompositeFieldContainer[Consumer]
    metering_mode: MeteringMode
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., partitioning_settings: _Optional[_Union[PartitioningSettings, _Mapping]] = ..., retention_period: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., retention_storage_mb: _Optional[int] = ..., supported_codecs: _Optional[_Union[SupportedCodecs, _Mapping]] = ..., partition_write_speed_bytes_per_second: _Optional[int] = ..., partition_write_burst_bytes: _Optional[int] = ..., attributes: _Optional[_Mapping[str, str]] = ..., consumers: _Optional[_Iterable[_Union[Consumer, _Mapping]]] = ..., metering_mode: _Optional[_Union[MeteringMode, str]] = ...) -> None: ...

class CreateTopicResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class CreateTopicResult(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PartitionLocation(_message.Message):
    __slots__ = ("node_id", "generation")
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    GENERATION_FIELD_NUMBER: _ClassVar[int]
    node_id: int
    generation: int
    def __init__(self, node_id: _Optional[int] = ..., generation: _Optional[int] = ...) -> None: ...

class DescribeTopicRequest(_message.Message):
    __slots__ = ("operation_params", "path", "include_stats", "include_location")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_STATS_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_LOCATION_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    include_stats: bool
    include_location: bool
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., include_stats: bool = ..., include_location: bool = ...) -> None: ...

class DescribeTopicResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class PartitionKeyRange(_message.Message):
    __slots__ = ("from_bound", "to_bound")
    FROM_BOUND_FIELD_NUMBER: _ClassVar[int]
    TO_BOUND_FIELD_NUMBER: _ClassVar[int]
    from_bound: bytes
    to_bound: bytes
    def __init__(self, from_bound: _Optional[bytes] = ..., to_bound: _Optional[bytes] = ...) -> None: ...

class DescribeTopicResult(_message.Message):
    __slots__ = ("self", "partitioning_settings", "partitions", "retention_period", "retention_storage_mb", "supported_codecs", "partition_write_speed_bytes_per_second", "partition_total_read_speed_bytes_per_second", "partition_consumer_read_speed_bytes_per_second", "partition_write_burst_bytes", "attributes", "consumers", "metering_mode", "topic_stats")
    class AttributesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class PartitionInfo(_message.Message):
        __slots__ = ("partition_id", "active", "child_partition_ids", "parent_partition_ids", "partition_stats", "partition_location", "key_range")
        PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
        ACTIVE_FIELD_NUMBER: _ClassVar[int]
        CHILD_PARTITION_IDS_FIELD_NUMBER: _ClassVar[int]
        PARENT_PARTITION_IDS_FIELD_NUMBER: _ClassVar[int]
        PARTITION_STATS_FIELD_NUMBER: _ClassVar[int]
        PARTITION_LOCATION_FIELD_NUMBER: _ClassVar[int]
        KEY_RANGE_FIELD_NUMBER: _ClassVar[int]
        partition_id: int
        active: bool
        child_partition_ids: _containers.RepeatedScalarFieldContainer[int]
        parent_partition_ids: _containers.RepeatedScalarFieldContainer[int]
        partition_stats: PartitionStats
        partition_location: PartitionLocation
        key_range: PartitionKeyRange
        def __init__(self, partition_id: _Optional[int] = ..., active: bool = ..., child_partition_ids: _Optional[_Iterable[int]] = ..., parent_partition_ids: _Optional[_Iterable[int]] = ..., partition_stats: _Optional[_Union[PartitionStats, _Mapping]] = ..., partition_location: _Optional[_Union[PartitionLocation, _Mapping]] = ..., key_range: _Optional[_Union[PartitionKeyRange, _Mapping]] = ...) -> None: ...
    class TopicStats(_message.Message):
        __slots__ = ("store_size_bytes", "min_last_write_time", "max_write_time_lag", "bytes_written")
        STORE_SIZE_BYTES_FIELD_NUMBER: _ClassVar[int]
        MIN_LAST_WRITE_TIME_FIELD_NUMBER: _ClassVar[int]
        MAX_WRITE_TIME_LAG_FIELD_NUMBER: _ClassVar[int]
        BYTES_WRITTEN_FIELD_NUMBER: _ClassVar[int]
        store_size_bytes: int
        min_last_write_time: _timestamp_pb2.Timestamp
        max_write_time_lag: _duration_pb2.Duration
        bytes_written: MultipleWindowsStat
        def __init__(self, store_size_bytes: _Optional[int] = ..., min_last_write_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., max_write_time_lag: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., bytes_written: _Optional[_Union[MultipleWindowsStat, _Mapping]] = ...) -> None: ...
    SELF_FIELD_NUMBER: _ClassVar[int]
    PARTITIONING_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    PARTITIONS_FIELD_NUMBER: _ClassVar[int]
    RETENTION_PERIOD_FIELD_NUMBER: _ClassVar[int]
    RETENTION_STORAGE_MB_FIELD_NUMBER: _ClassVar[int]
    SUPPORTED_CODECS_FIELD_NUMBER: _ClassVar[int]
    PARTITION_WRITE_SPEED_BYTES_PER_SECOND_FIELD_NUMBER: _ClassVar[int]
    PARTITION_TOTAL_READ_SPEED_BYTES_PER_SECOND_FIELD_NUMBER: _ClassVar[int]
    PARTITION_CONSUMER_READ_SPEED_BYTES_PER_SECOND_FIELD_NUMBER: _ClassVar[int]
    PARTITION_WRITE_BURST_BYTES_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    CONSUMERS_FIELD_NUMBER: _ClassVar[int]
    METERING_MODE_FIELD_NUMBER: _ClassVar[int]
    TOPIC_STATS_FIELD_NUMBER: _ClassVar[int]
    self: _ydb_scheme_pb2.Entry
    partitioning_settings: PartitioningSettings
    partitions: _containers.RepeatedCompositeFieldContainer[DescribeTopicResult.PartitionInfo]
    retention_period: _duration_pb2.Duration
    retention_storage_mb: int
    supported_codecs: SupportedCodecs
    partition_write_speed_bytes_per_second: int
    partition_total_read_speed_bytes_per_second: int
    partition_consumer_read_speed_bytes_per_second: int
    partition_write_burst_bytes: int
    attributes: _containers.ScalarMap[str, str]
    consumers: _containers.RepeatedCompositeFieldContainer[Consumer]
    metering_mode: MeteringMode
    topic_stats: DescribeTopicResult.TopicStats
    def __init__(self_, self: _Optional[_Union[_ydb_scheme_pb2.Entry, _Mapping]] = ..., partitioning_settings: _Optional[_Union[PartitioningSettings, _Mapping]] = ..., partitions: _Optional[_Iterable[_Union[DescribeTopicResult.PartitionInfo, _Mapping]]] = ..., retention_period: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., retention_storage_mb: _Optional[int] = ..., supported_codecs: _Optional[_Union[SupportedCodecs, _Mapping]] = ..., partition_write_speed_bytes_per_second: _Optional[int] = ..., partition_total_read_speed_bytes_per_second: _Optional[int] = ..., partition_consumer_read_speed_bytes_per_second: _Optional[int] = ..., partition_write_burst_bytes: _Optional[int] = ..., attributes: _Optional[_Mapping[str, str]] = ..., consumers: _Optional[_Iterable[_Union[Consumer, _Mapping]]] = ..., metering_mode: _Optional[_Union[MeteringMode, str]] = ..., topic_stats: _Optional[_Union[DescribeTopicResult.TopicStats, _Mapping]] = ...) -> None: ...

class DescribePartitionRequest(_message.Message):
    __slots__ = ("operation_params", "path", "partition_id", "include_stats", "include_location")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_STATS_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_LOCATION_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    partition_id: int
    include_stats: bool
    include_location: bool
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., partition_id: _Optional[int] = ..., include_stats: bool = ..., include_location: bool = ...) -> None: ...

class DescribePartitionResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribePartitionResult(_message.Message):
    __slots__ = ("partition",)
    PARTITION_FIELD_NUMBER: _ClassVar[int]
    partition: DescribeTopicResult.PartitionInfo
    def __init__(self, partition: _Optional[_Union[DescribeTopicResult.PartitionInfo, _Mapping]] = ...) -> None: ...

class DescribeConsumerRequest(_message.Message):
    __slots__ = ("operation_params", "path", "consumer", "include_stats", "include_location")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    CONSUMER_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_STATS_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_LOCATION_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    consumer: str
    include_stats: bool
    include_location: bool
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., consumer: _Optional[str] = ..., include_stats: bool = ..., include_location: bool = ...) -> None: ...

class DescribeConsumerResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DescribeConsumerResult(_message.Message):
    __slots__ = ("self", "consumer", "partitions")
    class PartitionInfo(_message.Message):
        __slots__ = ("partition_id", "active", "child_partition_ids", "parent_partition_ids", "partition_stats", "partition_consumer_stats", "partition_location")
        PARTITION_ID_FIELD_NUMBER: _ClassVar[int]
        ACTIVE_FIELD_NUMBER: _ClassVar[int]
        CHILD_PARTITION_IDS_FIELD_NUMBER: _ClassVar[int]
        PARENT_PARTITION_IDS_FIELD_NUMBER: _ClassVar[int]
        PARTITION_STATS_FIELD_NUMBER: _ClassVar[int]
        PARTITION_CONSUMER_STATS_FIELD_NUMBER: _ClassVar[int]
        PARTITION_LOCATION_FIELD_NUMBER: _ClassVar[int]
        partition_id: int
        active: bool
        child_partition_ids: _containers.RepeatedScalarFieldContainer[int]
        parent_partition_ids: _containers.RepeatedScalarFieldContainer[int]
        partition_stats: PartitionStats
        partition_consumer_stats: DescribeConsumerResult.PartitionConsumerStats
        partition_location: PartitionLocation
        def __init__(self, partition_id: _Optional[int] = ..., active: bool = ..., child_partition_ids: _Optional[_Iterable[int]] = ..., parent_partition_ids: _Optional[_Iterable[int]] = ..., partition_stats: _Optional[_Union[PartitionStats, _Mapping]] = ..., partition_consumer_stats: _Optional[_Union[DescribeConsumerResult.PartitionConsumerStats, _Mapping]] = ..., partition_location: _Optional[_Union[PartitionLocation, _Mapping]] = ...) -> None: ...
    class PartitionConsumerStats(_message.Message):
        __slots__ = ("last_read_offset", "committed_offset", "read_session_id", "partition_read_session_create_time", "last_read_time", "max_read_time_lag", "max_write_time_lag", "max_committed_time_lag", "bytes_read", "reader_name", "connection_node_id")
        LAST_READ_OFFSET_FIELD_NUMBER: _ClassVar[int]
        COMMITTED_OFFSET_FIELD_NUMBER: _ClassVar[int]
        READ_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
        PARTITION_READ_SESSION_CREATE_TIME_FIELD_NUMBER: _ClassVar[int]
        LAST_READ_TIME_FIELD_NUMBER: _ClassVar[int]
        MAX_READ_TIME_LAG_FIELD_NUMBER: _ClassVar[int]
        MAX_WRITE_TIME_LAG_FIELD_NUMBER: _ClassVar[int]
        MAX_COMMITTED_TIME_LAG_FIELD_NUMBER: _ClassVar[int]
        BYTES_READ_FIELD_NUMBER: _ClassVar[int]
        READER_NAME_FIELD_NUMBER: _ClassVar[int]
        CONNECTION_NODE_ID_FIELD_NUMBER: _ClassVar[int]
        last_read_offset: int
        committed_offset: int
        read_session_id: str
        partition_read_session_create_time: _timestamp_pb2.Timestamp
        last_read_time: _timestamp_pb2.Timestamp
        max_read_time_lag: _duration_pb2.Duration
        max_write_time_lag: _duration_pb2.Duration
        max_committed_time_lag: _duration_pb2.Duration
        bytes_read: MultipleWindowsStat
        reader_name: str
        connection_node_id: int
        def __init__(self, last_read_offset: _Optional[int] = ..., committed_offset: _Optional[int] = ..., read_session_id: _Optional[str] = ..., partition_read_session_create_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., last_read_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., max_read_time_lag: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., max_write_time_lag: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., max_committed_time_lag: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., bytes_read: _Optional[_Union[MultipleWindowsStat, _Mapping]] = ..., reader_name: _Optional[str] = ..., connection_node_id: _Optional[int] = ...) -> None: ...
    SELF_FIELD_NUMBER: _ClassVar[int]
    CONSUMER_FIELD_NUMBER: _ClassVar[int]
    PARTITIONS_FIELD_NUMBER: _ClassVar[int]
    self: _ydb_scheme_pb2.Entry
    consumer: Consumer
    partitions: _containers.RepeatedCompositeFieldContainer[DescribeConsumerResult.PartitionInfo]
    def __init__(self_, self: _Optional[_Union[_ydb_scheme_pb2.Entry, _Mapping]] = ..., consumer: _Optional[_Union[Consumer, _Mapping]] = ..., partitions: _Optional[_Iterable[_Union[DescribeConsumerResult.PartitionInfo, _Mapping]]] = ...) -> None: ...

class PartitionStats(_message.Message):
    __slots__ = ("partition_offsets", "store_size_bytes", "last_write_time", "max_write_time_lag", "bytes_written", "partition_node_id")
    PARTITION_OFFSETS_FIELD_NUMBER: _ClassVar[int]
    STORE_SIZE_BYTES_FIELD_NUMBER: _ClassVar[int]
    LAST_WRITE_TIME_FIELD_NUMBER: _ClassVar[int]
    MAX_WRITE_TIME_LAG_FIELD_NUMBER: _ClassVar[int]
    BYTES_WRITTEN_FIELD_NUMBER: _ClassVar[int]
    PARTITION_NODE_ID_FIELD_NUMBER: _ClassVar[int]
    partition_offsets: OffsetsRange
    store_size_bytes: int
    last_write_time: _timestamp_pb2.Timestamp
    max_write_time_lag: _duration_pb2.Duration
    bytes_written: MultipleWindowsStat
    partition_node_id: int
    def __init__(self, partition_offsets: _Optional[_Union[OffsetsRange, _Mapping]] = ..., store_size_bytes: _Optional[int] = ..., last_write_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., max_write_time_lag: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., bytes_written: _Optional[_Union[MultipleWindowsStat, _Mapping]] = ..., partition_node_id: _Optional[int] = ...) -> None: ...

class AlterTopicRequest(_message.Message):
    __slots__ = ("operation_params", "path", "alter_partitioning_settings", "set_retention_period", "set_retention_storage_mb", "set_supported_codecs", "set_partition_write_speed_bytes_per_second", "set_partition_write_burst_bytes", "alter_attributes", "add_consumers", "drop_consumers", "alter_consumers", "set_metering_mode")
    class AlterAttributesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    ALTER_PARTITIONING_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    SET_RETENTION_PERIOD_FIELD_NUMBER: _ClassVar[int]
    SET_RETENTION_STORAGE_MB_FIELD_NUMBER: _ClassVar[int]
    SET_SUPPORTED_CODECS_FIELD_NUMBER: _ClassVar[int]
    SET_PARTITION_WRITE_SPEED_BYTES_PER_SECOND_FIELD_NUMBER: _ClassVar[int]
    SET_PARTITION_WRITE_BURST_BYTES_FIELD_NUMBER: _ClassVar[int]
    ALTER_ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    ADD_CONSUMERS_FIELD_NUMBER: _ClassVar[int]
    DROP_CONSUMERS_FIELD_NUMBER: _ClassVar[int]
    ALTER_CONSUMERS_FIELD_NUMBER: _ClassVar[int]
    SET_METERING_MODE_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    alter_partitioning_settings: AlterPartitioningSettings
    set_retention_period: _duration_pb2.Duration
    set_retention_storage_mb: int
    set_supported_codecs: SupportedCodecs
    set_partition_write_speed_bytes_per_second: int
    set_partition_write_burst_bytes: int
    alter_attributes: _containers.ScalarMap[str, str]
    add_consumers: _containers.RepeatedCompositeFieldContainer[Consumer]
    drop_consumers: _containers.RepeatedScalarFieldContainer[str]
    alter_consumers: _containers.RepeatedCompositeFieldContainer[AlterConsumer]
    set_metering_mode: MeteringMode
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ..., alter_partitioning_settings: _Optional[_Union[AlterPartitioningSettings, _Mapping]] = ..., set_retention_period: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ..., set_retention_storage_mb: _Optional[int] = ..., set_supported_codecs: _Optional[_Union[SupportedCodecs, _Mapping]] = ..., set_partition_write_speed_bytes_per_second: _Optional[int] = ..., set_partition_write_burst_bytes: _Optional[int] = ..., alter_attributes: _Optional[_Mapping[str, str]] = ..., add_consumers: _Optional[_Iterable[_Union[Consumer, _Mapping]]] = ..., drop_consumers: _Optional[_Iterable[str]] = ..., alter_consumers: _Optional[_Iterable[_Union[AlterConsumer, _Mapping]]] = ..., set_metering_mode: _Optional[_Union[MeteringMode, str]] = ...) -> None: ...

class AlterTopicResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class AlterTopicResult(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DropTopicRequest(_message.Message):
    __slots__ = ("operation_params", "path")
    OPERATION_PARAMS_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    operation_params: _ydb_operation_pb2.OperationParams
    path: str
    def __init__(self, operation_params: _Optional[_Union[_ydb_operation_pb2.OperationParams, _Mapping]] = ..., path: _Optional[str] = ...) -> None: ...

class DropTopicResponse(_message.Message):
    __slots__ = ("operation",)
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    operation: _ydb_operation_pb2.Operation
    def __init__(self, operation: _Optional[_Union[_ydb_operation_pb2.Operation, _Mapping]] = ...) -> None: ...

class DropTopicResult(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
