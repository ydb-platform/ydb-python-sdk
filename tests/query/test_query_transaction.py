import pytest

import ydb
from ydb.query.base import QueryStatsMode
from ydb.query.transaction import QueryTxContext, QueryTxStateEnum


class TestQueryTransaction:
    def test_tx_begin(self, tx: QueryTxContext):
        assert tx.tx_id is None

        tx.begin()
        assert tx.tx_id is not None

    def test_tx_allow_double_commit(self, tx: QueryTxContext):
        tx.begin()
        tx.commit()
        tx.commit()

    def test_tx_allow_double_rollback(self, tx: QueryTxContext):
        tx.begin()
        tx.rollback()
        tx.rollback()

    def test_tx_commit_before_begin(self, tx: QueryTxContext):
        tx.commit()
        assert tx._tx_state._state == QueryTxStateEnum.COMMITTED

    def test_tx_rollback_before_begin(self, tx: QueryTxContext):
        tx.rollback()
        assert tx._tx_state._state == QueryTxStateEnum.ROLLBACKED

    def test_tx_first_execute_begins_tx(self, tx: QueryTxContext):
        tx.execute("select 1;")
        tx.commit()

    def test_interactive_tx_commit(self, tx: QueryTxContext):
        tx.execute("select 1;", commit_tx=True)
        with pytest.raises(RuntimeError):
            tx.execute("select 1;")

    def test_tx_execute_raises_after_commit(self, tx: QueryTxContext):
        tx.begin()
        tx.commit()
        with pytest.raises(RuntimeError):
            tx.execute("select 1;")

    def test_tx_execute_raises_after_rollback(self, tx: QueryTxContext):
        tx.begin()
        tx.rollback()
        with pytest.raises(RuntimeError):
            tx.execute("select 1;")

    def test_context_manager_rollbacks_tx(self, tx: QueryTxContext):
        with tx:
            tx.begin()

        assert tx._tx_state._state == QueryTxStateEnum.ROLLBACKED

    def test_context_manager_normal_flow(self, tx: QueryTxContext):
        with tx:
            tx.begin()
            tx.execute("select 1;")
            tx.commit()

        assert tx._tx_state._state == QueryTxStateEnum.COMMITTED

    def test_context_manager_does_not_hide_exceptions(self, tx: QueryTxContext):
        class CustomException(Exception):
            pass

        with pytest.raises(CustomException):
            with tx:
                raise CustomException()

    def test_execute_as_context_manager(self, tx: QueryTxContext):
        tx.begin()

        with tx.execute("select 1;") as results:
            res = [result_set for result_set in results]

        assert len(res) == 1

    def test_execute_two_results(self, tx: QueryTxContext):
        tx.begin()
        counter = 0
        res = []

        with tx.execute("select 1; select 2") as results:
            for result_set in results:
                counter += 1
                res.append(list(result_set.rows[0].values()))

        assert res == [[1], [2]]
        assert counter == 2

    def test_tx_identity_before_begin_raises(self, tx: QueryTxContext):
        with pytest.raises(RuntimeError):
            tx._tx_identity()

    def test_tx_identity_after_begin_works(self, tx: QueryTxContext):
        tx.begin()

        identity = tx._tx_identity()

        assert identity.tx_id == tx.tx_id
        assert identity.session_id == tx.session_id

    @pytest.mark.parametrize(
        "stats_mode",
        [
            None,
            QueryStatsMode.UNSPECIFIED,
            QueryStatsMode.NONE,
            QueryStatsMode.BASIC,
            QueryStatsMode.FULL,
            QueryStatsMode.PROFILE,
        ],
    )
    def test_stats_mode(self, tx: QueryTxContext, stats_mode: QueryStatsMode):
        for _ in tx.execute("SELECT 1; SELECT 2; SELECT 3;", commit_tx=True, stats_mode=stats_mode):
            pass

        stats = tx.last_query_stats

        if stats_mode in [None, QueryStatsMode.NONE, QueryStatsMode.UNSPECIFIED]:
            assert stats is None
            return

        assert stats is not None
        assert len(stats.query_phases) > 0

        if stats_mode != QueryStatsMode.BASIC:
            assert len(stats.query_plan) > 0
        else:
            assert stats.query_plan == ""

    def test_rollback_after_tli_aborted_is_safe(self, pool, table_path: str):
        # Given: a row in a table
        table_ref = f"`{table_path}`"
        pool.execute_with_retries(f"UPSERT INTO {table_ref} (id, i64Val) VALUES (1, 0);")

        # When: two concurrent transactions try to modify this row.
        with pool.checkout() as session1, pool.checkout() as session2:
            tx1 = session1.transaction()
            tx2 = session2.transaction()

            with tx1.execute(f"SELECT i64Val FROM {table_ref} WHERE id = 1;") as _:
                pass

            with tx2.execute(f"UPSERT INTO {table_ref} (id, i64Val) VALUES (1, 1);", commit_tx=True) as _:
                pass

            with tx1.execute(f"UPSERT INTO {table_ref} (id, i64Val) VALUES (1, 2);") as _:
                pass
            with pytest.raises(ydb.Aborted):
                tx1.commit()  # receive TLI here

            # Then: rollback (as a handling of Aborted exception) must be successful.
            tx1.rollback()
