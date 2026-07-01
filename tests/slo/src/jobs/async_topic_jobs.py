import asyncio
import logging
import time

# `aiolimiter` is a runtime dependency (see `tests/slo/requirements.txt`).
from aiolimiter import AsyncLimiter  # pyright: ignore[reportMissingImports]
from core.metrics import OP_TYPE_READ, OP_TYPE_WRITE, REF

import ydb
import ydb.aio

from .base import AsyncBaseJobManager

logger = logging.getLogger(__name__)


def encode_payload(writer_id: int, seqno: int, write_ts_ns: int, size: int) -> bytes:
    """`writer_id:seqno:write_ts_ns:` header, padded to `size` bytes.

    The write timestamp travels inside the message so the reader (same process)
    can compute end-to-end latency; writer_id + seqno let it validate per-producer
    ordering and detect loss/duplicates.
    """
    header = f"{writer_id}:{seqno}:{write_ts_ns}:".encode("utf-8")
    if len(header) < size:
        header += b"x" * (size - len(header))
    return header


def decode_payload(data: bytes):
    """Return (writer_id, seqno, write_ts_ns) or None if not our payload."""
    try:
        parts = data.split(b":", 3)
        return int(parts[0]), int(parts[1]), int(parts[2])
    except (ValueError, IndexError):
        return None


class AsyncTopicJobManager(AsyncBaseJobManager):
    def __init__(self, driver, args, metrics):
        super().__init__(driver, args, metrics)
        # Keep async driver separately to avoid type-incompatible override of BaseJobManager.driver
        self.aio_driver = driver
        self.partitions = max(1, int(getattr(self.args, "partitions_count", 1)))

    async def run_tests(self):
        tasks = [
            *self._run_topic_write_jobs(),
            *self._run_topic_read_jobs(),
            *self._run_metric_job(),
        ]
        await asyncio.gather(*tasks)

    def _run_topic_write_jobs(self):
        logger.info("Start async topic write jobs")

        # One shared limiter -> total offered write load is write_rps, evenly
        # spread across writers/partitions (simple, non-adaptive = reproducible).
        write_limiter = AsyncLimiter(max_rate=max(1, int(self.args.write_rps)), time_period=1)

        return [
            asyncio.create_task(self._run_topic_writes(i, write_limiter), name=f"slo_topic_write_{i}")
            for i in range(self.args.write_threads)
        ]

    def _run_topic_read_jobs(self):
        logger.info("Start async topic read jobs")

        return [
            asyncio.create_task(self._run_topic_reads(i), name=f"slo_topic_read_{i}")
            for i in range(self.args.read_threads)
        ]

    async def _run_topic_writes(self, writer_id: int, limiter: AsyncLimiter):
        start_time = time.time()
        partition_id = writer_id % self.partitions
        # producer_id is stable (seqno continues across reconnects) and ref-scoped
        # (current/baseline share the cluster) so server-side dedup works per writer.
        producer_id = f"{REF}-p{writer_id}"
        logger.info("Start async topic writer %s (partition %s, producer %s)", writer_id, partition_id, producer_id)

        async with self.aio_driver.topic_client.writer(
            self.args.path,
            producer_id=producer_id,
            partition_id=partition_id,
            codec=ydb.TopicCodec.GZIP,
        ) as writer:
            seqno = 0
            while time.time() - start_time < self.args.time:
                async with limiter:
                    seqno += 1
                    payload = encode_payload(writer_id, seqno, time.monotonic_ns(), self.args.message_size)
                    message = ydb.TopicWriterMessage(data=payload)

                    ts = self.metrics.start((OP_TYPE_WRITE,))
                    try:
                        await writer.write_with_ack(message)
                        self.metrics.stop((OP_TYPE_WRITE,), ts)
                        logger.debug("Write w%s seq%s", writer_id, seqno)
                    except Exception as e:
                        self.metrics.stop((OP_TYPE_WRITE,), ts, error=e)
                        logger.error("Write error: %s", e)

        logger.info("Stop async topic writer %s", writer_id)

    async def _run_topic_reads(self, reader_id: int):
        start_time = time.time()
        logger.info("Start async topic reader %s", reader_id)

        # Next expected seqno per producer (writer_id). First sighting seeds it,
        # so a reader that joins mid-stream (rebalance/restart) never reports a
        # false loss.
        expected = {}

        async with self.aio_driver.topic_client.reader(self.args.path, self.args.consumer) as reader:
            while time.time() - start_time < self.args.time:
                ts = self.metrics.start((OP_TYPE_READ,))
                try:
                    msg = await reader.receive_message()
                    self.metrics.stop((OP_TYPE_READ,), ts)
                except Exception as e:
                    self.metrics.stop((OP_TYPE_READ,), ts, error=e)
                    logger.error("Read error: %s", e)
                    continue

                if msg is None:
                    continue

                self._validate(msg, expected)

                try:
                    await reader.commit_with_ack(msg)
                except Exception as e:
                    logger.error("Commit error: %s", e)

        logger.info("Stop async topic reader %s", reader_id)

    def _validate(self, msg, expected: dict) -> None:
        self.metrics.inc_delivered()

        decoded = decode_payload(msg.data)
        if decoded is None:
            return
        writer_id, seqno, write_ts_ns = decoded

        self.metrics.record_e2e((time.monotonic_ns() - write_ts_ns) / 1e9)

        exp = expected.get(writer_id)
        if exp is None:
            expected[writer_id] = seqno + 1
        elif seqno == exp:
            expected[writer_id] = seqno + 1
        elif seqno > exp:
            # Partition order is server-guaranteed, so a forward gap is real loss.
            self.metrics.inc_lost(seqno - exp)
            expected[writer_id] = seqno + 1
            logger.warning("Lost w%s: expected %s got %s", writer_id, exp, seqno)
        else:
            # seqno < exp: an already-seen seqno came back (reconnect redelivery).
            self.metrics.inc_duplicated()
