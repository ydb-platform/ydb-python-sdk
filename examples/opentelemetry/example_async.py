import asyncio

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

from random import randint

resource = Resource(attributes={"service.name": "ydb-python-test-async"})

provider = TracerProvider(resource=resource)

provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4317/v1/traces"))
)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

import ydb
from ydb.opentelemetry import enable_tracing

enable_tracing()

endpoint = "grpc://localhost:2136"
database = "/local"


async def main():
    async with ydb.aio.Driver(endpoint=endpoint, database=database, credentials=ydb.default_credentials()) as driver:
        await driver.wait(timeout=5)

        with tracer.start_as_current_span("ydb-load-test-async"):
            async with ydb.aio.QuerySessionPool(driver) as pool:
                await pool.execute_with_retries("CREATE TABLE IF NOT EXISTS example(key UInt64, value String, PRIMARY KEY (key))")
                rand_value = randint(10000, 100000)
                val = f"value{rand_value}"
                await pool.execute_with_retries(f"INSERT INTO example (key, value) VALUES ({rand_value}, '{val}')")

                res = await pool.execute_with_retries("SELECT * FROM example")
                print(res.pop().rows)


asyncio.run(main())

provider.shutdown()
