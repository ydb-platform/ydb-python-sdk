import asyncio
import signal
from uuid import uuid4

import ydb.aio

from core.metrics import create_metrics
from jobs.rmw_jobs import AsyncRmwJobManager
from .base import BaseRunner


class RmwRunner(BaseRunner):
    @property
    def prefix(self):
        return "rmw"

    def create(self, args):
        raise ValueError("rmw-run owns its schema lifecycle")

    def cleanup(self, args):
        raise ValueError("rmw-run owns its schema lifecycle")

    def run(self, args):
        raise ValueError("RMW supports only the async Query adapter")

    async def run_async(self, args):
        metrics = create_metrics(args.otlp_endpoint)
        namespace = f"{args.db.rstrip('/')}/slo_rmw_{uuid4().hex}"
        counters, ledger = f"{namespace}_counters", f"{namespace}_ledger"
        self.logger.info("Creating RMW tables: %s, %s", counters, ledger)
        failure = None
        try:
            async with ydb.aio.QuerySessionPool(self.driver) as pool:
                owned = []
                handlers = {}
                loop = asyncio.get_running_loop()
                try:
                    for table, schema in (
                        (counters, "counter_id Uint64, value Uint64, version Uint64, PRIMARY KEY(counter_id)"),
                        (ledger, "op_id Utf8, counter_id Uint64, delta Uint64, payload Utf8, PRIMARY KEY(op_id)"),
                    ):
                        await pool.execute_with_retries(f"CREATE TABLE `{table}` ({schema});")
                        owned.append(table)
                    rows = ", ".join(f"({key}u, 0u, 0u)" for key in range(args.counter_count))
                    await pool.execute_with_retries(
                        f"UPSERT INTO `{counters}` (counter_id, value, version) VALUES {rows};"
                    )
                    manager = AsyncRmwJobManager(pool, args, metrics, counters, ledger)
                    for sig in (signal.SIGINT, signal.SIGTERM):
                        handlers[sig] = signal.getsignal(sig)
                        loop.add_signal_handler(sig, manager.stop.set)
                    self.logger.info("Starting RMW writers=%s counters=%s", args.write_threads, args.counter_count)
                    await manager.run_tests()
                    metrics.reset()
                except BaseException as exc:
                    failure = exc
                    raise
                finally:
                    for sig, handler in handlers.items():
                        loop.remove_signal_handler(sig)
                        signal.signal(sig, handler)
                    for table in reversed(owned):
                        try:
                            await pool.execute_with_retries(f"DROP TABLE `{table}`;")
                            self.logger.info("RMW table dropped: %s", table)
                        except BaseException as exc:
                            self.logger.exception("Cannot drop RMW table %s", table)
                            if failure is None:
                                failure = exc
                    if failure is not None:
                        raise failure
        except BaseException as exc:
            if failure is not None and exc is not failure:
                raise failure from exc
            raise
