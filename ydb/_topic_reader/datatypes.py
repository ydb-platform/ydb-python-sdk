import abc
import enum
from dataclasses import dataclass
import datetime
from typing import Mapping, Union, Any, List, Dict


class ICommittable(abc.ABC):
    @property
    @abc.abstractmethod
    def start_offset(self) -> int:
        pass

    @property
    @abc.abstractmethod
    def end_offset(self) -> int:
        pass


class ISessionAlive(abc.ABC):
    @property
    @abc.abstractmethod
    def is_alive(self) -> bool:
        pass


@dataclass
class PublicMessage(ICommittable, ISessionAlive):
    seqno: int
    created_at: datetime.datetime
    message_group_id: str
    session_metadata: Dict[str, str]
    offset: int
    written_at: datetime.datetime
    producer_id: str
    data: Union[
        bytes, Any
    ]  # set as original decompressed bytes or deserialized object if deserializer set in reader
    _partition_session: "PartitionSession"

    @property
    def start_offset(self) -> int:
        raise NotImplementedError()

    @property
    def end_offset(self) -> int:
        raise NotImplementedError()

    # ISessionAlive implementation
    @property
    def is_alive(self) -> bool:
        raise NotImplementedError()


@dataclass
class PartitionSession:
    id: int
    state: "PartitionSession.State"
    topic_path: str
    partition_id: int

    def stop(self):
        self.state = PartitionSession.State.Stopped

    class State(enum.Enum):
        Active = 1
        GracefulShutdown = 2
        Stopped = 3


@dataclass
class PublicBatch(ICommittable, ISessionAlive):
    session_metadata: Mapping[str, str]
    messages: List[PublicMessage]
    _partition_session: PartitionSession
    _bytes_size: int

    @property
    def start_offset(self) -> int:
        raise NotImplementedError()

    @property
    def end_offset(self) -> int:
        raise NotImplementedError()

    # ISessionAlive implementation
    @property
    def is_alive(self) -> bool:
        state = self._partition_session.state
        return (
            state == PartitionSession.State.Active
            or state == PartitionSession.State.GracefulShutdown
        )
