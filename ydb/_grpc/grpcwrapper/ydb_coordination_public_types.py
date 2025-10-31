from dataclasses import dataclass
from enum import Enum
import typing
import ydb

if typing.TYPE_CHECKING:
    from ..v4.protos import ydb_coordination_pb2
else:
    from ..common.protos import ydb_coordination_pb2


class ConsistencyMode(Enum):
    UNSET = 0
    STRICT = 1
    RELAXED = 2

    @classmethod
    def from_proto(cls, proto_val: int) -> "ConsistencyMode":
        mapping = {
            ydb_coordination_pb2.ConsistencyMode.CONSISTENCY_MODE_UNSET: cls.UNSET,
            ydb_coordination_pb2.ConsistencyMode.CONSISTENCY_MODE_STRICT: cls.STRICT,
            ydb_coordination_pb2.ConsistencyMode.CONSISTENCY_MODE_RELAXED: cls.RELAXED,
        }
        return mapping[proto_val]

    def to_proto(self) -> int:
        mapping = {
            self.UNSET: ydb_coordination_pb2.ConsistencyMode.CONSISTENCY_MODE_UNSET,
            self.STRICT: ydb_coordination_pb2.ConsistencyMode.CONSISTENCY_MODE_STRICT,
            self.RELAXED: ydb_coordination_pb2.ConsistencyMode.CONSISTENCY_MODE_RELAXED,
        }
        return mapping[self]


class RateLimiterCountersMode(Enum):
    UNSET = 0
    AGGREGATED = 1
    DETAILED = 2

    @classmethod
    def from_proto(cls, proto_val: int) -> "RateLimiterCountersMode":
        mapping = {
            ydb_coordination_pb2.RateLimiterCountersMode.RATE_LIMITER_COUNTERS_MODE_UNSET: cls.UNSET,
            ydb_coordination_pb2.RateLimiterCountersMode.RATE_LIMITER_COUNTERS_MODE_AGGREGATED: cls.AGGREGATED,
            ydb_coordination_pb2.RateLimiterCountersMode.RATE_LIMITER_COUNTERS_MODE_DETAILED: cls.DETAILED,
        }
        return mapping[proto_val]

    def to_proto(self) -> int:
        mapping = {
            self.UNSET: ydb_coordination_pb2.RateLimiterCountersMode.RATE_LIMITER_COUNTERS_MODE_UNSET,
            self.AGGREGATED: ydb_coordination_pb2.RateLimiterCountersMode.RATE_LIMITER_COUNTERS_MODE_AGGREGATED,
            self.DETAILED: ydb_coordination_pb2.RateLimiterCountersMode.RATE_LIMITER_COUNTERS_MODE_DETAILED,
        }
        return mapping[self]


@dataclass
class NodeConfig:
    attach_consistency_mode: ConsistencyMode
    rate_limiter_counters_mode: RateLimiterCountersMode
    read_consistency_mode: ConsistencyMode
    self_check_period_millis: int
    session_grace_period_millis: int

    @staticmethod
    def from_proto(msg: ydb_coordination_pb2.Config) -> "NodeConfig":
        return NodeConfig(
            attach_consistency_mode=ConsistencyMode.from_proto(msg.attach_consistency_mode),
            rate_limiter_counters_mode=RateLimiterCountersMode.from_proto(msg.rate_limiter_counters_mode),
            read_consistency_mode=ConsistencyMode.from_proto(msg.read_consistency_mode),
            self_check_period_millis=msg.self_check_period_millis,
            session_grace_period_millis=msg.session_grace_period_millis,
        )

    def to_proto(self) -> ydb_coordination_pb2.Config:
        return ydb_coordination_pb2.Config(
            attach_consistency_mode=self.attach_consistency_mode.to_proto(),
            rate_limiter_counters_mode=self.rate_limiter_counters_mode.to_proto(),
            read_consistency_mode=self.read_consistency_mode.to_proto(),
            self_check_period_millis=self.self_check_period_millis,
            session_grace_period_millis=self.session_grace_period_millis,
        )


@dataclass
class NodeDescription:
    path: str
    config: NodeConfig


class CoordinationClientSettings:
    def __init__(self):
        self._trace_id = None
        self._request_type = None
        self._timeout = None
        self._cancel_after = None
        self._operation_timeout = None
        self._compression = None
        self._need_rpc_auth = True
        self._headers = []

    def with_trace_id(self, trace_id: str) -> "CoordinationClientSettings":
        self._trace_id = trace_id
        return self

    def with_request_type(self, request_type: str) -> "CoordinationClientSettings":
        self._request_type = request_type
        return self

    def with_timeout(self, timeout: float) -> "CoordinationClientSettings":
        self._timeout = timeout
        return self

    def with_cancel_after(self, timeout: float) -> "CoordinationClientSettings":
        self._cancel_after = timeout
        return self

    def with_operation_timeout(self, timeout: float) -> "CoordinationClientSettings":
        self._operation_timeout = timeout
        return self

    def with_compression(self, compression) -> "CoordinationClientSettings":
        self._compression = compression
        return self

    def with_need_rpc_auth(self, need_rpc_auth: bool) -> "CoordinationClientSettings":
        self._need_rpc_auth = need_rpc_auth
        return self

    def with_header(self, key: str, value: str) -> "CoordinationClientSettings":
        self._headers.append((key, value))
        return self

    def to_base_request_settings(self) -> "ydb.BaseRequestSettings":
        brs = ydb.BaseRequestSettings()
        brs.trace_id = self._trace_id
        brs.request_type = self._request_type
        brs.timeout = self._timeout
        brs.cancel_after = self._cancel_after
        brs.operation_timeout = self._operation_timeout
        brs.compression = self._compression
        brs.need_rpc_auth = self._need_rpc_auth
        brs.headers.extend(self._headers)
        return brs
