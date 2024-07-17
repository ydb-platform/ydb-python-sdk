import abc

from typing import (
    Optional,
)

from .._grpc.grpcwrapper.common_utils import (
    SupportedDriverType,
)

from .._grpc.grpcwrapper.ydb_query_public_types import BaseQueryTxMode


class QueryClientSettings: ...


class IQueryTxContext: ...


class QuerySessionState:
    _session_id: Optional[str]
    _node_id: Optional[int]
    _attached: bool = False
    _settings: Optional[QueryClientSettings]

    def __init__(self, settings: QueryClientSettings = None):
        self._settings = settings
        self.reset()

    def reset(self) -> None:
        self._session_id = None
        self._node_id = None
        self._attached = False

    @property
    def session_id(self) -> Optional[str]:
        return self._session_id

    def set_session_id(self, session_id: str) -> "QuerySessionState":
        self._session_id = session_id
        return self

    @property
    def node_id(self) -> Optional[int]:
        return self._node_id

    def set_node_id(self, node_id: int) -> "QuerySessionState":
        self._node_id = node_id
        return self

    @property
    def attached(self) -> bool:
        return self._attached

    def set_attached(self, attached: bool) -> None:
        self._attached = attached


class IQuerySession(abc.ABC):
    def __init__(self, driver: SupportedDriverType, settings: QueryClientSettings = None):
        pass

    @abc.abstractmethod
    def create(self) -> None:
        pass

    @abc.abstractmethod
    def delete(self) -> None:
        pass

    @abc.abstractmethod
    def transaction(self, tx_mode: BaseQueryTxMode) -> IQueryTxContext:
        pass


class IQueryClient(abc.ABC):
    def __init__(self, driver: SupportedDriverType, query_client_settings: QueryClientSettings = None):
        pass

    @abc.abstractmethod
    def session(self) -> IQuerySession:
        pass



