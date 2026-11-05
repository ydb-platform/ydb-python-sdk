import asyncio
import logging
import time

from core.metrics import OP_TYPE_READ, OP_TYPE_WRITE, REF

import ydb
import ydb.aio

from .async_topic_jobs import AsyncTopicJobManager
from .topic_payload import decode_payload, encode_payload
from .topic_tx_jobs import SINK_UPSERT_TEMPLATE

logger = logging.getLogger(__name__)


class AsyncTopicTxJobManager(AsyncTopicJobManager):
    """Async mirror of :class:`TopicTxJobManager` (transactional topic <-> table
    pipeline). See that class for the scenario description."""

    def __init__(self, driver, args, metrics, sink_table):
        super().__init__(driver, args, metrics)
        self.sink_table = sink_table
        self.messages_per_tx = max(1, int(getattr(self.args, "messages_per_tx", 10)))
        self._sink_upsert_query = SINK_UPSERT_TEMPLATE.format(sink_table)
        self.retry_settings = ydb.RetrySettings(idempotent=True)

    # --- shared query helper --------------------------------------------------

    async def _upsert_sink(self, tx, decoded):
        writer_id, seqno, write_ts_ns = decoded
        async with await tx.execute(
            self._sink_upsert_query,
            {
                "$writer_id": (writer_id, ydb.PrimitiveType.Uint64),
                "$seqno": (seqno, ydb.PrimitiveType.Uint64),
                "$write_ts_ns": (write_ts_ns, ydb.PrimitiveType.Uint64),
            },
            commit_tx=False,
        ) as result_sets:
            async for _ in result_sets:
                pass

    # --- producer (transactional topic write) --------------------------------

    async def _run_topic_writes(self, writer_id, limiter):
        start_time = time.time()
        partition_id = writer_id % self.partitions
        producer_id = f"{REF}-p{writer_id}"
        logger.info("Start async topic tx writer %s (partition %s, producer %s)", writer_id, partition_id, producer_id)

        # `seqno` lives across recreations and advances only after a successful
        # commit, so the sequence the reader sees is gap-free.
        seqno = 1
        while time.time() - start_time < self.args.time:
            try:
                async with ydb.aio.QuerySessionPool(self.aio_driver) as pool:
                    while time.time() - start_time < self.args.time:
                        base_seqno = seqno
                        payloads = []
                        for k in range(self.messages_per_tx):
                            if time.time() - start_time >= self.args.time:
                                break
                            async with limiter:
                                payloads.append(
                                    encode_payload(
                                        writer_id, base_seqno + k, time.monotonic_ns(), self.args.message_size
                                    )
                                )
                        if not payloads:
                            break

                        async def callee(tx):
                            tx_writer = self.aio_driver.topic_client.tx_writer(
                                tx,
                                self.args.path,
                                producer_id=producer_id,
                                partition_id=partition_id,
                                codec=ydb.TopicCodec.RAW,
                            )
                            for payload in payloads:
                                await tx_writer.write(ydb.TopicWriterMessage(data=payload))

                        ts = self.metrics.start((OP_TYPE_WRITE,))
                        try:
                            await pool.retry_tx_async(callee, retry_settings=self.retry_settings)
                            self.metrics.stop((OP_TYPE_WRITE,), ts)
                            seqno = base_seqno + len(payloads)  # advance only on commit
                        except Exception as e:
                            self.metrics.stop((OP_TYPE_WRITE,), ts, error=e)
                            logger.error("Tx write error (recreating writer): %s", e)
                            break
            except Exception as e:
                logger.error("Topic tx writer %s recreate: %s", writer_id, e)
                await asyncio.sleep(0.2)

        logger.info("Stop async topic tx writer %s", writer_id)

    # --- consumer (topic -> table) -------------------------------------------

    async def _run_topic_reads(self, reader_id):
        start_time = time.time()
        read_timeout = self.args.read_timeout / 1000
        logger.info("Start async topic tx reader %s", reader_id)

        while time.time() - start_time < self.args.time:
            try:
                async with ydb.aio.QuerySessionPool(self.aio_driver) as pool:
                    async with self.aio_driver.topic_client.reader(self.args.path, self.args.consumer) as reader:
                        while time.time() - start_time < self.args.time:
                            committed = []

                            async def callee(tx):
                                nonlocal committed
                                committed = []
                                batch = await asyncio.wait_for(
                                    reader.receive_batch_with_tx(tx, max_messages=self.messages_per_tx), read_timeout
                                )
                                if batch is None:
                                    return
                                for msg in batch.messages:
                                    decoded = decode_payload(msg.data)
                                    if decoded is not None:
                                        await self._upsert_sink(tx, decoded)
                                    committed.append(decoded)

                            ts = self.metrics.start((OP_TYPE_READ,))
                            try:
                                await pool.retry_tx_async(callee, retry_settings=self.retry_settings)
                            except asyncio.TimeoutError:
                                # No batch within read_timeout: an idle reader or
                                # the SDK transparently reconnecting under chaos,
                                # not a read failure. Don't count the op (real
                                # errors surface as exceptions the tx retries).
                                self.metrics.cancel((OP_TYPE_READ,), ts)
                                continue
                            except Exception as e:
                                self.metrics.stop((OP_TYPE_READ,), ts, error=e)
                                logger.error("Tx read error (recreating reader): %s", e)
                                break

                            if not committed:
                                self.metrics.cancel((OP_TYPE_READ,), ts)
                                continue

                            # A batch committed: the offsets/rows are durable, so
                            # the seqnos are exactly-once delivered.
                            self.metrics.stop((OP_TYPE_READ,), ts)
                            for decoded in committed:
                                self._record(decoded)
            except Exception as e:
                logger.error("Topic tx reader %s recreate: %s", reader_id, e)
                await asyncio.sleep(0.2)

        logger.info("Stop async topic tx reader %s", reader_id)
