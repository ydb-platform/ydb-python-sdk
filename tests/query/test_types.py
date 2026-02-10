from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

import ydb


@pytest.mark.parametrize(
    "value,ydb_type",
    [
        (True, ydb.PrimitiveType.Bool),
        (-125, ydb.PrimitiveType.Int8),
        (None, ydb.OptionalType(ydb.PrimitiveType.Int8)),
        (-32766, ydb.PrimitiveType.Int16),
        (-1123, ydb.PrimitiveType.Int32),
        (-2157583648, ydb.PrimitiveType.Int64),
        (255, ydb.PrimitiveType.Uint8),
        (65534, ydb.PrimitiveType.Uint16),
        (5555, ydb.PrimitiveType.Uint32),
        (2157583649, ydb.PrimitiveType.Uint64),
        (3.1415, ydb.PrimitiveType.Double),
        (".31415926535e1", ydb.PrimitiveType.DyNumber),
        (Decimal("3.1415926535"), ydb.DecimalType(28, 10)),
        (b"Hello, YDB!", ydb.PrimitiveType.String),
        ("Hello, 🐍!", ydb.PrimitiveType.Utf8),
        ('{"foo": "bar"}', ydb.PrimitiveType.Json),
        (b'{"foo"="bar"}', ydb.PrimitiveType.Yson),
        ('{"foo":"bar"}', ydb.PrimitiveType.JsonDocument),
        (uuid4(), ydb.PrimitiveType.UUID),
        ([1, 2, 3], ydb.ListType(ydb.PrimitiveType.Int8)),
        ({1: None, 2: None, 3: None}, ydb.SetType(ydb.PrimitiveType.Int8)),
        ([b"a", b"b", b"c"], ydb.ListType(ydb.PrimitiveType.String)),
        ({"a": 1001, "b": 1002}, ydb.DictType(ydb.PrimitiveType.Utf8, ydb.PrimitiveType.Int32)),
        (
            ("a", 1001),
            ydb.TupleType().add_element(ydb.PrimitiveType.Utf8).add_element(ydb.PrimitiveType.Int32),
        ),
        (
            {"foo": True, "bar": None},
            ydb.StructType()
            .add_member("foo", ydb.OptionalType(ydb.PrimitiveType.Bool))
            .add_member("bar", ydb.OptionalType(ydb.PrimitiveType.Int32)),
        ),
        (100, ydb.PrimitiveType.Date),
        (100, ydb.PrimitiveType.Date32),
        (-100, ydb.PrimitiveType.Date32),
        (100, ydb.PrimitiveType.Datetime),
        (100, ydb.PrimitiveType.Datetime64),
        (-100, ydb.PrimitiveType.Datetime64),
        (-100, ydb.PrimitiveType.Interval),
        (-100, ydb.PrimitiveType.Interval64),
        (100, ydb.PrimitiveType.Timestamp),
        (100, ydb.PrimitiveType.Timestamp64),
        (-100, ydb.PrimitiveType.Timestamp64),
        (1511789040123456, ydb.PrimitiveType.Timestamp),
        (1511789040123456, ydb.PrimitiveType.Timestamp64),
        (-1511789040123456, ydb.PrimitiveType.Timestamp64),
    ],
)
def test_types(driver_sync: ydb.Driver, value, ydb_type):
    settings = (
        ydb.QueryClientSettings()
        .with_native_date_in_result_sets(False)
        .with_native_datetime_in_result_sets(False)
        .with_native_timestamp_in_result_sets(False)
        .with_native_interval_in_result_sets(False)
        .with_native_json_in_result_sets(False)
    )
    with ydb.QuerySessionPool(driver_sync, query_client_settings=settings) as pool:
        result = pool.execute_with_retries(
            f"DECLARE $param as {ydb_type}; SELECT $param as value",
            {"$param": (value, ydb_type)},
        )
        assert result[0].rows[0].value == value


test_td = timedelta(microseconds=-100)
test_now = datetime.utcnow()
test_old_date = datetime(1221, 1, 1, 0, 0)
test_today = test_now.date()
test_dt_today = datetime.today()
tz4h = timezone(timedelta(hours=4))


@pytest.mark.parametrize(
    "value,ydb_type,result_value",
    [
        # FIXME: TypeError: 'datetime.datetime' object cannot be interpreted as an integer
        # (test_dt_today, "Datetime", test_dt_today),
        (test_today, ydb.PrimitiveType.Date, test_today),
        (365, ydb.PrimitiveType.Date, date(1971, 1, 1)),
        (-365, ydb.PrimitiveType.Date32, date(1969, 1, 1)),
        (3600 * 24 * 365, ydb.PrimitiveType.Datetime, datetime(1971, 1, 1, 0, 0)),
        (3600 * 24 * 365 * (-1), ydb.PrimitiveType.Datetime64, datetime(1969, 1, 1, 0, 0)),
        (datetime(1970, 1, 1, 4, 0, tzinfo=tz4h), ydb.PrimitiveType.Timestamp, datetime(1970, 1, 1, 0, 0)),
        (test_td, ydb.PrimitiveType.Interval, test_td),
        (test_td, ydb.PrimitiveType.Interval64, test_td),
        (test_now, ydb.PrimitiveType.Timestamp, test_now),
        (test_old_date, ydb.PrimitiveType.Timestamp64, test_old_date),
        (
            1511789040123456,
            ydb.PrimitiveType.Timestamp,
            datetime.fromisoformat("2017-11-27 13:24:00.123456"),
        ),
        ('{"foo": "bar"}', ydb.PrimitiveType.Json, {"foo": "bar"}),
        ('{"foo": "bar"}', ydb.PrimitiveType.JsonDocument, {"foo": "bar"}),
    ],
)
def test_types_native(driver_sync, value, ydb_type, result_value):
    with ydb.QuerySessionPool(driver_sync) as pool:
        result = pool.execute_with_retries(
            f"DECLARE $param as {ydb_type}; SELECT $param as value",
            {"$param": (value, ydb_type)},
        )
        assert result[0].rows[0].value == result_value


@pytest.mark.parametrize(
    "value,ydb_type,str_repr,result_value",
    [
        (test_today, ydb.PrimitiveType.Date, str(test_today), test_today),
        (365, ydb.PrimitiveType.Date, "1971-01-01", date(1971, 1, 1)),
        (-365, ydb.PrimitiveType.Date32, "1969-01-01", date(1969, 1, 1)),
        (3600 * 24 * 365, ydb.PrimitiveType.Datetime, "1971-01-01T00:00:00Z", datetime(1971, 1, 1, 0, 0)),
        (3600 * 24 * 365 * (-1), ydb.PrimitiveType.Datetime64, "1969-01-01T00:00:00Z", datetime(1969, 1, 1, 0, 0)),
        (
            datetime(1970, 1, 1, 4, 0, tzinfo=tz4h),
            ydb.PrimitiveType.Timestamp,
            "1970-01-01T00:00:00Z",
            datetime(1970, 1, 1, 0, 0),
        ),
        (test_td, ydb.PrimitiveType.Interval, "-PT0.0001S", test_td),
        (test_td, ydb.PrimitiveType.Interval64, "-PT0.0001S", test_td),
        (test_old_date, ydb.PrimitiveType.Timestamp64, "1221-01-01T00:00:00Z", test_old_date),
    ],
)
def test_type_str_repr(driver_sync, value, ydb_type, str_repr, result_value):
    with ydb.QuerySessionPool(driver_sync) as pool:
        result = pool.execute_with_retries(
            f"DECLARE $param as {ydb_type}; SELECT CAST($param as Utf8) as value",
            {"$param": (value, ydb_type)},
        )
        assert result[0].rows[0].value == str_repr

        result = pool.execute_with_retries(
            f"DECLARE $param as Utf8; SELECT CAST($param as {ydb_type}) as value",
            {"$param": (str_repr, ydb.PrimitiveType.Utf8)},
        )
        assert result[0].rows[0].value == result_value
