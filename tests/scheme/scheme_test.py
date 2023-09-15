import typing

import ydb


class TestSchemeEntryType:
    def test_tables(self, driver_sync: ydb.Driver, database: str, table_name: str, column_table_name: str):
        dir = driver_sync.scheme_client.list_directory(database)  # type: ydb.Directory
        children = dir.children  # type: typing.List[ydb.SchemeEntry]

        has_column_table = False
        has_row_table = False

        for child in children:
            if child.name == table_name:
                has_row_table = True
                assert child.is_table()
                assert child.is_any_table()
                assert not child.is_column_table()
            if child.name == column_table_name:
                has_column_table = True
                assert child.is_column_table()
                assert child.is_any_table()
                assert not child.is_table()

        assert has_column_table
        assert has_row_table
