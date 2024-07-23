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
    QuerySerializableReadWrite,
)
from .. import convert
from .. import issues


class QueryClientSettings:
    pass


class IQuerySessionState(abc.ABC):
    def __init__(self, settings: QueryClientSettings = None):
        pass

    @abc.abstractmethod
    def reset(self) -> None:
        pass

    @property
    @abc.abstractmethod
    def session_id(self) -> Optional[str]:
        pass

    @abc.abstractmethod
    def set_session_id(self, session_id: str) -> "IQuerySessionState":
        pass

    @property
    @abc.abstractmethod
    def node_id(self) -> Optional[int]:
        pass

    @abc.abstractmethod
    def set_node_id(self, node_id: int) -> "IQuerySessionState":
        pass

    @property
    @abc.abstractmethod
    def attached(self) -> bool:
        pass

    @abc.abstractmethod
    def set_attached(self, attached: bool) -> "IQuerySessionState":
        pass


class IQuerySession(abc.ABC):
    @abc.abstractmethod
    def __init__(self, driver: SupportedDriverType, settings: QueryClientSettings = None):
        pass

    @abc.abstractmethod
    def create(self) -> "IQuerySession":
        pass

    @abc.abstractmethod
    def delete(self) -> None:
        pass

    @abc.abstractmethod
    def transaction(self, tx_mode: BaseQueryTxMode) -> "IQueryTxContext":
        pass


class IQueryTxContext(abc.ABC):
    @abc.abstractmethod
    def __init__(
        self,
        driver: SupportedDriverType,
        session_state: IQuerySessionState,
        session: IQuerySession,
        tx_mode: BaseQueryTxMode = None,
    ):
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
    def execute(query: str, commit_tx=False):
        pass


class IQueryClient(abc.ABC):
    def __init__(self, driver: SupportedDriverType, query_client_settings: QueryClientSettings = None):
        pass

    @abc.abstractmethod
    def session(self) -> IQuerySession:
        pass


class QuerySyntax(enum.IntEnum):
    UNSPECIFIED = 0
    YQL_V1 = 1
    PG = 2


class QueryExecMode(enum.IntEnum):
    UNSPECIFIED = 0
    PARSE = 10
    VALIDATE = 20
    EXPLAIN = 30
    EXECUTE = 50


def create_execute_query_request(
    query: str,
    session_id: str,
    tx_id: str = None,
    commit_tx: bool = False,
    tx_mode: BaseQueryTxMode = None,
    syntax: QuerySyntax = None,
    exec_mode: QueryExecMode = None,
    parameters: dict = None,
    concurrent_result_sets: bool = False,
    empty_tx_control: bool = False,
):
    syntax = QuerySyntax.YQL_V1 if not syntax else syntax
    exec_mode = QueryExecMode.EXECUTE if not exec_mode else exec_mode

    tx_control = None
    if empty_tx_control:
        tx_control = None
    elif tx_id:
        tx_control = ydb_query.TransactionControl(
            tx_id=tx_id,
            commit_tx=commit_tx,
        )
    else:
        tx_mode = tx_mode if tx_mode is not None else QuerySerializableReadWrite()
        tx_control = ydb_query.TransactionControl(
            begin_tx=ydb_query.TransactionSettings(
                tx_mode=tx_mode,
            ),
            commit_tx=commit_tx,
        )

    req = ydb_query.ExecuteQueryRequest(
        session_id=session_id,
        query_content=ydb_query.QueryContent.from_public(
            query=query,
            syntax=syntax,
        ),
        tx_control=tx_control,
        exec_mode=exec_mode,
        parameters=parameters,
        concurrent_result_sets=concurrent_result_sets,
    )

    return req.to_proto()


def wrap_execute_query_response(rpc_state, response_pb, tx, commit_tx=False):
    issues._process_response(response_pb)
    if response_pb.tx_meta and not tx.tx_id:
        tx._handle_tx_meta(response_pb.tx_meta)
    if commit_tx:
        tx._move_to_commited()
    return convert.ResultSet.from_message(response_pb.result_set)


X_YDB_SERVER_HINTS = "x-ydb-server-hints"
X_YDB_SESSION_CLOSE = "session-close"


def bad_session_handler(func):
    @functools.wraps(func)
    def decorator(rpc_state, response_pb, session_state, *args, **kwargs):
        try:
            return func(rpc_state, response_pb, session_state, *args, **kwargs)
        except issues.BadSession:
            session_state.reset()
            raise

    return decorator
