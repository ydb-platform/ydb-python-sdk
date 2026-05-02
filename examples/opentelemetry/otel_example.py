"""OpenTelemetry + YDB demo: bank table and concurrent transactions (TLI-style workload).

Uses ``disable_discovery=True`` so a single ``grpc://…`` to local YDB (e.g. ``local-ydb`` in Docker
from the host) is not replaced by internal discovery addresses.
"""

from __future__ import annotations

import asyncio
import os
import socket
import sys
from pathlib import Path

# For ``python otel_example.py`` in this tree without an installed ``ydb`` package.
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

import ydb  # noqa: E402
from ydb import _utilities as _yutil  # noqa: E402
from opentelemetry import trace  # noqa: E402
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter  # noqa: E402
from opentelemetry.sdk.resources import Resource  # noqa: E402
from opentelemetry.sdk.trace import TracerProvider  # noqa: E402
from opentelemetry.sdk.trace.export import BatchSpanProcessor  # noqa: E402
from ydb.opentelemetry import enable_tracing  # noqa: E402


def _env(name: str, default: str) -> str:
    v = os.environ.get(name)
    return v if v is not None and v != "" else default


def _assert_tcp_reachable_for_endpoint(endpoint: str) -> None:
    """Before ``Driver`` starts: fail fast if nothing listens (clearer than ``driver.wait`` timeout)."""
    bare = _yutil.wrap_endpoint(endpoint)
    if bare.count(":") < 1:
        return
    host, _, port_s = bare.rpartition(":")
    if not port_s or not host:
        return
    try:
        port = int(port_s)
    except ValueError:
        return
    try:
        with socket.create_connection((host, port), timeout=3.0):
            pass
    except OSError as e:
        raise RuntimeError(
            f"Nothing accepts TCP on {host}:{port} — start YDB first, e.g. from the repository root: "
            f"docker compose up -d   (then the script at grpc://{host}:{port} can connect).  Original error: {e!s}"
        ) from e


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


async def main() -> None:
    endpoint = _env("YDB_ENDPOINT", "grpc://localhost:2136")
    database = _env("YDB_DATABASE", "/local")
    otlp_endpoint = _env("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

    resource = Resource(attributes={"service.name": _env("OTEL_SERVICE_NAME", "ydb-otel-example")})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint)))
    trace.set_tracer_provider(provider)

    tracer = trace.get_tracer(__name__)
    enable_tracing(tracer)

    _assert_tcp_reachable_for_endpoint(endpoint)

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

    provider.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
