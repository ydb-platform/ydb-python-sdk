import pytest

from ydb.query.transaction import QueryTxStateEnum

class TestQueryTransaction:
    def test_tx_begin(self, tx):
        assert tx.tx_id is None

        tx.begin()
        assert tx.tx_id is not None

    def test_tx_allow_double_commit(self, tx):
        tx.begin()
        tx.commit()
        tx.commit()

    def test_tx_allow_double_rollback(self, tx):
        tx.begin()
        tx.rollback()
        tx.rollback()

    def test_tx_commit_raises_before_begin(self, tx):
        with pytest.raises(RuntimeError):
            tx.commit()

    def test_tx_rollback_raises_before_begin(self, tx):
        with pytest.raises(RuntimeError):
            tx.rollback()

    def test_tx_first_execute_begins_tx(self, tx):
        tx.execute("select 1;")
        tx.commit()

    def test_interactive_tx_commit(self, tx):
        tx.execute("select 1;", commit_tx=True)
        with pytest.raises(RuntimeError):
            tx.execute("select 1;")

    def test_tx_execute_raises_after_commit(self, tx):
        tx.begin()
        tx.commit()
        with pytest.raises(RuntimeError):
            tx.execute("select 1;")

    def test_tx_execute_raises_after_rollback(self, tx):
        tx.begin()
        tx.rollback()
        with pytest.raises(RuntimeError):
            tx.execute("select 1;")

    def test_context_manager_rollbacks_tx(self, tx):
        with tx:
            tx.begin()

        assert tx._tx_state._state == QueryTxStateEnum.ROLLBACKED

    def test_context_manager_normal_flow(self, tx):
        with tx:
            tx.begin()
            tx.execute("select 1;")
            tx.commit()

        assert tx._tx_state._state == QueryTxStateEnum.COMMITTED

    def test_context_manager_does_not_hide_exceptions(self, tx):
        with pytest.raises(RuntimeError):
            with tx:
                tx.commit()
