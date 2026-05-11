"""OpenTelemetry metrics demo for YDB client-side metrics.

The example exports SDK metrics to the OpenTelemetry Collector via OTLP. The
collector exposes them for Prometheus, which is configured in compose-e2e.yaml.
"""

from __future__ import annotations

import asyncio
import os
import signal
from types import FrameType
from typing import Callable, Optional

import ydb
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from ydb.opentelemetry import enable_registry


def _env(name: str, default: str) -> str:
    value = os.environ.get(name)
    return value if value else default


def _create_stop_event() -> asyncio.Event:
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    request_stop: Callable[[], None] = stop.set
    handle_stop_signal: Callable[[int, Optional[FrameType]], None] = lambda signum, frame: stop.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, request_stop)
        except NotImplementedError:
            signal.signal(sig, handle_stop_signal)

    return stop


async def _run_workload(pool: ydb.aio.QuerySessionPool, stop: asyncio.Event) -> None:
    counter = 0
    while not stop.is_set():
        counter += 1
        result_sets = await asyncio.gather(
            *(
                pool.execute_with_retries(
                    "SELECT $session_id AS session_id, $iteration AS iteration",
                    parameters={
                        "$session_id": (i, ydb.PrimitiveType.Uint64),
                        "$iteration": (counter, ydb.PrimitiveType.Uint64),
                    },
                )
                for i in range(4)
            )
        )
        session_ids = [int(list(result[0].rows)[0]["session_id"]) for result in result_sets]
        print(f"completed concurrent queries: {session_ids}")
        await asyncio.sleep(2)


async def main() -> None:
    endpoint = _env("YDB_ENDPOINT", "grpc://localhost:2136")
    database = _env("YDB_DATABASE", "/local")
    otlp_endpoint = _env("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

    resource = Resource(attributes={"service.name": _env("OTEL_SERVICE_NAME", "ydb-client-metrics-example")})
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=otlp_endpoint),
        export_interval_millis=1000,
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    enable_registry(meter_provider)

    stop = _create_stop_event()

    try:
        async with ydb.aio.Driver(endpoint=endpoint, database=database, disable_discovery=True) as driver:
            await driver.wait(timeout=60)

            async with ydb.aio.QuerySessionPool(driver, size=4) as pool:
                print("YDB client metrics are being exported. Open Prometheus and query ydb_query_session_count.")
                await _run_workload(pool, stop)
    finally:
        meter_provider.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
