import asyncio
import ydb.aio
import time
import logging
from aiolimiter import AsyncLimiter

from .base import BaseJobManager
from core.metrics import OP_TYPE_READ, OP_TYPE_WRITE

logger = logging.getLogger(__name__)


class AsyncTopicJobManager(BaseJobManager):
    def __init__(self, driver, args, metrics):
        super().__init__(driver, args, metrics)
        self.driver: ydb.aio.Driver = driver

    async def run_tests(self):
        tasks = [
            *await self._run_topic_write_jobs(),
            *await self._run_topic_read_jobs(),
            *self._run_metric_job(),
        ]

        await asyncio.gather(*tasks)

    async def _run_topic_write_jobs(self):
        logger.info("Start async topic write jobs")

        write_limiter = AsyncLimiter(max_rate=self.args.write_rps, time_period=1)

        tasks = []
        for i in range(self.args.write_threads):
            task = asyncio.create_task(self._run_topic_writes(write_limiter, i), name=f"slo_topic_write_{i}")
            tasks.append(task)

        return tasks

    async def _run_topic_read_jobs(self):
        logger.info("Start async topic read jobs")

        read_limiter = AsyncLimiter(max_rate=self.args.read_rps, time_period=1)

        tasks = []
        for i in range(self.args.read_threads):
            task = asyncio.create_task(self._run_topic_reads(read_limiter), name=f"slo_topic_read_{i}")
            tasks.append(task)

        return tasks

    async def _run_topic_writes(self, limiter, partition_id=None):
        start_time = time.time()
        logger.info("Start async topic write workload")

        async with self.driver.topic_client.writer(
            self.args.path,
            codec=ydb.TopicCodec.GZIP,
            partition_id=partition_id,
        ) as writer:
            logger.info("Async topic writer created")

            message_count = 0
            while time.time() - start_time < self.args.time:
                async with limiter:
                    message_count += 1

                    content = f"message_{message_count}_{asyncio.current_task().get_name()}".encode("utf-8")

                    if len(content) < self.args.message_size:
                        content += b"x" * (self.args.message_size - len(content))

                    message = ydb.TopicWriterMessage(data=content)

                    ts = self.metrics.start((OP_TYPE_WRITE,))
                    try:
                        await writer.write_with_ack(message)
                        logger.info("Write message: %s", content)
                        self.metrics.stop((OP_TYPE_WRITE,), ts)
                    except Exception as e:
                        self.metrics.stop((OP_TYPE_WRITE,), ts, error=e)
                        logger.error("Write error: %s", e)

        logger.info("Stop async topic write workload")

    async def _run_topic_reads(self, limiter):
        start_time = time.time()
        logger.info("Start async topic read workload")

        async with self.driver.topic_client.reader(
            self.args.path,
            self.args.consumer,
        ) as reader:
            logger.info("Async topic reader created")

            while time.time() - start_time < self.args.time:
                async with limiter:
                    ts = self.metrics.start((OP_TYPE_READ,))
                    try:
                        msg = await reader.receive_message()
                        if msg is not None:
                            logger.info("Read message: %s", msg.data.decode())
                            await reader.commit_with_ack(msg)

                        self.metrics.stop((OP_TYPE_READ,), ts)
                    except Exception as e:
                        self.metrics.stop((OP_TYPE_READ,), ts, error=e)
                        logger.error("Read error: %s", e)

        logger.info("Stop async topic read workload")

    def _run_metric_job(self):
        if not self.args.prom_pgw:
            return []

        # Create async task for metrics
        task = asyncio.create_task(self._async_metric_sender(self.args.time), name="slo_metrics_sender")
        return [task]

    async def _async_metric_sender(self, runtime):
        start_time = time.time()
        logger.info("Start push metrics (async)")

        limiter = AsyncLimiter(max_rate=10**6 // self.args.report_period, time_period=1)

        while time.time() - start_time < runtime:
            async with limiter:
                # Call sync metrics.push() in executor to avoid blocking
                await asyncio.get_event_loop().run_in_executor(None, self.metrics.push)

        logger.info("Stop push metrics (async)")
