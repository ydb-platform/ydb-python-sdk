import ydb
import time
import logging
import dataclasses
from random import randint
from typing import Callable, Tuple
from ratelimiter import RateLimiter

import threading

from metrics import Metrics, JOB_WRITE_LABEL, JOB_READ_LABEL

from generator import RowGenerator


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

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class RequestParams:
    pool: ydb.SessionPool
    query: str
    params: dict
    metrics: Metrics
    labels: Tuple[str]
    request_settings: ydb.BaseRequestSettings
    retry_settings: ydb.RetrySettings
    check_result_cb: Callable = None


def execute_query(params: RequestParams):
    attempt = 0
    error = None

    def transaction(session):
        nonlocal attempt
        attempt += 1

        result = session.transaction().execute(
            params.query,
            params.params,
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


def run_reads(driver, query, max_id, metrics, limiter, runtime, timeout):
    start_time = time.time()

    logger.info("Start read workload")

    request_settings = ydb.BaseRequestSettings().with_timeout(timeout)
    retry_setting = ydb.RetrySettings(
        idempotent=True,
        max_session_acquire_timeout=timeout,
    )

    with ydb.SessionPool(driver) as pool:
        logger.info("Session pool for read requests created")

        while time.time() - start_time < runtime:
            params = {"$object_id": randint(1, max_id)}
            with limiter:

                def check_result(result):
                    assert result[0].rows[0]

                params = RequestParams(
                    pool=pool,
                    query=query,
                    params=params,
                    metrics=metrics,
                    labels=(JOB_READ_LABEL,),
                    request_settings=request_settings,
                    retry_settings=retry_setting,
                    check_result_cb=check_result,
                )
                execute_query(params)

        logger.info("Stop read workload")


def run_read_jobs(args, driver, tb_name, max_id, metrics):
    logger.info("Start read jobs")

    session = ydb.retry_operation_sync(lambda: driver.table_client.session().create())
    read_q = session.prepare(READ_QUERY_TEMPLATE.format(tb_name))
    logger.info("Prepared write query")

    read_limiter = RateLimiter(max_calls=args.read_rps, period=1)
    futures = []
    for _ in range(args.read_threads):
        future = threading.Thread(
            name="slo_run_read",
            target=run_reads,
            args=(driver, read_q, max_id, metrics, read_limiter, args.time, args.read_timeout / 1000),
        )
        future.start()
        futures.append(future)
    return futures


def run_writes(driver, query, row_generator, metrics, limiter, runtime, timeout):
    start_time = time.time()

    logger.info("Start write workload")

    request_settings = ydb.BaseRequestSettings().with_timeout(timeout)
    retry_setting = ydb.RetrySettings(
        idempotent=True,
        max_session_acquire_timeout=timeout,
    )

    with ydb.SessionPool(driver) as pool:
        logger.info("Session pool for read requests created")

        while time.time() - start_time < runtime:
            row = row_generator.get()
            params = {
                "$object_id": row.object_id,
                "$payload_str": row.payload_str,
                "$payload_double": row.payload_double,
                "$payload_timestamp": row.payload_timestamp,
            }
            with limiter:
                params = RequestParams(
                    pool=pool,
                    query=query,
                    params=params,
                    metrics=metrics,
                    labels=(JOB_WRITE_LABEL,),
                    request_settings=request_settings,
                    retry_settings=retry_setting,
                )
                execute_query(params)

        logger.info("Stop write workload")


def run_write_jobs(args, driver, tb_name, max_id, metrics):
    logger.info("Start write jobs")

    session = ydb.retry_operation_sync(lambda: driver.table_client.session().create())
    write_q = session.prepare(WRITE_QUERY_TEMPLATE.format(tb_name))
    logger.info("Prepared write query")

    write_limiter = RateLimiter(max_calls=args.write_rps, period=1)
    row_generator = RowGenerator(max_id)

    futures = []
    for _ in range(args.write_threads):
        future = threading.Thread(
            name="slo_run_write",
            target=run_writes,
            args=(driver, write_q, row_generator, metrics, write_limiter, args.time, args.write_timeout / 1000),
        )
        future.start()
        futures.append(future)
    return futures


def push_metric(limiter, runtime, metrics):
    start_time = time.time()
    logger.info("Start push metrics")

    while time.time() - start_time < runtime:
        with limiter:
            metrics.push()

    logger.info("Stop push metrics")


def run_metric_job(args, metrics):
    limiter = RateLimiter(max_calls=10**6 // args.report_period, period=1)
    future = threading.Thread(
        name="slo_run_metrics",
        target=push_metric,
        args=(limiter, args.time, metrics),
    )
    future.start()
    return future
