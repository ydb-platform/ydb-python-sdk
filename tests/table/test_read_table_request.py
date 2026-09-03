from ydb import _apis
from ydb.table import TableClientSettings
from ydb._session_impl import SessionState, read_table_request_factory


def _session_state():
    state = SessionState(TableClientSettings())
    state.set_id("test-session-id")
    return state


def test_read_table_request_not_null_as_optional_enabled():
    request = read_table_request_factory(
        _session_state(), "/local/table", return_not_null_data_as_optional=True
    )
    assert request.return_not_null_data_as_optional == _apis.FeatureFlag.ENABLED


def test_read_table_request_not_null_as_optional_disabled():
    request = read_table_request_factory(
        _session_state(), "/local/table", return_not_null_data_as_optional=False
    )
    assert request.return_not_null_data_as_optional == _apis.FeatureFlag.DISABLED


def test_read_table_request_not_null_as_optional_unset_by_default():
    request = read_table_request_factory(_session_state(), "/local/table")
    assert request.return_not_null_data_as_optional == _apis.FeatureFlag.STATUS_UNSPECIFIED
