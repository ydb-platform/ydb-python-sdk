import pytest
import ydb
from ydb.aio.query.pool import QuerySessionPoolAsync
from ydb.aio.query.session import QuerySessionAsync, QuerySessionStateEnum


class TestQuerySessionPoolAsync:
    @pytest.mark.asyncio
    async def test_checkout_provides_created_session(self, pool: QuerySessionPoolAsync):
        async with pool.checkout() as session:
            assert session._state._state == QuerySessionStateEnum.CREATED

    @pytest.mark.asyncio
    async def test_oneshot_query_normal(self, pool: QuerySessionPoolAsync):
        res = await pool.execute_with_retries("select 1;")
        assert len(res) == 1

    @pytest.mark.asyncio
    async def test_oneshot_ddl_query(self, pool: QuerySessionPoolAsync):
        await pool.execute_with_retries("drop table if exists Queen;")
        await pool.execute_with_retries("create table Queen(key UInt64, PRIMARY KEY (key));")
        await pool.execute_with_retries("drop table Queen;")

    @pytest.mark.asyncio
    async def test_oneshot_query_raises(self, pool: QuerySessionPoolAsync):
        with pytest.raises(ydb.GenericError):
            await pool.execute_with_retries("Is this the real life? Is this just fantasy?")

    @pytest.mark.asyncio
    async def test_retry_op_uses_created_session(self, pool: QuerySessionPoolAsync):
        async def callee(session: QuerySessionAsync):
            assert session._state._state == QuerySessionStateEnum.CREATED

        await pool.retry_operation_async(callee)

    @pytest.mark.asyncio
    async def test_retry_op_normal(self, pool: QuerySessionPoolAsync):
        async def callee(session: QuerySessionAsync):
            async with session.transaction() as tx:
                iterator = await tx.execute("select 1;", commit_tx=True)
                return [result_set async for result_set in iterator]

        res = await pool.retry_operation_async(callee)
        assert len(res) == 1

    @pytest.mark.asyncio
    async def test_retry_op_raises(self, pool: QuerySessionPoolAsync):
        class CustomException(Exception):
            pass

        async def callee(session: QuerySessionAsync):
            raise CustomException()

        with pytest.raises(CustomException):
            await pool.retry_operation_async(callee)
