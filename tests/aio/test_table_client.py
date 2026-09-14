import pytest
import ydb


class TestTableClient:
    @pytest.mark.asyncio
    async def test_create_table(self, driver: ydb.aio.Driver):
        client = driver.table_client
        table_name = "/local/testtableclient"
        try:
            await client.drop_table(table_name)
        except ydb.SchemeError:
            pass

        with pytest.raises(ydb.SchemeError):
            await client.describe_table(table_name)

        description = (
            ydb.TableDescription()
            .with_primary_keys("key1", "key2")
            .with_columns(
                ydb.Column("key1", ydb.OptionalType(ydb.PrimitiveType.Uint64)),
                ydb.Column("key2", ydb.OptionalType(ydb.PrimitiveType.Uint64)),
                ydb.Column("value", ydb.OptionalType(ydb.PrimitiveType.Utf8)),
            )
        )

        await client.create_table(table_name, description)

        actual_description = await client.describe_table(table_name)

        assert actual_description.columns == description.columns

    @pytest.mark.asyncio
    async def test_alter_table(self, driver: ydb.aio.Driver):
        client = driver.table_client

        table_name = "/local/testtableclient"
        try:
            await client.drop_table(table_name)
        except ydb.SchemeError:
            pass

        description = (
            ydb.TableDescription()
            .with_primary_keys("key1", "key2")
            .with_columns(
                ydb.Column("key1", ydb.OptionalType(ydb.PrimitiveType.Uint64)),
                ydb.Column("key2", ydb.OptionalType(ydb.PrimitiveType.Uint64)),
                ydb.Column("value", ydb.OptionalType(ydb.PrimitiveType.Utf8)),
            )
        )

        await client.create_table(table_name, description)

        await client.alter_table(
            table_name,
            add_columns=[
                ydb.Column("value2", ydb.OptionalType(ydb.PrimitiveType.Uint64)),
            ],
        )

        description = await client.describe_table(table_name)
        assert len(description.columns) == 4

    @pytest.mark.asyncio
    async def test_copy_table(self, driver: ydb.aio.Driver):
        client = driver.table_client
        table_name = "/local/testtableclient"
        try:
            await client.drop_table(table_name)
        except ydb.SchemeError:
            pass

        description = (
            ydb.TableDescription()
            .with_primary_keys("key1", "key2")
            .with_columns(
                ydb.Column("key1", ydb.OptionalType(ydb.PrimitiveType.Uint64)),
                ydb.Column("key2", ydb.OptionalType(ydb.PrimitiveType.Uint64)),
                ydb.Column("value", ydb.OptionalType(ydb.PrimitiveType.Utf8)),
            )
        )

        await client.create_table(table_name, description)

        await client.copy_table(table_name, table_name + "_copy")

        copied_description = await client.describe_table(table_name + "_copy")

        assert description.columns == copied_description.columns

    @pytest.mark.asyncio
    async def test_rename_index(self, driver: ydb.aio.Driver):
        client = driver.table_client
        table_name = "/local/testtableclient"
        try:
            await client.drop_table(table_name)
        except ydb.SchemeError:
            pass

        description = (
            ydb.TableDescription()
            .with_primary_keys("key1", "key2")
            .with_columns(
                ydb.Column("key1", ydb.OptionalType(ydb.PrimitiveType.Uint64)),
                ydb.Column("key2", ydb.OptionalType(ydb.PrimitiveType.Uint64)),
                ydb.Column("value", ydb.OptionalType(ydb.PrimitiveType.Utf8)),
            )
            .with_index(ydb.TableIndex("index1").with_index_columns("key1"))
            .with_index(ydb.TableIndex("index2").with_index_columns("key1"))
        )

        await client.create_table(table_name, description)

        await client.alter_table(table_name, rename_indexes=[ydb.RenameIndexItem("index1", "index1_1")])

        description = await client.describe_table(table_name)
        names = [index.name for index in description.indexes]
        assert len(names) == 2
        for name in ["index1_1", "index2"]:
            assert name in names

        await client.alter_table(
            table_name, rename_indexes=[ydb.RenameIndexItem("index1_1", "index2", replace_destination=True)]
        )

        description = await client.describe_table(table_name)
        assert len(description.indexes) == 1
        assert description.indexes[0].name == "index2"

    @pytest.mark.asyncio
    async def test_describe_system_view(self, driver: ydb.aio.Driver):
        client = driver.table_client

        with pytest.raises(ydb.SchemeError):
            await client.describe_system_view("/local/.sys/does_not_exist")

        entry = await client.describe_system_view("/local/.sys/nodes")

        assert isinstance(entry, ydb.SystemViewSchemeEntry)
        assert entry.is_sysview()
        assert entry.sys_view_name == "nodes"
        assert entry.sys_view_id > 0
        assert entry.primary_key == ["NodeId"]
        assert "NodeId" in [column.name for column in entry.columns]

    @pytest.mark.asyncio
    async def test_read_rows(self, driver: ydb.aio.Driver):
        client = driver.table_client
        table_name = "/local/testtableclient_read_rows"
        try:
            await client.drop_table(table_name)
        except ydb.SchemeError:
            pass

        description = (
            ydb.TableDescription()
            .with_primary_keys("key1", "key2")
            .with_columns(
                ydb.Column("key1", ydb.PrimitiveType.Uint64),
                ydb.Column("key2", ydb.PrimitiveType.Uint64),
                ydb.Column("value", ydb.OptionalType(ydb.PrimitiveType.Utf8)),
            )
        )

        await client.create_table(table_name, description)

        row_types = (
            ydb.BulkUpsertColumns()
            .add_column("key1", ydb.PrimitiveType.Uint64)
            .add_column("key2", ydb.PrimitiveType.Uint64)
            .add_column("value", ydb.OptionalType(ydb.PrimitiveType.Utf8))
        )
        await client.bulk_upsert(
            table_name,
            [
                {"key1": 1, "key2": 10, "value": "alice"},
                {"key1": 2, "key2": 20, "value": "bob"},
                {"key1": 3, "key2": 30, "value": "carol"},
            ],
            row_types,
        )

        key_types = (
            ydb.BulkUpsertColumns()
            .add_column("key1", ydb.PrimitiveType.Uint64)
            .add_column("key2", ydb.PrimitiveType.Uint64)
        )
        result_set = await client.read_rows(
            table_name,
            [
                {"key1": 1, "key2": 10},
                {"key1": 3, "key2": 30},
                {"key1": 9, "key2": 90},
            ],
            key_types,
        )

        rows = {(row.key1, row.key2, row.value) for row in result_set.rows}
        assert rows == {(1, 10, "alice"), (3, 30, "carol")}

        columns_only = await client.read_rows(
            table_name,
            [{"key1": 2, "key2": 20}],
            key_types,
            columns=("value",),
        )
        assert [column.name for column in columns_only.columns] == ["value"]
        assert [row.value for row in columns_only.rows] == ["bob"]

        with pytest.raises(ydb.SchemeError):
            await client.read_rows("/local/does_not_exist", [{"key1": 1, "key2": 10}], key_types)
