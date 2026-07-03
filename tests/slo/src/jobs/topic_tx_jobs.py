import logging
import time

from core.metrics import OP_TYPE_READ, OP_TYPE_WRITE, REF

import ydb

from .topic_jobs import TopicJobManager
from .topic_payload import decode_payload, encode_payload

logger = logging.getLogger(__name__)

SINK_UPSERT_TEMPLATE = """
DECLARE $writer_id AS Uint64;
DECLARE $seqno AS Uint64;
DECLARE $write_ts_ns AS Uint64;
UPSERT INTO `{}` (writer_id, seqno, write_ts_ns, received_at)
VALUES ($writer_id, $seqno, $write_ts_ns, CurrentUtcTimestamp());
"""

HOT_SELECT_TEMPLATE = """
DECLARE $id AS Uint64;
SELECT val FROM `{}` WHERE id = $id;
"""

HOT_UPSERT_TEMPLATE = """
DECLARE $id AS Uint64;
DECLARE $val AS Uint64;
UPSERT INTO `{}` (id, val) VALUES ($id, $val);
"""


class TopicTxJobManager(TopicJobManager):
    """Both-ends transactional topic <-> table pipeline (sync).

    Producer: a ``tx_writer`` writes a batch of messages to the topic while the
    same transaction reads-and-bumps a hot counter row (table -> topic).
    Consumer: ``receive_batch_with_tx`` reads a batch while the same transaction
    UPSERTs each message into a sink table and bumps a hot counter row
    (topic -> table). The commit advances the topic offset and persists the
    table rows atomically -> exactly-once.

    The shared hot rows (``--tli-hot-keys`` of them) create optimistic-lock
    contention, so transactions occasionally fail with TLI (``ydb.Aborted``);
    the tx retry loop absorbs them and delivery stays exactly-once. TLI aborts
    are counted via ``RetrySettings.on_ydb_error_callback``.
    """

    def __init__(self, driver, args, metrics, sink_table, hot_table):
        super().__init__(driver, args, metrics)
        self.sink_table = sink_table
        self.hot_table = hot_table
        self.messages_per_tx = max(1, int(getattr(self.args, "messages_per_tx", 10)))
        self.hot_keys = max(1, int(getattr(self.args, "tli_hot_keys", 4)))

        self._sink_upsert_query = SINK_UPSERT_TEMPLATE.format(sink_table)
        self._hot_select_query = HOT_SELECT_TEMPLATE.format(hot_table)
        self._hot_upsert_query = HOT_UPSERT_TEMPLATE.format(hot_table)

        self.retry_settings = ydb.RetrySettings(idempotent=True, on_ydb_error_callback=self._on_ydb_error)

    def run_tests(self):
        # Emit the TLI counter at 0 up front so it shows as 0 (not a missing
        # series) on a clean run; the delivery counters are emitted by super().
        self.metrics.inc_tli(0)
        super().run_tests()

    def _on_ydb_error(self, e):
        if isinstance(e, ydb.Aborted):
            self.metrics.inc_tli()
            logger.debug("TLI abort (will retry): %s", e)

    # --- shared query helpers -------------------------------------------------

    def _exec(self, tx, query, params):
        rows = []
        with tx.execute(query, params, commit_tx=False) as result_sets:
            for result_set in result_sets:
                rows.extend(result_set.rows)
        return rows

    def _bump_hot(self, tx, hot_id):
        # Read-modify-write on a shared hot row: the read takes an optimistic
        # lock, so concurrent writers/readers on the same key conflict -> TLI.
        rows = self._exec(tx, self._hot_select_query, {"$id": (hot_id, ydb.PrimitiveType.Uint64)})
        cur = rows[0]["val"] if rows and rows[0]["val"] is not None else 0
        self._exec(
            tx,
            self._hot_upsert_query,
            {"$id": (hot_id, ydb.PrimitiveType.Uint64), "$val": (cur + 1, ydb.PrimitiveType.Uint64)},
        )

    def _upsert_sink(self, tx, decoded):
        writer_id, seqno, write_ts_ns = decoded
        self._exec(
            tx,
            self._sink_upsert_query,
            {
                "$writer_id": (writer_id, ydb.PrimitiveType.Uint64),
                "$seqno": (seqno, ydb.PrimitiveType.Uint64),
                "$write_ts_ns": (write_ts_ns, ydb.PrimitiveType.Uint64),
            },
        )

    # --- producer (table -> topic) -------------------------------------------

    def _run_topic_writes(self, writer_id, limiter):
        start_time = time.time()
        partition_id = writer_id % self.partitions
        producer_id = f"{REF}-p{writer_id}"
        hot_id = writer_id % self.hot_keys
        logger.info("Start topic tx writer %s (partition %s, producer %s)", writer_id, partition_id, producer_id)

        # `seqno` lives across recreations and advances only after a successful
        # commit, so the sequence the reader sees is gap-free (a failed/aborted
        # tx leaves no gap; a retried commit is at worst an app-level duplicate).
        seqno = 1
        while time.time() - start_time < self.args.time:
            try:
                with ydb.QuerySessionPool(self.driver) as pool:
                    while time.time() - start_time < self.args.time:
                        base_seqno = seqno
                        payloads = []
                        for k in range(self.messages_per_tx):
                            if time.time() - start_time >= self.args.time:
                                break
                            with limiter:
                                payloads.append(
                                    encode_payload(
                                        writer_id, base_seqno + k, time.monotonic_ns(), self.args.message_size
                                    )
                                )
                        if not payloads:
                            break

                        def callee(tx):
                            self._bump_hot(tx, hot_id)
                            tx_writer = self.driver.topic_client.tx_writer(
                                tx,
                                self.args.path,
                                producer_id=producer_id,
                                partition_id=partition_id,
                                codec=ydb.TopicCodec.RAW,
                            )
                            for payload in payloads:
                                tx_writer.write(ydb.TopicWriterMessage(data=payload))

                        ts = self.metrics.start((OP_TYPE_WRITE,))
                        try:
                            pool.retry_tx_sync(callee, retry_settings=self.retry_settings)
                            self.metrics.stop((OP_TYPE_WRITE,), ts)
                            seqno = base_seqno + len(payloads)  # advance only on commit
                        except Exception as e:
                            self.metrics.stop((OP_TYPE_WRITE,), ts, error=e)
                            logger.error("Tx write error (recreating writer): %s", e)
                            break
            except Exception as e:
                logger.error("Topic tx writer %s recreate: %s", writer_id, e)
                time.sleep(0.2)

        logger.info("Stop topic tx writer %s", writer_id)

    # --- consumer (topic -> table) -------------------------------------------

    def _run_topic_reads(self, reader_id):
        start_time = time.time()
        read_timeout = self.args.read_timeout / 1000
        hot_id = reader_id % self.hot_keys
        logger.info("Start topic tx reader %s", reader_id)

        while time.time() - start_time < self.args.time:
            try:
                with ydb.QuerySessionPool(self.driver) as pool:
                    with self.driver.topic_client.reader(self.args.path, self.args.consumer) as reader:
                        while time.time() - start_time < self.args.time:
                            committed = []

                            def callee(tx):
                                nonlocal committed
                                committed = []
                                batch = reader.receive_batch_with_tx(
                                    tx, max_messages=self.messages_per_tx, timeout=read_timeout
                                )
                                if batch is None:
                                    return
                                self._bump_hot(tx, hot_id)
                                for msg in batch.messages:
                                    decoded = decode_payload(msg.data)
                                    if decoded is not None:
                                        self._upsert_sink(tx, decoded)
                                    committed.append(decoded)

                            ts = self.metrics.start((OP_TYPE_READ,))
                            try:
                                pool.retry_tx_sync(callee, retry_settings=self.retry_settings)
                                self.metrics.stop((OP_TYPE_READ,), ts)
                            except TimeoutError as e:
                                # Starved reader (outage/stall): a visible read
                                # failure, not a silent wait.
                                self.metrics.stop((OP_TYPE_READ,), ts, error=e)
                                continue
                            except Exception as e:
                                self.metrics.stop((OP_TYPE_READ,), ts, error=e)
                                logger.error("Tx read error (recreating reader): %s", e)
                                break

                            # Validate only after commit: these offsets/rows are
                            # durable, so the seqnos are exactly-once delivered.
                            for decoded in committed:
                                self._record(decoded)
            except Exception as e:
                logger.error("Topic tx reader %s recreate: %s", reader_id, e)
                time.sleep(0.2)

        logger.info("Stop topic tx reader %s", reader_id)
