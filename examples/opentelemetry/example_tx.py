from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

from random import randint

resource = Resource(attributes={"service.name": "ydb-python-test-tx"})

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

with ydb.Driver(endpoint=endpoint, database=database, credentials=ydb.default_credentials()) as driver:
    driver.wait(timeout=5)

    with tracer.start_as_current_span("ydb-tx-test"):
        pool = ydb.QuerySessionPool(driver)

        pool.execute_with_retries("CREATE TABLE IF NOT EXISTS example(key UInt64, value String, PRIMARY KEY (key))")

        # Commit example: insert a row inside an explicit transaction
        with tracer.start_as_current_span("commit-flow"):
            with pool.checkout() as session:
                with session.transaction() as tx:
                    rand_value = randint(10000, 100000)
                    with tx.execute(f"INSERT INTO example (key, value) VALUES ({rand_value}, 'committed')") as _:
                        pass
                    tx.commit()

        # Rollback example: insert a row and then rollback
        with tracer.start_as_current_span("rollback-flow"):
            with pool.checkout() as session:
                with session.transaction() as tx:
                    rand_value = randint(10000, 100000)
                    with tx.execute(f"INSERT INTO example (key, value) VALUES ({rand_value}, 'rolled_back')") as _:
                        pass
                    tx.rollback()

        # Verify: only the committed row should be present
        res = pool.execute_with_retries("SELECT * FROM example ORDER BY key")
        print(res.pop().rows)

        pool.stop()

provider.shutdown()
