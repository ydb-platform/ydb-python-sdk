import time

import ydb
from ydb._grpc.v5.protos.ydb_coordination_pb2 import SessionRequest
from ydb._grpc.v5.ydb_coordination_v1_pb2_grpc import CoordinationServiceStub
from ydb._utilities import SyncResponseIterator


class CoordinationSession:
    def __init__(self, driver: "ydb.Driver"):
        self._driver = driver
        self._session_id = None

    def _ensure_session(self):
        if self._session_id is None:
            req = SessionRequest(session_start=SessionRequest.SessionStart())
            stream_it = self._driver(
                req,
                CoordinationServiceStub,
                "Session",
            )
            iterator = SyncResponseIterator(stream_it, lambda resp: resp)
            first_resp = next(iterator)
            self._session_id = first_resp.session_started.session_id
        return self._session_id

    def acquire_semaphore(self, path: str, count: int = 1, timeout_millis: int = 5000):
        session_id = self._ensure_session()
        acquire_req = SessionRequest(
            acquire_semaphore=SessionRequest.AcquireSemaphore(
                name=path,
                count=count,
                timeout_millis=timeout_millis,
                req_id=int(time.time() * 1000),
                data=b"",
                ephemeral=True,
            ),
            session_start=SessionRequest.SessionStart(session_id=session_id)
        )
        stream_it = self._driver(acquire_req, CoordinationServiceStub, "Session")
        iterator = SyncResponseIterator(stream_it, lambda resp: resp)
        resp = next(iterator)
        result = getattr(resp, "acquire_semaphore_result", None)
        if not result or not result.acquired:
            raise RuntimeError(f"Failed to acquire semaphore {path}")

    def release_semaphore(self, path: str):
        if self._session_id is None:
            return
        release_req = SessionRequest(
            release_semaphore=SessionRequest.ReleaseSemaphore(
                name=path,
                req_id=int(time.time() * 1000),
            ),
            session_stop=SessionRequest.SessionStop()
        )
        stream_it = self._driver(release_req, CoordinationServiceStub, "Session")
        SyncResponseIterator(stream_it, lambda resp: resp)
        self._session_id = None