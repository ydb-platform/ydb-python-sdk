import logging
import threading
import time
from contextlib import nullcontext
from random import randint
from uuid import uuid4

from core.generator import RowGenerator
from core.metrics import OP_TYPE_READ, OP_TYPE_WRITE

import ydb

from .base import BaseJobManager, SyncRateLimiter

logger = logging.getLogger(__name__)

READ_QUERY_TEMPLATE = """
DECLARE $object_id AS Uint64;
SELECT * FROM `{}` WHERE object_id = $object_id AND object_hash = Digest::NumericHash($object_id);
"""

WRITE_QUERY_TEMPLATE = """
DECLARE $object_id AS Uint64;
DECLARE $payload_str AS Utf8;
DECLARE $payload_double AS Double;
DECLARE $payload_timestamp AS Timestamp;

UPSERT INTO `{}` (
    object_id, object_hash, payload_str, payload_double, payload_timestamp
) VALUES (
    $object_id, Digest::NumericHash($object_id), $payload_str, $payload_double, $payload_timestamp
);
"""


class RequestParams:
    def __init__(
        self,
        pool,
        query,
        params,
        metrics,
        labels,
        request_settings,
        retry_settings,
        check_result_cb=None,
        on_error=None,
    ):
        self.pool = pool
        self.query = query
        self.params = params
        self.metrics = metrics
        self.labels = labels
        self.request_settings = request_settings
        self.retry_settings = retry_settings
        self.check_result_cb = check_result_cb
        self.on_error = on_error


CONTROL_SCHEMA = """
CREATE TABLE `{}` (
    object_hash Uint64, object_id Uint64, payload_str Utf8,
    payload_double Double, payload_timestamp Timestamp,
    PRIMARY KEY (object_hash, object_id)
);
"""
CONTROL_READ_QUERY = """
SELECT object_hash, object_id, payload_str, payload_double,
    CAST(payload_timestamp AS Uint64) AS payload_timestamp
FROM `{}` WHERE object_hash = 0 AND object_id = 0;
"""


def control_row(generation):
    return dict(
        object_hash=0,
        object_id=0,
        payload_str=f"generation:{generation}",
        payload_double=generation + 0.25,
        payload_timestamp=946684800000000 + generation,
    )


def check_control_result(rows, expected):
    if [dict(row) for row in rows] != [expected]:
        raise RuntimeError(f"KV control data mismatch: expected {expected!r}, got {rows!r}")


def execute_query(params: RequestParams):
    attempt = 0
    error = None

    def transaction(session):
        nonlocal attempt
        attempt += 1

        result = session.transaction().execute(
            params.query,
            parameters=params.params,
            commit_tx=True,
            settings=params.request_settings,
        )
        with result if hasattr(result, "__enter__") else nullcontext(result):
            return [row for part in result for row in part.rows]

    ts = params.metrics.start(params.labels)

    try:
        result = params.pool.retry_operation_sync(transaction, retry_settings=params.retry_settings)
        if params.check_result_cb:
            params.check_result_cb(result)
        return result
    except ydb.Error as err:
        error = err
        if params.on_error is not None:
            params.on_error(err)
        logger.exception("[labels: %s] Cannot retry error:", params.labels)
        raise
    except BaseException as err:
        error = err
        if params.on_error is not None:
            params.on_error(err)
        logger.exception("[labels: %s] Unexpected error:", params.labels)
        raise
    finally:
        params.metrics.stop(params.labels, ts, attempts=attempt, error=error)


class TableJobManager(BaseJobManager):
    def __init__(self, driver, args, metrics, table_name, max_id):
        super().__init__(driver, args, metrics)
        self.table_name = table_name
        self.max_id = max_id

        from core.metrics import WORKLOAD

        self.workload_type = WORKLOAD

    def run_tests(self):
        self._run_control_checks()
        if self.workload_type == "sync-table":
            futures = [
                *self._run_table_read_jobs(),
                *self._run_table_write_jobs(),
                *self._run_metric_job(),
            ]
        elif self.workload_type == "sync-query":
            futures = [
                *self._run_query_read_jobs(),
                *self._run_query_write_jobs(),
                *self._run_metric_job(),
            ]
        else:
            raise ValueError(f"Unsupported workload type: {self.workload_type}")

        for future in futures:
            future.join()
        self.raise_if_failed()

    def _run_control_checks(self):
        table = f"{self.table_name}_control_{uuid4().hex}"
        is_table = self.workload_type == "sync-table"
        pool_type = ydb.SessionPool if is_table else ydb.QuerySessionPool
        write = WRITE_QUERY_TEMPLATE.format(table).replace("Digest::NumericHash($object_id)", "0")
        read = CONTROL_READ_QUERY.format(table)
        failure = None
        with ydb.SessionPool(self.driver) as schema_pool:
            schema_pool.retry_operation_sync(lambda session: session.execute_scheme(CONTROL_SCHEMA.format(table)))
            try:
                if is_table:
                    write = schema_pool.retry_operation_sync(lambda session: session.prepare(write))
                    read = schema_pool.retry_operation_sync(lambda session: session.prepare(read))
                with pool_type(self.driver) as pool:
                    for generation in (1, 2):
                        expected = control_row(generation)
                        values = {f"${key}": value for key, value in expected.items() if key != "object_hash"}
                        if not is_table:
                            types = (
                                ydb.PrimitiveType.Uint64,
                                ydb.PrimitiveType.Utf8,
                                ydb.PrimitiveType.Double,
                                ydb.PrimitiveType.Timestamp,
                            )
                            values = {key: (value, kind) for (key, value), kind in zip(values.items(), types)}
                        for query, params, operation, timeout, checker in (
                            (write, values, OP_TYPE_WRITE, self.args.write_timeout, None),
                            (
                                read,
                                {},
                                OP_TYPE_READ,
                                self.args.read_timeout,
                                lambda rows: check_control_result(rows, expected),
                            ),
                        ):
                            execute_query(
                                RequestParams(
                                    pool,
                                    query,
                                    params,
                                    self.metrics,
                                    (operation,),
                                    ydb.BaseRequestSettings().with_timeout(timeout / 1000),
                                    ydb.RetrySettings(idempotent=True, max_session_acquire_timeout=timeout / 1000),
                                    check_result_cb=checker,
                                    on_error=self.record_failure,
                                )
                            )
            except BaseException as error:
                failure = error
                raise
            finally:
                try:
                    schema_pool.retry_operation_sync(lambda session: session.drop_table(table))
                except BaseException:
                    if failure is None:
                        raise
                    logger.exception("Cannot clean up control table %s", table)

    def _run_table_read_jobs(self):
        logger.info("Start table read jobs")

        session = ydb.retry_operation_sync(lambda: self.driver.table_client.session().create())
        read_query = session.prepare(READ_QUERY_TEMPLATE.format(self.table_name))

        read_rps = int(getattr(self.args, "read_rps", 0))
        read_limiter = SyncRateLimiter(min_interval_s=0.0 if read_rps <= 0 else 1.0 / read_rps)

        futures = []
        for i in range(self.args.read_threads):
            future = threading.Thread(
                name=f"slo_table_read_{i}",
                target=self._run_worker,
                args=(self._run_table_reads, read_query, read_limiter),
            )
            future.start()
            futures.append(future)

        return futures

    def _run_table_write_jobs(self):
        logger.info("Start table write jobs")

        session = ydb.retry_operation_sync(lambda: self.driver.table_client.session().create())
        write_query = session.prepare(WRITE_QUERY_TEMPLATE.format(self.table_name))

        write_rps = int(getattr(self.args, "write_rps", 0))
        write_limiter = SyncRateLimiter(min_interval_s=0.0 if write_rps <= 0 else 1.0 / write_rps)

        futures = []
        for i in range(self.args.write_threads):
            future = threading.Thread(
                name=f"slo_table_write_{i}",
                target=self._run_worker,
                args=(self._run_table_writes, write_query, write_limiter),
            )
            future.start()
            futures.append(future)

        return futures

    def _run_query_read_jobs(self):
        logger.info("Start query read jobs")

        read_query = READ_QUERY_TEMPLATE.format(self.table_name)
        read_rps = int(getattr(self.args, "read_rps", 0))
        read_limiter = SyncRateLimiter(min_interval_s=0.0 if read_rps <= 0 else 1.0 / read_rps)

        futures = []
        for i in range(self.args.read_threads):
            future = threading.Thread(
                name=f"slo_query_read_{i}",
                target=self._run_worker,
                args=(self._run_query_reads, read_query, read_limiter),
            )
            future.start()
            futures.append(future)

        return futures

    def _run_query_write_jobs(self):
        logger.info("Start query write jobs")

        write_query = WRITE_QUERY_TEMPLATE.format(self.table_name)
        write_rps = int(getattr(self.args, "write_rps", 0))
        write_limiter = SyncRateLimiter(min_interval_s=0.0 if write_rps <= 0 else 1.0 / write_rps)

        futures = []
        for i in range(self.args.write_threads):
            future = threading.Thread(
                name=f"slo_query_write_{i}",
                target=self._run_worker,
                args=(self._run_query_writes, write_query, write_limiter),
            )
            future.start()
            futures.append(future)

        return futures

    def _run_table_reads(self, query, limiter):
        start_time = time.time()
        logger.info("Start table read workload")

        request_settings = ydb.BaseRequestSettings().with_timeout(self.args.read_timeout / 1000)
        retry_setting = ydb.RetrySettings(
            idempotent=True,
            max_session_acquire_timeout=self.args.read_timeout / 1000,
        )

        with ydb.SessionPool(self.driver) as pool:
            while not self._stop.is_set() and time.time() - start_time < self.args.time:
                params = {"$object_id": randint(1, self.max_id)}

                with limiter:
                    request_params = RequestParams(
                        pool=pool,
                        query=query,
                        params=params,
                        metrics=self.metrics,
                        labels=(OP_TYPE_READ,),
                        request_settings=request_settings,
                        retry_settings=retry_setting,
                        on_error=self.record_failure,
                    )
                    execute_query(request_params)

        logger.info("Stop table read workload")

    def _run_table_writes(self, query, limiter):
        start_time = time.time()
        logger.info("Start table write workload")

        request_settings = ydb.BaseRequestSettings().with_timeout(self.args.write_timeout / 1000)
        retry_setting = ydb.RetrySettings(
            idempotent=True,
            max_session_acquire_timeout=self.args.write_timeout / 1000,
        )

        row_generator = RowGenerator(self.max_id)

        with ydb.SessionPool(self.driver) as pool:
            while not self._stop.is_set() and time.time() - start_time < self.args.time:
                row = row_generator.get()
                params = {
                    "$object_id": row.object_id,
                    "$payload_str": row.payload_str,
                    "$payload_double": row.payload_double,
                    "$payload_timestamp": row.payload_timestamp,
                }

                with limiter:
                    request_params = RequestParams(
                        pool=pool,
                        query=query,
                        params=params,
                        metrics=self.metrics,
                        labels=(OP_TYPE_WRITE,),
                        request_settings=request_settings,
                        retry_settings=retry_setting,
                        on_error=self.record_failure,
                    )
                    execute_query(request_params)

        logger.info("Stop table write workload")

    def _run_query_reads(self, query, limiter):
        start_time = time.time()
        logger.info("Start query read workload")

        request_settings = ydb.BaseRequestSettings().with_timeout(self.args.read_timeout / 1000)
        retry_setting = ydb.RetrySettings(
            idempotent=True,
            max_session_acquire_timeout=self.args.read_timeout / 1000,
        )

        with ydb.QuerySessionPool(self.driver) as pool:
            while not self._stop.is_set() and time.time() - start_time < self.args.time:
                params = {"$object_id": (randint(1, self.max_id), ydb.PrimitiveType.Uint64)}

                with limiter:
                    request_params = RequestParams(
                        pool=pool,
                        query=query,
                        params=params,
                        metrics=self.metrics,
                        labels=(OP_TYPE_READ,),
                        request_settings=request_settings,
                        retry_settings=retry_setting,
                        on_error=self.record_failure,
                    )
                    execute_query(request_params)

        logger.info("Stop query read workload")

    def _run_query_writes(self, query, limiter):
        start_time = time.time()
        logger.info("Start query write workload")

        request_settings = ydb.BaseRequestSettings().with_timeout(self.args.write_timeout / 1000)
        retry_setting = ydb.RetrySettings(
            idempotent=True,
            max_session_acquire_timeout=self.args.write_timeout / 1000,
        )

        row_generator = RowGenerator(self.max_id)

        with ydb.QuerySessionPool(self.driver) as pool:
            while not self._stop.is_set() and time.time() - start_time < self.args.time:
                row = row_generator.get()
                params = {
                    "$object_id": (row.object_id, ydb.PrimitiveType.Uint64),
                    "$payload_str": (row.payload_str, ydb.PrimitiveType.Utf8),
                    "$payload_double": (row.payload_double, ydb.PrimitiveType.Double),
                    "$payload_timestamp": (
                        row.payload_timestamp,
                        ydb.PrimitiveType.Timestamp,
                    ),
                }

                with limiter:
                    request_params = RequestParams(
                        pool=pool,
                        query=query,
                        params=params,
                        metrics=self.metrics,
                        labels=(OP_TYPE_WRITE,),
                        request_settings=request_settings,
                        retry_settings=retry_setting,
                        on_error=self.record_failure,
                    )
                    execute_query(request_params)

        logger.info("Stop query write workload")
