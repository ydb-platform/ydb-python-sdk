import ydb


def test_driver_works(driver: ydb.Driver):
    """Tests the functionality of the YDB driver.

    Waits for the driver to become ready and executes a simple SQL query to verify that the driver works as expected.

    Args:
        driver (ydb.Driver): The YDB driver instance to test.

    Raises:
        AssertionError: If the SQL query does not return the expected result.
    """
    driver.wait(5)
    pool = ydb.QuerySessionPool(driver)
    result = pool.execute_with_retries("SELECT 1 as cnt")
    assert result[0].rows[0].cnt == 1


def auth_with_static_credentials(endpoint: str, database: str, user: str, password: str, ca_path: str):
    """Authenticate using static credentials.

    Args:
        endpoint (str): Accepts a string in the format `grpcs://<node-fqdn>:2136` or `grpcs://<node-ip>:2136`.
        database (str): Accepts a string, the database name in the format `/Root/<database-name>`.
        user (str): Username.
        password (str): User password.
        ca_path (str): Path to CA cert

    Notes:
        The argument `root_certificates` of the function `ydb.DriverConfig` takes the content of the cluster's root certificate for connecting to cluster nodes via TLS.
        Note that the VM from which you are connecting must be in the cluster's domain for which the CA certificate is issued.
    """

    driver_config = ydb.DriverConfig(
        endpoint=endpoint,
        database=database,
        credentials=ydb.StaticCredentials.from_user_password(user, password),
        root_certificates=ydb.load_ydb_root_certificate(ca_path)
    )

    with ydb.Driver(driver_config=driver_config) as driver:
        test_driver_works(driver)


def run(endpoint: str, database: str, user: str, password: str):
    auth_with_static_credentials(endpoint, database, user, password)
