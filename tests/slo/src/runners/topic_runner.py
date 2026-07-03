import time
from os import path

from core.metrics import WORKLOAD, create_metrics
from jobs.async_topic_jobs import AsyncTopicJobManager
from jobs.async_topic_tx_jobs import AsyncTopicTxJobManager
from jobs.topic_jobs import TopicJobManager
from jobs.topic_tx_jobs import TopicTxJobManager

import ydb
import ydb.aio

from .base import BaseRunner

SINK_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS `{}` (
    writer_id Uint64,
    seqno Uint64,
    write_ts_ns Uint64,
    received_at Timestamp,
    PRIMARY KEY (writer_id, seqno)
);
"""

HOT_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS `{}` (
    id Uint64,
    val Uint64,
    PRIMARY KEY (id)
);
"""


class TopicRunner(BaseRunner):
    @property
    def prefix(self) -> str:
        return "topic"

    @staticmethod
    def _is_tx_workload() -> bool:
        return str(WORKLOAD).endswith("topic-tx")

    @staticmethod
    def _tx_table_names(args):
        return path.join(args.db, args.sink_table), path.join(args.db, args.hot_table)

    def create(self, args):
        self._create_topic(args)
        if self._is_tx_workload():
            self._create_tx_tables(args)

    def _create_tx_tables(self, args):
        sink_table, hot_table = self._tx_table_names(args)
        hot_keys = max(1, int(getattr(args, "tli_hot_keys", 4)))
        self.logger.info("Creating tx tables: sink=%s hot=%s (hot_keys=%d)", sink_table, hot_table, hot_keys)

        assert self.driver is not None, "Driver is not initialized. Call set_driver() before create()."
        with ydb.QuerySessionPool(self.driver) as pool:
            pool.execute_with_retries(SINK_TABLE_DDL.format(sink_table))
            pool.execute_with_retries(HOT_TABLE_DDL.format(hot_table))
            # Seed the hot rows so the producer/consumer read-modify-write always
            # hits an existing row (a strong, deterministic optimistic lock).
            for i in range(hot_keys):
                pool.execute_with_retries(
                    "DECLARE $id AS Uint64; UPSERT INTO `{}` (id, val) VALUES ($id, 0);".format(hot_table),
                    {"$id": (i, ydb.PrimitiveType.Uint64)},
                )
        self.logger.info("Tx tables ready")

    def _create_topic(self, args):
        assert self.driver is not None, "Driver is not initialized. Call set_driver() before create()."
        retry_no = 0
        while retry_no < 3:
            self.logger.info("Creating topic: %s (retry no: %d)", args.path, retry_no)

            try:
                self.driver.topic_client.create_topic(
                    path=args.path,
                    min_active_partitions=args.partitions_count,
                    max_active_partitions=args.partitions_count,
                    consumers=[args.consumer],
                )

                self.logger.info("Topic created successfully: %s", args.path)
                self.logger.info("Consumer created: %s", args.consumer)
                return

            except ydb.Error as e:
                error_msg = str(e).lower()
                if "already exists" in error_msg:
                    self.logger.info("Topic already exists: %s", args.path)

                    try:
                        description = self.driver.topic_client.describe_topic(args.path)
                        consumer_exists = any(c.name == args.consumer for c in description.consumers)

                        if not consumer_exists:
                            self.logger.info("Adding consumer %s to existing topic", args.consumer)
                            self.driver.topic_client.alter_topic(path=args.path, add_consumers=[args.consumer])
                            self.logger.info("Consumer added successfully: %s", args.consumer)
                            return
                        else:
                            self.logger.info("Consumer already exists: %s", args.consumer)
                            return

                    except Exception as alter_err:
                        self.logger.warning("Failed to add consumer: %s", alter_err)
                        raise
                elif "storage pool" in error_msg or "pq" in error_msg:
                    self.logger.error("YDB instance does not support topics (PersistentQueues): %s", e)
                    self.logger.error("Please use YDB instance with topic support")
                    raise
                elif isinstance(e, ydb.Unavailable):
                    self.logger.info("YDB instance is not ready, retrying in 5 seconds...")
                    time.sleep(5)
                    retry_no += 1
                else:
                    self.logger.error("Failed to create topic: %s", e)
                    raise

        raise RuntimeError("Failed to create topic")

    def run(self, args):
        assert self.driver is not None, "Driver is not initialized. Call set_driver() before run()."
        metrics = create_metrics(args.otlp_endpoint)

        self.logger.info("Starting topic SLO tests")

        if self._is_tx_workload():
            sink_table, hot_table = self._tx_table_names(args)
            job_manager = TopicTxJobManager(self.driver, args, metrics, sink_table, hot_table)
        else:
            job_manager = TopicJobManager(self.driver, args, metrics)
        job_manager.run_tests()

        self.logger.info("Topic SLO tests completed")

        if hasattr(metrics, "reset"):
            metrics.reset()

    async def run_async(self, args):
        """Async version of topic SLO tests using ydb.aio.Driver"""
        assert self.driver is not None, "Driver is not initialized. Call set_driver() before run_async()."
        metrics = create_metrics(args.otlp_endpoint)

        self.logger.info("Starting async topic SLO tests")

        # Use async driver for topic operations
        if self._is_tx_workload():
            sink_table, hot_table = self._tx_table_names(args)
            job_manager = AsyncTopicTxJobManager(self.driver, args, metrics, sink_table, hot_table)
        else:
            job_manager = AsyncTopicJobManager(self.driver, args, metrics)
        await job_manager.run_tests()

        self.logger.info("Async topic SLO tests completed")

        if hasattr(metrics, "reset"):
            metrics.reset()

    def cleanup(self, args):
        self.logger.info("Cleaning up topic: %s", args.path)

        assert self.driver is not None, "Driver is not initialized. Call set_driver() before cleanup()."
        try:
            self.driver.topic_client.drop_topic(args.path)
            self.logger.info("Topic dropped: %s", args.path)
        except ydb.Error as e:
            if "does not exist" in str(e).lower():
                self.logger.info("Topic does not exist: %s", args.path)
            else:
                self.logger.error("Failed to drop topic: %s", e)
                raise

        if self._is_tx_workload():
            sink_table, hot_table = self._tx_table_names(args)
            with ydb.QuerySessionPool(self.driver) as pool:
                for table in (sink_table, hot_table):
                    try:
                        pool.execute_with_retries("DROP TABLE `{}`;".format(table))
                        self.logger.info("Table dropped: %s", table)
                    except ydb.Error as e:
                        self.logger.info("Table not dropped (%s): %s", table, e)
