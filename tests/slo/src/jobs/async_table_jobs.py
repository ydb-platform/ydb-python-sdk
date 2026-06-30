import asyncio
import logging
import time
from random import randint

# `aiolimiter` is a runtime dependency (see `tests/slo/requirements.txt`).
from aiolimiter import AsyncLimiter  # pyright: ignore[reportMissingImports]
from core.generator import RowGenerator
from core.metrics import OP_TYPE_READ, OP_TYPE_WRITE

import ydb
import ydb.aio

from .base import AsyncBaseJobManager
from .table_jobs import READ_QUERY_TEMPLATE, WRITE_QUERY_TEMPLATE

logger = logging.getLogger(__name__)


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
            *self._run_query_read_jobs(),
            *self._run_query_write_jobs(),
            *self._run_metric_job(),
        ]
        await asyncio.gather(*tasks)

    def _run_query_read_jobs(self):
        logger.info("Start async query read jobs")

        read_query = READ_QUERY_TEMPLATE.format(self.table_name)
        read_limiter = AsyncLimiter(max_rate=max(1, int(self.args.read_rps)), time_period=1)

        tasks = []
        for i in range(self.args.read_threads):
            tasks.append(
                asyncio.create_task(
                    self._run_query_reads(read_query, read_limiter),
                    name=f"slo_async_query_read_{i}",
                )
            )
        return tasks

    def _run_query_write_jobs(self):
        logger.info("Start async query write jobs")

        write_query = WRITE_QUERY_TEMPLATE.format(self.table_name)
        write_limiter = AsyncLimiter(max_rate=max(1, int(self.args.write_rps)), time_period=1)

        tasks = []
        for i in range(self.args.write_threads):
            tasks.append(
                asyncio.create_task(
                    self._run_query_writes(write_query, write_limiter),
                    name=f"slo_async_query_write_{i}",
                )
            )
        return tasks

    async def _run_query_reads(self, query, limiter):
        start_time = time.time()
        logger.info("Start async query read workload")

        request_settings = ydb.BaseRequestSettings().with_timeout(self.args.read_timeout / 1000)
        retry_setting = ydb.RetrySettings(
            idempotent=True,
            max_session_acquire_timeout=self.args.read_timeout / 1000,
        )

        async with ydb.aio.QuerySessionPool(self.aio_driver) as pool:
            while time.time() - start_time < self.args.time:
                params = {"$object_id": (randint(1, self.max_id), ydb.PrimitiveType.Uint64)}

                async with limiter:
                    await self._execute_query(pool, query, params, request_settings, retry_setting, (OP_TYPE_READ,))

        logger.info("Stop async query read workload")

    async def _run_query_writes(self, query, limiter):
        start_time = time.time()
        logger.info("Start async query write workload")

        request_settings = ydb.BaseRequestSettings().with_timeout(self.args.write_timeout / 1000)
        retry_setting = ydb.RetrySettings(
            idempotent=True,
            max_session_acquire_timeout=self.args.write_timeout / 1000,
        )

        row_generator = RowGenerator(self.max_id)

        async with ydb.aio.QuerySessionPool(self.aio_driver) as pool:
            while time.time() - start_time < self.args.time:
                row = row_generator.get()
                params = {
                    "$object_id": (row.object_id, ydb.PrimitiveType.Uint64),
                    "$payload_str": (row.payload_str, ydb.PrimitiveType.Utf8),
                    "$payload_double": (row.payload_double, ydb.PrimitiveType.Double),
                    "$payload_timestamp": (row.payload_timestamp, ydb.PrimitiveType.Timestamp),
                }

                async with limiter:
                    await self._execute_query(pool, query, params, request_settings, retry_setting, (OP_TYPE_WRITE,))

        logger.info("Stop async query write workload")

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
