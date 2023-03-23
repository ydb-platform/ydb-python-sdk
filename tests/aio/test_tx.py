import pytest
from contextlib import suppress

import ydb.aio.iam


@pytest.mark.asyncio
async def test_tx_commit(driver, database):
    session = await driver.table_client.session().create()
    prepared = await session.prepare(
        "DECLARE $param as Int32;\n SELECT $param as value",
    )

    tx = session.transaction()
    await tx.execute(prepared, {"$param": 2})
    await tx.commit()
    await tx.commit()


@pytest.mark.asyncio
async def test_tx_rollback(driver, database):
    session = await driver.table_client.session().create()
    prepared = await session.prepare(
        "DECLARE $param as Int32;\n SELECT $param as value",
    )

    tx = session.transaction()
    await tx.execute(prepared, {"$param": 2})
    await tx.rollback()
    await tx.rollback()


@pytest.mark.asyncio
async def test_tx_begin(driver, database):
    session = await driver.table_client.session().create()
    await session.create()

    tx = session.transaction()
    await tx.begin()
    await tx.begin()
    await tx.rollback()


@pytest.mark.asyncio
async def test_credentials():
    credentials = ydb.aio.iam.MetadataUrlCredentials()
    raised = False
    try:
        await credentials.auth_metadata()
    except Exception:
        raised = True

    assert raised


@pytest.mark.asyncio
async def test_tx_snapshot_ro(driver, database):
    session = await driver.table_client.session().create()
    description = (
        ydb.TableDescription()
        .with_primary_keys("key")
        .with_columns(
            ydb.Column("key", ydb.OptionalType(ydb.PrimitiveType.Uint64)),
            ydb.Column("value", ydb.OptionalType(ydb.PrimitiveType.Uint64)),
        )
    )
    tb_name = f"{database}/test"
    with suppress(ydb.issues.SchemeError):
        await session.drop_table(tb_name)
    await session.create_table(tb_name, description)
    await session.transaction(ydb.SerializableReadWrite()).execute(
        """INSERT INTO `test` (`key`, `value`) VALUES (1, 1), (2, 2)""",
        commit_tx=True,
    )

    ro_tx = session.transaction(tx_mode=ydb.SnapshotReadOnly())
    data1 = await ro_tx.execute("SELECT value FROM `test` WHERE key = 1")

    await session.transaction(ydb.SerializableReadWrite()).execute(
        "UPDATE `test` SET value = value + 1", commit_tx=True
    )

    data2 = await ro_tx.execute("SELECT value FROM `test` WHERE key = 1")
    assert data1[0].rows == data2[0].rows == [{"value": 1}]

    await ro_tx.commit()

    ro_tx = session.transaction(tx_mode=ydb.SnapshotReadOnly())
    with pytest.raises(ydb.issues.GenericError) as exc_info:
        await ro_tx.execute("UPDATE `test` SET value = value + 1")
    assert "read only transaction" in exc_info.value.message

    data = await session.transaction(tx_mode=ydb.SnapshotReadOnly()).execute(
        "SELECT value FROM `test` WHERE key = 1",
        commit_tx=True,
    )
    assert data[0].rows == [{"value": 2}]


@pytest.mark.asyncio
async def test_split_transactions_deny_split_explicit_commit(driver, table_name):
    async with ydb.aio.SessionPool(driver, 1) as pool:

        async def check_transaction(s: ydb.aio.table.Session):
            async with s.transaction(allow_split_transactions=False) as tx:
                await tx.execute("INSERT INTO %s (id) VALUES (1)" % table_name)
                await tx.commit()

                with pytest.raises(RuntimeError):
                    await tx.execute("INSERT INTO %s (id) VALUES (2)" % table_name)

                await tx.commit()

            async with s.transaction() as tx:
                rs = await tx.execute("SELECT COUNT(*) as cnt FROM %s" % table_name)
                assert rs[0].rows[0].cnt == 1

        await pool.retry_operation(check_transaction)


@pytest.mark.asyncio
async def test_split_transactions_deny_split_flag_commit(driver, table_name):
    async with ydb.aio.SessionPool(driver, 1) as pool:

        async def check_transaction(s: ydb.aio.table.Session):
            async with s.transaction(allow_split_transactions=False) as tx:
                await tx.execute("INSERT INTO %s (id) VALUES (1)" % table_name, commit_tx=True)

                with pytest.raises(RuntimeError):
                    await tx.execute("INSERT INTO %s (id) VALUES (2)" % table_name)

                await tx.commit()

            async with s.transaction() as tx:
                rs = await tx.execute("SELECT COUNT(*) as cnt FROM %s" % table_name)
                assert rs[0].rows[0].cnt == 1

        await pool.retry_operation(check_transaction)


@pytest.mark.asyncio
async def test_split_transactions_allow_split(driver, table_name):
    async with ydb.aio.SessionPool(driver, 1) as pool:

        async def check_transaction(s: ydb.aio.table.Session):
            async with s.transaction(allow_split_transactions=True) as tx:
                await tx.execute("INSERT INTO %s (id) VALUES (1)" % table_name)
                await tx.commit()

                await tx.execute("INSERT INTO %s (id) VALUES (2)" % table_name)
                await tx.commit()

            async with s.transaction() as tx:
                rs = await tx.execute("SELECT COUNT(*) as cnt FROM %s" % table_name)
                assert rs[0].rows[0].cnt == 2

        await pool.retry_operation(check_transaction)


@pytest.mark.asyncio
async def test_split_transactions_default(driver, table_name):
    async with ydb.aio.SessionPool(driver, 1) as pool:

        async def check_transaction(s: ydb.aio.table.Session):
            async with s.transaction() as tx:
                await tx.execute("INSERT INTO %s (id) VALUES (1)" % table_name)
                await tx.commit()

                with pytest.raises(RuntimeError):
                    await tx.execute("INSERT INTO %s (id) VALUES (2)" % table_name)

                await tx.commit()

            async with s.transaction() as tx:
                rs = await tx.execute("SELECT COUNT(*) as cnt FROM %s" % table_name)
                assert rs[0].rows[0].cnt == 1

        await pool.retry_operation(check_transaction)


@pytest.mark.asyncio
async def test_truncated_response(driver, table_name, table_path):
    column_types = ydb.BulkUpsertColumns().add_column("id", ydb.PrimitiveType.Int64)

    rows = []

    rows_count = 1100
    for i in range(rows_count):
        rows.append({"id": i})

    await driver.table_client.bulk_upsert(table_path, rows, column_types)

    table_client = driver.table_client  # default table client with driver's settings
    s = table_client.session()
    await s.create()
    t = s.transaction()
    with pytest.raises(ydb.TruncatedResponseError):
        await t.execute("SELECT * FROM %s" % table_name)


@pytest.mark.asyncio
async def test_truncated_response_allow(driver, table_name, table_path):
    column_types = ydb.BulkUpsertColumns().add_column("id", ydb.PrimitiveType.Int64)

    rows = []

    rows_count = 1100
    for i in range(rows_count):
        rows.append({"id": i})

    await driver.table_client.bulk_upsert(table_path, rows, column_types)

    table_client = ydb.TableClient(driver, ydb.TableClientSettings().with_allow_truncated_result(True))
    s = table_client.session()
    await s.create()
    t = s.transaction()
    result = await t.execute("SELECT * FROM %s" % table_name)
    assert result[0].truncated
    assert len(result[0].rows) == 1000
