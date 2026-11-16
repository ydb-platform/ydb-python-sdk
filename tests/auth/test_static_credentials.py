import base64
import json

import pytest
import ydb
from unittest.mock import patch, MagicMock

USERNAME = "root"
PASSWORD = "1234"


def make_login_token(expires_at):
    payload = base64.urlsafe_b64encode(json.dumps({"exp": expires_at}).encode()).decode().rstrip("=")
    return "eyJhbGciOiJSUzI1NiJ9.{}.signature".format(payload)


@pytest.mark.parametrize("lifetime", [15, 60, 12 * 60 * 60])
def test_static_credentials_use_jwt_expiration(lifetime):
    credentials = ydb.StaticCredentials(ydb.DriverConfig("localhost:2135", "/local"), USERNAME, PASSWORD)
    token = make_login_token(1000 + lifetime)
    conn = MagicMock(return_value=MagicMock(token=token))

    with patch("ydb.credentials.connection.Connection.ready_factory", return_value=conn):
        with patch("ydb.credentials.time.time", return_value=1000):
            response = credentials._make_token_request()

    assert response == {"access_token": token, "expires_in": lifetime}
    conn.close.assert_called_once_with()


def test_static_credentials_refresh_short_lived_jwt():
    credentials = ydb.StaticCredentials(ydb.DriverConfig("localhost:2135", "/local"), USERNAME, PASSWORD)
    token1 = make_login_token(1015)
    token2 = make_login_token(1017)
    conn = MagicMock(side_effect=[MagicMock(token=token1), MagicMock(token=token2)])
    background_calls = []
    credentials._tp.submit = background_calls.append

    with patch("ydb.credentials.connection.Connection.ready_factory", return_value=conn):
        with patch("ydb.credentials.time.time", return_value=1000) as clock:
            assert credentials.get_auth_token() == token1
            assert credentials.get_auth_token() == token1
            assert conn.call_count == 1

            clock.return_value = 1002
            assert credentials.get_auth_token() == token1
            assert len(background_calls) == 1
            background_calls.pop()()
            assert credentials.get_auth_token() == token2
            assert conn.call_count == 2

            clock.return_value = 1015
            assert credentials.get_auth_token() == token2
            assert conn.call_count == 2


def test_static_credentials_refresh_expired_jwt_synchronously():
    credentials = ydb.StaticCredentials(ydb.DriverConfig("localhost:2135", "/local"), USERNAME, PASSWORD)
    token1 = make_login_token(1015)
    token2 = make_login_token(1031)
    conn = MagicMock(side_effect=[MagicMock(token=token1), MagicMock(token=token2)])
    credentials._tp.submit = MagicMock()

    with patch("ydb.credentials.connection.Connection.ready_factory", return_value=conn):
        with patch("ydb.credentials.time.time", return_value=1000) as clock:
            assert credentials.get_auth_token() == token1
            clock.return_value = 1016
            assert credentials.get_auth_token() == token2
            assert conn.call_count == 2
            credentials._tp.submit.assert_not_called()


def check_driver_works(driver):
    driver.wait(timeout=15)
    pool = ydb.QuerySessionPool(driver)
    result = pool.execute_with_retries("SELECT 1 as cnt")
    assert result[0].rows[0].cnt == 1


def test_static_credentials_default(endpoint, database):
    driver_config = ydb.DriverConfig(
        endpoint,
        database,
    )
    credentials = ydb.StaticCredentials(driver_config, USERNAME, PASSWORD)

    with ydb.Driver(driver_config=driver_config, credentials=credentials) as driver:
        check_driver_works(driver)


def test_static_credentials_classmethod(endpoint, database):
    driver_config = ydb.DriverConfig(
        endpoint,
        database,
        credentials=ydb.StaticCredentials.from_user_password(USERNAME, PASSWORD),
    )

    with ydb.Driver(driver_config=driver_config) as driver:
        check_driver_works(driver)


def test_static_credentials_wrong_creds(endpoint, database):
    driver_config = ydb.DriverConfig(
        endpoint,
        database,
        credentials=ydb.StaticCredentials.from_user_password(USERNAME, PASSWORD * 2),
    )

    with pytest.raises(ydb.ConnectionFailure):
        with ydb.Driver(driver_config=driver_config) as driver:
            driver.wait(5, fail_fast=True)


def test_token_lazy_refresh():
    credentials = ydb.StaticCredentials.from_user_password(USERNAME, PASSWORD)

    credentials._tp.submit = MagicMock()

    mock_response = {"access_token": "token_v1", "expires_in": 3600}
    credentials._make_token_request = MagicMock(return_value=mock_response)

    with patch("time.time") as mock_time:
        mock_time.return_value = 1000

        token1 = credentials.token
        assert token1 == "token_v1"
        assert credentials._make_token_request.call_count == 1

        token2 = credentials.token
        assert token2 == "token_v1"
        assert credentials._make_token_request.call_count == 1

        mock_time.return_value = 1000 + 3600 - 30 + 1
        credentials._make_token_request.return_value = {"access_token": "token_v2", "expires_in": 3600}

        token3 = credentials.token
        assert token3 == "token_v2"
        assert credentials._make_token_request.call_count == 2


def test_token_double_check_locking():
    credentials = ydb.StaticCredentials.from_user_password(USERNAME, PASSWORD)
    credentials._tp.submit = MagicMock()

    call_count = 0

    def mock_make_request():
        nonlocal call_count
        call_count += 1
        return {"access_token": f"token_v{call_count}", "expires_in": 3600}

    credentials._make_token_request = mock_make_request

    with patch("time.time") as mock_time:
        mock_time.return_value = 1000

        import threading

        results = []

        def get_token():
            results.append(credentials.token)

        threads = [threading.Thread(target=get_token) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(set(results)) == 1
        assert call_count == 1


def test_token_expiration_calculation():
    credentials = ydb.StaticCredentials.from_user_password(USERNAME, PASSWORD)

    credentials._tp.submit = MagicMock()

    with patch("time.time") as mock_time:
        mock_time.return_value = 1000

        credentials._make_token_request = MagicMock(return_value={"access_token": "token", "expires_in": 3600})

        credentials.token

        expected_expires = 1000 + 3600 - 30
        assert credentials._expires_in == expected_expires


def test_token_refresh_error_handling():
    credentials = ydb.StaticCredentials.from_user_password(USERNAME, PASSWORD)
    credentials._tp.submit = MagicMock()
    credentials._make_token_request = MagicMock(side_effect=Exception("Network error"))

    with patch("time.time") as mock_time:
        mock_time.return_value = 1000 + 3600

        with pytest.raises(ydb.ConnectionError) as exc_info:
            credentials.token

        assert "Network error" in str(exc_info.value)
        assert credentials.last_error == "Network error"


def test_hybrid_background_and_sync_refresh():
    credentials = ydb.StaticCredentials.from_user_password(USERNAME, PASSWORD)

    call_count = 0
    background_calls = []

    def mock_make_request():
        nonlocal call_count
        call_count += 1
        return {"access_token": f"token_v{call_count}", "expires_in": 3600}

    def mock_submit(callback):
        background_calls.append(callback)

    credentials._make_token_request = mock_make_request
    credentials._tp.submit = mock_submit

    with patch("time.time") as mock_time:
        mock_time.return_value = 1000

        token1 = credentials.token
        assert token1 == "token_v1"
        assert call_count == 1
        assert len(background_calls) == 0

        mock_time.return_value = 1000 + min(1800, 3600 / 10) + 1
        token2 = credentials.token
        assert token2 == "token_v1"
        assert call_count == 1
        assert len(background_calls) == 1

        mock_time.return_value = 1000 + 3600 - 30 + 1
        token3 = credentials.token
        assert token3 == "token_v2"
        assert call_count == 2
