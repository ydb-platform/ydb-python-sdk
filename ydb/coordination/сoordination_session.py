import time

from ydb._grpc.v5.protos.ydb_coordination_pb2 import SessionRequest
from ydb._grpc.v5.ydb_coordination_v1_pb2_grpc import CoordinationServiceStub


class CoordinationSession:
    def __init__(self, driver: "ydb.Driver"):
        self._driver = driver

    def acquire_semaphore(self, name: str, count: int = 1, timeout: int = 5000):
        req = SessionRequest(
            acquire_semaphore=SessionRequest.AcquireSemaphore(
                name=name,
                count=count,
                timeout_millis=timeout,
                req_id=int(time.time() * 1000),
                data=b"",
                ephemeral=True,
            ),
            session_start=SessionRequest.SessionStart()
        )

        res_iter = self._driver(req, CoordinationServiceStub, "Session")
        res = next(res_iter)
        acquire_result = getattr(res, "acquire_semaphore_result", None)

        if not acquire_result or not acquire_result.acquired:
            raise RuntimeError(f"Failed to acquire semaphore {name}")

        return res.session_started.session_id

    def release_semaphore(self, name: str, session_id: int):
        req = SessionRequest(
            release_semaphore=SessionRequest.ReleaseSemaphore(
                name=name,
                req_id=int(time.time() * 1000),
            ),
            session_stop=SessionRequest.SessionStop()
        )
        self._driver(req, CoordinationServiceStub, "Session")