import pytest
import ydb


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
