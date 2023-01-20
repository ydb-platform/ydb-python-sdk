import abc
import datetime
import typing
from codecs import Codec
from dataclasses import dataclass, field
from typing import List, Union, Dict

from google.protobuf.message import Message

from ydb._topic_wrapper.common import OffsetsRange


class StreamReadMessage:
    @dataclass
    class PartitionSession:
        partition_session_id: int
        path: str
        partition_id: int

    @dataclass
    class InitRequest:
        topics_read_settings: List["TopicReadSettings"]
        consumer: str

        @dataclass
        class TopicReadSettings:
            path: str
            partition_ids: List[int] = field(default_factory=list)
            max_lag_seconds: Union[float, None] = None
            read_from: Union[int, float, datetime.datetime, None] = None

    @dataclass
    class InitResponse:
        session_id: str

    @dataclass
    class ReadRequest:
        bytes_size: int

    @dataclass
    class ReadResponse:
        partition_data: List["PartitionData"]
        bytes_size: int

        @dataclass
        class MessageData:
            offset: int
            seq_no: int
            created_at: float  # unix timestamp
            data: bytes
            uncompresed_size: int
            message_group_id: str

        @dataclass
        class Batch:
            message_data: List["MessageData"]
            producer_id: str
            write_session_meta: Dict[str, str]
            codec: int
            written_at: float  # unix timestamp

        @dataclass
        class PartitionData:
            partition_session_id: int
            batches: List["Batch"]

    @dataclass
    class CommitOffsetRequest:
        commit_offsets: List["PartitionCommitOffset"]

        @dataclass
        class PartitionCommitOffset:
            partition_session_id: int
            offsets: List[OffsetsRange]

    @dataclass
    class CommitOffsetResponse:
        partitions_committed_offsets: List["PartitionCommittedOffset"]

        @dataclass
        class PartitionCommittedOffset:
            partition_session_id: int
            committed_offset: int

    @dataclass
    class PartitionSessionStatusRequest:
        partition_session_id: int

    @dataclass
    class PartitionSessionStatusResponse:
        partition_session_id: int
        partition_offsets: OffsetsRange
        committed_offset: int
        write_time_high_watermark: float

    @dataclass
    class StartPartitionSessionRequest:
        partition_session: "PartitionSession"
        committed_offset: int
        partition_offsets: OffsetsRange

    @dataclass
    class StartPartitionSessionResponse:
        partition_session_id: int
        read_offset: int
        commit_offset: int

    @dataclass
    class StopPartitionSessionRequest:
        partition_session_id: int
        graceful: bool
        committed_offset: int

    @dataclass
    class StopPartitionSessionResponse:
        partition_session_id: int

