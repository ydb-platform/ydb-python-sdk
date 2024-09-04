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

    @pytest.mark.asyncio
    async def test_pool_size_limit_logic(self, pool: QuerySessionPoolAsync):
        target_size = 5
        pool._size = target_size
        ids = set()

        for i in range(1, target_size + 1):
            session = await pool.acquire_wih_timeout(timeout=0.5)
            assert pool._current_size == i
            assert session._state.session_id not in ids
            ids.add(session._state.session_id)

        with pytest.raises(ydb.SessionPoolEmpty):
            await pool.acquire_wih_timeout(timeout=0.5)

        await pool.release(session)

        session = await pool.acquire_wih_timeout(timeout=0.5)
        assert pool._current_size == target_size
        assert session._state.session_id in ids

    @pytest.mark.asyncio
    async def test_checkout_do_not_increase_size(self, pool: QuerySessionPoolAsync):
        session_id = None
        for _ in range(10):
            async with pool.checkout() as session:
                if session_id is None:
                    session_id = session._state.session_id
                assert pool._current_size == 1
                assert session_id == session._state.session_id

    @pytest.mark.asyncio
    async def test_pool_recreates_bad_sessions(self, pool: QuerySessionPoolAsync):
        async with pool.checkout() as session:
            session_id = session._state.session_id
            await session.delete()

        async with pool.checkout() as session:
            assert session_id != session._state.session_id
            assert pool._current_size == 1

    @pytest.mark.asyncio
    async def test_acquire_from_closed_pool_raises(self, pool: QuerySessionPoolAsync):
        await pool.stop()
        with pytest.raises(RuntimeError):
            await pool.acquire()

    @pytest.mark.asyncio
    async def test_acquire_with_timeout_from_closed_pool_raises(self, pool: QuerySessionPoolAsync):
        await pool.stop()
        with pytest.raises(RuntimeError):
            await pool.acquire_wih_timeout(timeout=0.5)

    @pytest.mark.asyncio
    async def test_no_session_leak(self, driver, docker_project):
        pool = ydb.aio.QuerySessionPoolAsync(driver, 1)
        docker_project.stop()
        try:
            await pool.acquire_wih_timeout(timeout=0.5)
        except ydb.Error:
            pass
        assert pool._current_size == 0

        docker_project.start()
        await pool.stop()
