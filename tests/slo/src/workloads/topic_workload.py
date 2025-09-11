import datetime
import ydb
from .base import BaseWorkload
from jobs.topic_jobs import TopicJobManager


class TopicWorkload(BaseWorkload):
    @property
    def name(self) -> str:
        return "topic"

    def create(self):
        self.logger.info("Creating topic: %s", self.args.topic_path)

        try:
            self.driver.topic_client.create_topic(
                path=self.args.topic_path,
                min_active_partitions=self.args.topic_min_partitions,
                max_active_partitions=self.args.topic_max_partitions,
                retention_period=datetime.timedelta(hours=self.args.topic_retention_hours),
                consumers=[self.args.topic_consumer],
            )
            self.logger.info("Topic created successfully: %s", self.args.topic_path)
            self.logger.info("Consumer created: %s", self.args.topic_consumer)

        except ydb.Error as e:
            error_msg = str(e).lower()
            if "already exists" in error_msg:
                self.logger.info("Topic already exists: %s", self.args.topic_path)

                try:
                    description = self.driver.topic_client.describe_topic(self.args.topic_path)
                    consumer_exists = any(c.name == self.args.topic_consumer for c in description.consumers)

                    if not consumer_exists:
                        self.logger.info("Adding consumer %s to existing topic", self.args.topic_consumer)
                        self.driver.topic_client.alter_topic(
                            path=self.args.topic_path, add_consumers=[self.args.topic_consumer]
                        )
                        self.logger.info("Consumer added successfully: %s", self.args.topic_consumer)
                    else:
                        self.logger.info("Consumer already exists: %s", self.args.topic_consumer)

                except Exception as alter_err:
                    self.logger.warning("Failed to add consumer: %s", alter_err)
                    raise
            elif "storage pool" in error_msg or "pq" in error_msg:
                self.logger.error("YDB instance does not support topics (PersistentQueues): %s", e)
                self.logger.error("Please use YDB instance with topic support")
                raise
            else:
                self.logger.error("Failed to create topic: %s", e)
                raise

    def run_slo(self, metrics):
        self.logger.info("Starting topic SLO tests")

        self._verify_topic_exists()

        job_manager = TopicJobManager(self.driver, self.args, metrics)
        job_manager.run_tests()

        self.logger.info("Topic SLO tests completed")

    def cleanup(self):
        self.logger.info("Cleaning up topic: %s", self.args.topic_path)

        try:
            self.driver.topic_client.drop_topic(self.args.topic_path)
            self.logger.info("Topic dropped: %s", self.args.topic_path)
        except ydb.Error as e:
            if "not found" in str(e).lower():
                self.logger.info("Topic does not exist: %s", self.args.topic_path)
            else:
                self.logger.error("Failed to drop topic: %s", e)
                raise

    def _verify_topic_exists(self):
        try:
            description = self.driver.topic_client.describe_topic(self.args.topic_path)
            self.logger.info("Topic exists: %s", self.args.topic_path)

            consumer_exists = any(c.name == self.args.topic_consumer for c in description.consumers)

            if not consumer_exists:
                self.logger.error(
                    "Consumer '%s' does not exist in topic '%s'", self.args.topic_consumer, self.args.topic_path
                )
                self.logger.error("Please create the topic with consumer first using topic-create command")
                raise RuntimeError(f"Consumer '{self.args.topic_consumer}' not found")
            else:
                self.logger.info("Consumer exists: %s", self.args.topic_consumer)

        except ydb.Error as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg:
                self.logger.error("Topic does not exist: %s", self.args.topic_path)
                self.logger.error("Please create the topic first using topic-create command")
                raise RuntimeError(f"Topic '{self.args.topic_path}' not found")
            else:
                self.logger.error("Failed to check topic: %s", e)
                raise
