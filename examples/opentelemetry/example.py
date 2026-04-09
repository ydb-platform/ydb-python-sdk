"""Minimal example: OpenTelemetry tracing for YDB Python SDK."""

import asyncio

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

import ydb
from ydb.opentelemetry import enable_tracing

resource = Resource(attributes={"service.name": "ydb-example"})
provider = TracerProvider(resource=resource)
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4317")))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)
enable_tracing(tracer)

ENDPOINT = "grpc://localhost:2136"
DATABASE = "/local"


def sync_example():
    """Sync: session execute and transaction execute + commit."""
    with ydb.Driver(endpoint=ENDPOINT, database=DATABASE) as driver:
        driver.wait(timeout=5)

        with ydb.QuerySessionPool(driver) as pool:
            with tracer.start_as_current_span("sync-example"):
                pool.execute_with_retries("SELECT 1")

                def tx_callee(session):
                    with session.transaction() as tx:
                        list(tx.execute("SELECT 1"))
                        tx.commit()

                pool.retry_operation_sync(tx_callee)


async def async_example():
    """Async: session execute and transaction execute + commit."""
    async with ydb.aio.Driver(endpoint=ENDPOINT, database=DATABASE) as driver:
        await driver.wait(timeout=5)

        async with ydb.aio.QuerySessionPool(driver) as pool:
            with tracer.start_as_current_span("async-example"):
                await pool.execute_with_retries("SELECT 1")

                async def tx_callee(session):
                    async with session.transaction() as tx:
                        result = await tx.execute("SELECT 1")
                        async for _ in result:
                            pass
                        await tx.commit()

                await pool.retry_operation_async(tx_callee)


sync_example()
asyncio.run(async_example())

provider.shutdown()
