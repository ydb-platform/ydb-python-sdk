import json

import pytest
import threading
import time
from concurrent.futures import _base as b
from unittest import mock

from ydb import QuerySessionPool
from ydb.query.base import QueryStatsMode, QueryExplainResultFormat
from ydb.query.session import QuerySession
from ydb.connection import EndpointKey


def _check_session_not_ready(session: QuerySession):
    assert not session.is_active


def _check_session_ready(session: QuerySession):
    assert session.session_id is not None
    assert session.node_id is not None
    assert session.is_active
    assert not session.is_closed


class TestQuerySession:
    def test_session_normal_lifecycle(self, session: QuerySession):
        _check_session_not_ready(session)

        session.create()
        _check_session_ready(session)

        session.delete()
        assert session.is_closed

    def test_second_create_do_nothing(self, session: QuerySession):
        session.create()
        _check_session_ready(session)

        session_id_before = session.session_id
        node_id_before = session.node_id

        session.create()
        _check_session_ready(session)

        assert session.session_id == session_id_before
        assert session.node_id == node_id_before

    def test_second_delete_do_nothing(self, session: QuerySession):
        session.create()

        session.delete()
        session.delete()

    def test_delete_before_create_is_noop(self, session: QuerySession):
        session.delete()
        assert session.is_closed

    def test_create_after_delete_not_possible(self, session: QuerySession):
        session.create()
        session.delete()
        with pytest.raises(RuntimeError):
            session.create()

    def test_transaction_before_create_raises(self, session: QuerySession):
        with pytest.raises(RuntimeError):
            session.transaction()

    def test_transaction_after_delete_raises(self, session: QuerySession):
        session.create()

        session.delete()

        with pytest.raises(RuntimeError):
            session.transaction()

    def test_transaction_after_create_not_raises(self, session: QuerySession):
        session.create()
        session.transaction()

    def test_execute_before_create_raises(self, session: QuerySession):
        with pytest.raises(RuntimeError):
            session.execute("select 1;")

    def test_execute_after_delete_raises(self, session: QuerySession):
        session.create()
        session.delete()
        with pytest.raises(RuntimeError):
            session.execute("select 1;")

    def test_basic_execute(self, session: QuerySession):
        session.create()
        it = session.execute("select 1;")
        result_sets = [result_set for result_set in it]

        assert len(result_sets) == 1
        assert len(result_sets[0].rows) == 1
        assert len(result_sets[0].columns) == 1
        assert list(result_sets[0].rows[0].values()) == [1]

    def test_two_results(self, session: QuerySession):
        session.create()
        res = []
        counter = 0

        with session.execute("select 1; select 2") as results:
            for result_set in results:
                counter += 1
                if len(result_set.rows) > 0:
                    res.append(list(result_set.rows[0].values()))

        assert res == [[1], [2]]
        assert counter == 2

    def test_thread_leaks(self, session: QuerySession):
        session.create()
        thread_names = [t.name for t in threading.enumerate()]
        assert "first response attach stream thread" not in thread_names
        assert "attach stream thread" in thread_names

    def test_first_resp_timeout(self, session: QuerySession):
        class FakeResponse:
            """Fake response that passes through ServerStatus.from_proto()"""

            status = 0  # SUCCESS
            issues = []

        class FakeStream:
            def __init__(self):
                self.cancel_called = False
                self._cancelled = threading.Event()

            def __iter__(self):
                return self

            def __next__(self):
                # Wait until cancelled or timeout
                self._cancelled.wait(timeout=10)
                # Return fake response instead of raising - avoids thread exception warning
                return FakeResponse()

            def cancel(self):
                self.cancel_called = True
                self._cancelled.set()

        fake_stream = FakeStream()

        session._attach_call = mock.MagicMock(return_value=fake_stream)
        assert session._attach_call() == fake_stream

        session._create_call()
        with pytest.raises(b.TimeoutError):
            session._attach(0.1)

        assert fake_stream.cancel_called

        # Give background thread time to finish
        time.sleep(0.1)

        thread_names = [t.name for t in threading.enumerate()]
        assert "first response attach stream thread" not in thread_names
        assert "attach stream thread" not in thread_names

        assert session.is_closed

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
    def test_stats_mode(self, session: QuerySession, stats_mode: QueryStatsMode):
        session.create()

        for _ in session.execute("SELECT 1; SELECT 2; SELECT 3;", stats_mode=stats_mode):
            pass

        stats = session.last_query_stats

        if stats_mode in [None, QueryStatsMode.NONE, QueryStatsMode.UNSPECIFIED]:
            assert stats is None
            return

        assert stats is not None
        assert len(stats.query_phases) > 0

        if stats_mode != QueryStatsMode.BASIC:
            assert len(stats.query_plan) > 0
        else:
            assert stats.query_plan == ""

    def test_explain(self, pool: QuerySessionPool):
        pool.execute_with_retries("DROP TABLE IF EXISTS test_explain")
        pool.execute_with_retries("CREATE TABLE test_explain (id Int64, PRIMARY KEY (id))")
        try:
            plan_fullscan = ""
            plan_lookup = ""

            def callee(session: QuerySession):
                nonlocal plan_fullscan, plan_lookup

                plan = session.explain("SELECT * FROM test_explain", result_format=QueryExplainResultFormat.STR)
                isinstance(plan, str)
                assert "FullScan" in plan

                plan_fullscan = session.explain(
                    "SELECT * FROM test_explain", result_format=QueryExplainResultFormat.DICT
                )

                plan_lookup = session.explain(
                    "SELECT * FROM test_explain WHERE id = $id",
                    {"$id": 1},
                    result_format=QueryExplainResultFormat.DICT,
                )

            pool.retry_operation_sync(callee)

            plan_fulltext_string = json.dumps(plan_fullscan)
            assert "FullScan" in plan_fulltext_string

            plan_lookup_string = json.dumps(plan_lookup)
            assert "Lookup" in plan_lookup_string
        finally:
            pool.execute_with_retries("DROP TABLE test_explain")


class TestQuerySessionPreferredEndpoint:
    def test_endpoint_key_is_none_before_create(self, session: QuerySession):
        assert session._endpoint_key is None

    def test_endpoint_key_is_set_after_create(self, session: QuerySession):
        session.create()
        assert session.node_id is not None
        assert session._endpoint_key is not None
        assert isinstance(session._endpoint_key, EndpointKey)
        assert session._endpoint_key.node_id == session.node_id

    def test_session_uses_preferred_endpoint_on_execute(self, session: QuerySession):
        session.create()
        original_driver_call = session._driver

        calls = []

        def mock_driver_call(*args, **kwargs):
            calls.append(kwargs)
            return original_driver_call(*args, **kwargs)

        session._driver = mock_driver_call

        with session.execute("select 1;") as results:
            for _ in results:
                pass

        assert len(calls) > 0
        assert "preferred_endpoint" in calls[0]
        assert calls[0]["preferred_endpoint"] is not None
        assert calls[0]["preferred_endpoint"].node_id == session.node_id

    def test_session_uses_preferred_endpoint_on_delete(self, session: QuerySession):
        session.create()
        original_driver_call = session._driver

        calls = []

        def mock_driver_call(*args, **kwargs):
            calls.append(kwargs)
            return original_driver_call(*args, **kwargs)

        session._driver = mock_driver_call

        session.delete()

        assert len(calls) > 0
        assert "preferred_endpoint" in calls[0]
        assert calls[0]["preferred_endpoint"] is not None
        assert calls[0]["preferred_endpoint"].node_id == session.node_id

    def test_transaction_uses_preferred_endpoint(self, session: QuerySession):
        session.create()
        original_driver_call = session._driver

        calls = []

        def mock_driver_call(*args, **kwargs):
            calls.append(kwargs)
            return original_driver_call(*args, **kwargs)

        session._driver = mock_driver_call

        with session.transaction() as tx:
            with tx.execute("select 1;") as results:
                for _ in results:
                    pass

        execute_calls = [c for c in calls if "preferred_endpoint" in c]
        assert len(execute_calls) > 0
        for call in execute_calls:
            assert call["preferred_endpoint"] is not None
            assert call["preferred_endpoint"].node_id == session.node_id
