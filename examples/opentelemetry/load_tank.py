"""Small OpenTelemetry load generator for the YDB Python SDK example."""

from __future__ import annotations

import asyncio
import os
import random
import time
from dataclasses import dataclass
from typing import AsyncIterator, Tuple, cast

from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics._internal.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

import ydb
from ydb.opentelemetry import enable_metrics

from metrics_views import ydb_metrics_views


@dataclass(frozen=True)
class LoadConfig:
    endpoint: str
    database: str
    otlp_endpoint: str
    service_name: str
    pool_size: int
    worker_count: int
    peak_rps: int
    medium_rps: int
    min_rps: int
    peak_duration: int
    medium_duration: int
    min_duration: int
    total_time: int
    query: str
    error_rps: int
    error_query: str
    pressure_pool_size: int
    pressure_workers: int
    pressure_hold_time: float
    pressure_acquire_timeout: float
    pressure_interval: float
    session_churn_interval: float


def _env(name: str, default: str) -> str:
    value = os.environ.get(name)
    return value if value is not None and value != "" else default


def _env_int(name: str, default: int) -> int:
    return int(_env(name, str(default)))


def _env_float(name: str, default: float) -> float:
    return float(_env(name, str(default)))


def _load_config() -> LoadConfig:
    return LoadConfig(
        endpoint=_env("YDB_ENDPOINT", "grpc://localhost:2136"),
        database=_env("YDB_DATABASE", "/local"),
        otlp_endpoint=_env("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
        service_name=_env("OTEL_SERVICE_NAME", "ydb-python-load-tank"),
        pool_size=_env_int("LOAD_TANK_POOL_SIZE", 20),
        worker_count=_env_int("LOAD_TANK_WORKERS", 40),
        peak_rps=_env_int("LOAD_TANK_PEAK_RPS", 120),
        medium_rps=_env_int("LOAD_TANK_MEDIUM_RPS", 30),
        min_rps=_env_int("LOAD_TANK_MIN_RPS", 3),
        peak_duration=_env_int("LOAD_TANK_PEAK_DURATION", 60),
        medium_duration=_env_int("LOAD_TANK_MEDIUM_DURATION", 90),
        min_duration=_env_int("LOAD_TANK_MIN_DURATION", 60),
        total_time=_env_int("LOAD_TANK_TOTAL_TIME", 300),
        query=_env("LOAD_TANK_QUERY", "SELECT 1 AS value"),
        error_rps=_env_int("LOAD_TANK_ERROR_RPS", 1),
        error_query=_env("LOAD_TANK_ERROR_QUERY", "SELECT * FROM table_that_does_not_exist_for_metrics"),
        pressure_pool_size=_env_int("LOAD_TANK_PRESSURE_POOL_SIZE", 1),
        pressure_workers=_env_int("LOAD_TANK_PRESSURE_WORKERS", 8),
        pressure_hold_time=_env_float("LOAD_TANK_PRESSURE_HOLD_TIME", 1.5),
        pressure_acquire_timeout=_env_float("LOAD_TANK_PRESSURE_ACQUIRE_TIMEOUT", 1.0),
        pressure_interval=_env_float("LOAD_TANK_PRESSURE_INTERVAL", 0.2),
        session_churn_interval=_env_float("LOAD_TANK_SESSION_CHURN_INTERVAL", 2.0),
    )


async def _load_steps(config: LoadConfig) -> AsyncIterator[Tuple[int, str, int]]:
    pattern = (
        (config.peak_rps, "Peak", config.peak_duration),
        (config.medium_rps, "Medium down", config.medium_duration),
        (config.min_rps, "Min", config.min_duration),
        (config.medium_rps, "Medium up", config.medium_duration),
    )
    deadline = time.monotonic() + config.total_time

    while time.monotonic() < deadline:
        for rps, label, duration in pattern:
            remaining = int(deadline - time.monotonic())
            if remaining <= 0:
                return
            yield rps, label, min(duration, remaining)


async def _worker(
    pool: ydb.aio.QuerySessionPool,
    queue: asyncio.Queue[object],
    query: str,
    stop: asyncio.Event,
) -> None:
    while not stop.is_set():
        try:
            await asyncio.wait_for(queue.get(), timeout=0.5)
        except asyncio.TimeoutError:
            continue

        try:
            await pool.execute_with_retries(query)
        except Exception as exc:
            print("Load operation failed: %s" % exc)
        finally:
            queue.task_done()


async def _feed_phase(queue: asyncio.Queue[object], rps: int, duration: int) -> None:
    interval = 1.0 / max(rps, 1)
    deadline = time.monotonic() + duration
    next_tick = time.monotonic()

    while time.monotonic() < deadline:
        await queue.put(object())
        next_tick += interval
        delay = next_tick - time.monotonic()
        if delay > 0:
            await asyncio.sleep(delay)
        else:
            await asyncio.sleep(0)


async def _error_worker(pool: ydb.aio.QuerySessionPool, config: LoadConfig, stop: asyncio.Event) -> None:
    if config.error_rps <= 0:
        return

    interval = 1.0 / config.error_rps
    next_tick = time.monotonic()

    while not stop.is_set():
        try:
            await pool.execute_with_retries(config.error_query)
        except Exception:
            pass

        next_tick += interval
        delay = next_tick - time.monotonic()
        if delay > 0:
            try:
                await asyncio.wait_for(stop.wait(), timeout=delay)
            except asyncio.TimeoutError:
                pass
        else:
            await asyncio.sleep(0)


async def _pressure_round(pool: ydb.aio.QuerySessionPool, config: LoadConfig) -> None:
    async def holder() -> None:
        async with pool.checkout(timeout=5):
            await asyncio.sleep(config.pressure_hold_time)

    async def contender() -> None:
        try:
            async with pool.checkout(timeout=config.pressure_acquire_timeout):
                pass
        except Exception:
            pass

    holder_task = asyncio.create_task(holder())
    await asyncio.sleep(0)
    contenders = [asyncio.create_task(contender()) for _ in range(config.pressure_workers)]
    await asyncio.gather(holder_task, *contenders, return_exceptions=True)


async def _pool_pressure_worker(driver: ydb.aio.Driver, config: LoadConfig, stop: asyncio.Event) -> None:
    if config.pressure_workers <= 0 or config.pressure_pool_size <= 0:
        return

    async with ydb.aio.QuerySessionPool(
        driver,
        size=config.pressure_pool_size,
        name="pool-pressure",
    ) as pool:
        while not stop.is_set():
            await _pressure_round(pool, config)
            try:
                await asyncio.wait_for(stop.wait(), timeout=config.pressure_interval)
            except asyncio.TimeoutError:
                pass


async def _session_churn_worker(driver: ydb.aio.Driver, config: LoadConfig, stop: asyncio.Event) -> None:
    if config.session_churn_interval <= 0:
        return

    while not stop.is_set():
        async with ydb.aio.QuerySessionPool(driver, size=1, name="session-churn") as pool:
            await pool.execute_with_retries("SELECT 1 AS value")

        try:
            await asyncio.wait_for(stop.wait(), timeout=config.session_churn_interval)
        except asyncio.TimeoutError:
            pass


async def main() -> None:
    config = _load_config()

    resource = Resource(attributes={"service.name": config.service_name})
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=config.otlp_endpoint),
        export_interval_millis=2000,
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader], views=ydb_metrics_views())
    enable_metrics(meter_provider)

    print(
        "=== YDB Python SDK load tank ===\n"
        "    total=%ss workers=%s pool_size=%s query=%r error_rps=%s\n"
        "    pressure_pool_size=%s pressure_workers=%s pressure_timeout=%ss session_churn_interval=%ss\n"
        "    pattern: Peak(%s rps, %ss) -> Medium(%s rps, %ss) -> "
        "Min(%s rps, %ss) -> Medium -> repeat"
        % (
            config.total_time,
            config.worker_count,
            config.pool_size,
            config.query,
            config.error_rps,
            config.pressure_pool_size,
            config.pressure_workers,
            config.pressure_acquire_timeout,
            config.session_churn_interval,
            config.peak_rps,
            config.peak_duration,
            config.medium_rps,
            config.medium_duration,
            config.min_rps,
            config.min_duration,
        )
    )

    async with ydb.aio.Driver(
        endpoint=config.endpoint,
        database=config.database,
        disable_discovery=True,
    ) as raw_driver:
        driver = cast(ydb.aio.Driver, raw_driver)
        await driver.wait(timeout=60)

        async with ydb.aio.QuerySessionPool(driver, size=config.pool_size, name="load-tank") as pool:
            queue: asyncio.Queue[object] = asyncio.Queue(maxsize=max(config.worker_count * 4, config.peak_rps))
            stop = asyncio.Event()
            workers = [
                asyncio.create_task(_worker(pool, queue, config.query, stop)) for _ in range(config.worker_count)
            ]
            error_task = asyncio.create_task(_error_worker(pool, config, stop))
            pressure_task = asyncio.create_task(_pool_pressure_worker(driver, config, stop))
            churn_task = asyncio.create_task(_session_churn_worker(driver, config, stop))

            try:
                async for rps, label, duration in _load_steps(config):
                    print("[%s] Phase: %s (%s RPS for %ss)" % (time.strftime("%H:%M:%S"), label, rps, duration))
                    await _feed_phase(queue, rps, duration)
                    await asyncio.sleep(random.random() / 10.0)

                await queue.join()
            finally:
                stop.set()
                for worker in workers:
                    worker.cancel()
                error_task.cancel()
                pressure_task.cancel()
                churn_task.cancel()
                await asyncio.gather(*workers, error_task, pressure_task, churn_task, return_exceptions=True)

    print("Waiting 10s to flush metrics...")
    await asyncio.sleep(10)
    meter_provider.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
