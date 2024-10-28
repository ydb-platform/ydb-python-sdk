import pytest

import ydb

from datetime import date, datetime, timedelta


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


params = pytest.mark.parametrize(
    "value,ydb_type,casted_result,uncasted_result",
    [
        (365, "Date", date(1971, 1, 1), 365),
        (3600 * 24 * 365, "Datetime", datetime(1971, 1, 1, 0, 0), 3600 * 24 * 365),
        (timedelta(seconds=1), "Interval", timedelta(seconds=1), 1000000),
        (
            1511789040123456,
            "Timestamp",
            datetime.fromisoformat("2017-11-27 13:24:00.123456"),
            1511789040123456,
        ),
        ('{"foo": "bar"}', "Json", {"foo": "bar"}, '{"foo": "bar"}'),
        ('{"foo": "bar"}', "JsonDocument", {"foo": "bar"}, '{"foo":"bar"}'),
    ],
)


class TestQueryClientSettings:
    @params
    def test_driver_turn_on(self, driver_sync, settings_on, value, ydb_type, casted_result, uncasted_result):
        driver_sync._driver_config.query_client_settings = settings_on
        pool = ydb.QuerySessionPool(driver_sync)
        result = pool.execute_with_retries(
            f"DECLARE $param as {ydb_type}; SELECT $param as value",
            {"$param": (value, getattr(ydb.PrimitiveType, ydb_type))},
        )
        assert result[0].rows[0].value == casted_result
        pool.stop()

    @params
    def test_driver_turn_off(self, driver_sync, settings_off, value, ydb_type, casted_result, uncasted_result):
        driver_sync._driver_config.query_client_settings = settings_off
        pool = ydb.QuerySessionPool(driver_sync)
        result = pool.execute_with_retries(
            f"DECLARE $param as {ydb_type}; SELECT $param as value",
            {"$param": (value, getattr(ydb.PrimitiveType, ydb_type))},
        )
        assert result[0].rows[0].value == uncasted_result
        pool.stop()

    @params
    def test_session_pool_turn_on(self, driver_sync, settings_on, value, ydb_type, casted_result, uncasted_result):
        pool = ydb.QuerySessionPool(driver_sync, query_client_settings=settings_on)
        result = pool.execute_with_retries(
            f"DECLARE $param as {ydb_type}; SELECT $param as value",
            {"$param": (value, getattr(ydb.PrimitiveType, ydb_type))},
        )
        assert result[0].rows[0].value == casted_result
        pool.stop()

    @params
    def test_session_pool_turn_off(self, driver_sync, settings_off, value, ydb_type, casted_result, uncasted_result):
        pool = ydb.QuerySessionPool(driver_sync, query_client_settings=settings_off)
        result = pool.execute_with_retries(
            f"DECLARE $param as {ydb_type}; SELECT $param as value",
            {"$param": (value, getattr(ydb.PrimitiveType, ydb_type))},
        )
        assert result[0].rows[0].value == uncasted_result
        pool.stop()

    @pytest.mark.asyncio
    @params
    async def test_driver_async_turn_on(self, driver, settings_on, value, ydb_type, casted_result, uncasted_result):
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
    async def test_driver_async_turn_off(self, driver, settings_off, value, ydb_type, casted_result, uncasted_result):
        driver._driver_config.query_client_settings = settings_off
        pool = ydb.aio.QuerySessionPool(driver)
        result = await pool.execute_with_retries(
            f"DECLARE $param as {ydb_type}; SELECT $param as value",
            {"$param": (value, getattr(ydb.PrimitiveType, ydb_type))},
        )
        assert result[0].rows[0].value == uncasted_result
        await pool.stop()

    @pytest.mark.asyncio
    @params
    async def test_session_pool_async_turn_on(
        self, driver, settings_on, value, ydb_type, casted_result, uncasted_result
    ):
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
        self, driver, settings_off, value, ydb_type, casted_result, uncasted_result
    ):
        pool = ydb.aio.QuerySessionPool(driver, query_client_settings=settings_off)
        result = await pool.execute_with_retries(
            f"DECLARE $param as {ydb_type}; SELECT $param as value",
            {"$param": (value, getattr(ydb.PrimitiveType, ydb_type))},
        )
        assert result[0].rows[0].value == uncasted_result
        await pool.stop()
