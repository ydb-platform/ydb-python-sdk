"""OpenTelemetry + YDB demo: table operations, retries, and topic Reader metrics.

Uses ``disable_discovery=True`` so a single ``grpc://…`` to local YDB (e.g. ``local-ydb`` in Docker
from the host) is not replaced by internal discovery addresses.
"""

from __future__ import annotations

import asyncio
import os
import uuid

from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics._internal.export import PeriodicExportingMetricReader

import ydb
from ydb.opentelemetry import enable_metrics, enable_tracing
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def _env(name: str, default: str) -> str:
    v = os.environ.get(name)
    return v if v is not None and v != "" else default


async def _first_amount(tx) -> int:
    async with await tx.execute("SELECT amount FROM bank WHERE id = 1") as results:
        async for rs in results:
            for row in rs.rows:
                return int(row["amount"])
    raise RuntimeError("no row for id=1")


async def _bank_read_update(tx) -> None:
    count = await _first_amount(tx)
    async with await tx.execute(
        "UPDATE bank SET amount = $amt + 1 WHERE id = 1",
        {"$amt": (count, ydb.PrimitiveType.Int32)},
    ):
        pass


async def _topic_reader_metrics_demo(
    driver: ydb.aio.Driver,
    database: str,
    observation_seconds: float,
) -> None:
    topic_path = f"{database.rstrip('/')}/otel-reader-metrics-{uuid.uuid4().hex}"
    consumer = "otel-example-consumer"

    await driver.topic_client.create_topic(topic_path, consumers=[consumer])
    try:
        async with driver.topic_client.writer(topic_path, codec=ydb.TopicCodec.GZIP) as writer:
            await writer.write("OpenTelemetry topic Reader metrics")

        async with driver.topic_client.reader(
            topic_path,
            consumer,
            reader_name="otel-example-reader",
        ) as reader:
            await asyncio.wait_for(reader.wait_message(), timeout=10)
            await asyncio.sleep(observation_seconds)
            message = await asyncio.wait_for(reader.receive_message(), timeout=10)
            await reader.commit_with_ack(message)
            await asyncio.sleep(observation_seconds)
    finally:
        await driver.topic_client.drop_topic(topic_path)


async def main() -> None:
    endpoint = _env("YDB_ENDPOINT", "grpc://localhost:2136")
    database = _env("YDB_DATABASE", "/local")
    otlp_endpoint = _env("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    topic_buffer_observation_seconds = float(_env("OTEL_TOPIC_BUFFER_OBSERVATION_SECONDS", "7"))

    resource = Resource(attributes={"service.name": _env("OTEL_SERVICE_NAME", "ydb-otel-example")})
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint)))
    trace.set_tracer_provider(tracer_provider)

    tracer = trace.get_tracer(__name__)
    enable_tracing(tracer)

    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=otlp_endpoint),
        export_interval_millis=1000,
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    enable_metrics(meter_provider)

    async with ydb.aio.Driver(
        endpoint=endpoint,
        database=database,
        disable_discovery=True,
    ) as driver:
        await driver.wait(timeout=60)

        async with ydb.aio.QuerySessionPool(driver) as pool:
            with tracer.start_as_current_span("app_startup") as startup:
                startup.set_attribute("app.message", "hello")

                await pool.execute_with_retries("DROP TABLE IF EXISTS bank")
                await pool.execute_with_retries("CREATE TABLE bank (id Int32, amount Int32, PRIMARY KEY (id))")

            print("Insert row...")
            await pool.execute_with_retries("INSERT INTO bank (id, amount) VALUES (1, 0)")

            print("Preparing queries...")
            await pool.retry_tx_async(_bank_read_update)

            print("Emulation TLI...")

            async def concurrent_task(task_num: int) -> None:
                with tracer.start_as_current_span("example_tli") as act:
                    act.set_attribute("app.message", f"concurrent task {task_num}")
                    await pool.retry_tx_async(_bank_read_update)

            await asyncio.gather(*(concurrent_task(i) for i in range(10)))

            final_rows = await pool.execute_with_retries("SELECT amount FROM bank WHERE id = 1")
            amount = int(list(final_rows[0].rows)[0]["amount"])
            print(f"Final amount (after serializable retries): {amount}")

        print("Emitting topic Reader metrics...")
        await _topic_reader_metrics_demo(driver, database, topic_buffer_observation_seconds)
    print("Application will shut down in 15 seconds...")
    await asyncio.sleep(15)
    tracer_provider.shutdown()
    meter_provider.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
