"""Small OpenTelemetry load generator for the YDB Python SDK example."""

from __future__ import annotations

import asyncio
import os
import random
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator, Awaitable, Dict, Optional, Tuple

import ydb
from ydb.opentelemetry import enable_metrics


@dataclass(frozen=True)
class LoadConfig:
    endpoint: str
    database: str
    otlp_endpoint: str
    service_name: str
    run_id: str
    run_id_file: str
    ready_file: str
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
    retry_probe_interval: float
    retry_probe_failures: int
    topic_write_rps: int
    topic_read_delay: float
    topic_message_size: int
    topic_partitions: int
    topic_reader_name: str
    topic_error_probe_endpoint: str
    topic_error_probe_seconds: float


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
        run_id=_env("LOAD_TANK_RUN_ID", uuid.uuid4().hex),
        run_id_file=_env("LOAD_TANK_RUN_ID_FILE", ""),
        ready_file=_env("LOAD_TANK_READY_FILE", ""),
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
        retry_probe_interval=_env_float("LOAD_TANK_RETRY_PROBE_INTERVAL", 5.0),
        retry_probe_failures=_env_int("LOAD_TANK_RETRY_PROBE_FAILURES", 2),
        topic_write_rps=_env_int("LOAD_TANK_TOPIC_WRITE_RPS", 20),
        topic_read_delay=_env_float("LOAD_TANK_TOPIC_READ_DELAY", 0.1),
        topic_message_size=_env_int("LOAD_TANK_TOPIC_MESSAGE_SIZE", 1024),
        topic_partitions=_env_int("LOAD_TANK_TOPIC_PARTITIONS", 2),
        topic_reader_name=_env("LOAD_TANK_TOPIC_READER_NAME", "load-tank-topic-reader"),
        topic_error_probe_endpoint=_env(
            "LOAD_TANK_TOPIC_ERROR_PROBE_ENDPOINT",
            _env("YDB_ENDPOINT", "grpc://localhost:2136"),
        ),
        topic_error_probe_seconds=_env_float("LOAD_TANK_TOPIC_ERROR_PROBE_SECONDS", 0),
    )


def _publish_run_id(run_id: str, run_id_file: str, ready_file: str) -> None:
    if ready_file:
        Path(ready_file).unlink(missing_ok=True)

    if run_id_file:
        target = Path(run_id_file)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name("%s.%s.tmp" % (target.name, uuid.uuid4().hex))
        temporary.write_text("%s\n" % run_id, encoding="utf-8")
        os.replace(temporary, target)

    if ready_file:
        target = Path(ready_file)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()


async def _await_with_background(
    awaitable: Awaitable[Any],
    background_tasks: Dict[asyncio.Task, str],
) -> Any:
    operation_task = asyncio.ensure_future(awaitable)
    try:
        while True:
            done, _ = await asyncio.wait(
                {operation_task, *background_tasks},
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in done:
                if task is operation_task:
                    continue
                name = background_tasks[task]
                await _raise_background_failure(task, name)

            if operation_task in done:
                return await operation_task
    finally:
        if not operation_task.done():
            operation_task.cancel()
            await asyncio.gather(operation_task, return_exceptions=True)


async def _raise_background_failure(task: asyncio.Task, name: str) -> None:
    try:
        await task
    except asyncio.CancelledError as error:
        raise RuntimeError("%s was cancelled unexpectedly" % name) from error
    except Exception as error:
        raise RuntimeError("%s failed" % name) from error
    raise RuntimeError("%s stopped unexpectedly" % name)


async def _cancel_background_tasks(
    background_tasks: Dict[asyncio.Task, str],
    excluded_task: Optional[asyncio.Task] = None,
    raise_failures: bool = False,
) -> None:
    tasks = [(task, name) for task, name in background_tasks.items() if task is not excluded_task]
    unexpectedly_done = [(task, name) for task, name in tasks if task.done()]

    for task, _ in tasks:
        task.cancel()
    results = await asyncio.gather(*(task for task, _ in tasks), return_exceptions=True)

    if not raise_failures:
        return
    if unexpectedly_done:
        await _raise_background_failure(*unexpectedly_done[0])
    for (task, name), result in zip(tasks, results):
        if isinstance(result, BaseException) and not isinstance(result, asyncio.CancelledError):
            await _raise_background_failure(task, name)


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
        except ydb.SchemeError:
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
        except ydb.SessionPoolEmpty:
            pass

    holder_task = asyncio.create_task(holder())
    await asyncio.sleep(0)
    contenders = [asyncio.create_task(contender()) for _ in range(config.pressure_workers)]
    await asyncio.gather(holder_task, *contenders)


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


async def _retry_probe_worker(config: LoadConfig, stop: asyncio.Event) -> None:
    if config.retry_probe_interval <= 0 or config.retry_probe_failures <= 0:
        return

    retry_settings = ydb.RetrySettings(max_retries=config.retry_probe_failures)
    while not stop.is_set():
        attempt = 0

        async def transient_failure() -> None:
            nonlocal attempt
            attempt += 1
            if attempt <= config.retry_probe_failures:
                raise ydb.Aborted("load-tank retry probe")

        await ydb.retry_operation_async(transient_failure, retry_settings)
        try:
            await asyncio.wait_for(stop.wait(), timeout=config.retry_probe_interval)
        except asyncio.TimeoutError:
            pass


def _topic_payload(sequence_number: int, size: int) -> bytes:
    prefix = "%s:%s" % (sequence_number, time.time_ns())
    return prefix.encode("ascii").ljust(max(size, 1), b"x")[: max(size, 1)]


async def _topic_writer(writer, config: LoadConfig, stop: asyncio.Event) -> None:
    interval = 1.0 / config.topic_write_rps
    next_tick = time.monotonic()
    sequence_number = 0

    while not stop.is_set():
        await writer.write(_topic_payload(sequence_number, config.topic_message_size))
        sequence_number += 1
        next_tick += interval
        delay = next_tick - time.monotonic()
        if delay > 0:
            try:
                await asyncio.wait_for(stop.wait(), timeout=delay)
            except asyncio.TimeoutError:
                pass
        else:
            await asyncio.sleep(0)


async def _topic_reader(reader, config: LoadConfig, stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            message = await asyncio.wait_for(reader.receive_message(), timeout=1)
        except asyncio.TimeoutError:
            continue

        if config.topic_read_delay > 0:
            try:
                await asyncio.wait_for(stop.wait(), timeout=config.topic_read_delay)
            except asyncio.TimeoutError:
                pass
        await reader.commit_with_ack(message)


async def _topic_stream_worker(driver: ydb.aio.Driver, config: LoadConfig, stop: asyncio.Event) -> None:
    if config.topic_write_rps <= 0:
        return

    topic_path = "%s/otel-load-%s" % (config.database.rstrip("/"), uuid.uuid4().hex)
    consumer = "load-tank-consumer"
    await driver.topic_client.create_topic(
        topic_path,
        min_active_partitions=config.topic_partitions,
        partition_count_limit=config.topic_partitions,
        consumers=[consumer],
    )
    print(
        "Topic stream: path=%s writer=%s RPS reader_delay=%ss message_size=%sB partitions=%s"
        % (
            topic_path,
            config.topic_write_rps,
            config.topic_read_delay,
            config.topic_message_size,
            config.topic_partitions,
        )
    )

    try:
        async with driver.topic_client.writer(topic_path, codec=ydb.TopicCodec.GZIP) as writer:
            async with driver.topic_client.reader(
                topic_path,
                consumer,
                reader_name=config.topic_reader_name,
            ) as reader:
                writer_task = asyncio.create_task(_topic_writer(writer, config, stop))
                reader_task = asyncio.create_task(_topic_reader(reader, config, stop))
                try:
                    await asyncio.gather(writer_task, reader_task)
                finally:
                    writer_task.cancel()
                    reader_task.cancel()
                    await asyncio.gather(writer_task, reader_task, return_exceptions=True)
    finally:
        await driver.topic_client.drop_topic(topic_path)


async def _topic_error_probe(config: LoadConfig) -> None:
    if config.topic_error_probe_seconds <= 0:
        return

    topic_path = "%s/otel-unreachable" % config.database.rstrip("/")
    try:
        async with ydb.aio.Driver(
            endpoint=config.topic_error_probe_endpoint,
            database=config.database,
            disable_discovery=True,
        ) as driver:
            async with driver.topic_client.reader(
                topic_path,
                "load-tank-error-probe",
                reader_name="load-tank-topic-error-probe",
            ) as reader:
                await asyncio.wait_for(reader.wait_message(), timeout=config.topic_error_probe_seconds)
    except ydb.SchemeError as error:
        print("Topic error probe produced the expected session failure: %s" % type(error).__name__)
    except asyncio.TimeoutError as error:
        raise RuntimeError("Topic error probe did not produce SCHEME_ERROR before its timeout") from error
    else:
        raise RuntimeError("Topic error probe unexpectedly received a message")


async def main() -> None:
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics._internal.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource

    config = _load_config()

    resource = Resource(
        attributes={
            "service.name": config.service_name,
            "service.instance.id": config.run_id,
        }
    )
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=config.otlp_endpoint),
        export_interval_millis=2000,
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    enable_metrics(meter_provider)

    print(
        "=== YDB Python SDK load tank ===\n"
        "    run_id=%s total=%ss workers=%s pool_size=%s query=%r error_rps=%s\n"
        "    pressure_pool_size=%s pressure_workers=%s pressure_timeout=%ss session_churn_interval=%ss\n"
        "    retry_probe_interval=%ss retry_probe_failures=%s\n"
        "    topic_write_rps=%s topic_read_delay=%ss topic_message_size=%sB topic_partitions=%s\n"
        "    topic_error_probe=%ss at %s\n"
        "    pattern: Peak(%s rps, %ss) -> Medium(%s rps, %ss) -> "
        "Min(%s rps, %ss) -> Medium -> repeat"
        % (
            config.run_id,
            config.total_time,
            config.worker_count,
            config.pool_size,
            config.query,
            config.error_rps,
            config.pressure_pool_size,
            config.pressure_workers,
            config.pressure_acquire_timeout,
            config.session_churn_interval,
            config.retry_probe_interval,
            config.retry_probe_failures,
            config.topic_write_rps,
            config.topic_read_delay,
            config.topic_message_size,
            config.topic_partitions,
            config.topic_error_probe_seconds,
            config.topic_error_probe_endpoint,
            config.peak_rps,
            config.peak_duration,
            config.medium_rps,
            config.medium_duration,
            config.min_rps,
            config.min_duration,
        )
    )

    try:
        async with ydb.aio.Driver(
            endpoint=config.endpoint,
            database=config.database,
            disable_discovery=True,
        ) as driver:
            await driver.wait(timeout=60)
            await _topic_error_probe(config)
            _publish_run_id(config.run_id, config.run_id_file, config.ready_file)

            async with ydb.aio.QuerySessionPool(driver, size=config.pool_size, name="load-tank") as pool:
                queue: asyncio.Queue[object] = asyncio.Queue(maxsize=max(config.worker_count * 4, config.peak_rps))
                stop = asyncio.Event()
                background_tasks: Dict[asyncio.Task, str] = {}

                def start(coroutine: Awaitable[None], name: str) -> asyncio.Task:
                    task = asyncio.create_task(coroutine)
                    background_tasks[task] = name
                    return task

                for index in range(config.worker_count):
                    start(_worker(pool, queue, config.query, stop), "query worker %s" % index)
                if config.error_rps > 0:
                    start(_error_worker(pool, config, stop), "query error worker")
                if config.pressure_workers > 0 and config.pressure_pool_size > 0:
                    start(_pool_pressure_worker(driver, config, stop), "pool pressure worker")
                if config.session_churn_interval > 0:
                    start(_session_churn_worker(driver, config, stop), "session churn worker")
                if config.retry_probe_interval > 0 and config.retry_probe_failures > 0:
                    start(_retry_probe_worker(config, stop), "retry probe worker")
                topic_task = None
                if config.topic_write_rps > 0:
                    topic_task = start(_topic_stream_worker(driver, config, stop), "topic stream worker")

                completed = False
                try:
                    async for rps, label, duration in _load_steps(config):
                        print("[%s] Phase: %s (%s RPS for %ss)" % (time.strftime("%H:%M:%S"), label, rps, duration))
                        await _await_with_background(_feed_phase(queue, rps, duration), background_tasks)
                        await _await_with_background(asyncio.sleep(random.random() / 10.0), background_tasks)

                    await _await_with_background(queue.join(), background_tasks)
                    completed = True
                finally:
                    topic_was_done = topic_task is not None and topic_task.done()
                    stop.set()
                    background_failure = None
                    try:
                        await _cancel_background_tasks(
                            background_tasks,
                            excluded_task=topic_task,
                            raise_failures=completed,
                        )
                    except Exception as error:
                        if not completed:
                            raise
                        background_failure = error

                    if topic_task is not None:
                        try:
                            await asyncio.wait_for(topic_task, timeout=30)
                        except asyncio.TimeoutError:
                            topic_task.cancel()
                            await asyncio.gather(topic_task, return_exceptions=True)
                            if completed:
                                raise RuntimeError("Topic load did not stop within 30 seconds")
                        except Exception:
                            if completed:
                                raise
                        else:
                            if completed and topic_was_done:
                                raise RuntimeError("Topic stream worker stopped unexpectedly")
                    if background_failure is not None:
                        raise background_failure

        print("Waiting 10s to flush metrics...")
        await asyncio.sleep(10)
    finally:
        meter_provider.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
