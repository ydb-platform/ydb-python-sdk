import ydb
from os import path
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from .base import BaseWorkload
from jobs.table_jobs import TableJobManager
from core.generator import batch_generator


class TableWorkload(BaseWorkload):
    @property
    def name(self) -> str:
        return "table"

    def create(self):
        table_name = path.join(self.args.db, self.args.table_name)
        timeout = self.args.write_timeout / 1000

        self.logger.info("Creating table: %s", table_name)

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

        def create_table(session):
            session.create_table(
                table_name,
                ydb.TableDescription()
                .with_column(ydb.Column("object_hash", ydb.OptionalType(ydb.PrimitiveType.Uint64)))
                .with_column(ydb.Column("object_id", ydb.OptionalType(ydb.PrimitiveType.Uint64)))
                .with_column(ydb.Column("payload_str", ydb.OptionalType(ydb.PrimitiveType.Utf8)))
                .with_column(ydb.Column("payload_double", ydb.OptionalType(ydb.PrimitiveType.Double)))
                .with_column(ydb.Column("payload_timestamp", ydb.OptionalType(ydb.PrimitiveType.Timestamp)))
                .with_primary_keys("object_hash", "object_id")
                .with_uniform_partitions(self.args.min_partitions_count)
                .with_partitioning_settings(
                    ydb.PartitioningSettings()
                    .with_partitioning_by_size(ydb.FeatureFlag.ENABLED)
                    .with_min_partitions_count(self.args.min_partitions_count)
                    .with_max_partitions_count(self.args.max_partitions_count)
                    .with_partition_size_mb(self.args.partition_size)
                ),
                settings=ydb.BaseRequestSettings().with_timeout(timeout),
            )

            return session.prepare(INSERT_ROWS_TEMPLATE.format(table_name))

        def insert_rows(pool, prepared, data, timeout):
            def transaction(session: ydb.table.Session):
                session.transaction().execute(
                    prepared,
                    {"$items": data},
                    commit_tx=True,
                    settings=ydb.BaseRequestSettings().with_timeout(timeout),
                )

            pool.retry_operation_sync(transaction)
            self.logger.info("Insert %s rows", len(data))

        with ydb.SessionPool(self.driver) as pool:
            prepared = pool.retry_operation_sync(create_table)
            self.logger.info("Table created: %s", table_name)

            self.logger.info("Filling table with initial data")
            futures = set()
            with ThreadPoolExecutor(max_workers=self.args.threads, thread_name_prefix="slo_create") as executor:
                for batch in batch_generator(self.args):
                    futures.add(executor.submit(insert_rows, pool, prepared, batch, timeout))
                for f in concurrent.futures.as_completed(futures):
                    f.result()

            self.logger.info("Table creation completed")

    def run_slo(self, metrics):
        self.logger.info("Starting table SLO tests")

        table_name = path.join(self.args.db, self.args.table_name)

        session = self.driver.table_client.session().create()
        result = session.transaction().execute(
            "SELECT MAX(`object_id`) as max_id FROM `{}`".format(table_name),
            commit_tx=True,
        )
        max_id = result[0].rows[0]["max_id"]
        self.logger.info("Max ID: %s", max_id)

        job_manager = TableJobManager(self.driver, self.args, metrics, table_name, max_id)
        job_manager.run_tests()

        self.logger.info("Table SLO tests completed")

    def cleanup(self):
        table_name = path.join(self.args.db, self.args.table_name)
        self.logger.info("Cleaning up table: %s", table_name)

        session = self.driver.table_client.session().create()
        session.drop_table(table_name)

        self.logger.info("Table dropped: %s", table_name)
