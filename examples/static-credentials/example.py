import ydb


def test_driver_works(driver: ydb.Driver):
    driver.wait(5)
    pool = ydb.QuerySessionPool(driver)
    pool.execute_with_retries("SELECT 1")
    print("everything is fine")


def auth_with_static_credentials_old(endpoint: str, database: str, user: str, password: str):
    driver_config_temp = ydb.DriverConfig(
        endpoint=endpoint,
        database=database,
    )
    creds = ydb.StaticCredentials(
        driver_config=driver_config_temp,
        user=user,
        password=password,
    )

    driver_config = ydb.DriverConfig(
        endpoint=endpoint,
        database=database,
        credentials=creds,
    )

    with ydb.Driver(driver_config=driver_config) as driver:
        test_driver_works(driver)


def auth_with_static_credentials_new(endpoint: str, database: str, user: str, password: str):
    driver_config = ydb.DriverConfig(
        endpoint,
        database,
    )
    creds = ydb.StaticCredentials(
        driver_config,
        user,
        password,
    )

    with ydb.Driver(driver_config=driver_config, credentials=creds) as driver:
        test_driver_works(driver)


def auth_with_user_password_credentials(endpoint: str, database: str, user: str, password: str):
    driver_config = ydb.DriverConfig(
        endpoint=endpoint,
        database=database,
        credentials=ydb.UserPasswordCredentials(
            user=user,
            password=password,
            endpoint=endpoint,
            database=database,
        ),
    )

    with ydb.Driver(driver_config=driver_config) as driver:
        test_driver_works(driver)


def run(endpoint: str, database: str, user: str, password: str):
    auth_with_static_credentials_old(endpoint, database, user, password)
    auth_with_static_credentials_new(endpoint, database, user, password)
    auth_with_user_password_credentials(endpoint, database, user, password)
