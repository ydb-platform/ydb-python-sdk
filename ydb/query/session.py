import abc
from abc import abstractmethod
import asyncio
import logging
from typing import (
    Set,
)

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

class SessionState:
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

    def set_attached(self, is_attached):
        self._is_attached = is_attached

    @property
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

    async def create(self):
        if self._state.session_id is not None:
            return self

        # TODO: check what is settings

        res = await self._driver(
            _apis.ydb_query.CreateSessionRequest(),
            _apis.QueryService.Stub,
            _apis.QueryService.CreateSession,
            common_utils.create_result_wrapper(_ydb_query.CreateSessionResponse),
        )

        logging.info("session.create: success")

        self._state.set_id(res.session_id).set_node_id(res.node_id)

        return None

    async def delete(self):

        if self._state.session_id is None:
            return None

        res = await self._driver(
            _apis.ydb_query.DeleteSessionRequest(session_id=self._state.session_id),
            _apis.QueryService.Stub,
            _apis.QueryService.DeleteSession,
            common_utils.create_result_wrapper(_ydb_query.DeleteSessionResponse),
        )
        logging.info("session.delete: success")

        self._state.reset()
        if self._stream is not None:
            await self._stream.close()
            self._stream = None

        return None

    async def attach(self):
        self._stream = await SessionStateReaderStream.create(self._driver, self._state)

        print(self._state.attached)




class SessionStateReaderStream:
    _started: bool
    _stream: common_utils.IGrpcWrapperAsyncIO
    _session: QuerySession
    _background_tasks: Set[asyncio.Task]

    def __init__(self, session_state: SessionState):
        self._session_state = session_state
        self._background_tasks = set()
        self._started = False


    @staticmethod
    async def create(driver: common_utils.SupportedDriverType, session_state: SessionState):
        stream = common_utils.GrpcWrapperUnaryStreamAsyncIO(common_utils.ServerStatus.from_proto)
        await stream.start(
            driver,
            _ydb_query.AttachSessionRequest(session_id=session_state.session_id).to_proto(),
            _apis.QueryService.Stub,
            _apis.QueryService.AttachSession
        )

        reader = SessionStateReaderStream(session_state)

        await reader._start(stream)

        return reader

    async def _start(self, stream: common_utils.IGrpcWrapperAsyncIO):
        if self._started:
            return # TODO: error

        self._started = True
        self._stream = stream

        response = await self._stream.receive()

        if response.is_success():
            self._session_state.set_attached(True)
        else:
            raise common_utils.YdbError(response.error)

        self._background_tasks.add(asyncio.create_task(self._update_session_state_loop(), name="update_session_state_loop"))

        return response

    async def _update_session_state_loop(self):
        while True:
            response = await self._stream.receive()

            if response.is_success():
                pass
            else:
                self._session_state.set_attached(False)

    async def close(self):
        self._stream.close()
        for task in self._background_tasks:
            task.cancel()

        if self._background_tasks:
            await asyncio.wait(self._background_tasks)


async def main():
    from ..aio.driver import Driver

    endpoint = "grpc://localhost:2136"
    database = "/local"

    driver = Driver(endpoint=endpoint, database=database)  # Creating new database driver to execute queries

    await driver.wait(timeout=10)  # Wait until driver can execute calls

    session = QuerySession(driver)

    print(session.session_id)
    print(session.node_id)

    await session.create()

    print(session.session_id)
    print(session.node_id)


    await session.attach()

    await session.delete()

    print(session.session_id)
    print(session.node_id)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

