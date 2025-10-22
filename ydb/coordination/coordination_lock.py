from ydb.coordination.сoordination_session import CoordinationSession


class CoordinationLock:
    def __init__(self, session: CoordinationSession, path: str, timeout: int = 5000, count: int = 1):
        self._session = session
        self._path = path
        self._timeout = timeout
        self._count = count

    def acquire(self):
        self._session.acquire_semaphore(self._path, self._count, self._timeout)

    def release(self):
        self._session.release_semaphore(self._path)

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
