import pytest
import ydb
import datetime


@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.asyncio
async def test_interval(driver, database, enabled):
    client = ydb.TableClient(
        driver, ydb.TableClientSettings().with_native_interval_in_result_sets(enabled)
    )
    session = await client.session().create()
    prepared = await session.prepare(
        "DECLARE $param as Interval;\n SELECT $param as value",
    )

    param = datetime.timedelta(microseconds=-100) if enabled else -100
    result = await session.transaction().execute(
        prepared, {"$param": param}, commit_tx=True
    )
    assert result[0].rows[0].value == param


@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.asyncio
async def test_timestamp(driver, database, enabled):
    client = ydb.TableClient(
        driver, ydb.TableClientSettings().with_native_timestamp_in_result_sets(enabled)
    )
    session = await client.session().create()
    prepared = await session.prepare(
        "DECLARE $param as Timestamp;\n SELECT $param as value",
    )

    param = datetime.datetime.utcnow() if enabled else 100
    result = await session.transaction().execute(
        prepared, {"$param": param}, commit_tx=True
    )
    assert result[0].rows[0].value == param

    result = await session.transaction().execute(
        prepared, {"$param": 1511789040123456}, commit_tx=True
    )
    if enabled:
        assert result[0].rows[0].value == datetime.datetime.fromisoformat(
            "2017-11-27 13:24:00.123456"
        )
    else:
        assert result[0].rows[0].value == 1511789040123456
