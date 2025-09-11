import ydb
import time
import logging
import threading
from ratelimiter import RateLimiter

from .base import BaseJobManager
from core.metrics import OP_TYPE_TOPIC_READ, OP_TYPE_TOPIC_WRITE

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

        write_limiter = RateLimiter(max_calls=self.args.topic_write_rps, period=1)

        futures = []
        for i in range(self.args.topic_write_threads):
            future = threading.Thread(
                name=f"slo_topic_write_{i}",
                target=self._run_topic_writes,
                args=(write_limiter,),
            )
            future.start()
            futures.append(future)

        return futures

    def _run_topic_read_jobs(self):
        logger.info("Start topic read jobs")

        read_limiter = RateLimiter(max_calls=self.args.topic_read_rps, period=1)

        futures = []
        for i in range(self.args.topic_read_threads):
            future = threading.Thread(
                name=f"slo_topic_read_{i}",
                target=self._run_topic_reads,
                args=(read_limiter,),
            )
            future.start()
            futures.append(future)

        return futures

    def _run_topic_writes(self, limiter):
        start_time = time.time()
        logger.info("Start topic write workload")

        writer = self.driver.topic_client.writer(self.args.topic_path, codec=ydb.TopicCodec.GZIP)
        logger.info("Topic writer created")

        try:
            write_session = writer.__enter__()

            message_count = 0
            while time.time() - start_time < self.args.time:
                with limiter:
                    message_count += 1

                    content = f"message_{message_count}_{threading.current_thread().name}".encode("utf-8")

                    if len(content) < self.args.topic_message_size:
                        content += b"x" * (self.args.topic_message_size - len(content))

                    message = ydb.TopicWriterMessage(data=content)

                    ts = self.metrics.start((OP_TYPE_TOPIC_WRITE,))
                    try:
                        write_session.write(message)
                        self.metrics.stop((OP_TYPE_TOPIC_WRITE,), ts)
                    except Exception as e:
                        self.metrics.stop((OP_TYPE_TOPIC_WRITE,), ts, error=e)
                        logger.error("Write error: %s", e)

        finally:
            writer.__exit__(None, None, None)

        logger.info("Stop topic write workload")

    def _run_topic_reads(self, limiter):
        start_time = time.time()
        logger.info("Start topic read workload")

        reader = self.driver.topic_client.reader(self.args.topic_consumer, self.args.topic_path)
        logger.info("Topic reader created")

        try:
            read_session = reader.__enter__()

            while time.time() - start_time < self.args.time:
                with limiter:
                    ts = self.metrics.start((OP_TYPE_TOPIC_READ,))
                    try:
                        batch = read_session.receive_message(timeout=self.args.topic_read_timeout / 1000)
                        if batch is not None:
                            read_session.commit_offset(batch.batches[-1].message_offset_end)
                        self.metrics.stop((OP_TYPE_TOPIC_READ,), ts)
                    except Exception as e:
                        self.metrics.stop((OP_TYPE_TOPIC_READ,), ts, error=e)
                        logger.debug("Read timeout or error: %s", e)

        finally:
            reader.__exit__(None, None, None)

        logger.info("Stop topic read workload")
