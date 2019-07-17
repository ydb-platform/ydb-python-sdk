# -*- coding: utf-8 -*-
import collections
from concurrent import futures
from six.moves import queue
import time
import threading
from . import settings, issues, _utilities


class SessionPoolImpl(object):
    def __init__(self, driver, size, workers_threads_count=4, initializer=None):
        self._lock = threading.RLock()
        self._waiters = collections.OrderedDict()
        self._driver = driver
        self._active_queue = queue.PriorityQueue()
        self._active_count = 0
        self._size = size
        self._req_settings = settings.BaseRequestSettings().with_timeout(3)
        self._tp = futures.ThreadPoolExecutor(workers_threads_count)
        self._initializer = initializer
        self._should_stop = threading.Event()
        self._keep_alive_threshold = 4 * 60
        self._spin_timeout = 30
        self._pool_thread = _PoolThread(self)
        self._pool_thread.start()

    def stop(self, timeout):
        self._should_stop.set()
        self._pool_thread.join(timeout)

    def pick(self):
        with self._lock:
            try:
                priority, session = self._active_queue.get_nowait()
            except queue.Empty:
                return None

            till_expire = priority - time.time()
            if till_expire < self._keep_alive_threshold:
                return session
            self._active_queue.put((priority, session))
            return None

    def _create(self):
        with self._lock:
            session = self._driver.table_client.session()
            self._active_count += 1
            return session

    @property
    def active_size(self):
        with self._lock:
            return self._active_count

    def _destroy(self, session):
        with self._lock:
            self._active_count -= 1
            if len(self._waiters) > 0:
                # we have a waiter that should be replied, so we have to prepare replacement
                self._prepare(self._create())

        if session.initialized():
            session.async_delete(self._req_settings)

    def put(self, session):
        with self._lock:
            if not session.initialized():
                self._destroy(session)
                # we should probably prepare replacement session here
                return False

            try:
                _, waiter = self._waiters.popitem(last=False)
                waiter.set_result(session)
            except KeyError:
                priority = time.time() + 10 * 60
                self._active_queue.put(
                    (priority, session))

    def _on_session_create(self, session, f):
        with self._lock:
            try:
                f.result()
                if self._initializer is None:
                    return self.put(session)
            except issues.Error:
                self._prepare(session)
                return

        init_f = self._tp.submit(self._initializer, session)

        def _on_initialize(in_f):
            try:
                in_f.result()
                self.put(session)
            except Exception:
                self._prepare(session)

        init_f.add_done_callback(_on_initialize)

    def _prepare(self, session):
        if self._should_stop.is_set():
            self._destroy(session)
            return

        f = session.async_create(self._req_settings)
        f.add_done_callback(lambda _: self._on_session_create(session, _))

    def _waiter_cleanup(self, w):
        with self._lock:
            try:
                self._waiters.pop(w)
            except KeyError:
                return None

    def subscribe(self):
        with self._lock:
            try:
                _, session = self._active_queue.get(block=False)
                return _utilities.wrap_result_in_future(session)
            except queue.Empty:
                waiter = _utilities.future()
                waiter.add_done_callback(self._waiter_cleanup)
                self._waiters[waiter] = waiter
                if self._active_count < self._size:
                    session = self._create()
                    self._prepare(session)
                return waiter

    def unsubscribe(self, waiter):
        with self._lock:
            try:
                # at first we remove waiter from list of the waiters to ensure
                # we will not signal it right now
                self._waiters.pop(waiter)
            except KeyError:
                try:
                    session = waiter.result(timeout=-1)
                    self.put(session)
                except (futures.CancelledError, futures.TimeoutError):
                    # future is cancelled and not signalled
                    pass

    def _on_keep_alive(self, session, f):
        try:
            self.put(f.result())
            # additional logic should be added to check
            # current status of the session
        except issues.Error:
            self._destroy(
                session)

    def acquire(self, blocking=True, timeout=None):
        waiter = self.subscribe()
        if blocking:
            try:
                session = waiter.result(timeout=timeout)
                return session
            except futures.TimeoutError:
                self.unsubscribe(waiter)
                raise issues.SessionPoolEmpty("Timeout on session acquire.")
        else:
            try:
                return waiter.result(timeout=-1)
            except futures.TimeoutError:
                self.unsubscribe(waiter)
                raise issues.SessionPoolEmpty("Session pool is empty.")

    def should_stop(self):
        signaled = self._should_stop.wait(self._spin_timeout)
        return signaled

    def send_keep_alive(self):
        session = self.pick()
        if session is None:
            return False

        if self._should_stop.is_set():
            self._destroy(session)
            return False

        f = session.async_keep_alive(self._req_settings)
        f.add_done_callback(lambda q: self._on_keep_alive(session, q))
        return True


class _PoolThread(threading.Thread):
    def __init__(self, pool_impl):
        super(_PoolThread, self).__init__()
        self.daemon = True
        self._pool_impl = pool_impl

    def run(self):
        while not self._pool_impl.should_stop():
            while True:
                if not self._pool_impl.send_keep_alive():
                    break
