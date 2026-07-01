import asyncio
import logging
import time
from random import randint

from core.generator import RowGenerator
from core.metrics import OP_TYPE_READ, OP_TYPE_WRITE

import ydb
import ydb.aio

from .base import AsyncBaseJobManager
from .table_jobs import READ_QUERY_TEMPLATE, WRITE_QUERY_TEMPLATE

logger = logging.getLogger(__name__)

# Upper bound on concurrently in-flight requests per operation (open-loop
# backpressure). Steady-state in-flight self-regulates to rps * latency
# (~16 for 1000 rps @ ~16 ms); the cap only engages if latency spikes (chaos).
MAX_INFLIGHT = 256


class AsyncTableJobManager(AsyncBaseJobManager):
    def __init__(self, driver, args, metrics, table_name, max_id):
        super().__init__(driver, args, metrics)
        # Keep async driver separately to avoid type-incompatible override of BaseJobManager.driver
        self.aio_driver = driver
        self.table_name = table_name
        self.max_id = max_id

        from core.metrics import WORKLOAD

        self.workload_type = WORKLOAD

    async def run_tests(self):
        if self.workload_type != "async-query":
            raise ValueError(f"Unsupported async workload type: {self.workload_type}")

        tasks = [
            asyncio.create_task(self._run_reads(), name="slo_async_query_read"),
            asyncio.create_task(self._run_writes(), name="slo_async_query_write"),
            *self._run_metric_job(),
        ]
        await asyncio.gather(*tasks)

    async def _run_reads(self):
        # read_threads is kept as an on/off gate; concurrency is driven open-loop.
        read_rps = int(getattr(self.args, "read_rps", 0))
        if int(getattr(self.args, "read_threads", 0)) <= 0 or read_rps <= 0:
            return

        logger.info("Start async query read workload")
        query = READ_QUERY_TEMPLATE.format(self.table_name)
        request_settings = ydb.BaseRequestSettings().with_timeout(self.args.read_timeout / 1000)
        retry_setting = ydb.RetrySettings(
            idempotent=True,
            max_session_acquire_timeout=self.args.read_timeout / 1000,
        )

        def make_params():
            return {"$object_id": (randint(1, self.max_id), ydb.PrimitiveType.Uint64)}

        async with ydb.aio.QuerySessionPool(self.aio_driver, size=MAX_INFLIGHT) as pool:
            await self._generate(read_rps, pool, query, make_params, request_settings, retry_setting, (OP_TYPE_READ,))

        logger.info("Stop async query read workload")

    async def _run_writes(self):
        write_rps = int(getattr(self.args, "write_rps", 0))
        if int(getattr(self.args, "write_threads", 0)) <= 0 or write_rps <= 0:
            return

        logger.info("Start async query write workload")
        query = WRITE_QUERY_TEMPLATE.format(self.table_name)
        request_settings = ydb.BaseRequestSettings().with_timeout(self.args.write_timeout / 1000)
        retry_setting = ydb.RetrySettings(
            idempotent=True,
            max_session_acquire_timeout=self.args.write_timeout / 1000,
        )

        row_generator = RowGenerator(self.max_id)

        def make_params():
            row = row_generator.get()
            return {
                "$object_id": (row.object_id, ydb.PrimitiveType.Uint64),
                "$payload_str": (row.payload_str, ydb.PrimitiveType.Utf8),
                "$payload_double": (row.payload_double, ydb.PrimitiveType.Double),
                "$payload_timestamp": (row.payload_timestamp, ydb.PrimitiveType.Timestamp),
            }

        async with ydb.aio.QuerySessionPool(self.aio_driver, size=MAX_INFLIGHT) as pool:
            await self._generate(write_rps, pool, query, make_params, request_settings, retry_setting, (OP_TYPE_WRITE,))

        logger.info("Stop async query write workload")

    async def _generate(self, rps, pool, query, make_params, request_settings, retry_setting, labels):
        """Open-loop request generator with even pacing.

        Submissions are spaced evenly at 1/rps; each request runs as its own task,
        so achieved throughput holds at the target regardless of per-request
        latency. A semaphore bounds in-flight requests (backpressure); if the DB
        stalls, submission slows down instead of bursting to catch up.
        """
        interval = 1.0 / rps
        sem = asyncio.Semaphore(MAX_INFLIGHT)
        deadline = time.time() + self.args.time
        next_ts = time.monotonic()
        tasks = set()

        async def one_request():
            try:
                await self._execute_query(pool, query, make_params(), request_settings, retry_setting, labels)
            finally:
                sem.release()

        while time.time() < deadline:
            await sem.acquire()  # backpressure: block once MAX_INFLIGHT are in flight
            delay = next_ts - time.monotonic()
            if delay > 0:
                await asyncio.sleep(delay)
            next_ts = max(next_ts + interval, time.monotonic())  # even pacing, no burst catch-up
            task = asyncio.create_task(one_request())
            tasks.add(task)
            task.add_done_callback(tasks.discard)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_query(self, pool, query, params, request_settings, retry_setting, labels):
        attempt = 0
        error = None

        async def callee(session):
            nonlocal attempt
            attempt += 1

            result_stream = await session.execute(query, parameters=params, settings=request_settings)
            async for _ in result_stream:
                pass

        ts = self.metrics.start(labels)

        try:
            await pool.retry_operation_async(callee, retry_setting)
        except ydb.Error as err:
            error = err
            logger.exception("[labels: %s] Cannot retry error:", labels)
        except BaseException as err:
            error = err
            logger.exception("[labels: %s] Unexpected error:", labels)

        self.metrics.stop(labels, ts, attempts=attempt, error=error)
