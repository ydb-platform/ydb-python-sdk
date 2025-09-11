import time
import ydb

from .base import BaseRunner
from jobs.topic_jobs import TopicJobManager
from core.metrics import create_metrics


class TopicRunner(BaseRunner):
    @property
    def prefix(self) -> str:
        return "topic"

    def create(self, args):
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
        metrics = create_metrics(args.prom_pgw)

        self.logger.info("Starting topic SLO tests")

        job_manager = TopicJobManager(self.driver, args, metrics)
        job_manager.run_tests()

        self.logger.info("Topic SLO tests completed")

        if hasattr(metrics, "reset"):
            metrics.reset()

    def cleanup(self, args):
        self.logger.info("Cleaning up topic: %s", args.path)

        try:
            self.driver.topic_client.drop_topic(args.path)
            self.logger.info("Topic dropped: %s", args.path)
        except ydb.Error as e:
            if "does not exist" in str(e).lower():
                self.logger.info("Topic does not exist: %s", args.path)
            else:
                self.logger.error("Failed to drop topic: %s", e)
                raise
