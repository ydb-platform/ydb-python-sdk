import pytest

from ydb.query.session import QuerySession


def _check_session_state_empty(session: QuerySession):
    assert session._state.session_id is None
    assert session._state.node_id is None
    assert not session._state.attached


def _check_session_state_full(session: QuerySession):
    assert session._state.session_id is not None
    assert session._state.node_id is not None
    assert session._state.attached


class TestQuerySession:
    def test_session_normal_lifecycle(self, session: QuerySession):
        _check_session_state_empty(session)

        session.create()
        _check_session_state_full(session)

        session.delete()
        _check_session_state_empty(session)

    def test_second_create_do_nothing(self, session: QuerySession):
        session.create()
        _check_session_state_full(session)

        session_id_before = session._state.session_id
        node_id_before = session._state.node_id

        session.create()
        _check_session_state_full(session)

        assert session._state.session_id == session_id_before
        assert session._state.node_id == node_id_before

    def test_second_delete_do_nothing(self, session: QuerySession):
        session.create()

        session.delete()
        session.delete()

    def test_delete_before_create_not_possible(self, session: QuerySession):
        with pytest.raises(RuntimeError):
            session.delete()

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

        with session.execute("select 1; select 2") as results:
            for result_set in results:
                if len(result_set.rows) > 0:
                    res.append(list(result_set.rows[0].values()))

        assert res == [[1], [2]]
