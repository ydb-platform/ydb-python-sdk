import abc
import enum
import functools

from typing import (
    Optional,
)

from .._grpc.grpcwrapper.common_utils import (
    SupportedDriverType,
)
from .._grpc.grpcwrapper import ydb_query
from .._grpc.grpcwrapper.ydb_query_public_types import (
    BaseQueryTxMode,
    QuerySerializableReadWrite
)
from .. import convert
from .. import issues

class QueryClientSettings: ...


class QuerySessionStateEnum(enum.Enum):
    NOT_INITIALIZED = "NOT_INITIALIZED"
    CREATED = "CREATED"
    CLOSED = "CLOSED"


class QuerySessionStateHelper(abc.ABC):
    _VALID_TRANSITIONS = {
        QuerySessionStateEnum.NOT_INITIALIZED: [QuerySessionStateEnum.CREATED],
        QuerySessionStateEnum.CREATED: [QuerySessionStateEnum.CLOSED],
        QuerySessionStateEnum.CLOSED: []
    }

    @classmethod
    def valid_transition(cls, before: QuerySessionStateEnum, after: QuerySessionStateEnum) -> bool:
        return after in cls._VALID_TRANSITIONS[before]


class QueryTxStateEnum(enum.Enum):
    NOT_INITIALIZED = "NOT_INITIALIZED"
    BEGINED = "BEGINED"
    COMMITTED = "COMMITTED"
    ROLLBACKED = "ROLLBACKED"
    DEAD = "DEAD"


class QueryTxStateHelper(abc.ABC):
    _VALID_TRANSITIONS = {
        QueryTxStateEnum.NOT_INITIALIZED: [QueryTxStateEnum.BEGINED, QueryTxStateEnum.DEAD],
        QueryTxStateEnum.BEGINED: [QueryTxStateEnum.COMMITTED, QueryTxStateEnum.ROLLBACKED, QueryTxStateEnum.DEAD],
        QueryTxStateEnum.COMMITTED: [],
        QueryTxStateEnum.ROLLBACKED: [],
        QueryTxStateEnum.DEAD: [],
    }

    @classmethod
    def valid_transition(cls, before: QueryTxStateEnum, after: QueryTxStateEnum) -> bool:
        return after in cls._VALID_TRANSITIONS[before]


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
    @abc.abstractmethod
    def __init__(self, driver: SupportedDriverType, settings: QueryClientSettings = None):
        pass

    @abc.abstractmethod
    def create(self) -> None:
        pass

    @abc.abstractmethod
    def delete(self) -> None:
        pass

    @abc.abstractmethod
    def transaction(self, tx_mode: BaseQueryTxMode) -> "IQueryTxContext":
        pass


class IQueryTxContext(abc.ABC):

    @abc.abstractmethod
    def __init__(self, driver: SupportedDriverType, session_state: QuerySessionState, session: IQuerySession, tx_mode: BaseQueryTxMode = None):
        pass

    @abc.abstractmethod
    def __enter__(self):
        pass

    @abc.abstractmethod
    def __exit__(self, *args, **kwargs):
        pass

    @property
    @abc.abstractmethod
    def session_id(self):
        pass

    @property
    @abc.abstractmethod
    def tx_id(self):
        pass

    @abc.abstractmethod
    def begin(settings: QueryClientSettings = None):
        pass

    @abc.abstractmethod
    def commit(settings: QueryClientSettings = None):
        pass

    @abc.abstractmethod
    def rollback(settings: QueryClientSettings = None):
        pass

    @abc.abstractmethod
    def execute(query: str):
        pass


class IQueryClient(abc.ABC):
    def __init__(self, driver: SupportedDriverType, query_client_settings: QueryClientSettings = None):
        pass

    @abc.abstractmethod
    def session(self) -> IQuerySession:
        pass


def create_execute_query_request(query: str, session_id: str, commit_tx: bool):
    req = ydb_query.ExecuteQueryRequest(
        session_id=session_id,
        query_content=ydb_query.QueryContent.from_public(
            query=query,
        ),
        tx_control=ydb_query.TransactionControl(
            begin_tx=ydb_query.TransactionSettings(
                tx_mode=QuerySerializableReadWrite(),
            ),
            commit_tx=commit_tx
        ),
    )

    return req.to_proto()

def wrap_execute_query_response(rpc_state, response_pb):

    return convert.ResultSet.from_message(response_pb.result_set)

X_YDB_SERVER_HINTS = "x-ydb-server-hints"
X_YDB_SESSION_CLOSE = "session-close"


def _check_session_is_closing(rpc_state, session_state):
    metadata = rpc_state.trailing_metadata()
    if X_YDB_SESSION_CLOSE in metadata.get(X_YDB_SERVER_HINTS, []):
        session_state.set_closing()


def bad_session_handler(func):
    @functools.wraps(func)
    def decorator(rpc_state, response_pb, session_state, *args, **kwargs):
        try:
            _check_session_is_closing(rpc_state, session_state)
            return func(rpc_state, response_pb, session_state, *args, **kwargs)
        except issues.BadSession:
            session_state.reset()
            raise

    return decorator