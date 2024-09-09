import asyncio
import pytest
import ydb
from ydb.aio.query.pool import QuerySessionPool
from ydb.aio.query.session import QuerySession, QuerySessionStateEnum


class TestQuerySessionPool:
    @pytest.mark.asyncio
    async def test_checkout_provides_created_session(self, pool: QuerySessionPool):
        async with pool.checkout() as session:
            assert session._state._state == QuerySessionStateEnum.CREATED

    @pytest.mark.asyncio
    async def test_oneshot_query_normal(self, pool: QuerySessionPool):
        res = await pool.execute_with_retries("select 1;")
        assert len(res) == 1

    @pytest.mark.asyncio
    async def test_oneshot_ddl_query(self, pool: QuerySessionPool):
        await pool.execute_with_retries("drop table if exists Queen;")
        await pool.execute_with_retries("create table Queen(key UInt64, PRIMARY KEY (key));")
        await pool.execute_with_retries("drop table Queen;")

    @pytest.mark.asyncio
    async def test_oneshot_query_raises(self, pool: QuerySessionPool):
        with pytest.raises(ydb.GenericError):
            await pool.execute_with_retries("Is this the real life? Is this just fantasy?")

    @pytest.mark.asyncio
    async def test_retry_op_uses_created_session(self, pool: QuerySessionPool):
        async def callee(session: QuerySession):
            assert session._state._state == QuerySessionStateEnum.CREATED

        await pool.retry_operation_async(callee)

    @pytest.mark.asyncio
    async def test_retry_op_normal(self, pool: QuerySessionPool):
        async def callee(session: QuerySession):
            async with session.transaction() as tx:
                iterator = await tx.execute("select 1;", commit_tx=True)
                return [result_set async for result_set in iterator]

        res = await pool.retry_operation_async(callee)
        assert len(res) == 1

    @pytest.mark.asyncio
    async def test_retry_op_raises(self, pool: QuerySessionPool):
        class CustomException(Exception):
            pass

        async def callee(session: QuerySession):
            raise CustomException()

        with pytest.raises(CustomException):
            await pool.retry_operation_async(callee)

    @pytest.mark.asyncio
    async def test_pool_size_limit_logic(self, pool: QuerySessionPool):
        target_size = 5
        pool._size = target_size
        ids = set()

        for i in range(1, target_size + 1):
            session = await pool.acquire()
            assert pool._current_size == i
            assert session._state.session_id not in ids
            ids.add(session._state.session_id)

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(pool.acquire(), timeout=0.1)

        last_id = session._state.session_id
        await pool.release(session)

        session = await pool.acquire()
        assert session._state.session_id == last_id
        assert pool._current_size == target_size

    @pytest.mark.asyncio
    async def test_checkout_do_not_increase_size(self, pool: QuerySessionPool):
        session_id = None
        for _ in range(10):
            async with pool.checkout() as session:
                if session_id is None:
                    session_id = session._state.session_id
                assert pool._current_size == 1
                assert session_id == session._state.session_id

    @pytest.mark.asyncio
    async def test_pool_recreates_bad_sessions(self, pool: QuerySessionPool):
        async with pool.checkout() as session:
            session_id = session._state.session_id
            await session.delete()

        async with pool.checkout() as session:
            assert session_id != session._state.session_id
            assert pool._current_size == 1

    @pytest.mark.asyncio
    async def test_acquire_from_closed_pool_raises(self, pool: QuerySessionPool):
        await pool.stop()
        with pytest.raises(RuntimeError):
            await pool.acquire()

    @pytest.mark.asyncio
    async def test_acquire_with_timeout_from_closed_pool_raises(self, pool: QuerySessionPool):
        await pool.stop()
        with pytest.raises(RuntimeError):
            await asyncio.wait_for(pool.acquire(), timeout=0.1)

    @pytest.mark.asyncio
    async def test_no_session_leak(self, driver, docker_project):
        pool = ydb.aio.QuerySessionPool(driver, 1)
        docker_project.stop()
        try:
            await asyncio.wait_for(pool.acquire(), timeout=0.1)
        except ydb.Error:
            pass
        assert pool._current_size == 0

        docker_project.start()
        await pool.stop()
