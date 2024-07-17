import ydb

from ydb.query.session import QuerySessionSync


def main():
    driver_config = ydb.DriverConfig(
        endpoint="grpc://localhost:2136",
        database="/local",
        # credentials=ydb.credentials_from_env_variables(),
        # root_certificates=ydb.load_ydb_root_certificate(),
    )
    try:
        driver = ydb.Driver(driver_config)
        driver.wait(timeout=5)
    except TimeoutError:
        raise RuntimeError("Connect failed to YDB")

    session = QuerySessionSync(driver)
    session.create()

    it = session.execute("select 1; select 2;", commit_tx=False)
    for result_set in it:
        # pass
        print(f"columns: {str(result_set.columns)}")
        print(f"rows: {str(result_set.rows)}")


if __name__ == '__main__':
    main()
