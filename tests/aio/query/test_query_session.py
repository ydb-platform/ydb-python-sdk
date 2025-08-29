import json

import pytest

import ydb
from ydb import QueryExplainResultFormat
from ydb.aio.query.session import QuerySession


def _check_session_state_empty(session: QuerySession):
    assert session._state.session_id is None
    assert session._state.node_id is None
    assert not session._state.attached


def _check_session_state_full(session: QuerySession):
    assert session._state.session_id is not None
    assert session._state.node_id is not None
    assert session._state.attached


class TestAsyncQuerySession:
    @pytest.mark.asyncio
    async def test_session_normal_lifecycle(self, session: QuerySession):
        _check_session_state_empty(session)

        await session.create()
        _check_session_state_full(session)

        await session.delete()
        _check_session_state_empty(session)

    @pytest.mark.asyncio
    async def test_second_create_do_nothing(self, session: QuerySession):
        await session.create()
        _check_session_state_full(session)

        session_id_before = session._state.session_id
        node_id_before = session._state.node_id

        await session.create()
        _check_session_state_full(session)

        assert session._state.session_id == session_id_before
        assert session._state.node_id == node_id_before

    @pytest.mark.asyncio
    async def test_second_delete_do_nothing(self, session: QuerySession):
        await session.create()

        await session.delete()
        await session.delete()

    @pytest.mark.asyncio
    async def test_delete_before_create_not_possible(self, session: QuerySession):
        with pytest.raises(RuntimeError):
            await session.delete()

    @pytest.mark.asyncio
    async def test_create_after_delete_not_possible(self, session: QuerySession):
        await session.create()
        await session.delete()
        with pytest.raises(RuntimeError):
            await session.create()

    def test_transaction_before_create_raises(self, session: QuerySession):
        with pytest.raises(RuntimeError):
            session.transaction()

    @pytest.mark.asyncio
    async def test_transaction_after_delete_raises(self, session: QuerySession):
        await session.create()

        await session.delete()

        with pytest.raises(RuntimeError):
            session.transaction()

    @pytest.mark.asyncio
    async def test_transaction_after_create_not_raises(self, session: QuerySession):
        await session.create()
        session.transaction()

    @pytest.mark.asyncio
    async def test_execute_before_create_raises(self, session: QuerySession):
        with pytest.raises(RuntimeError):
            await session.execute("select 1;")

    @pytest.mark.asyncio
    async def test_execute_after_delete_raises(self, session: QuerySession):
        await session.create()
        await session.delete()
        with pytest.raises(RuntimeError):
            await session.execute("select 1;")

    @pytest.mark.asyncio
    async def test_basic_execute(self, session: QuerySession):
        await session.create()
        it = await session.execute("select 1;")
        result_sets = [result_set async for result_set in it]

        assert len(result_sets) == 1
        assert len(result_sets[0].rows) == 1
        assert len(result_sets[0].columns) == 1
        assert list(result_sets[0].rows[0].values()) == [1]

    @pytest.mark.asyncio
    async def test_two_results(self, session: QuerySession):
        await session.create()
        res = []
        counter = 0

        async with await session.execute("select 1; select 2") as results:
            async for result_set in results:
                counter += 1
                if len(result_set.rows) > 0:
                    res.append(list(result_set.rows[0].values()))

        assert res == [[1], [2]]
        assert counter == 2

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("ydb_terminates_streams_with_unavailable")
    async def test_terminated_stream_raises_ydb_error(self, session: QuerySession):
        await session.create()

        with pytest.raises(ydb.Unavailable):
            async with await session.execute("select 1") as results:
                async for _ in results:
                    pass

    @pytest.mark.asyncio
    async def test_explain(self, pool: ydb.aio.query.QuerySessionPool):
        await pool.execute_with_retries("DROP TABLE IF EXISTS test_explain")
        await pool.execute_with_retries("CREATE TABLE test_explain (id Int64, PRIMARY KEY (id))")
        try:
            plan_fullscan = ""
            plan_lookup = ""

            async def callee(session: QuerySession):
                nonlocal plan_fullscan, plan_lookup

                plan = await session.explain("SELECT * FROM test_explain", result_format=QueryExplainResultFormat.STR)
                isinstance(plan, str)
                assert "FullScan" in plan

                plan_fullscan = await session.explain(
                    "SELECT * FROM test_explain", result_format=QueryExplainResultFormat.DICT
                )
                plan_lookup = await session.explain(
                    "SELECT * FROM test_explain WHERE id = $id",
                    {"$id": 1},
                    result_format=QueryExplainResultFormat.DICT,
                )

            await pool.retry_operation_async(callee)

            plan_fulltext_string = json.dumps(plan_fullscan)
            assert "FullScan" in plan_fulltext_string

            plan_lookup_string = json.dumps(plan_lookup)
            assert "Lookup" in plan_lookup_string
        finally:
            await pool.execute_with_retries("DROP TABLE test_explain")
