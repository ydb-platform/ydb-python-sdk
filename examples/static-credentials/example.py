import ydb


def test_driver_works(driver: ydb.Driver):
    driver.wait(5)
    pool = ydb.QuerySessionPool(driver)
    result = pool.execute_with_retries("SELECT 1 as cnt")
    assert result[0].rows[0].cnt == 1


def auth_with_static_credentials(endpoint: str, database: str, user: str, password: str):
    driver_config = ydb.DriverConfig(
        endpoint=endpoint,
        database=database,
        credentials=ydb.StaticCredentials.from_user_password(user, password),
    )

    with ydb.Driver(driver_config=driver_config) as driver:
        test_driver_works(driver)


def run(endpoint: str, database: str, user: str, password: str):
    auth_with_static_credentials(endpoint, database, user, password)
