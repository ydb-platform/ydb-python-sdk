import pytest
from unittest import mock

from ydb.aio.query.transaction import QueryTxContext
from ydb.query.transaction import QueryTxStateEnum
from ydb.query.base import TxListenerAsyncIO


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


class TestQueryTransactionListeners:
    class FakeListener(TxListenerAsyncIO):
        def __init__(self):
            self._call_stack = []

        async def _on_before_commit(self):
            self._call_stack.append("before_commit")

        async def _on_after_commit(self, exc):
            if exc is not None:
                self._call_stack.append("after_commit_exc")
                return
            self._call_stack.append("after_commit")

        async def _on_before_rollback(self):
            self._call_stack.append("before_rollback")

        async def _on_after_rollback(self, exc):
            if exc is not None:
                self._call_stack.append("after_rollback_exc")
                return
            self._call_stack.append("after_rollback")

        @property
        def call_stack(self):
            return self._call_stack

    @pytest.mark.asyncio
    async def test_tx_commit_normal(self, tx: QueryTxContext):
        listener = TestQueryTransactionListeners.FakeListener()
        tx._add_listener(listener)
        await tx.begin()
        await tx.commit()

        assert listener.call_stack == ["before_commit", "after_commit"]

    @pytest.mark.asyncio
    async def test_tx_commit_exc(self, tx: QueryTxContext):
        listener = TestQueryTransactionListeners.FakeListener()
        tx._add_listener(listener)
        await tx.begin()
        with mock.patch.object(tx, "_commit_call", side_effect=BaseException("commit failed")):
            with pytest.raises(BaseException):
                await tx.commit()

        assert listener.call_stack == ["before_commit", "after_commit_exc"]

    @pytest.mark.asyncio
    async def test_tx_rollback_normal(self, tx: QueryTxContext):
        listener = TestQueryTransactionListeners.FakeListener()
        tx._add_listener(listener)
        await tx.begin()
        await tx.rollback()

        assert listener.call_stack == ["before_rollback", "after_rollback"]

    @pytest.mark.asyncio
    async def test_tx_rollback_exc(self, tx: QueryTxContext):
        listener = TestQueryTransactionListeners.FakeListener()
        tx._add_listener(listener)
        await tx.begin()
        with mock.patch.object(tx, "_rollback_call", side_effect=BaseException("commit failed")):
            with pytest.raises(BaseException):
                await tx.rollback()

        assert listener.call_stack == ["before_rollback", "after_rollback_exc"]
