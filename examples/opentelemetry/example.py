from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

from random import randint

resource = Resource(attributes={"service.name": "ydb-python-test"})

provider = TracerProvider(resource=resource)

provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4317/v1/traces"))  # или 4317 grpc
)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

import ydb
from ydb.opentelemetry import enable_tracing

enable_tracing()

endpoint = "grpc://localhost:2136"
database = "/local"

with ydb.Driver(endpoint=endpoint, database=database, credentials=ydb.default_credentials()) as driver:
    driver.wait(timeout=5)

    with tracer.start_as_current_span("ydb-load-test"):
        with ydb.QuerySessionPool(driver) as pool:
            pool.execute_with_retries("CREATE TABLE IF NOT EXISTS example(key UInt64, value String, PRIMARY KEY (key))")
            rand_value = randint(10000, 99999)
            for i in range(rand_value, rand_value + 3):
                val = f"value{i}"
                pool.execute_with_retries(f"INSERT INTO example (key, value) VALUES ({i}, '{val}')")

            res = pool.execute_with_retries("SELECT * FROM example")
            print(res.pop().rows)

provider.shutdown()