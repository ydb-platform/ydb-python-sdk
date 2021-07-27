import asyncio
import logging
import time
import typing
import ydb

from kikimr.public.sdk.python.client import issues, settings

from kikimr.public.sdk.python.client.table import (
    BaseSession,
    BaseTableClient,
    _scan_query_request_factory,
    _wrap_scan_query_response,
    BaseTxContext
)
from . import _utilities
from kikimr.public.sdk.python.client import _apis, _session_impl
logger = logging.getLogger(__name__)


class Session(BaseSession):

    async def read_table(
        self, path, key_range=None, columns=(), ordered=False, row_limit=None, settings=None, use_snapshot=None
    ):
        request = _session_impl.read_table_request_factory(self._state, path, key_range, columns, ordered, row_limit,
                                                           use_snapshot=use_snapshot)
        stream_it = await self._driver(
            request, _apis.TableService.Stub, _apis.TableService.StreamReadTable, settings=settings
        )
        return _utilities.AsyncResponseIterator(stream_it, _session_impl.wrap_read_table_response)

    async def keep_alive(self, settings=None):
        return await super(Session, self).keep_alive(settings)

    async def create(self, settings=None):
        return await super(Session, self).create(settings)

    async def delete(self, settings=None):
        return await super(Session, self).delete(settings)

    async def execute_scheme(self, yql_text, settings=None):
        return await super(Session, self).execute_scheme(yql_text, settings)

    async def prepare(self, query, settings=None):
        return await super(Session, self).prepare(query, settings)

    async def explain(self, yql_text, settings=None):
        return await super(Session, self).explain(yql_text, settings)

    async def create_table(self, path, table_description, settings=None):
        return await super(Session, self).create_table(path, table_description, settings)

    async def drop_table(self, path, settings=None):
        return await super(Session, self).drop_table(path, settings)

    async def alter_table(
            self, path,
            add_columns=None, drop_columns=None,
            settings=None,
            alter_attributes=None,
            add_indexes=None, drop_indexes=None,
            set_ttl_settings=None, drop_ttl_settings=None,
            add_column_families=None, alter_column_families=None,
            alter_storage_settings=None,
            set_compaction_policy=None,
            alter_partitioning_settings=None,
            set_key_bloom_filter=None,
            set_read_replicas_settings=None):
        return await super(Session, self).alter_table(
            path,
            add_columns,
            drop_columns,
            settings,
            alter_attributes,
            add_indexes,
            drop_indexes,
            set_ttl_settings,
            drop_ttl_settings,
            add_column_families,
            alter_column_families,
            alter_storage_settings,
            set_compaction_policy,
            alter_partitioning_settings,
            set_key_bloom_filter,
            set_read_replicas_settings
        )

    def transaction(self, tx_mode=None):
        return TxContext(self._driver, self._state, self, tx_mode)

    async def describe_table(self, path, settings=None):
        return await super(Session, self).describe_table(path, settings)

    async def copy_table(self, source_path, destination_path, settings=None):
        return await super(Session, self).copy_table(source_path, destination_path, settings)

    async def copy_tables(self, source_destination_pairs, settings=None):
        return await super(Session, self).copy_tables(source_destination_pairs, settings)


class TableClient(BaseTableClient):

    def session(self):
        return Session(self._driver, self._table_client_settings)

    async def bulk_upsert(self, *args, **kwargs):
        return await super(TableClient, self).bulk_upsert(*args, **kwargs)

    async def scan_query(self, query, parameters=None, settings=None):
        request = _scan_query_request_factory(query, parameters, settings)
        response = await self._driver(
            request, _apis.TableService.Stub, _apis.TableService.StreamExecuteScanQuery, settings=settings
        )
        return _utilities.AsyncResponseIterator(
            response, lambda resp: _wrap_scan_query_response(resp, self._table_client_settings)
        )


class TxContext(BaseTxContext):
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._tx_state.tx_id is not None:
            # It's strictly recommended to close transactions directly
            # by using commit_tx=True flag while executing statement or by
            # .commit() or .rollback() methods, but here we trying to do best
            # effort to avoid useless open transactions
            logger.warning("Potentially leaked tx: %s", self._tx_state.tx_id)
            try:
                await self.rollback()
            except issues.Error:
                logger.warning(
                    "Failed to rollback leaked tx: %s", self._tx_state.tx_id)

            self._tx_state.tx_id = None

    async def execute(self, query, parameters=None, commit_tx=False, settings=None):
        return await super(TxContext, self).execute(query, parameters, commit_tx, settings)

    async def commit(self, settings=None):
        return await super(TxContext, self).commit(settings)

    async def rollback(self, settings=None):
        return await super(TxContext, self).rollback(settings)

    async def begin(self, settings=None):
        return await super(TxContext, self).begin(settings)


class SessionPool:
    def __init__(self, driver: ydb.pool.IConnectionPool, size: int, min_pool_size: int = 0):
        self._driver_await_timeout = 3
        self._should_stop = asyncio.Event()
        self._waiters = 0
        self._driver = driver
        self._active_queue = asyncio.PriorityQueue()
        self._active_count = 0
        self._size = size
        self._req_settings = settings.BaseRequestSettings().with_timeout(3)
        self._logger = logger.getChild(self.__class__.__name__)
        self._min_pool_size = min_pool_size
        self._keep_alive_threshold = 4 * 60
        self._terminating = False
        self._init_session_timeout = 20

        self._keep_alive_task = asyncio.ensure_future(self._keep_alive_loop())

        self._min_pool_tasks = []

        for _ in range(self._min_pool_size):
            self._min_pool_tasks.append(asyncio.ensure_future(self._init_and_put(self._init_session_timeout)))

    def _create(self) -> ydb.ISession:
        self._active_count += 1
        session = self._driver.table_client.session()
        self._logger.debug("Created session %s", session)
        return session

    async def _init_session_logic(
        self, session: ydb.ISession
    ) -> typing.Optional[ydb.ISession]:
        try:
            await self._driver.wait(self._driver_await_timeout)
            session = await session.create(self._req_settings)
            return session
        except issues.Error as e:
            self._logger.error("Failed to create session. Reason: %s", str(e))
        except Exception as e:
            self._logger.exception("Failed to create session. Reason: %s", str(e))

        return None

    async def _init_session(
        self, session: ydb.ISession, retry_num: int = None
    ) -> typing.Optional[ydb.ISession]:
        """
        :param retry_num: Number of retries. If None - retries until success.
        :return:
        """
        i = 0
        while retry_num is None or i < retry_num:
            curr_sess = await self._init_session_logic(session)
            if curr_sess:
                return curr_sess
            i += 1
        return None

    async def _prepare_session(self, timeout, retry_num) -> ydb.ISession:
        session = self._create()
        try:
            new_sess = await asyncio.wait_for(self._init_session(
                session,
                retry_num=retry_num
            ), timeout=timeout)
            if not new_sess:
                self._destroy(session)
            return new_sess
        except Exception as e:
            self._destroy(session)
            raise e

    async def _get_session_from_queue(self, timeout: float):
        task_wait = asyncio.ensure_future(asyncio.wait_for(self._active_queue.get(), timeout=timeout))
        task_should_stop = asyncio.ensure_future(self._should_stop.wait())
        done, pending = await asyncio.wait(
            (
                task_wait,
                task_should_stop
            ),
            return_when=asyncio.FIRST_COMPLETED
        )
        if task_should_stop in done:
            task_wait.cancel()
            return self._create()
        _, session = task_wait.result()
        return session

    async def acquire(self, timeout: float = None, retry_timeout: float = None, retry_num: int = None) -> ydb.ISession:

        if self._should_stop.is_set():
            return self._create()

        if retry_timeout is None:
            retry_timeout = timeout

        try:
            _, session = self._active_queue.get_nowait()
            return session
        except asyncio.QueueEmpty:
            pass

        if self._active_count < self._size:
            self._logger.debug(
                "Session pool is not large enough (active_count < size: %d < %d). "
                "will create a new session.", self._active_count, self._size)
            try:
                session = await self._prepare_session(timeout=retry_timeout, retry_num=retry_num)
            except asyncio.TimeoutError:
                raise issues.SessionPoolEmpty("Timeout when creating session")

            if session is not None:
                return session

        try:
            self._waiters += 1
            session = await self._get_session_from_queue(timeout)
            return session
        except asyncio.TimeoutError:
            raise issues.SessionPoolEmpty("Timeout when wait")
        finally:
            self._waiters -= 1

    def _is_min_pool_size_satisfied(self, delta=0):
        if self._terminating:
            return True
        return self._active_count + delta >= self._min_pool_size

    async def _init_and_put(self, timeout=10):
        sess = await self._prepare_session(
                        timeout=timeout,
                        retry_num=None
                    )
        await self.release(session=sess)

    def _destroy(self, session: ydb.ISession, wait_for_del: bool = False):
        self._logger.debug("Requested session destroy: %s.", session)
        self._active_count -= 1
        self._logger.debug("Session %s is no longer active. Current active count %d.", session, self._active_count)

        if self._waiters > 0 or not self._is_min_pool_size_satisfied():
            asyncio.ensure_future(
                self._init_and_put(self._init_session_timeout)
            )

        if session.initialized():
            coro = session.delete(self._req_settings)
            if wait_for_del:
                self._logger.debug("Sent delete on session %s", session)
                return coro
            else:
                asyncio.ensure_future(coro)

    async def release(self, session: ydb.ISession):
        self._logger.debug("Put on session %s", session)
        if session.pending_query():
            self._destroy(session)
            return False
        if not session.initialized() or self._should_stop.is_set():
            self._destroy(session)
            return False

        await self._active_queue.put(
            (time.time() + 10 * 60, session)
        )

    async def _pick_for_keepalive(self):
        try:
            priority, session = self._active_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

        till_expire = priority - time.time()
        if till_expire < self._keep_alive_threshold:
            return session
        await self._active_queue.put((priority, session))
        return None

    async def _send_keep_alive(self, session: ydb.ISession):
        if session is None:
            return False
        if self._should_stop.is_set():
            self._destroy(session)
            return False
        await session.keep_alive(self._req_settings)
        try:
            await self.release(session)
        except Exception:
            self._destroy(session)

    async def _keep_alive_loop(self):
        while True:
            try:
                await asyncio.wait_for(self._should_stop.wait(), timeout=self._keep_alive_threshold // 4)
                break
            except asyncio.TimeoutError:
                while True:
                    session = await self._pick_for_keepalive()
                    if not session:
                        break
                    asyncio.ensure_future(self._send_keep_alive(session))

    async def stop(self, timeout=None):
        self._logger.debug("Requested session pool stop.")
        self._should_stop.set()
        self._terminating = True

        for task in self._min_pool_tasks:
            task.cancel()

        self._logger.debug("Destroying sessions in active queue")

        tasks = []

        while True:
            try:
                _, session = self._active_queue.get_nowait()
                tasks.append(self._destroy(session, wait_for_del=True))

            except asyncio.QueueEmpty:
                break

        await asyncio.gather(*tasks)

        self._logger.debug("Destroyed active sessions")

        await asyncio.wait_for(self._keep_alive_task, timeout=timeout)

    async def wait_until_min_size(self):
        await asyncio.gather(*self._min_pool_tasks)
