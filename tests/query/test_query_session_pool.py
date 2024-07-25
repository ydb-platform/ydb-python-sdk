import pytest
import ydb
from ydb.query.pool import QuerySessionPool
from ydb.query.session import QuerySessionSync, QuerySessionStateEnum


class TestQuerySessionPool:
    def test_checkout_provides_created_session(self, pool: QuerySessionPool):
        with pool.checkout() as session:
            assert session._state._state == QuerySessionStateEnum.CREATED

        assert session._state._state == QuerySessionStateEnum.CLOSED

    def test_oneshot_query_normal(self, pool: QuerySessionPool):
        res = pool.execute_with_retries("select 1;")
        assert len(res) == 1

    def test_oneshot_ddl_query(self, pool: QuerySessionPool):
        pool.execute_with_retries("create table Queen(key UInt64, PRIMARY KEY (key));")
        pool.execute_with_retries("drop table Queen;")

    def test_oneshot_query_raises(self, pool: QuerySessionPool):
        with pytest.raises(ydb.GenericError):
            pool.execute_with_retries("Is this the real life? Is this just fantasy?")

    def test_retry_op_uses_created_session(self, pool: QuerySessionPool):
        def callee(session: QuerySessionSync):
            assert session._state._state == QuerySessionStateEnum.CREATED

        pool.retry_operation_sync(callee)

    def test_retry_op_normal(self, pool: QuerySessionPool):
        def callee(session: QuerySessionSync):
            with session.transaction() as tx:
                iterator = tx.execute("select 1;", commit_tx=True)
                return [result_set for result_set in iterator]

        res = pool.retry_operation_sync(callee)
        assert len(res) == 1

    def test_retry_op_raises(self, pool: QuerySessionPool):
        def callee(session: QuerySessionSync):
            with session.execute("Caught in a landslide, no escape from reality"):
                pass

        with pytest.raises(ydb.GenericError):
            pool.retry_operation_sync(callee)
