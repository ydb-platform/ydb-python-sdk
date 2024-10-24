import pytest

import ydb

from datetime import date, datetime, timedelta, timezone


@pytest.fixture
def settings_on():
    settings = (
        ydb.QueryClientSettings()
        .with_native_date_in_result_sets(True)
        .with_native_datetime_in_result_sets(True)
        .with_native_timestamp_in_result_sets(True)
        .with_native_interval_in_result_sets(True)
        .with_native_json_in_result_sets(True)
    )
    return settings


@pytest.fixture
def settings_off():
    settings = (
        ydb.QueryClientSettings()
        .with_native_date_in_result_sets(False)
        .with_native_datetime_in_result_sets(False)
        .with_native_timestamp_in_result_sets(False)
        .with_native_interval_in_result_sets(False)
        .with_native_json_in_result_sets(False)
    )
    return settings


test_td = timedelta(microseconds=-100)
test_now = datetime.utcnow()
test_today = test_now.date()
test_dt_today = datetime.today()
tz4h = timezone(timedelta(hours=4))


params = pytest.mark.parametrize(
    "value,ydb_type,casted_result,uncasted_type",
    [
        (test_today, "Date", test_today, int),
        (365, "Date", date(1971, 1, 1), int),
        (3600 * 24 * 365, "Datetime", datetime(1971, 1, 1, 0, 0), int),
        (datetime(1970, 1, 1, 4, 0, tzinfo=tz4h), "Timestamp", datetime(1970, 1, 1, 0, 0), int),
        (test_td, "Interval", test_td, int),
        (test_now, "Timestamp", test_now, int),
        (
            1511789040123456,
            "Timestamp",
            datetime.fromisoformat("2017-11-27 13:24:00.123456"),
            int,
        ),
        ('{"foo": "bar"}', "Json", {"foo": "bar"}, str),
        ('{"foo": "bar"}', "JsonDocument", {"foo": "bar"}, str),
    ],
)


class TestQueryClientSettings:
    @params
    def test_driver_turn_on(self, driver_sync, settings_on, value, ydb_type, casted_result, uncasted_type):
        driver_sync._driver_config.query_client_settings = settings_on
        pool = ydb.QuerySessionPool(driver_sync)
        result = pool.execute_with_retries(
            f"DECLARE $param as {ydb_type}; SELECT $param as value",
            {"$param": (value, getattr(ydb.PrimitiveType, ydb_type))},
        )
        assert result[0].rows[0].value == casted_result
        pool.stop()

    @params
    def test_driver_turn_off(self, driver_sync, settings_off, value, ydb_type, casted_result, uncasted_type):
        driver_sync._driver_config.query_client_settings = settings_off
        pool = ydb.QuerySessionPool(driver_sync)
        result = pool.execute_with_retries(
            f"DECLARE $param as {ydb_type}; SELECT $param as value",
            {"$param": (value, getattr(ydb.PrimitiveType, ydb_type))},
        )
        assert type(result[0].rows[0].value) == uncasted_type
        pool.stop()

    @params
    def test_session_pool_turn_on(self, driver_sync, settings_on, value, ydb_type, casted_result, uncasted_type):
        pool = ydb.QuerySessionPool(driver_sync, query_client_settings=settings_on)
        result = pool.execute_with_retries(
            f"DECLARE $param as {ydb_type}; SELECT $param as value",
            {"$param": (value, getattr(ydb.PrimitiveType, ydb_type))},
        )
        assert result[0].rows[0].value == casted_result
        pool.stop()

    @params
    def test_session_pool_turn_off(self, driver_sync, settings_off, value, ydb_type, casted_result, uncasted_type):
        pool = ydb.QuerySessionPool(driver_sync, query_client_settings=settings_off)
        result = pool.execute_with_retries(
            f"DECLARE $param as {ydb_type}; SELECT $param as value",
            {"$param": (value, getattr(ydb.PrimitiveType, ydb_type))},
        )
        assert type(result[0].rows[0].value) == uncasted_type
        pool.stop()

    @pytest.mark.asyncio
    @params
    async def test_driver_async_turn_on(self, driver, settings_on, value, ydb_type, casted_result, uncasted_type):
        driver._driver_config.query_client_settings = settings_on
        pool = ydb.aio.QuerySessionPool(driver)
        result = await pool.execute_with_retries(
            f"DECLARE $param as {ydb_type}; SELECT $param as value",
            {"$param": (value, getattr(ydb.PrimitiveType, ydb_type))},
        )
        assert result[0].rows[0].value == casted_result
        await pool.stop()

    @pytest.mark.asyncio
    @params
    async def test_driver_async_turn_off(self, driver, settings_off, value, ydb_type, casted_result, uncasted_type):
        driver._driver_config.query_client_settings = settings_off
        pool = ydb.aio.QuerySessionPool(driver)
        result = await pool.execute_with_retries(
            f"DECLARE $param as {ydb_type}; SELECT $param as value",
            {"$param": (value, getattr(ydb.PrimitiveType, ydb_type))},
        )
        assert type(result[0].rows[0].value) == uncasted_type
        await pool.stop()

    @pytest.mark.asyncio
    @params
    async def test_session_pool_async_turn_on(self, driver, settings_on, value, ydb_type, casted_result, uncasted_type):
        pool = ydb.aio.QuerySessionPool(driver, query_client_settings=settings_on)
        result = await pool.execute_with_retries(
            f"DECLARE $param as {ydb_type}; SELECT $param as value",
            {"$param": (value, getattr(ydb.PrimitiveType, ydb_type))},
        )
        assert result[0].rows[0].value == casted_result
        await pool.stop()

    @pytest.mark.asyncio
    @params
    async def test_session_pool_async_turn_off(
        self, driver, settings_off, value, ydb_type, casted_result, uncasted_type
    ):
        pool = ydb.aio.QuerySessionPool(driver, query_client_settings=settings_off)
        result = await pool.execute_with_retries(
            f"DECLARE $param as {ydb_type}; SELECT $param as value",
            {"$param": (value, getattr(ydb.PrimitiveType, ydb_type))},
        )
        assert type(result[0].rows[0].value) == uncasted_type
        await pool.stop()
