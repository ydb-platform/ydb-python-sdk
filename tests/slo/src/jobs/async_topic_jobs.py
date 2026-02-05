import asyncio
import logging
import time
from typing import Optional

# `aiolimiter` is a runtime dependency (see `tests/slo/requirements.txt`).
from aiolimiter import AsyncLimiter  # pyright: ignore[reportMissingImports]
from core.metrics import OP_TYPE_READ, OP_TYPE_WRITE

import ydb.aio

from .base import BaseJobManager

logger = logging.getLogger(__name__)


class AsyncTopicJobManager(BaseJobManager):
    def __init__(self, driver, args, metrics):
        super().__init__(driver, args, metrics)
        # Keep async driver separately to avoid type-incompatible override of BaseJobManager.driver
        self.aio_driver = driver

    async def run_tests(self):
        tasks = [
            *await self._run_topic_write_jobs(),
            *await self._run_topic_read_jobs(),
            *self._run_metric_job(),
        ]
        await asyncio.gather(*tasks)

    async def _run_topic_write_jobs(self):
        logger.info("Start async topic write jobs")

        tasks = []
        write_limiter = AsyncLimiter(max_rate=self.args.write_rps, time_period=1)

        for i in range(self.args.write_threads):
            task = asyncio.create_task(
                self._run_topic_writes(write_limiter, i),
                name=f"slo_topic_write_{i}",
            )
            tasks.append(task)

        return tasks

    async def _run_topic_read_jobs(self):
        logger.info("Start async topic read jobs")

        tasks = []
        read_limiter = AsyncLimiter(max_rate=self.args.read_rps, time_period=1)

        for i in range(self.args.read_threads):
            task = asyncio.create_task(
                self._run_topic_reads(read_limiter),
                name=f"slo_topic_read_{i}",
            )
            tasks.append(task)

        return tasks

    async def _run_topic_writes(self, limiter: AsyncLimiter, partition_id: Optional[int] = None):
        start_time = time.time()
        logger.info("Start async topic write workload")

        async with self.aio_driver.topic_client.writer(
            self.args.path,
            codec=getattr(ydb, "PublicCodec", ydb.TopicCodec).GZIP,
            partition_id=partition_id,
        ) as writer:
            logger.info("Async topic writer created")

            message_count = 0
            while time.time() - start_time < self.args.time:
                async with limiter:
                    message_count += 1

                    task = asyncio.current_task()
                    task_name = task.get_name() if task is not None else "unknown_task"
                    content = f"message_{message_count}_{task_name}".encode("utf-8")
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

    async def _run_topic_reads(self, limiter: AsyncLimiter):
        start_time = time.time()
        logger.info("Start async topic read workload")

        async with self.aio_driver.topic_client.reader(
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
        # Metrics are enabled only if an OTLP endpoint is provided (CLI: --otlp-endpoint).
        if not getattr(self.args, "otlp_endpoint", None):
            return []

        task = asyncio.create_task(
            self._async_metric_sender(self.args.time),
            name="slo_metrics_sender",
        )
        return [task]

    async def _async_metric_sender(self, runtime: int):
        start_time = time.time()
        logger.info("Start push metrics (async)")

        limiter = AsyncLimiter(max_rate=10**6 // self.args.report_period, time_period=1)

        while time.time() - start_time < runtime:
            async with limiter:
                # Call sync metrics.push() in executor to avoid blocking the event loop.
                await asyncio.get_event_loop().run_in_executor(None, self.metrics.push)

        logger.info("Stop push metrics (async)")
