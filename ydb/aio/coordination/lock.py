import asyncio
from ydb import issues
from ydb._grpc.grpcwrapper.ydb_coordination import AcquireSemaphore, ReleaseSemaphore, FromServer, SessionStart


class CoordinationLock:
    def __init__(self, client, name, node_path=None):
        self._client = client
        self._name = name
        self._node_path = node_path
        self._req_id = None
        self._entered_client = False
        self._count = 1
        self._timeout_millis = 30000
        self._next_req_id = 1

    def next_req_id(self) -> int:
        r = self._next_req_id
        self._next_req_id += 1
        return r

    async def send(self, req):
        if self._client._stream is None:
            raise issues.Error("Stream is not started yet")
        await self._client._stream.send(req)

    async def __aenter__(self):
        if self._client.session_id is None:
            if not self._client._node_path:
                self._client._node_path = self._node_path

            await self._client._request_queue.put(
                SessionStart(
                    path=self._client._node_path,
                    session_id=0,
                    timeout_millis=30000
                ).to_proto()
            )

            self._client._reconnector.start()

            await self._client._session_ready.wait()
            self._entered_client = True

        self._req_id = self.next_req_id()

        req = AcquireSemaphore(
            req_id=self._req_id,
            name=self._name,
            count=self._count,
            ephemeral=True,
            timeout_millis=self._timeout_millis
        ).to_proto()

        await self.send(req)

        resp = await self._wait_for_acquire_response()
        if resp.acquired:
            return self
        else:
            raise issues.Error(f"Failed to acquire lock: {resp.issues}")

    async def _wait_for_acquire_response(self):
        try:
            while True:
                resp = await asyncio.wait_for(
                    self._client._stream._incoming_queue.get(), timeout=30.0
                )
                acquire_resp = FromServer.from_proto(resp).acquire_semaphore_result
                if acquire_resp and acquire_resp.req_id == self._req_id:
                    return acquire_resp
        except asyncio.TimeoutError:
            raise issues.Error(f"Timeout waiting for lock {self._name} acquisition")

    async def __aexit__(self, exc_type, exc, tb):
        if self._req_id is not None:
            req = ReleaseSemaphore(req_id=self._req_id, name=self._name)
            await self.send(req)

        if self._entered_client:
            self._client._closed.set()
            if self._client._stream:
                await self._client._stream.close()
                self._client._stream = None
            await self._client._reconnector.stop()
            self._client.session_id = None
            self._client._node_path = None
