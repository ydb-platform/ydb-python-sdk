import pytest

import ydb.query.session

def _check_session_state_empty(session):
    assert session._state.session_id == None
    assert session._state.node_id == None
    assert session._state.attached == False

def _check_session_state_full(session):
    assert session._state.session_id != None
    assert session._state.node_id != None
    assert session._state.attached == True

class TestQuerySession:
    def test_session_normal_lifecycle(self, driver_sync):
        session = ydb.query.session.QuerySessionSync(driver_sync)
        _check_session_state_empty(session)

        session.create()
        _check_session_state_full(session)

        session.delete()
        _check_session_state_empty(session)
