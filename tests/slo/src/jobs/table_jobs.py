import ydb
import time
import logging
import threading
from random import randint
from ratelimiter import RateLimiter

from .base import BaseJobManager
from core.metrics import OP_TYPE_READ, OP_TYPE_WRITE
from core.generator import RowGenerator

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
    def __init__(self, pool, query, params, metrics, labels, request_settings, retry_settings, check_result_cb=None):
        self.pool = pool
        self.query = query
        self.params = params
        self.metrics = metrics
        self.labels = labels
        self.request_settings = request_settings
        self.retry_settings = retry_settings
        self.check_result_cb = check_result_cb


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
        if params.check_result_cb:
            params.check_result_cb(result)

        return result

    ts = params.metrics.start(params.labels)

    try:
        params.pool.retry_operation_sync(transaction, retry_settings=params.retry_settings)
    except ydb.Error as err:
        error = err
        logger.exception("[labels: %s] Cannot retry error:", params.labels)
    except BaseException as err:
        error = err
        logger.exception("[labels: %s] Unexpected error:", params.labels)

    params.metrics.stop(params.labels, ts, attempts=attempt, error=error)


class TableJobManager(BaseJobManager):
    def __init__(self, driver, args, metrics, table_name, max_id):
        super().__init__(driver, args, metrics)
        self.table_name = table_name
        self.max_id = max_id

        from core.metrics import WORKLOAD

        self.workload_type = WORKLOAD

    def run_tests(self):
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

    def _run_table_read_jobs(self):
        logger.info("Start table read jobs")

        session = ydb.retry_operation_sync(lambda: self.driver.table_client.session().create())
        read_query = session.prepare(READ_QUERY_TEMPLATE.format(self.table_name))

        read_limiter = RateLimiter(max_calls=self.args.read_rps, period=1)

        futures = []
        for i in range(self.args.read_threads):
            future = threading.Thread(
                name=f"slo_table_read_{i}",
                target=self._run_table_reads,
                args=(read_query, read_limiter),
            )
            future.start()
            futures.append(future)

        return futures

    def _run_table_write_jobs(self):
        logger.info("Start table write jobs")

        session = ydb.retry_operation_sync(lambda: self.driver.table_client.session().create())
        write_query = session.prepare(WRITE_QUERY_TEMPLATE.format(self.table_name))

        write_limiter = RateLimiter(max_calls=self.args.write_rps, period=1)

        futures = []
        for i in range(self.args.write_threads):
            future = threading.Thread(
                name=f"slo_table_write_{i}",
                target=self._run_table_writes,
                args=(write_query, write_limiter),
            )
            future.start()
            futures.append(future)

        return futures

    def _run_query_read_jobs(self):
        logger.info("Start query read jobs")

        read_query = READ_QUERY_TEMPLATE.format(self.table_name)
        read_limiter = RateLimiter(max_calls=self.args.read_rps, period=1)

        futures = []
        for i in range(self.args.read_threads):
            future = threading.Thread(
                name=f"slo_query_read_{i}",
                target=self._run_query_reads,
                args=(read_query, read_limiter),
            )
            future.start()
            futures.append(future)

        return futures

    def _run_query_write_jobs(self):
        logger.info("Start query write jobs")

        write_query = WRITE_QUERY_TEMPLATE.format(self.table_name)
        write_limiter = RateLimiter(max_calls=self.args.write_rps, period=1)

        futures = []
        for i in range(self.args.write_threads):
            future = threading.Thread(
                name=f"slo_query_write_{i}",
                target=self._run_query_writes,
                args=(write_query, write_limiter),
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
            while time.time() - start_time < self.args.time:
                params = {"$object_id": randint(1, self.max_id)}

                with limiter:

                    def check_result(result):
                        assert result[0].rows[0]

                    request_params = RequestParams(
                        pool=pool,
                        query=query,
                        params=params,
                        metrics=self.metrics,
                        labels=(OP_TYPE_READ,),
                        request_settings=request_settings,
                        retry_settings=retry_setting,
                        check_result_cb=check_result,
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
            while time.time() - start_time < self.args.time:
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
            while time.time() - start_time < self.args.time:
                params = {"$object_id": (randint(1, self.max_id), ydb.PrimitiveType.Uint64)}

                with limiter:

                    def check_result(result):
                        with result:
                            pass

                    request_params = RequestParams(
                        pool=pool,
                        query=query,
                        params=params,
                        metrics=self.metrics,
                        labels=(OP_TYPE_READ,),
                        request_settings=request_settings,
                        retry_settings=retry_setting,
                        check_result_cb=check_result,
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
            while time.time() - start_time < self.args.time:
                row = row_generator.get()
                params = {
                    "$object_id": (row.object_id, ydb.PrimitiveType.Uint64),
                    "$payload_str": (row.payload_str, ydb.PrimitiveType.Utf8),
                    "$payload_double": (row.payload_double, ydb.PrimitiveType.Double),
                    "$payload_timestamp": (row.payload_timestamp, ydb.PrimitiveType.Timestamp),
                }

                def check_result(result):
                    with result:
                        pass

                with limiter:
                    request_params = RequestParams(
                        pool=pool,
                        query=query,
                        params=params,
                        metrics=self.metrics,
                        labels=(OP_TYPE_WRITE,),
                        request_settings=request_settings,
                        retry_settings=retry_setting,
                        check_result_cb=check_result,
                    )
                    execute_query(request_params)

        logger.info("Stop query write workload")
