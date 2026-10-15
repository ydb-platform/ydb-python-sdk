import asyncio
import logging
from dataclasses import dataclass

import ydb

from core.metrics import OP_TYPE_READ, OP_TYPE_WRITE

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Operation:
    op_id: str
    counter_id: int
    delta: int

    def row(self):
        return dict(
            op_id=self.op_id,
            counter_id=self.counter_id,
            delta=self.delta,
            payload=f"{self.op_id}:{self.counter_id}:{self.delta}",
        )


async def read_rows(tx, query, settings, parameters=None):
    rows = []
    async with await tx.execute(query, parameters=parameters, settings=settings) as stream:
        async for part in stream:
            rows.extend(part.rows)
    return rows


class AsyncRmwJobManager:
    def __init__(self, pool, args, metrics, counters, ledger):
        self.pool, self.args, self.metrics = pool, args, metrics
        self.counters, self.ledger = counters, ledger
        self.stop = asyncio.Event()
        self.expected = {}
        self.failure = None
        self.diagnostic_failure = None
        self.attempts = 0
        self.replays = 0
        self.write_settings = ydb.BaseRequestSettings().with_timeout(args.write_timeout / 1000)
        self.read_settings = ydb.BaseRequestSettings().with_timeout(args.read_timeout / 1000)
        self.retry_settings = ydb.RetrySettings(idempotent=True, max_session_acquire_timeout=args.write_timeout / 1000)

    async def apply(self, operation):
        attempts = 0
        error = None
        labels = (OP_TYPE_WRITE,)
        started = self.metrics.start(labels)

        async def transaction():
            nonlocal attempts
            attempts += 1
            async with self.pool.checkout(timeout=self.retry_settings.max_session_acquire_timeout) as session:
                async with session.transaction(ydb.QuerySerializableReadWrite()) as tx:
                    rows = await read_rows(
                        tx,
                        f"SELECT op_id, counter_id, delta, payload FROM `{self.ledger}` WHERE op_id = $op_id;",
                        self.write_settings,
                        {"$op_id": (operation.op_id, ydb.PrimitiveType.Utf8)},
                    )
                    if rows:
                        if rows != [operation.row()]:
                            raise RuntimeError(f"RMW replay mismatch: {operation.op_id}: {rows!r}")
                        await tx.commit(settings=self.write_settings)
                        self.replays += 1
                        return
                    rows = await read_rows(
                        tx,
                        f"SELECT counter_id, value, version FROM `{self.counters}` WHERE counter_id = $counter_id;",
                        self.write_settings,
                        {"$counter_id": (operation.counter_id, ydb.PrimitiveType.Uint64)},
                    )
                    if len(rows) != 1 or rows[0]["counter_id"] != operation.counter_id:
                        raise RuntimeError(f"RMW counter missing: {operation.counter_id}: {rows!r}")
                    values = dict(
                        operation.row(), value=rows[0]["value"] + operation.delta, version=rows[0]["version"] + 1
                    )
                    parameters = {
                        f"${key}": (
                            value,
                            ydb.PrimitiveType.Utf8 if isinstance(value, str) else ydb.PrimitiveType.Uint64,
                        )
                        for key, value in values.items()
                    }
                    await read_rows(
                        tx,
                        f"UPSERT INTO `{self.counters}` (counter_id, value, version) VALUES ($counter_id, $value, $version);"
                        f" INSERT INTO `{self.ledger}` (op_id, counter_id, delta, payload)"
                        " VALUES ($op_id, $counter_id, $delta, $payload);",
                        self.write_settings,
                        parameters,
                    )
                    await tx.commit(settings=self.write_settings)

        try:
            await ydb.retry_operation_async(transaction, self.retry_settings)
        except BaseException as exc:
            error = exc
            if self.failure is None:
                self.failure = exc
            self.stop.set()
            raise
        finally:
            self.attempts += attempts
            self._finish_metric(labels, started, attempts, error)

    def _finish_metric(self, labels, started, attempts, error):
        try:
            self.metrics.stop(labels, started, attempts=attempts, error=error)
        except BaseException:
            if error is None:
                raise
            logger.exception("Cannot finish RMW metrics after operation failure")

    async def validate(self):
        async def snapshot(session):
            async with session.transaction(ydb.QuerySerializableReadWrite()) as tx:
                counters = await read_rows(
                    tx, f"SELECT counter_id, value, version FROM `{self.counters}`;", self.read_settings
                )
                ledger = await read_rows(
                    tx, f"SELECT op_id, counter_id, delta, payload FROM `{self.ledger}`;", self.read_settings
                )
                await tx.commit(settings=self.read_settings)
                return counters, ledger

        error = None
        started = self.metrics.start((OP_TYPE_READ,))
        attempts = 0

        retry_settings = ydb.RetrySettings(idempotent=True, max_session_acquire_timeout=self.args.read_timeout / 1000)

        async def read():
            nonlocal attempts
            attempts += 1
            async with self.pool.checkout(timeout=retry_settings.max_session_acquire_timeout) as session:
                return await snapshot(session)

        try:
            counters, ledger = await ydb.retry_operation_async(read, retry_settings)
            observed = {}
            for row in ledger:
                op_id = row["op_id"]
                if op_id in observed:
                    raise RuntimeError(f"RMW duplicate ledger ID: {op_id}")
                observed[op_id] = dict(row)
            expected = {key: operation.row() for key, operation in self.expected.items()}
            if observed != expected:
                raise RuntimeError(
                    f"RMW ledger mismatch: expected {len(expected)} exact operations, observed {len(observed)}"
                )
            totals = {key: dict(counter_id=key, value=0, version=0) for key in range(self.args.counter_count)}
            for operation in self.expected.values():
                totals[operation.counter_id]["value"] += operation.delta
                totals[operation.counter_id]["version"] += 1
            if len(counters) != len(totals) or {row["counter_id"]: dict(row) for row in counters} != totals:
                raise RuntimeError(f"RMW counter mismatch: expected {totals!r}, observed {counters!r}")
            logger.info(
                "Validated RMW counters=%s operations=%s attempts=%s replays=%s tables=%s,%s",
                len(totals),
                len(expected),
                self.attempts,
                self.replays,
                self.counters,
                self.ledger,
            )
        except BaseException as exc:
            error = exc
            raise
        finally:
            self._finish_metric((OP_TYPE_READ,), started, attempts, error)

    async def _apply_operation(self, operation):
        try:
            await self.apply(operation)
        except BaseException as exc:
            if self.diagnostic_failure is None:
                self.diagnostic_failure = exc
            self.stop.set()

    async def _metrics_sender(self):
        try:
            while not self.stop.is_set():
                try:
                    await asyncio.wait_for(self.stop.wait(), self.args.report_period / 1000)
                except asyncio.TimeoutError:
                    await asyncio.get_running_loop().run_in_executor(None, self.metrics.push)
        except BaseException as exc:
            self.stop.set()
            return exc
        return None

    async def run_tests(self):
        timer = asyncio.get_running_loop().call_later(self.args.time, self.stop.set)
        sender = asyncio.create_task(self._metrics_sender())
        sequence = 0
        try:
            while not self.stop.is_set():
                sequence += 1
                operations = [
                    Operation(f"{writer}:{sequence}", (sequence - 1) % self.args.counter_count, 1 + writer % 3)
                    for writer in range(self.args.write_threads)
                ]
                self.expected.update((operation.op_id, operation) for operation in operations)
                # Bound admission to one contended round; never cancel an admitted SDK call.
                await asyncio.gather(*(self._apply_operation(operation) for operation in operations))
        finally:
            self.stop.set()
            timer.cancel()
            metric_failure = await sender
        try:
            await self.validate()
        except BaseException:
            if self.failure is None and self.diagnostic_failure is None and metric_failure is None:
                raise
            logger.exception("RMW final validation failed after workload failure")
        if self.failure is not None:
            raise self.failure
        if self.diagnostic_failure is not None:
            raise self.diagnostic_failure
        if metric_failure is not None:
            raise metric_failure
        self.metrics.push()
