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

    with pytest.raises(ydb.issues.GenericError) as exc_info:
        await ro_tx.execute("UPDATE `test` SET value = value + 1")
    assert "read only transaction" in exc_info.value.message

    data = await session.transaction(tx_mode=ydb.SnapshotReadOnly()).execute(
        "SELECT value FROM `test` WHERE key = 1",
        commit_tx=True,
    )
    assert data[0].rows == [{"value": 2}]
