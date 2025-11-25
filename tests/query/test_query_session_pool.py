import json

import pytest
import ydb
import time
from concurrent import futures

from typing import Optional

from tests.conftest import wait_container_ready
from ydb import QueryExplainResultFormat
from ydb.query.pool import QuerySessionPool
from ydb.query.session import QuerySession, QuerySessionStateEnum
from ydb.query.transaction import QueryTxContext


class TestQuerySessionPool:
    def test_checkout_provides_created_session(self, pool: QuerySessionPool):
        with pool.checkout() as session:
            assert session._state._state == QuerySessionStateEnum.CREATED

    def test_oneshot_query_normal(self, pool: QuerySessionPool):
        res = pool.execute_with_retries("select 1;")
        assert len(res) == 1

    def test_oneshot_query_result_set_index(self, pool: QuerySessionPool):
        res = pool.execute_with_retries("select 1; select 2; select 3")
        assert len(res) == 3
        indexes = [result_set.index for result_set in res]
        assert indexes == [0, 1, 2]

    def test_oneshot_ddl_query(self, pool: QuerySessionPool):
        pool.execute_with_retries("create table Queen(key UInt64, PRIMARY KEY (key));")
        pool.execute_with_retries("drop table Queen;")

    def test_oneshot_query_raises(self, pool: QuerySessionPool):
        with pytest.raises(ydb.GenericError):
            pool.execute_with_retries("Is this the real life? Is this just fantasy?")

    def test_retry_op_uses_created_session(self, pool: QuerySessionPool):
        def callee(session: QuerySession):
            assert session._state._state == QuerySessionStateEnum.CREATED

        pool.retry_operation_sync(callee)

    def test_retry_op_normal(self, pool: QuerySessionPool):
        def callee(session: QuerySession):
            with session.transaction() as tx:
                iterator = tx.execute("select 1;", commit_tx=True)
                return [result_set for result_set in iterator]

        res = pool.retry_operation_sync(callee)
        assert len(res) == 1

    def test_retry_op_raises(self, pool: QuerySessionPool):
        class CustomException(Exception):
            pass

        def callee(session: QuerySession):
            raise CustomException()

        with pytest.raises(CustomException):
            pool.retry_operation_sync(callee)

    @pytest.mark.parametrize(
        "tx_mode",
        [
            (None),
            (ydb.QuerySerializableReadWrite()),
            (ydb.QuerySnapshotReadOnly()),
            (ydb.QuerySnapshotReadWrite()),
            (ydb.QueryOnlineReadOnly()),
            (ydb.QueryStaleReadOnly()),
        ],
    )
    def test_retry_tx_normal(self, pool: QuerySessionPool, tx_mode: Optional[ydb.BaseQueryTxMode]):
        retry_no = 0

        def callee(tx: QueryTxContext):
            nonlocal retry_no
            if retry_no < 2:
                retry_no += 1
                raise ydb.Unavailable("Fake fast backoff error")
            result_stream = tx.execute("SELECT 1")
            return [result_set for result_set in result_stream]

        result = pool.retry_tx_sync(callee=callee, tx_mode=tx_mode)
        assert len(result) == 1
        assert retry_no == 2

    def test_retry_tx_raises(self, pool: QuerySessionPool):
        class CustomException(Exception):
            pass

        def callee(tx: QueryTxContext):
            raise CustomException()

        with pytest.raises(CustomException):
            pool.retry_tx_sync(callee)

    def test_pool_size_limit_logic(self, pool: QuerySessionPool):
        target_size = 5
        pool._size = target_size
        ids = set()

        for i in range(1, target_size + 1):
            session = pool.acquire(timeout=0.1)
            assert pool._current_size == i
            assert session._state.session_id not in ids
            ids.add(session._state.session_id)

        with pytest.raises(ydb.SessionPoolEmpty):
            pool.acquire(timeout=0.1)

        last_id = session._state.session_id
        pool.release(session)

        session = pool.acquire(timeout=0.1)
        assert session._state.session_id == last_id
        assert pool._current_size == target_size

    def test_checkout_do_not_increase_size(self, pool: QuerySessionPool):
        session_id = None
        for _ in range(10):
            with pool.checkout() as session:
                if session_id is None:
                    session_id = session._state.session_id
                assert pool._current_size == 1
                assert session_id == session._state.session_id

    def test_pool_recreates_bad_sessions(self, pool: QuerySessionPool):
        with pool.checkout() as session:
            session_id = session._state.session_id
            session.delete()

        with pool.checkout() as session:
            assert session_id != session._state.session_id
            assert pool._current_size == 1

    def test_acquire_from_closed_pool_raises(self, pool: QuerySessionPool):
        pool.stop()
        with pytest.raises(ydb.SessionPoolClosed):
            pool.acquire(1)

    def test_no_session_leak(self, driver_sync, docker_project):
        pool = ydb.QuerySessionPool(driver_sync, 1)
        docker_project.stop()
        try:
            pool.acquire(timeout=0.1)
        except ydb.Error:
            pass
        assert pool._current_size == 0

        docker_project.start()
        wait_container_ready(driver_sync)
        pool.stop()

    def test_execute_with_retries_async(self, pool: QuerySessionPool):
        fut = pool.execute_with_retries_async("select 1;")
        res = fut.result()
        assert len(res) == 1

    def test_retry_operation_async(self, pool: QuerySessionPool):
        def callee(session: QuerySession):
            with session.transaction() as tx:
                iterator = tx.execute("select 1;", commit_tx=True)
                return [result_set for result_set in iterator]

        fut = pool.retry_operation_async(callee)
        res = fut.result()
        assert len(res) == 1

    def test_retry_tx_async(self, pool: QuerySessionPool):
        retry_no = 0

        def callee(tx: QueryTxContext):
            nonlocal retry_no
            if retry_no < 2:
                retry_no += 1
                raise ydb.Unavailable("Fake fast backoff error")
            result_stream = tx.execute("SELECT 1")
            return [result_set for result_set in result_stream]

        result = pool.retry_tx_async(callee=callee).result()
        assert len(result) == 1
        assert retry_no == 2

    def test_execute_with_retries_async_many_calls(self, pool: QuerySessionPool):
        futs = [pool.execute_with_retries_async("select 1;") for _ in range(10)]
        results = [f.result() for f in futures.as_completed(futs)]
        assert all(len(r) == 1 for r in results)

    def test_future_waits_on_stop(self, pool: QuerySessionPool):
        def callee(session: QuerySession):
            time.sleep(0.1)
            with session.transaction() as tx:
                it = tx.execute("select 1;", commit_tx=True)
                return [rs for rs in it]

        fut = pool.retry_operation_async(callee)
        pool.stop()
        assert fut.done()
        assert len(fut.result()) == 1

    def test_async_methods_after_stop_raise(self, pool: QuerySessionPool):
        pool.stop()
        with pytest.raises(ydb.SessionPoolClosed):
            pool.execute_with_retries_async("select 1;")

    def test_explain_with_retries(self, pool: QuerySessionPool):
        pool.execute_with_retries("DROP TABLE IF EXISTS test_explain")
        pool.execute_with_retries("CREATE TABLE test_explain (id Int64, PRIMARY KEY (id))")
        try:

            plan = pool.explain_with_retries("SELECT * FROM test_explain", result_format=QueryExplainResultFormat.STR)
            isinstance(plan, str)
            assert "FullScan" in plan

            plan = pool.explain_with_retries("SELECT * FROM test_explain", result_format=QueryExplainResultFormat.DICT)
            assert isinstance(plan, dict)

            plan_string = json.dumps(plan)
            assert "FullScan" in plan_string

            plan = pool.explain_with_retries(
                "SELECT * FROM test_explain WHERE id = $id",
                {"$id": 1},
                result_format=ydb.QueryExplainResultFormat.DICT,
            )
            plan_string = json.dumps(plan)
            assert "Lookup" in plan_string
        finally:
            pool.execute_with_retries("DROP TABLE test_explain")
