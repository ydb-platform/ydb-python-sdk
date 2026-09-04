"""Topic SLO workload variant that writes through the multi-partition writer.

The regular topic workload pins one writer per partition and drives it directly. This one
writes by key instead and lets the multi-writer decide the partition, so the chaos run
exercises the parts that only exist there: routing, the per-partition sub-writer pool, and
recovery of both when nodes go away underneath.

Everything else is inherited: the reader side, the metrics, and the delivery accounting.
That works unchanged because the accounting only needs a stream whose sequence numbers grow
monotonically, and per-key ordering gives exactly that -- one payload stream per key rather
than per partition.
"""

import logging
import threading
import time

from core.metrics import OP_TYPE_WRITE, REF

import ydb

from .base import SyncRateLimiter
from .topic_jobs import TopicJobManager
from .topic_payload import encode_payload

logger = logging.getLogger(__name__)


class TopicMultiWriterJobManager(TopicJobManager):
    def __init__(self, driver, args, metrics):
        super().__init__(driver, args, metrics)
        self.keys_per_writer = max(1, int(getattr(self.args, "keys_per_writer", 8)))

    def _run_topic_write_jobs(self):
        logger.info(
            "Start topic multi-writer jobs: %d writers x %d keys",
            self.args.write_threads,
            self.keys_per_writer,
        )

        write_rps = int(getattr(self.args, "write_rps", 0))
        write_limiter = SyncRateLimiter(min_interval_s=0.0 if write_rps <= 0 else 1.0 / write_rps)

        futures = []
        for i in range(self.args.write_threads):
            future = threading.Thread(
                name=f"slo_topic_multiwrite_{i}",
                target=self._run_topic_writes,
                args=(i, write_limiter),
            )
            future.start()
            futures.append(future)
        return futures

    def _stream_id(self, writer_id: int, key_index: int) -> int:
        """Payload stream id for one key.

        The reader validates ordering per stream id, so it has to be one id per key: a key is
        what the multi-writer keeps ordered, and two keys may share a partition.
        """
        return writer_id * self.keys_per_writer + key_index

    def _run_topic_writes(self, writer_id, limiter):
        start_time = time.time()
        producer_id_prefix = f"{REF}-mw{writer_id}"
        write_timeout = self.args.write_timeout / 1000
        keys = [f"slo-key-{self._stream_id(writer_id, j)}" for j in range(self.keys_per_writer)]

        logger.info("Start topic multi-writer %s (prefix %s, keys %s)", writer_id, producer_id_prefix, len(keys))

        # Sequence numbers live across writer recreations so the reader never sees a stream
        # restart, exactly as in the single-partition workload.
        seqno = {key: 1 for key in keys}
        next_key = 0

        while time.time() - start_time < self.args.time:
            try:
                with self.driver.topic_client.multiwriter(
                    self.args.path,
                    producer_id_prefix=producer_id_prefix,
                    codec=ydb.TopicCodec.RAW,
                ) as writer:
                    while time.time() - start_time < self.args.time:
                        with limiter:
                            key_index = next_key % len(keys)
                            key = keys[key_index]
                            next_key += 1

                            payload = encode_payload(
                                self._stream_id(writer_id, key_index),
                                seqno[key],
                                time.monotonic_ns(),
                                self.args.message_size,
                            )
                            message = ydb.TopicWriterMessage(data=payload, key=key)

                            ts = self.metrics.start((OP_TYPE_WRITE,))
                            try:
                                writer.write_with_ack(message, timeout=write_timeout)
                                self.metrics.stop((OP_TYPE_WRITE,), ts)
                                # Advance only on success: a failed write retries the same
                                # seqno, so at worst it duplicates, never fakes a loss.
                                seqno[key] += 1
                            except Exception as e:
                                self.metrics.stop((OP_TYPE_WRITE,), ts, error=e)
                                logger.error("Multi-writer write error (recreating writer): %s", e)
                                break  # drop the possibly wedged writer and remake it
            except Exception as e:
                logger.error("Topic multi-writer %s recreate: %s", writer_id, e)
                time.sleep(0.2)

        logger.info("Stop topic multi-writer %s", writer_id)
