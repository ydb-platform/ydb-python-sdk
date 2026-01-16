import logging
import threading
import time

from core.metrics import OP_TYPE_READ, OP_TYPE_WRITE

import ydb

from .base import BaseJobManager, SyncRateLimiter

logger = logging.getLogger(__name__)


class TopicJobManager(BaseJobManager):
    def run_tests(self):
        futures = [
            *self._run_topic_write_jobs(),
            *self._run_topic_read_jobs(),
            *self._run_metric_job(),
        ]

        for future in futures:
            future.join()

    def _run_topic_write_jobs(self):
        logger.info("Start topic write jobs")

        write_rps = int(getattr(self.args, "write_rps", 0))
        write_limiter = SyncRateLimiter(min_interval_s=0.0 if write_rps <= 0 else 1.0 / write_rps)

        futures = []
        for i in range(self.args.write_threads):
            future = threading.Thread(
                name=f"slo_topic_write_{i}",
                target=self._run_topic_writes,
                args=(
                    write_limiter,
                    i,
                ),
            )
            future.start()
            futures.append(future)

        return futures

    def _run_topic_read_jobs(self):
        logger.info("Start topic read jobs")

        read_rps = int(getattr(self.args, "read_rps", 0))
        read_limiter = SyncRateLimiter(min_interval_s=0.0 if read_rps <= 0 else 1.0 / read_rps)

        futures = []
        for i in range(self.args.read_threads):
            future = threading.Thread(
                name=f"slo_topic_read_{i}",
                target=self._run_topic_reads,
                args=(read_limiter,),
            )
            future.start()
            futures.append(future)

        return futures

    def _run_topic_writes(self, limiter, partition_id=None):
        start_time = time.time()
        logger.info("Start topic write workload")

        with self.driver.topic_client.writer(
            self.args.path,
            codec=ydb.TopicCodec.GZIP,
            partition_id=partition_id,
        ) as writer:
            logger.info("Topic writer created")

            message_count = 0
            while time.time() - start_time < self.args.time:
                with limiter:
                    message_count += 1

                    content = f"message_{message_count}_{threading.current_thread().name}".encode("utf-8")

                    if len(content) < self.args.message_size:
                        content += b"x" * (self.args.message_size - len(content))

                    message = ydb.TopicWriterMessage(data=content)

                    ts = self.metrics.start((OP_TYPE_WRITE,))
                    try:
                        writer.write_with_ack(message)
                        logger.info("Write message: %s", content)
                        self.metrics.stop((OP_TYPE_WRITE,), ts)
                    except Exception as e:
                        self.metrics.stop((OP_TYPE_WRITE,), ts, error=e)
                        logger.error("Write error: %s", e)

        logger.info("Stop topic write workload")

    def _run_topic_reads(self, limiter):
        start_time = time.time()
        logger.info("Start topic read workload")

        with self.driver.topic_client.reader(
            self.args.path,
            self.args.consumer,
        ) as reader:
            logger.info("Topic reader created")

            while time.time() - start_time < self.args.time:
                with limiter:
                    ts = self.metrics.start((OP_TYPE_READ,))
                    try:
                        msg = reader.receive_message()
                        if msg is not None:
                            logger.info("Read message: %s", msg.data.decode())
                            reader.commit_with_ack(msg)

                        self.metrics.stop((OP_TYPE_READ,), ts)
                    except Exception as e:
                        self.metrics.stop((OP_TYPE_READ,), ts, error=e)
                        logger.error("Read error: %s", e)

        logger.info("Stop topic read workload")
