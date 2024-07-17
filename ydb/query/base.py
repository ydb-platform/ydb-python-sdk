import abc

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

class QueryClientSettings: ...


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
    def begin():
        pass

    @abc.abstractmethod
    def commit():
        pass

    @abc.abstractmethod
    def rollback():
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

    # print("RESP:")
    # print(f"meta: {response_pb.tx_meta}")
    # print(response_pb)


    return convert.ResultSet.from_message(response_pb.result_set)
