import ydb
import logging

from os import path
from generator import batch_generator

import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from jobs import (
    run_read_jobs,
    run_write_jobs,
    run_read_jobs_query,
    run_write_jobs_query,
    run_metric_job,
)
from metrics import Metrics, SDK_SERVICE_NAME

logger = logging.getLogger(__name__)


INSERT_ROWS_TEMPLATE = """
DECLARE $items AS List<Struct<
    object_id: Uint64,
    payload_str: Utf8,
    payload_double: Double,
    payload_timestamp: Timestamp>>;
UPSERT INTO `{}`
SELECT Digest::NumericHash(object_id) AS object_hash, object_id, payload_str, payload_double, payload_timestamp
FROM AS_TABLE($items);
"""


def insert_rows(pool, prepared, data, timeout):
    def transaction(session: ydb.table.Session):
        session.transaction().execute(
            prepared,
            {"$items": data},
            commit_tx=True,
            settings=ydb.BaseRequestSettings().with_timeout(timeout),
        )

    pool.retry_operation_sync(transaction)
    logger.info("Insert %s rows", len(data))


def run_create(args, driver, tb_name):
    timeout = args.write_timeout / 1000

    def create_table(session):
        session.create_table(
            tb_name,
            ydb.TableDescription()
            .with_column(ydb.Column("object_hash", ydb.OptionalType(ydb.PrimitiveType.Uint64)))
            .with_column(ydb.Column("object_id", ydb.OptionalType(ydb.PrimitiveType.Uint64)))
            .with_column(ydb.Column("payload_str", ydb.OptionalType(ydb.PrimitiveType.Utf8)))
            .with_column(ydb.Column("payload_double", ydb.OptionalType(ydb.PrimitiveType.Double)))
            .with_column(ydb.Column("payload_timestamp", ydb.OptionalType(ydb.PrimitiveType.Timestamp)))
            .with_primary_keys("object_hash", "object_id")
            .with_uniform_partitions(args.min_partitions_count)
            .with_partitioning_settings(
                ydb.PartitioningSettings()
                .with_partitioning_by_size(ydb.FeatureFlag.ENABLED)
                .with_min_partitions_count(args.min_partitions_count)
                .with_max_partitions_count(args.max_partitions_count)
                .with_partition_size_mb(args.partition_size)
            ),
            settings=ydb.BaseRequestSettings().with_timeout(timeout),
        )

        return session.prepare(INSERT_ROWS_TEMPLATE.format(tb_name))

    with ydb.SessionPool(driver) as pool:
        prepared = pool.retry_operation_sync(create_table)

        futures = set()
        with ThreadPoolExecutor(max_workers=args.threads, thread_name_prefix="slo_create") as executor:
            for batch in batch_generator(args):
                futures.add(executor.submit(insert_rows, pool, prepared, batch, timeout))
            for f in concurrent.futures.as_completed(futures):
                f.result()


def run_slo(args, driver, tb_name):
    session = driver.table_client.session().create()
    result = session.transaction().execute(
        "SELECT MAX(`object_id`) as max_id FROM `{}`".format(tb_name),
        commit_tx=True,
    )
    max_id = result[0].rows[0]["max_id"]
    logger.info("Max ID: %s", max_id)

    metrics = Metrics(args.prom_pgw)
    if SDK_SERVICE_NAME == "sync-python-table":
        futures = (
            *run_read_jobs(args, driver, tb_name, max_id, metrics),
            *run_write_jobs(args, driver, tb_name, max_id, metrics),
            run_metric_job(args, metrics),
        )
    elif SDK_SERVICE_NAME == "sync-python-query":
        futures = (
            *run_read_jobs_query(args, driver, tb_name, max_id, metrics),
            *run_write_jobs_query(args, driver, tb_name, max_id, metrics),
            run_metric_job(args, metrics),
        )
    else:
        raise ValueError(f"Unsupported service: {SDK_SERVICE_NAME}")

    for future in futures:
        future.join()

    metrics.reset()


def run_cleanup(args, driver, tb_name):
    session = driver.table_client.session().create()
    session.drop_table(tb_name)


def run_from_args(args):
    driver_config = ydb.DriverConfig(
        args.endpoint,
        database=args.db,
        credentials=ydb.credentials_from_env_variables(),
        grpc_keep_alive_timeout=5000,
    )

    table_name = path.join(args.db, args.table_name)

    with ydb.Driver(driver_config) as driver:
        driver.wait(timeout=60)
        try:
            if args.subcommand == "create":
                run_create(args, driver, table_name)
            elif args.subcommand == "run":
                run_slo(args, driver, table_name)
            elif args.subcommand == "cleanup":
                run_cleanup(args, driver, table_name)
            else:
                raise RuntimeError(f"Unknown command {args.subcommand}")
        except BaseException:
            logger.exception("Something went wrong")
            raise
        finally:
            driver.stop(timeout=getattr(args, "shutdown_time", 10))
