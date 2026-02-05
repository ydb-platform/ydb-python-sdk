import typing  # noqa: F401
import pytest

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

    @pytest.mark.parametrize(
        "scheme_entry_type",
        [
            ydb.scheme.SchemeEntryType.TYPE_UNSPECIFIED,
            ydb.scheme.SchemeEntryType.DIRECTORY,
            ydb.scheme.SchemeEntryType.TABLE,
            ydb.scheme.SchemeEntryType.PERS_QUEUE_GROUP,
            ydb.scheme.SchemeEntryType.DATABASE,
            ydb.scheme.SchemeEntryType.RTMR_VOLUME,
            ydb.scheme.SchemeEntryType.BLOCK_STORE_VOLUME,
            ydb.scheme.SchemeEntryType.COORDINATION_NODE,
            ydb.scheme.SchemeEntryType.COLUMN_STORE,
            ydb.scheme.SchemeEntryType.COLUMN_TABLE,
            ydb.scheme.SchemeEntryType.SEQUENCE,
            ydb.scheme.SchemeEntryType.REPLICATION,
            ydb.scheme.SchemeEntryType.TOPIC,
            ydb.scheme.SchemeEntryType.EXTERNAL_TABLE,
            ydb.scheme.SchemeEntryType.EXTERNAL_DATA_SOURCE,
            ydb.scheme.SchemeEntryType.VIEW,
            ydb.scheme.SchemeEntryType.RESOURCE_POOL,
        ],
    )
    def test_scheme_entry(self, scheme_entry_type):
        from ydb.scheme import SchemeEntryType as et

        scheme_entry = ydb.scheme.SchemeEntry(
            effective_permissions=None,
            kwargs=None,
            name="example",
            owner=None,
            permissions=None,
            size_bytes=42,
            type=scheme_entry_type,
        )

        assert scheme_entry.is_table() == (scheme_entry_type in (et.TABLE,))
        assert scheme_entry.is_any_table() == (scheme_entry_type in (et.TABLE, et.COLUMN_TABLE))
        assert scheme_entry.is_column_table() == (scheme_entry_type in (et.COLUMN_TABLE,))
        assert scheme_entry.is_column_store() == (scheme_entry_type in (et.COLUMN_STORE,))
        assert scheme_entry.is_row_table() == (scheme_entry_type in (et.TABLE,))
        assert scheme_entry.is_directory() == (scheme_entry_type in (et.DIRECTORY,))
        assert scheme_entry.is_database() == (scheme_entry_type in (et.DATABASE,))
        assert scheme_entry.is_coordination_node() == (scheme_entry_type in (et.COORDINATION_NODE,))
        assert scheme_entry.is_directory_or_database() == (scheme_entry_type in (et.DIRECTORY, et.DATABASE))
        assert scheme_entry.is_external_table() == (scheme_entry_type in (et.EXTERNAL_TABLE,))
        assert scheme_entry.is_external_data_source() == (scheme_entry_type in (et.EXTERNAL_DATA_SOURCE,))
        assert scheme_entry.is_view() == (scheme_entry_type in (et.VIEW,))
        assert scheme_entry.is_resource_pool() == (scheme_entry_type in (et.RESOURCE_POOL,))
