import logging
import threading
import time

from core.metrics import OP_TYPE_READ, OP_TYPE_WRITE, REF

import ydb

from .base import BaseJobManager, SyncRateLimiter
from .topic_payload import decode_payload, encode_payload

logger = logging.getLogger(__name__)


class TopicJobManager(BaseJobManager):
    def __init__(self, driver, args, metrics):
        super().__init__(driver, args, metrics)
        self.partitions = max(1, int(getattr(self.args, "partitions_count", 1)))
        # Next expected seqno per producer (writer_id), shared across reader
        # threads (a partition can move between readers on rebalance). Guarded by
        # a lock because sync readers are real threads (unlike the async loop).
        self._expected = {}
        self._expected_lock = threading.Lock()

    def run_tests(self):
        # Emit delivery counters at 0 up front so lost/duplicates show as 0 in the
        # report even on a clean run (instead of a missing series).
        self.metrics.inc_delivered(0)
        self.metrics.inc_lost(0)
        self.metrics.inc_duplicated(0)

        futures = [
            *self._run_topic_write_jobs(),
            *self._run_topic_read_jobs(),
            *self._run_metric_job(),
        ]
        for future in futures:
            future.join()

    def _run_topic_write_jobs(self):
        logger.info("Start topic write jobs")

        # One shared limiter -> total offered write load is write_rps, evenly
        # spread across writers/partitions (simple, non-adaptive = reproducible).
        write_rps = int(getattr(self.args, "write_rps", 0))
        write_limiter = SyncRateLimiter(min_interval_s=0.0 if write_rps <= 0 else 1.0 / write_rps)

        futures = []
        for i in range(self.args.write_threads):
            future = threading.Thread(
                name=f"slo_topic_write_{i}",
                target=self._run_topic_writes,
                args=(i, write_limiter),
            )
            future.start()
            futures.append(future)
        return futures

    def _run_topic_read_jobs(self):
        logger.info("Start topic read jobs")

        futures = []
        for i in range(self.args.read_threads):
            future = threading.Thread(
                name=f"slo_topic_read_{i}",
                target=self._run_topic_reads,
                args=(i,),
            )
            future.start()
            futures.append(future)
        return futures

    def _run_topic_writes(self, writer_id, limiter):
        start_time = time.time()
        partition_id = writer_id % self.partitions
        producer_id = f"{REF}-p{writer_id}"
        write_timeout = self.args.write_timeout / 1000
        logger.info("Start topic writer %s (partition %s, producer %s)", writer_id, partition_id, producer_id)

        # `seqno` lives across writer recreations so the sequence the reader sees
        # never resets. The outer loop recreates the writer if it breaks/stalls so
        # the workload never silently hangs.
        seqno = 1
        while time.time() - start_time < self.args.time:
            try:
                with self.driver.topic_client.writer(
                    self.args.path,
                    producer_id=producer_id,
                    partition_id=partition_id,
                    codec=ydb.TopicCodec.RAW,
                ) as writer:
                    while time.time() - start_time < self.args.time:
                        with limiter:
                            payload = encode_payload(writer_id, seqno, time.monotonic_ns(), self.args.message_size)
                            message = ydb.TopicWriterMessage(data=payload)

                            ts = self.metrics.start((OP_TYPE_WRITE,))
                            try:
                                writer.write_with_ack(message, timeout=write_timeout)
                                self.metrics.stop((OP_TYPE_WRITE,), ts)
                                # Advance only on success -> a failed write leaves
                                # no gap (a timeout retries the seqno: at worst a
                                # duplicate, never a false loss).
                                seqno += 1
                            except Exception as e:
                                self.metrics.stop((OP_TYPE_WRITE,), ts, error=e)
                                logger.error("Write error (recreating writer): %s", e)
                                break  # drop the (possibly wedged) writer and remake it
            except Exception as e:
                logger.error("Topic writer %s recreate: %s", writer_id, e)
                time.sleep(0.2)

        logger.info("Stop topic writer %s", writer_id)

    def _run_topic_reads(self, reader_id):
        start_time = time.time()
        read_timeout = self.args.read_timeout / 1000
        logger.info("Start topic reader %s", reader_id)

        while time.time() - start_time < self.args.time:
            try:
                with self.driver.topic_client.reader(self.args.path, self.args.consumer) as reader:
                    while time.time() - start_time < self.args.time:
                        ts = self.metrics.start((OP_TYPE_READ,))
                        try:
                            msg = reader.receive_message(timeout=read_timeout)
                        except TimeoutError as e:
                            # No message within read_timeout: at steady rate this
                            # means the reader is starved (outage/stall), so it is
                            # a read failure (visible), not a silent wait.
                            self.metrics.stop((OP_TYPE_READ,), ts, error=e)
                            continue
                        except Exception as e:
                            self.metrics.stop((OP_TYPE_READ,), ts, error=e)
                            logger.error("Read error (recreating reader): %s", e)
                            break

                        if msg is None:
                            self.metrics.stop((OP_TYPE_READ,), ts)
                            continue

                        self._validate(msg)

                        # The read op spans receive+commit, so a commit failure
                        # shows up as a read error instead of being only logged.
                        try:
                            reader.commit_with_ack(msg, timeout=read_timeout)
                            self.metrics.stop((OP_TYPE_READ,), ts)
                        except Exception as e:
                            self.metrics.stop((OP_TYPE_READ,), ts, error=e)
                            logger.error("Commit error: %s", e)
            except Exception as e:
                logger.error("Topic reader %s recreate: %s", reader_id, e)
                time.sleep(0.2)

        logger.info("Stop topic reader %s", reader_id)

    def _validate(self, msg):
        decoded = decode_payload(msg.data)
        if decoded is None:
            self.metrics.inc_delivered()
            return
        writer_id, seqno, write_ts_ns = decoded

        lost_n = 0
        with self._expected_lock:
            exp = self._expected.get(writer_id)
            duplicate = exp is not None and seqno < exp
            if not duplicate:
                if exp is not None and seqno > exp:
                    lost_n = seqno - exp
                self._expected[writer_id] = seqno + 1

        if duplicate:
            # Already-seen seqno came back (reconnect redelivery): not a fresh
            # delivery, excluded from delivered / e2e (old write_ts).
            self.metrics.inc_duplicated()
            return

        self.metrics.inc_delivered()
        self.metrics.record_e2e((time.monotonic_ns() - write_ts_ns) / 1e9)
        if lost_n:
            # Partition order is server-guaranteed, so a forward gap is real loss.
            self.metrics.inc_lost(lost_n)
            logger.warning("Lost w%s: expected %s got %s", writer_id, exp, seqno)
