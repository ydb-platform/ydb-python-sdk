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
from topic_jobs import (
    run_topic_write_jobs,
    run_topic_read_jobs,
    create_topic,
    cleanup_topic,
)
from metrics import Metrics, WORKLOAD

logger = logging.getLogger(__name__)


class DummyMetrics:
    """Заглушка для метрик, когда Prometheus отключен"""

    def start(self, labels):
        return 0

    def stop(self, labels, start_time, attempts=1, error=None):
        pass


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
    if WORKLOAD == "sync-table":
        futures = (
            *run_read_jobs(args, driver, tb_name, max_id, metrics),
            *run_write_jobs(args, driver, tb_name, max_id, metrics),
            run_metric_job(args, metrics),
        )
    elif WORKLOAD == "sync-query":
        futures = (
            *run_read_jobs_query(args, driver, tb_name, max_id, metrics),
            *run_write_jobs_query(args, driver, tb_name, max_id, metrics),
            run_metric_job(args, metrics),
        )
    else:
        raise ValueError(f"Unsupported service: {WORKLOAD}")

    for future in futures:
        future.join()

    metrics.reset()


def run_cleanup(args, driver, tb_name):
    session = driver.table_client.session().create()
    session.drop_table(tb_name)


def run_topic_create(args, driver):
    """
    Создает топик и консьюмера для SLO тестов.

    :param args: аргументы командной строки
    :param driver: YDB driver
    """
    logger.info("Creating topic for SLO tests")

    create_topic(
        driver,
        args.topic_path,
        args.topic_consumer,
        min_partitions=args.topic_min_partitions,
        max_partitions=args.topic_max_partitions,
        retention_hours=args.topic_retention_hours
    )

    logger.info("Topic creation completed")


def run_topic_cleanup(args, driver):
    """
    Удаляет топик после SLO тестов.

    :param args: аргументы командной строки
    :param driver: YDB driver
    """
    logger.info("Cleaning up topic")

    cleanup_topic(driver, args.topic_path)

    logger.info("Topic cleanup completed")


def run_topic_slo(args, driver):
    """
    Запускает SLO тесты для топиков.
    Ожидает, что топик уже создан командой topic-create.

    :param args: аргументы командной строки
    :param driver: YDB driver
    """
    logger.info("Starting topic SLO test")

    # Проверяем, что топик существует
    try:
        description = driver.topic_client.describe_topic(args.topic_path)
        logger.info("Topic exists: %s", args.topic_path)

        # Проверяем, есть ли консьюмер
        consumer_exists = any(c.name == args.topic_consumer for c in description.consumers)

        if not consumer_exists:
            logger.error("Consumer '%s' does not exist in topic '%s'", args.topic_consumer, args.topic_path)
            logger.error("Please create the topic with consumer first using topic-create command")
            raise RuntimeError(f"Consumer '{args.topic_consumer}' not found")
        else:
            logger.info("Consumer exists: %s", args.topic_consumer)

    except ydb.Error as e:
        error_msg = str(e).lower()
        if "does not exist" in error_msg:
            logger.error("Topic does not exist: %s", args.topic_path)
            logger.error("Please create the topic first using topic-create command")
            raise RuntimeError(f"Topic '{args.topic_path}' not found")
        else:
            logger.error("Failed to check topic: %s", e)
            raise

    # Создаем объект для сбора метрик (если Prometheus включен)
    if args.prom_pgw:
        metrics = Metrics(args.prom_pgw)
        metric_futures = (run_metric_job(args, metrics),)
    else:
        logger.info("Prometheus disabled, creating dummy metrics")
        metrics = DummyMetrics()
        metric_futures = ()

    # Запускаем задачи для записи и чтения
    futures = (
        *run_topic_write_jobs(args, driver, args.topic_path, metrics),
        *run_topic_read_jobs(args, driver, args.topic_path, args.topic_consumer, metrics),
        *metric_futures,
    )

    # Ждем завершения всех задач
    for future in futures:
        future.join()

    # Сбрасываем метрики (если они реальные)
    if hasattr(metrics, 'reset'):
        metrics.reset()

    logger.info("Topic SLO test completed")


def run_from_args(args):
    driver_config = ydb.DriverConfig(
        args.endpoint,
        database=args.db,
        grpc_keep_alive_timeout=5000,
    )

    table_name = path.join(args.db, args.table_name)

    with ydb.Driver(driver_config) as driver:
        driver.wait(timeout=300)
        try:
            if args.subcommand == "table-create":
                run_create(args, driver, table_name)
            elif args.subcommand == "table-run":
                run_slo(args, driver, table_name)
            elif args.subcommand == "table-cleanup":
                run_cleanup(args, driver, table_name)
            elif args.subcommand == "topic-create":
                run_topic_create(args, driver)
            elif args.subcommand == "topic-run":
                run_topic_slo(args, driver)
            elif args.subcommand == "topic-cleanup":
                run_topic_cleanup(args, driver)
            else:
                raise RuntimeError(f"Unknown command {args.subcommand}")
        except BaseException:
            logger.exception("Something went wrong")
            raise
        finally:
            driver.stop(timeout=getattr(args, "shutdown_time", 10))
