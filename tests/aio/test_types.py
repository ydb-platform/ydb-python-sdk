import pytest
import ydb

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


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
        ("2019-09-17,Europe/Moscow", "TzDate"),
        ("2019-09-16T18:24:00,Europe/Moscow", "TzDatetime"),
        ("2019-09-16T18:24:00.123456,Europe/Moscow", "TzTimestamp"),
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
test_today = test_now.date()
test_dt_today = datetime.today()
tz4h = timezone(timedelta(hours=4))
try:
    tzmsk = ZoneInfo("Europe/Moscow")
    tzny = ZoneInfo("America/New_York")
except ZoneInfoNotFoundError:  # no system tzdata / tzdata wheel on this platform
    tzmsk = tzny = None
requires_tzdata = pytest.mark.skipif(tzmsk is None, reason="system timezone database (tzdata) not available")


@pytest.mark.parametrize(
    "value,ydb_type,result_value",
    [
        (test_today, "Date", test_today),
        (365, "Date", date(1971, 1, 1)),
        (3600 * 24 * 365, "Datetime", datetime(1971, 1, 1, 0, 0)),
        (datetime(1971, 1, 1, 0, 0), "Datetime", datetime(1971, 1, 1, 0, 0)),
        (datetime(1970, 1, 1, 4, 0, tzinfo=tz4h), "Datetime", datetime(1970, 1, 1, 0, 0)),
        (datetime(1969, 1, 1, 0, 0), "Datetime64", datetime(1969, 1, 1, 0, 0)),
        (datetime(1970, 1, 1, 4, 0, tzinfo=tz4h), "Datetime64", datetime(1970, 1, 1, 0, 0)),
        (datetime(1970, 1, 1, 4, 0, tzinfo=tz4h), "Timestamp", datetime(1970, 1, 1, 0, 0)),
        (test_td, "Interval", test_td),
        (test_now, "Timestamp", test_now),
        (
            1511789040123456,
            "Timestamp",
            datetime.fromisoformat("2017-11-27 13:24:00.123456"),
        ),
        ('{"foo": "bar"}', "Json", {"foo": "bar"}),
        ('{"foo": "bar"}', "JsonDocument", {"foo": "bar"}),
        pytest.param(
            datetime(2019, 9, 17, tzinfo=tzmsk),
            "TzDate",
            datetime(2019, 9, 17, tzinfo=tzmsk),
            marks=requires_tzdata,
        ),
        pytest.param(
            datetime(2019, 9, 16, 18, 24, tzinfo=tzmsk),
            "TzDatetime",
            datetime(2019, 9, 16, 18, 24, tzinfo=tzmsk),
            marks=requires_tzdata,
        ),
        pytest.param(
            datetime(2019, 9, 16, 18, 24, 0, 123456, tzinfo=tzmsk),
            "TzTimestamp",
            datetime(2019, 9, 16, 18, 24, 0, 123456, tzinfo=tzmsk),
            marks=requires_tzdata,
        ),
        pytest.param(
            datetime(2019, 9, 16, 12, 0, tzinfo=tzny),
            "TzDatetime",
            datetime(2019, 9, 16, 12, 0, tzinfo=tzny),
            marks=requires_tzdata,
        ),
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
