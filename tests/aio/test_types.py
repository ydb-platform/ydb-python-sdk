import pytest
import ydb

from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4


@pytest.mark.parametrize(
    "value,ydb_type",
    [
        (True, "Bool"),
        (-125, "Int8"),
        (None, "Int8?"),
        (-32766, "Int16"),
        (-1123, "Int32"),
        (-2157583648, "Int64"),
        (255, "UInt8"),
        (65534, "UInt16"),
        (5555, "UInt32"),
        (2157583649, "UInt64"),
        (3.1415, "Double"),
        (".31415926535e1", "DyNumber"),
        (Decimal("3.1415926535"), "Decimal(28, 10)"),
        (b"Hello, YDB!", "String"),
        ("Hello, 🐍!", "Utf8"),
        ('{"foo": "bar"}', "Json"),
        (b'{"foo"="bar"}', "Yson"),
        ('{"foo":"bar"}', "JsonDocument"),
        (uuid4(), "Uuid"),
        ([1, 2, 3], "List<Int8>"),
        ({1: None, 2: None, 3: None}, "Set<Int8>"),
        ([b"a", b"b", b"c"], "List<String>"),
        ({"a": 1001, "b": 1002}, "Dict<Utf8, Int32>"),
        (("a", 1001), "Tuple<Utf8, Int32>"),
        ({"foo": True, "bar": None}, "Struct<foo:Bool?, bar:Int32?>"),
        (100, "Date"),
        (100, "Datetime"),
        (-100, "Interval"),
        (100, "Timestamp"),
        (1511789040123456, "Timestamp"),
    ],
)
@pytest.mark.asyncio
async def test_types(driver, database, value, ydb_type):
    session = await driver.table_client.session().create()
    prepared = await session.prepare(f"DECLARE $param as {ydb_type}; SELECT $param as value")
    result = await session.transaction().execute(prepared, {"$param": value}, commit_tx=True)
    assert result[0].rows[0].value == value


test_td = timedelta(microseconds=-100)
test_now = datetime.utcnow()
test_today = date.today()
test_dt_today = datetime.today()


@pytest.mark.parametrize(
    "value,ydb_type,result_value",
    [
        # FIXME: TypeError: 'datetime.datetime' object cannot be interpreted as an integer
        # (test_dt_today, "Datetime", test_dt_today),
        (test_today, "Date", test_today),
        (365, "Date", date(1971, 1, 1)),
        (3600 * 24 * 365, "Datetime", datetime(1971, 1, 1, 0, 0)),
        (test_td, "Interval", test_td),
        (test_now, "Timestamp", test_now),
        (
            1511789040123456,
            "Timestamp",
            datetime.fromisoformat("2017-11-27 13:24:00.123456"),
        ),
        ('{"foo": "bar"}', "Json", {"foo": "bar"}),
        ('{"foo": "bar"}', "JsonDocument", {"foo": "bar"}),
    ],
)
@pytest.mark.asyncio
async def test_types_native(driver, database, value, ydb_type, result_value):
    settings = (
        ydb.TableClientSettings()
        .with_native_date_in_result_sets(True)
        .with_native_datetime_in_result_sets(True)
        .with_native_timestamp_in_result_sets(True)
        .with_native_interval_in_result_sets(True)
        .with_native_json_in_result_sets(True)
    )

    client = ydb.TableClient(driver, settings)
    session = await client.session().create()

    prepared = await session.prepare(f"DECLARE $param as {ydb_type}; SELECT $param as value")

    result = await session.transaction().execute(prepared, {"$param": value}, commit_tx=True)
    assert result[0].rows[0].value == result_value
