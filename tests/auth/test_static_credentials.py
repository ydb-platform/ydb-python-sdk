import pytest
import ydb
from unittest.mock import patch, MagicMock


USERNAME = "root"
PASSWORD = "1234"


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

        mock_time.return_value = 2000
        credentials._make_token_request.return_value = {"access_token": "token_v2", "expires_in": 3600}

        token3 = credentials.token
        assert token3 == "token_v2"
        assert credentials._make_token_request.call_count == 2


def test_token_double_check_locking():
    credentials = ydb.StaticCredentials.from_user_password(USERNAME, PASSWORD)

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

    with patch("time.time") as mock_time:
        mock_time.return_value = 1000

        credentials._make_token_request = MagicMock(return_value={"access_token": "token", "expires_in": 3600})

        credentials.token

        expected_expires = 1000 + min(1800, 3600 / 4)
        assert credentials._expires_in == expected_expires


def test_token_refresh_error_handling():
    credentials = ydb.StaticCredentials.from_user_password(USERNAME, PASSWORD)

    credentials._make_token_request = MagicMock(side_effect=Exception("Network error"))

    with pytest.raises(ydb.ConnectionError) as exc_info:
        credentials.token

    assert "Network error" in str(exc_info.value)
    assert credentials.last_error == "Network error"
