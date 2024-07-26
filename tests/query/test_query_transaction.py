import pytest

from ydb.query.transaction import BaseQueryTxContext
from ydb.query.transaction import QueryTxStateEnum


class TestQueryTransaction:
    def test_tx_begin(self, tx: BaseQueryTxContext):
        assert tx.tx_id is None

        tx.begin()
        assert tx.tx_id is not None

    def test_tx_allow_double_commit(self, tx: BaseQueryTxContext):
        tx.begin()
        tx.commit()
        tx.commit()

    def test_tx_allow_double_rollback(self, tx: BaseQueryTxContext):
        tx.begin()
        tx.rollback()
        tx.rollback()

    def test_tx_commit_before_begin(self, tx: BaseQueryTxContext):
        tx.commit()
        assert tx._tx_state._state == QueryTxStateEnum.COMMITTED

    def test_tx_rollback_before_begin(self, tx: BaseQueryTxContext):
        tx.rollback()
        assert tx._tx_state._state == QueryTxStateEnum.ROLLBACKED

    def test_tx_first_execute_begins_tx(self, tx: BaseQueryTxContext):
        tx.execute("select 1;")
        tx.commit()

    def test_interactive_tx_commit(self, tx: BaseQueryTxContext):
        tx.execute("select 1;", commit_tx=True)
        with pytest.raises(RuntimeError):
            tx.execute("select 1;")

    def test_tx_execute_raises_after_commit(self, tx: BaseQueryTxContext):
        tx.begin()
        tx.commit()
        with pytest.raises(RuntimeError):
            tx.execute("select 1;")

    def test_tx_execute_raises_after_rollback(self, tx: BaseQueryTxContext):
        tx.begin()
        tx.rollback()
        with pytest.raises(RuntimeError):
            tx.execute("select 1;")

    def test_context_manager_rollbacks_tx(self, tx: BaseQueryTxContext):
        with tx:
            tx.begin()

        assert tx._tx_state._state == QueryTxStateEnum.ROLLBACKED

    def test_context_manager_normal_flow(self, tx: BaseQueryTxContext):
        with tx:
            tx.begin()
            tx.execute("select 1;")
            tx.commit()

        assert tx._tx_state._state == QueryTxStateEnum.COMMITTED

    def test_context_manager_does_not_hide_exceptions(self, tx: BaseQueryTxContext):
        class CustomException(Exception):
            pass

        with pytest.raises(CustomException):
            with tx:
                raise CustomException()

    def test_execute_as_context_manager(self, tx: BaseQueryTxContext):
        tx.begin()

        with tx.execute("select 1;") as results:
            res = [result_set for result_set in results]

        assert len(res) == 1
