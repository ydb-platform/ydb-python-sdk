from dataclasses import dataclass
from enum import Enum
import typing

if typing.TYPE_CHECKING:
    from ..v4.protos import ydb_coordination_pb2
else:
    from ..common.protos import ydb_coordination_pb2

class ConsistencyMode(Enum):
    STRICT = 0
    RELAXED = 1

class RateLimiterCountersMode(Enum):
    NONE = 0
    BASIC = 1
    FULL = 2

@dataclass
class NodeConfig:
    attach_consistency_mode: ConsistencyMode
    path: str
    rate_limiter_counters_mode: RateLimiterCountersMode
    read_consistency_mode: ConsistencyMode
    self_check_period_millis: int
    session_grace_period_millis: int

    @staticmethod
    def from_proto(msg: ydb_coordination_pb2.Config) -> "NodeConfig":
        return NodeConfig(
            attach_consistency_mode=ConsistencyMode(msg.attach_consistency_mode),
            path=msg.path,
            rate_limiter_counters_mode=RateLimiterCountersMode(msg.rate_limiter_counters_mode),
            read_consistency_mode=ConsistencyMode(msg.read_consistency_mode),
            self_check_period_millis=msg.self_check_period_millis,
            session_grace_period_millis=msg.session_grace_period_millis,
        )

    def to_proto(self) -> ydb_coordination_pb2.Config:
        return ydb_coordination_pb2.Config(
            attach_consistency_mode=self.attach_consistency_mode.value,
            path=self.path,
            rate_limiter_counters_mode=self.rate_limiter_counters_mode.value,
            read_consistency_mode=self.read_consistency_mode.value,
            self_check_period_millis=self.self_check_period_millis,
            session_grace_period_millis=self.session_grace_period_millis,
        )
