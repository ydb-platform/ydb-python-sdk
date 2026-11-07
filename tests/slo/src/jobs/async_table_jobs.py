import asyncio
import logging
import time
from random import randint
from uuid import uuid4

# `aiolimiter` is a runtime dependency (see `tests/slo/requirements.txt`).
from aiolimiter import AsyncLimiter  # pyright: ignore[reportMissingImports]
from core.generator import RowGenerator
from core.metrics import OP_TYPE_READ, OP_TYPE_WRITE

import ydb
import ydb.aio

from .base import AsyncBaseJobManager
from .table_jobs import CONTROL_READ_QUERY, CONTROL_SCHEMA, READ_QUERY_TEMPLATE, WRITE_QUERY_TEMPLATE
from .table_jobs import check_control_result, control_row

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

        await self._run_control_checks()
        tasks = [
            *self._run_query_read_jobs(),
            *self._run_query_write_jobs(),
            *self._run_metric_job(),
        ]
        await self._wait_jobs(tasks)

    async def _run_control_checks(self):
        table = f"{self.table_name}_control_{uuid4().hex}"
        write = WRITE_QUERY_TEMPLATE.format(table).replace("Digest::NumericHash($object_id)", "0")
        types = (
            ydb.PrimitiveType.Uint64,
            ydb.PrimitiveType.Utf8,
            ydb.PrimitiveType.Double,
            ydb.PrimitiveType.Timestamp,
        )
        failure = None
        async with ydb.aio.QuerySessionPool(self.aio_driver) as pool:
            await pool.execute_with_retries(CONTROL_SCHEMA.format(table))
            try:
                for generation in (1, 2):
                    expected = control_row(generation)
                    values = {f"${key}": value for key, value in expected.items() if key != "object_hash"}
                    values = {key: (value, kind) for (key, value), kind in zip(values.items(), types)}
                    for query, params, operation, timeout, checker in (
                        (write, values, OP_TYPE_WRITE, self.args.write_timeout, None),
                        (
                            CONTROL_READ_QUERY.format(table),
                            {},
                            OP_TYPE_READ,
                            self.args.read_timeout,
                            lambda rows: check_control_result(rows, expected),
                        ),
                    ):
                        await self._execute_query(
                            pool,
                            query,
                            params,
                            ydb.BaseRequestSettings().with_timeout(timeout / 1000),
                            ydb.RetrySettings(idempotent=True, max_session_acquire_timeout=timeout / 1000),
                            (operation,),
                            check_result_cb=checker,
                        )
            except BaseException as error:
                failure = error
                raise
            finally:
                try:
                    await pool.execute_with_retries(f"DROP TABLE `{table}`;")
                except BaseException:
                    if failure is None:
                        raise
                    logger.exception("Cannot clean up control table %s", table)

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

    async def _execute_query(self, pool, query, params, request_settings, retry_setting, labels, check_result_cb=None):
        attempt = 0
        error = None

        async def callee(session):
            nonlocal attempt
            attempt += 1

            result_stream = await session.execute(query, parameters=params, settings=request_settings)
            rows = []
            async for part in result_stream:
                rows.extend(part.rows)
            return rows

        ts = self.metrics.start(labels)

        try:
            rows = await pool.retry_operation_async(callee, retry_setting)
            if check_result_cb:
                check_result_cb(rows)
            return rows
        except asyncio.CancelledError:
            raise
        except ydb.Error as err:
            error = err
            self.record_failure(err)
            logger.exception("[labels: %s] Cannot retry error:", labels)
            raise
        except BaseException as err:
            error = err
            self.record_failure(err)
            logger.exception("[labels: %s] Unexpected error:", labels)
            raise
        finally:
            self.metrics.stop(labels, ts, attempts=attempt, error=error)
