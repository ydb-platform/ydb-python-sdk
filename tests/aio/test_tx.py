import pytest
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
