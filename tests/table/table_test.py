import ydb


class TestTable:
    def test_create_table_with_not_null_primary_key_by_api(self, driver_sync, database):
        table_path = database + "/test_table"

        def create_table(session: ydb.Session):
            try:
                session.drop_table(table_path)
            except ydb.issues.SchemeError:
                pass

            description = (
                ydb.TableDescription()
                .with_primary_keys("key1")
                .with_columns(
                    ydb.Column("key1", ydb.PrimitiveType.Uint64),
                    ydb.Column("value", ydb.OptionalType(ydb.PrimitiveType.Utf8)),
                )
            )

            session.create_table(table_path, description)

        with ydb.SessionPool(driver_sync) as pool:
            pool.retry_operation_sync(create_table)

        res = driver_sync.scheme_client.describe_path(table_path)
        assert res.type == ydb.scheme.SchemeEntryType.TABLE
