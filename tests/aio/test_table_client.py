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
