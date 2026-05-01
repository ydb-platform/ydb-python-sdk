import asyncio
from unittest import mock

import pytest

import ydb
from ydb.aio.query.transaction import QueryTxContext
from ydb.query.transaction import QueryTxStateEnum


class TestAsyncQueryTransaction:
    @pytest.mark.asyncio
    async def test_tx_begin(self, tx: QueryTxContext):
        assert tx.tx_id is None

        await tx.begin()
        assert tx.tx_id is not None

    @pytest.mark.asyncio
    async def test_tx_allow_double_commit(self, tx: QueryTxContext):
        await tx.begin()
        await tx.commit()
        await tx.commit()

    @pytest.mark.asyncio
    async def test_tx_allow_double_rollback(self, tx: QueryTxContext):
        await tx.begin()
        await tx.rollback()
        await tx.rollback()

    @pytest.mark.asyncio
    async def test_tx_commit_before_begin(self, tx: QueryTxContext):
        await tx.commit()
        assert tx._tx_state._state == QueryTxStateEnum.COMMITTED

    @pytest.mark.asyncio
    async def test_tx_rollback_before_begin(self, tx: QueryTxContext):
        await tx.rollback()
        assert tx._tx_state._state == QueryTxStateEnum.ROLLBACKED

    @pytest.mark.asyncio
    async def test_tx_first_execute_begins_tx(self, tx: QueryTxContext):
        await tx.execute("select 1;")
        await tx.commit()

    @pytest.mark.asyncio
    async def test_interactive_tx_commit(self, tx: QueryTxContext):
        await tx.execute("select 1;", commit_tx=True)
        with pytest.raises(RuntimeError):
            await tx.execute("select 1;")

    @pytest.mark.asyncio
    async def test_tx_execute_raises_after_commit(self, tx: QueryTxContext):
        await tx.begin()
        await tx.commit()
        with pytest.raises(RuntimeError):
            await tx.execute("select 1;")

    @pytest.mark.asyncio
    async def test_tx_execute_raises_after_rollback(self, tx: QueryTxContext):
        await tx.begin()
        await tx.rollback()
        with pytest.raises(RuntimeError):
            await tx.execute("select 1;")

    @pytest.mark.asyncio
    async def test_context_manager_rollbacks_tx(self, tx: QueryTxContext):
        async with tx:
            await tx.begin()

        assert tx._tx_state._state == QueryTxStateEnum.ROLLBACKED

    @pytest.mark.asyncio
    async def test_context_manager_normal_flow(self, tx: QueryTxContext):
        async with tx:
            await tx.begin()
            await tx.execute("select 1;")
            await tx.commit()

        assert tx._tx_state._state == QueryTxStateEnum.COMMITTED

    @pytest.mark.asyncio
    async def test_context_manager_does_not_hide_exceptions(self, tx: QueryTxContext):
        class CustomException(Exception):
            pass

        with pytest.raises(CustomException):
            async with tx:
                raise CustomException()

    @pytest.mark.asyncio
    async def test_execute_as_context_manager(self, tx: QueryTxContext):
        await tx.begin()

        async with await tx.execute("select 1;") as results:
            res = [result_set async for result_set in results]

        assert len(res) == 1

    @pytest.mark.asyncio
    async def test_execute_two_results(self, tx: QueryTxContext):
        await tx.begin()
        counter = 0
        res = []

        async with await tx.execute("select 1; select 2") as results:
            async for result_set in results:
                counter += 1
                if len(result_set.rows) > 0:
                    res.append(list(result_set.rows[0].values()))

        assert res == [[1], [2]]
        assert counter == 2

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("ydb_terminates_streams_with_unavailable")
    async def test_terminated_stream_raises_ydb_error(self, tx: QueryTxContext):
        await tx.begin()

        with pytest.raises(ydb.Unavailable):
            async with await tx.execute("select 1") as results:
                async for _ in results:
                    pass

    @pytest.mark.asyncio
    async def test_cancelled_rollback_in_aexit_invalidates_session(self, session):
        await session.create()
        tx = session.transaction()
        await tx.begin()

        async def slow_rollback_call(settings=None):
            await asyncio.sleep(10)

        with mock.patch.object(tx, "_rollback_call", slow_rollback_call):
            task = asyncio.ensure_future(tx.__aexit__(None, None, None))
            await asyncio.sleep(0)
            task.cancel()
            await task  # completes normally; CancelledError is swallowed to preserve original exception

        assert not session.is_active

    @pytest.mark.asyncio
    async def test_cancelled_rollback_in_aexit_session_not_reused(self, pool):
        async with pool.checkout() as session:
            session_id_before = session.session_id
            tx = session.transaction()
            await tx.begin()

            async def slow_rollback_call(settings=None):
                await asyncio.sleep(10)

            with mock.patch.object(tx, "_rollback_call", slow_rollback_call):
                task = asyncio.ensure_future(tx.__aexit__(None, None, None))
                await asyncio.sleep(0)
                task.cancel()
                await task

        async with pool.checkout() as session:
            assert session.session_id != session_id_before

    @pytest.mark.asyncio
    async def test_successful_stream_keeps_session_active(self, tx: QueryTxContext):
        # Guard for issue #812 fix: the widened _next handler (BaseException
        # instead of Exception) must still let StopAsyncIteration terminate
        # the stream without feeding it to _on_execute_stream_error — which
        # would then invalidate the session on every normal SELECT.
        await tx.begin()

        async with await tx.execute("SELECT 1") as results:
            async for _ in results:
                pass

        assert tx.session.is_active

    @pytest.mark.asyncio
    async def test_query_level_error_keeps_session_active(self, pool):
        # Guard for issue #812 fix: _on_execute_stream_error now invalidates
        # the session on a broader set of errors (CancelledError, SessionBusy,
        # BadSession, ConnectionError, Cancelled, DeadlineExceed). Query-level
        # errors like syntax errors must NOT invalidate — the session is fine,
        # only the statement is bad.
        async with pool.checkout() as session:
            session_id_before = session.session_id
            with pytest.raises(ydb.issues.Error):
                async with await session.execute("this is not valid SQL") as results:
                    async for _ in results:
                        pass
            assert session.is_active
            # And the session must remain reusable for the next statement.
            async with await session.execute("SELECT 1") as results:
                async for _ in results:
                    pass
            assert session.session_id == session_id_before
            assert session.is_active

    @pytest.mark.asyncio
    async def test_cancelled_error_during_stream_invalidates_session(self, tx: QueryTxContext):
        # Regression for issue #812: once a gRPC aio call is cancelled, every
        # subsequent read on it raises asyncio.CancelledError. Because
        # CancelledError inherits from BaseException, the old _next handler
        # (which caught Exception) never invoked _on_error, and the session
        # was returned to the pool in a bad state. Verify the hook now runs
        # on CancelledError and invalidates the session.
        await tx.begin()

        from ydb.aio._utilities import AsyncResponseIterator

        results = await tx.execute("SELECT 1")

        async def raising_next(self):
            raise asyncio.CancelledError("simulated grpc.aio call cancellation")

        with mock.patch.object(AsyncResponseIterator, "_next", raising_next):
            with pytest.raises(asyncio.CancelledError):
                async for _ in results:
                    pass

        assert not tx.session.is_active

    @pytest.mark.asyncio
    async def test_session_busy_during_stream_invalidates_session(self, tx: QueryTxContext):
        # Regression for issue #812, case 2: SessionBusy from the stream means
        # the server still considers the previous query in flight; continuing
        # to use this session poisons the next caller. Must invalidate.
        await tx.begin()

        from ydb.aio._utilities import AsyncResponseIterator

        results = await tx.execute("SELECT 1")

        async def raising_next(self):
            raise ydb.issues.SessionBusy("simulated SessionBusy from stream")

        with mock.patch.object(AsyncResponseIterator, "_next", raising_next):
            with pytest.raises(ydb.issues.SessionBusy):
                async for _ in results:
                    pass

        assert not tx.session.is_active

    @pytest.mark.asyncio
    async def test_cancelled_stream_in_pool_does_not_poison_next_caller(self, pool):
        # Regression for issue #812: a single mis-timed cancel during
        # tx.execute(...) iteration should not leave the session in a state
        # where the next unrelated caller sees SessionBusy or otherwise reuses
        # a session the server considers busy.
        from ydb.aio._utilities import AsyncResponseIterator

        victim_sid = None

        async def victim(tx):
            nonlocal victim_sid
            victim_sid = tx.session.session_id
            results = await tx.execute("SELECT 1")

            orig_next = AsyncResponseIterator._next

            async def raising_next(self):
                raise asyncio.CancelledError("simulated grpc.aio call cancellation")

            with mock.patch.object(AsyncResponseIterator, "_next", raising_next):
                async for _ in results:
                    pass
            # Restore so later operations in this session (if any) would work.
            AsyncResponseIterator._next = orig_next

        with pytest.raises(asyncio.CancelledError):
            await pool.retry_tx_async(victim)

        async with pool.checkout() as session:
            assert session.session_id != victim_sid

    @pytest.mark.asyncio
    async def test_rollback_after_tli_aborted_is_safe(self, pool, table_path: str):
        # Given: a row in a table
        table_ref = f"`{table_path}`"
        await pool.execute_with_retries(f"UPSERT INTO {table_ref} (id, i64Val) VALUES (1, 0);")

        # When: two concurrent transactions try to modify this row.
        async with pool.checkout() as session1, pool.checkout() as session2:
            tx1 = session1.transaction()
            tx2 = session2.transaction()

            async with await tx1.execute(f"SELECT i64Val FROM {table_ref} WHERE id = 1;") as _:
                pass

            async with await tx2.execute(f"UPSERT INTO {table_ref} (id, i64Val) VALUES (1, 1);", commit_tx=True) as _:
                pass

            async with await tx1.execute(f"UPSERT INTO {table_ref} (id, i64Val) VALUES (1, 2);") as _:
                pass
            with pytest.raises(ydb.Aborted):
                await tx1.commit()  # receive TLI here

            # Then: rollback (as a handling of Aborted exception) must be successful.
            await tx1.rollback()
