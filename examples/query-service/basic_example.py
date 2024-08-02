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

    pool = ydb.QuerySessionPool(driver)

    print("=" * 50)
    print("DELETE TABLE IF EXISTS")
    pool.execute_with_retries("DROP TABLE IF EXISTS example")

    print("=" * 50)
    print("CREATE TABLE")
    pool.execute_with_retries("CREATE TABLE example(key UInt64, value String, PRIMARY KEY (key))")

    pool.execute_with_retries("INSERT INTO example (key, value) VALUES (1, 'onepieceisreal')")

    def callee(session):
        print("=" * 50)
        with session.execute("DELETE FROM example"):
            pass

        print("BEFORE ACTION")
        with session.execute("SELECT COUNT(*) AS rows_count FROM example") as results:
            for result_set in results:
                print(f"rows: {str(result_set.rows)}")

        print("=" * 50)
        print("INSERT WITH COMMIT TX")

        with session.transaction() as tx:
            tx.begin()

            with tx.execute("INSERT INTO example (key, value) VALUES (1, 'onepieceisreal')"):
                pass

            with tx.execute("SELECT COUNT(*) AS rows_count FROM example") as results:
                for result_set in results:
                    print(f"rows: {str(result_set.rows)}")

            tx.commit()

        print("=" * 50)
        print("AFTER COMMIT TX")

        with session.execute("SELECT COUNT(*) AS rows_count FROM example") as results:
            for result_set in results:
                print(f"rows: {str(result_set.rows)}")

        print("=" * 50)
        print("INSERT WITH ROLLBACK TX")

        with session.transaction() as tx:
            tx.begin()

            with tx.execute("INSERT INTO example (key, value) VALUES (2, 'onepieceisreal')"):
                pass

            with tx.execute("SELECT COUNT(*) AS rows_count FROM example") as results:
                for result_set in results:
                    print(f"rows: {str(result_set.rows)}")

            tx.rollback()

        print("=" * 50)
        print("AFTER ROLLBACK TX")

        with session.execute("SELECT COUNT(*) AS rows_count FROM example") as results:
            for result_set in results:
                print(f"rows: {str(result_set.rows)}")

    pool.retry_operation_sync(callee)

    def callee(session: ydb.QuerySessionSync):
        query_print = """select $a"""

        print("=" * 50)
        print("Check implicit typed parameters")

        values = [
            1,
            1.0,
            True,
            "text",
            {"4": 8, "15": 16, "23": 42},
            [{"name": "Michael"}, {"surname": "Scott"}],
        ]

        for value in values:
            print(f"value: {value}")
            with session.transaction().execute(
                query=query_print,
                parameters={"$a": value},
                commit_tx=True,
            ) as results:
                for result_set in results:
                    print(f"rows: {str(result_set.rows)}")

        print("=" * 50)
        print("Check typed parameters as tuple pair")

        typed_value = ([1, 2, 3], ydb.ListType(ydb.PrimitiveType.Int64))
        print(f"value: {typed_value}")

        with session.transaction().execute(
            query=query_print,
            parameters={"$a": typed_value},
            commit_tx=True,
        ) as results:
            for result_set in results:
                print(f"rows: {str(result_set.rows)}")

        print("=" * 50)
        print("Check typed parameters as ydb.TypedValue")

        typed_value = ydb.TypedValue(111, ydb.PrimitiveType.Int64)
        print(f"value: {typed_value}")

        with session.transaction().execute(
            query=query_print,
            parameters={"$a": typed_value},
            commit_tx=True,
        ) as results:
            for result_set in results:
                print(f"rows: {str(result_set.rows)}")

    pool.retry_operation_sync(callee)


if __name__ == "__main__":
    main()
