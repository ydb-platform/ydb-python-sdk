import abc
from abc import abstractmethod
import logging

from .. import _apis, issues, _utilities
from .._grpc.grpcwrapper import common_utils
from .._grpc.grpcwrapper import ydb_query as _ydb_query


logger = logging.getLogger(__name__)


class ISession(abc.ABC):

    @abc.abstractmethod
    def create(self):
        pass

    @abc.abstractmethod
    def delete(self):
        pass

    @property
    @abstractmethod
    def session_id(self):
        pass

class SessionState(object):
    def __init__(self, settings=None):
        self._settings = settings
        self.reset()

    def reset(self):
        self._session_id = None
        self._node_id = None
        self._is_attached = False

    @property
    def session_id(self):
        return self._session_id

    @property
    def node_id(self):
        return self._node_id

    def set_id(self, session_id):
        self._session_id = session_id
        return self

    def set_node_id(self, node_id):
        self._node_id = node_id
        return self

    def attached(self):
        return self._is_attached



class QuerySession(ISession):
    def __init__(self, driver, settings=None):
        self._driver = driver
        self._state = SessionState(settings)

    @property
    def session_id(self):
        return self._state.session_id

    @property
    def node_id(self):
        return self._state.node_id

    def create(self):
        if self._state.session_id is not None:
            return self

        # TODO: check what is settings

        res = self._driver(
            _apis.ydb_query.CreateSessionRequest(),
            _apis.QueryService.Stub,
            _apis.QueryService.CreateSession,
            common_utils.create_result_wrapper(_ydb_query.CreateSessionResponse),
        )

        logging.info("session.create: success")

        self._state.set_id(res.session_id).set_node_id(res.node_id)

        return None

    def delete(self):

        if self._state.session_id is None:
            return None

        res = self._driver(
            _apis.ydb_query.DeleteSessionRequest(session_id=self._state.session_id),
            _apis.QueryService.Stub,
            _apis.QueryService.DeleteSession,
            common_utils.create_result_wrapper(_ydb_query.DeleteSessionResponse),
        )
        logging.info("session.delete: success")

        self._state.reset()

        return None

    # def attach(self):
    #     if self._state.attached():
    #         return self

    #     stream_it = self._driver(
    #         _apis.ydb_query.AttachSessionRequest(session_id=self._state.session_id),
    #         _apis.QueryService.Stub,
    #         _apis.QueryService.AttachSession,
    #         common_utils.create_result_wrapper(_ydb_query.AttachSessionResponse),
    #     )

        # it = _utilities.SyncResponseIterator(

    #     )

    #     return None



if __name__ == "__main__":

    from ..driver import Driver

    endpoint = "grpc://localhost:2136"
    database = "/local"

    with Driver(endpoint=endpoint, database=database) as driver:
        driver.wait(timeout=5)
        session = QuerySession(driver)
        print(session.session_id)
        print(session.node_id)

        session.create()

        print(session.session_id)
        print(session.node_id)

        session.delete()

        print(session.session_id)
        print(session.node_id)

