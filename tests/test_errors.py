import ydb
import pytest

from os import path


def test_scheme_error(driver_sync, database):
    session = driver_sync.table_client.session().create()
    with pytest.raises(ydb.issues.SchemeError) as exc:
        session.drop_table(path.join(database, "foobartable"))

    server_code = ydb.issues.StatusCode.SCHEME_ERROR

    assert type(exc.value) == ydb.issues.SchemeError
    assert exc.value.status == server_code
    assert f"server_code: {server_code}" in str(exc.value)
    assert "Path does not exist" in str(exc.value)
