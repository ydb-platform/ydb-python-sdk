import pytest

def _check_session_state_empty(session):
    assert session._state.session_id == None
    assert session._state.node_id == None
    assert session._state.attached == False

def _check_session_state_full(session):
    assert session._state.session_id != None
    assert session._state.node_id != None
    assert session._state.attached == True

class TestQuerySession:
    def test_session_normal_lifecycle(self, session):
        _check_session_state_empty(session)

        session.create()
        _check_session_state_full(session)

        session.delete()
        _check_session_state_empty(session)

    def test_second_create_do_nothing(self, session):
        session.create()
        _check_session_state_full(session)

        session_id_before = session._state.session_id
        node_id_before = session._state.node_id

        session.create()
        _check_session_state_full(session)

        assert session._state.session_id == session_id_before
        assert session._state.node_id == node_id_before

    def test_second_delete_do_nothing(self, session):
        session.create()

        session.delete()
        session.delete()

    def test_delete_before_create_not_possible(self, session):
        with pytest.raises(RuntimeError):
            session.delete()

    def test_create_after_delete_not_possible(self, session):
        session.create()
        session.delete()
        with pytest.raises(RuntimeError):
            session.create()

    def test_transaction_before_create_raises(self, session):
        with pytest.raises(RuntimeError):
            session.transaction()

    def test_transaction_after_delete_raises(self, session):
        session.create()

        session.delete()

        with pytest.raises(RuntimeError):
            session.transaction()

    def test_transaction_after_create_not_raises(self, session):
        session.create()
        session.transaction()

    def test_execute_before_create_raises(self, session):
        with pytest.raises(RuntimeError):
            session.execute("select 1;")

    def test_execute_after_delete_raises(self, session):
        session.create()
        session.delete()
        with pytest.raises(RuntimeError):
            session.execute("select 1;")

    def test_basic_execute(self, session):
        session.create()
        it = session.execute("select 1;")
        result_sets = [result_set for result_set in it]

        assert len(result_sets) == 1
        assert len(result_sets[0].rows) == 1
        assert len(result_sets[0].columns) == 1
        assert list(result_sets[0].rows[0].values()) == [1]