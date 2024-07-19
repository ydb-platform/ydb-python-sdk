import ydb


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

    # client = ydb.QueryClientSync(driver)
    # session = client.session().create()
    pool = ydb.QuerySessionPool(driver)
    # with pool.checkout() as session:
    def callee(session):
        print("="*50)
        print("BEFORE ACTION")
        it = session.execute("""SELECT COUNT(*) FROM example;""")
        for result_set in it:
            print(f"rows: {str(result_set.rows)}")

        print("="*50)
        print("INSERT WITH COMMIT TX")
        tx = session.transaction()

        tx.begin()

        tx.execute("""INSERT INTO example (key, value) VALUES (0033, "onepieceisreal");""")

        for result_set in tx.execute("""SELECT COUNT(*) FROM example;"""):
            print(f"rows: {str(result_set.rows)}")

        tx.commit()

        print("="*50)
        print("AFTER COMMIT TX")

        for result_set in session.execute("""SELECT COUNT(*) FROM example;"""):
            print(f"rows: {str(result_set.rows)}")

        print("="*50)
        print("INSERT WITH ROLLBACK TX")

        tx = session.transaction()

        tx.begin()

        tx.execute("""INSERT INTO example (key, value) VALUES (0044, "onepieceisreal");""")

        for result_set in tx.execute("""SELECT COUNT(*) FROM example;"""):
            print(f"rows: {str(result_set.rows)}")

        tx.rollback()

        print("="*50)
        print("AFTER ROLLBACK TX")

        for result_set in session.execute("""SELECT COUNT(*) FROM example;"""):
            print(f"rows: {str(result_set.rows)}")

    pool.retry_operation_sync(callee)


if __name__ == "__main__":
    main()
