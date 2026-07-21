from __future__ import annotations

import asyncio
import concurrent.futures
import inspect
import uuid
import logging
import weakref
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Mapping, Optional, Union

from .topic_writer import (
    Message,
    PublicMessage,
    PublicWriterSettings,
    PublicWriteResult,
    PublicWriteResultTypes,
    TopicWriterClosedError,
    TopicWriterError,
    TopicWriterPartitionSplitError,
    TopicWriterStopped,
)
from .topic_writer_asyncio import WriterAsyncIO
from .topic_writer_partition_chooser import (
    PublicPartitionByKeyBound,
    PublicPartitionByKeyKafka,
    PublicPartitionChooser,
)
from .. import _apis, issues
from .._topic_common.common import create_result_wrapper
from .._grpc.grpcwrapper import ydb_topic as _ydb_topic
from .._grpc.grpcwrapper import ydb_topic_public_types as _ydb_topic_public_types
from .._grpc.grpcwrapper.ydb_topic_public_types import PublicAutoPartitioningStrategy, PublicCodec

_PartitionInfo = _ydb_topic_public_types.PublicDescribeTopicResult.PartitionInfo

logger = logging.getLogger(__name__)

# An OVERLOADED response may be an in-progress split/merge (children not yet visible in
# DescribeTopic) or ordinary transient overload. Re-describe a few times before deciding.
_REPARTITION_DISCOVER_ATTEMPTS = 4
_REPARTITION_DISCOVER_DELAY = 0.25

# A per-partition sub-writer with no in-flight messages and no writes for this long is closed;
# it is recreated on demand. Set <= 0 to disable idle eviction.
_DEFAULT_WRITER_IDLE_TIMEOUT = 60.0


@dataclass
class MultiWriterSettings:
    """Settings for the multi-partition (write-by-key) topic writer.

    order of fields IS NOT stable, use keywords only
    """

    topic: str
    producer_id_prefix: Optional[str] = None
    partition_chooser: Optional[PublicPartitionChooser] = None
    auto_seqno: bool = True
    auto_created_at: bool = True
    codec: Optional[PublicCodec] = None
    encoders: Optional[Mapping[PublicCodec, Callable[[bytes], bytes]]] = None
    encoder_executor: Optional[concurrent.futures.Executor] = None
    max_buffer_size_bytes: Optional[int] = None
    max_buffer_messages: Optional[int] = None
    buffer_wait_timeout_sec: Optional[float] = None
    # Idle per-partition sub-writers are closed after this many seconds and recreated on demand.
    # None -> default; <= 0 disables eviction.
    writer_idle_timeout_sec: Optional[float] = None

    def __post_init__(self):
        if self.producer_id_prefix is None:
            self.producer_id_prefix = uuid.uuid4().hex
        # partition_chooser is left as-is; when None the writer picks one adaptively
        # after describing the topic (Bound if the topic reports key ranges, else Kafka).


@dataclass
class _InflightMessage:
    message: PublicMessage
    user_future: asyncio.Future
    seqno: int
    partition_id: int
    sub_future: Optional[asyncio.Future] = field(default=None)


def _is_overloaded(err: BaseException) -> bool:
    return isinstance(err, issues.Overloaded)


class TopicWriterMultiAsyncIO:
    """One logical writer that routes messages to per-partition sub-writers by key.

    Each partition is served by an ordinary :class:`WriterAsyncIO` (buffering,
    encoding, reconnection and token refresh are reused as-is). On top of that this
    class:

    * routes each message to a partition via the partition chooser;
    * owns the in-flight messages and assigns their sequence numbers, so that on an
      auto-partition split it can transparently resend the un-acked messages of the
      split partition to its children — without duplicating messages that were
      already persisted (the ``maxSeqNo`` cut).
    """

    def __init__(self, driver, settings: MultiWriterSettings, _parent=None):
        self._loop = asyncio.get_running_loop()
        self._driver = driver
        self._parent = _parent  # keep parent client alive against GC
        self._settings = settings
        # producer_id_prefix is guaranteed set in __post_init__
        prefix = settings.producer_id_prefix
        assert prefix is not None
        self._prefix: str = prefix
        # Resolved in _init(): the configured chooser, or an adaptive default.
        self._chooser: Optional[PublicPartitionChooser] = settings.partition_chooser
        self._closed = False
        self._lock = asyncio.Lock()
        self._writers: Dict[int, WriterAsyncIO] = {}
        self._partitions: Dict[int, object] = {}
        # partition_id -> {seqno -> in-flight message}, un-acked messages we may resend.
        self._inflight: Dict[int, Dict[int, _InflightMessage]] = {}
        # partition_id -> next seqno cursor (seeded from the sub-writer's last_seqno).
        self._partition_seqno: Dict[int, int] = {}
        # partition_id -> highest acked seqno (fallback maxSeqNo if a probe fails).
        self._max_acked: Dict[int, int] = {}
        # partition_id -> monotonic time of the last write/creation, for idle eviction.
        self._last_write_at: Dict[int, float] = {}
        self._idle_timeout = (
            settings.writer_idle_timeout_sec
            if settings.writer_idle_timeout_sec is not None
            else _DEFAULT_WRITER_IDLE_TIMEOUT
        )
        self._init_task = asyncio.ensure_future(self._init())
        self._reaper_task: Optional[asyncio.Future] = None
        if self._idle_timeout > 0:
            # Hold only a weakref so the reaper does not keep the writer alive against GC.
            self._reaper_task = asyncio.ensure_future(self._idle_reaper(weakref.ref(self), self._idle_timeout))

    async def __aenter__(self) -> "TopicWriterMultiAsyncIO":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            await self.close()
        except BaseException:
            if exc_val is None:
                raise

    def __del__(self):
        if self._closed or self._loop.is_closed():
            return
        try:
            logger.debug("Topic multi-writer was not closed properly. Consider using method close().")
            task = self._loop.create_task(self.close(flush=False))
            task.set_name("close multiwriter")
        except BaseException:
            logger.warning("Something went wrong during multi-writer close in __del__")

    async def _describe(self):
        req = _ydb_topic_public_types.DescribeTopicRequestParams(path=self._settings.topic, include_stats=False)
        # The async driver returns a coroutine; the sync driver (used behind the
        # sync facade) returns the result directly. Support both.
        res = self._driver(
            req.to_proto(),
            _apis.TopicService.Stub,
            _apis.TopicService.DescribeTopic,
            create_result_wrapper(_ydb_topic.DescribeTopicResult),
        )
        if inspect.isawaitable(res):
            res = await res
        return res.to_public()

    async def _init(self):
        description = await self._describe()
        leaves = [p for p in description.partitions if p.active and not p.child_partition_ids]
        self._partitions = {p.partition_id: p for p in leaves}
        if self._chooser is None:
            self._chooser = self._default_chooser(leaves, description)
        self._chooser.add_partitions(leaves)

    @staticmethod
    def _default_chooser(partitions, description=None) -> PublicPartitionChooser:
        # Route by key range on auto-partitioned topics, else by Kafka hash. Prefer the
        # topic's auto-partitioning strategy as the signal: a single auto partition can
        # report no key_range at all (open b""..b""), yet its split-children are bounded,
        # which only the Bound chooser can accept.
        aps = getattr(description, "auto_partitioning_settings", None)
        auto_enabled = aps is not None and aps.strategy not in (
            None,
            PublicAutoPartitioningStrategy.UNSPECIFIED,
            PublicAutoPartitioningStrategy.DISABLED,
        )
        has_key_ranges = any(p.key_range is not None for p in partitions)
        if auto_enabled or has_key_ranges:
            return PublicPartitionByKeyBound()
        return PublicPartitionByKeyKafka()

    async def wait_init(self):
        await self._init_task

    def _check_closed(self):
        if self._closed:
            raise TopicWriterClosedError()

    def _build_writer_settings(self, partition_id: int, with_split_hook: bool) -> PublicWriterSettings:
        return PublicWriterSettings(
            topic=self._settings.topic,
            producer_id="%s-%d" % (self._prefix, partition_id),
            partition_id=partition_id,
            # The multi-writer assigns sequence numbers itself so it can resend
            # messages to child partitions after a split, keeping them monotonic.
            auto_seqno=False,
            auto_created_at=self._settings.auto_created_at,
            codec=self._settings.codec,
            encoders=self._settings.encoders,
            encoder_executor=self._settings.encoder_executor,
            max_buffer_size_bytes=self._settings.max_buffer_size_bytes,
            max_buffer_messages=self._settings.max_buffer_messages,
            buffer_wait_timeout_sec=self._settings.buffer_wait_timeout_sec,
            _on_check_retriable_error=self._make_overloaded_hook(partition_id) if with_split_hook else None,
        )

    async def _get_or_create_writer(self, partition_id: int) -> WriterAsyncIO:
        writer = self._writers.get(partition_id)
        if writer is None:
            writer = WriterAsyncIO(self._driver, self._build_writer_settings(partition_id, with_split_hook=True))
            self._writers[partition_id] = writer
            self._last_write_at[partition_id] = self._loop.time()
            # Seed the seqno cursor from the producer's last persisted seqno so a
            # stable producer_id_prefix resumes numbering instead of colliding.
            init_info = await writer.wait_init()
            self._partition_seqno.setdefault(partition_id, init_info.last_seqno or 0)
        return writer

    def _next_seqno(self, partition_id: int) -> int:
        self._partition_seqno[partition_id] = self._partition_seqno.get(partition_id, 0) + 1
        return self._partition_seqno[partition_id]

    def _assign_seqno(self, partition_id: int, message: PublicMessage) -> int:
        if self._settings.auto_seqno:
            seqno = self._next_seqno(partition_id)
            message.seqno = seqno
        else:
            if message.seqno is None:
                raise TopicWriterStopped()  # auto_seqno disabled but no seqno provided
            seqno = message.seqno
            self._partition_seqno[partition_id] = max(self._partition_seqno.get(partition_id, 0), seqno)
        return seqno

    def _make_overloaded_hook(self, partition_id: int):
        def hook(err: BaseException) -> bool:
            if _is_overloaded(err):
                logger.debug("multi-writer: partition %d overloaded, re-describing (split/merge)", partition_id)
                task = self._loop.create_task(self._on_partition_overloaded(partition_id))
                task.set_name("multiwriter repartition %d" % partition_id)
                return True
            return False

        return hook

    def _attach_ack(self, entry: _InflightMessage) -> None:
        sub_future = entry.sub_future
        assert sub_future is not None
        sub_future.add_done_callback(lambda f: self._on_sub_result(entry.partition_id, entry.seqno, f))

    def _on_sub_result(self, partition_id: int, seqno: int, sub_future: asyncio.Future) -> None:
        entry = self._inflight.get(partition_id, {}).get(seqno)
        if entry is None or entry.sub_future is not sub_future:
            return  # stale: the message was already resolved or moved to a child

        if sub_future.cancelled():
            return

        exc = sub_future.exception()
        if isinstance(exc, TopicWriterPartitionSplitError):
            # Leave the message in flight; the split handler will resend it.
            return

        self._inflight.get(partition_id, {}).pop(seqno, None)
        if entry.user_future.done():
            return
        if exc is not None:
            entry.user_future.set_exception(exc)
        else:
            result = sub_future.result()
            self._max_acked[partition_id] = max(self._max_acked.get(partition_id, 0), seqno)
            entry.user_future.set_result(result)

    def _detach_inflight(self, partition_id: int) -> None:
        # Sever the link to the current sub-writer so its ack callbacks (e.g. failures
        # raised while it is being closed) are ignored while we migrate the messages.
        for entry in self._inflight.get(partition_id, {}).values():
            entry.sub_future = None

    @staticmethod
    async def _safe_close(writer: WriterAsyncIO) -> None:
        # A sub-writer stopped by the split hook re-raises TopicWriterPartitionSplitError from
        # close(); closing a writer we are discarding must never abort a repartition.
        try:
            await writer.close(flush=False)
        except Exception:  # noqa: BLE001
            logger.debug("multi-writer: ignoring error while closing a discarded sub-writer", exc_info=True)

    def _max_seqno_cut(self, partition_id: int) -> int:
        """Dedup cut for a repartition: messages with seqno <= this were persisted to the
        (now retired) partition and must not be resent to the child.

        We use the highest acked seqno we already observed for the partition. A fresh writer
        cannot be used to read the server's last_seqno here: the split partition is inactive,
        so such a writer never finishes init and would block the whole multi-writer. On a
        graceful split the server acks everything it persisted before it returns OVERLOADED,
        so the acked seqno is exact in practice; a lost ack in the split moment could at worst
        cause one message to be re-sent (a rare duplicate), never a loss.
        """
        return self._max_acked.get(partition_id, 0)

    async def _discover_children(self, partition_id: int) -> List[_PartitionInfo]:
        """Re-describe until the split/merge children of ``partition_id`` appear.

        Returns an empty list if none appear (ordinary transient overload).
        """
        for attempt in range(_REPARTITION_DISCOVER_ATTEMPTS):
            description = await self._describe()
            children = [
                p
                for p in description.partitions
                if p.active and not p.child_partition_ids and partition_id in p.parent_partition_ids
            ]
            if children:
                return children
            if attempt + 1 < _REPARTITION_DISCOVER_ATTEMPTS:
                await asyncio.sleep(_REPARTITION_DISCOVER_DELAY)
        return []

    async def _on_partition_overloaded(self, partition_id: int):
        """Entry point for the OVERLOADED hook: handle a repartition, or recover on failure.

        The hook force-stops the sub-writer, so if handling fails we must not leave the
        partition's messages stranded — recreate the writer and resend them.
        """
        try:
            await self._handle_repartition(partition_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("multi-writer: repartition of partition %d failed; recovering", partition_id)
            try:
                async with self._lock:
                    if partition_id in self._partitions:
                        await self._recover_partition(partition_id)
            except Exception:
                logger.exception("multi-writer: recovery of partition %d failed", partition_id)

    async def _handle_repartition(self, partition_id: int):
        """Resolve an OVERLOADED partition: split, merge, or ordinary transient overload.

        A split turns one partition into two children (each with a single parent); a merge
        turns two into one child (with both as parents). Both are discovered by finding the
        active leaf partitions that list ``partition_id`` as a parent. All parents of those
        children that we still hold are retired together, so a merge does not leave the
        sibling parent lingering with an overlapping key range. If no children ever appear
        the overload was transient and the partition is recovered in place.
        """
        async with self._lock:
            if partition_id not in self._partitions:
                return  # already handled by a sibling parent's event
            assert self._chooser is not None  # resolved by _init() before any repartition

            children = await self._discover_children(partition_id)
            if not children:
                # Transient overload, not a topology change: keep the partition.
                await self._recover_partition(partition_id)
                return

            retired = {partition_id}
            for child in children:
                for parent in child.parent_partition_ids:
                    if parent in self._partitions:
                        retired.add(parent)

            # Update the routing view first: add children, drop every retired parent, so
            # migration re-routes only to the surviving partitions (no overlapping ranges).
            new_children = [c for c in children if c.partition_id not in self._partitions]
            if new_children:
                self._chooser.add_partitions(new_children)
                for child in new_children:
                    self._partitions[child.partition_id] = child
            for old in retired:
                self._chooser.remove_partition(old)
                self._partitions.pop(old, None)

            # Quiesce every retired parent BEFORE reading its cutoff, so a sibling cannot
            # persist a message after its maxSeqNo was probed (which would duplicate on resend).
            for old in retired:
                writer = self._writers.pop(old, None)
                if writer is not None:
                    self._detach_inflight(old)
                    await self._safe_close(writer)

            for old in retired:
                if self._inflight.get(old):
                    await self._migrate_messages(old, self._max_seqno_cut(old))
                else:
                    self._inflight.pop(old, None)

    async def _recover_partition(self, partition_id: int):
        # The hook stopped the sub-writer; drop it and resend the partition's in-flight
        # messages to a fresh writer for the SAME partition. Same producer/partition means
        # the server deduplicates any message that was actually persisted before the error.
        old_writer = self._writers.pop(partition_id, None)
        if old_writer is not None:
            self._detach_inflight(partition_id)
            await self._safe_close(old_writer)

        writer = await self._get_or_create_writer(partition_id)
        for seqno, entry in sorted(self._inflight.get(partition_id, {}).items()):
            entry.message.seqno = seqno
            sub_future = await writer.write_with_ack_future(entry.message)
            assert not isinstance(sub_future, list)  # single message -> single future
            entry.sub_future = sub_future
            self._attach_ack(entry)

    async def _migrate_messages(self, partition_id: int, max_seqno: int):
        entries = self._inflight.get(partition_id, {})
        # Snapshot in seqno order so re-routed messages keep their relative order.
        for seqno, entry in sorted(entries.items()):
            if seqno <= max_seqno:
                # Already persisted to the retired partition: resolve as written
                # (offset is unknown because the ack was lost) and do not resend.
                self._inflight.get(partition_id, {}).pop(seqno, None)
                if not entry.user_future.done():
                    entry.user_future.set_result(PublicWriteResult.Written(offset=-1))
                continue

            self._inflight.get(partition_id, {}).pop(seqno, None)
            assert self._chooser is not None
            child_id = self._chooser.choose_partition(entry.message)
            child_writer = await self._get_or_create_writer(child_id)
            new_seqno = self._assign_seqno(child_id, entry.message)
            entry.seqno = new_seqno
            entry.partition_id = child_id
            self._inflight.setdefault(child_id, {})[new_seqno] = entry
            sub_future = await child_writer.write_with_ack_future(entry.message)
            assert not isinstance(sub_future, list)  # single message -> single future
            entry.sub_future = sub_future
            self._attach_ack(entry)

        self._inflight.pop(partition_id, None)

    async def write_with_ack_future(
        self,
        messages: Union[Message, List[Message]],
    ) -> Union[asyncio.Future, List[asyncio.Future]]:
        self._check_closed()
        await self.wait_init()

        input_single_message = not isinstance(messages, list)
        raw = messages if isinstance(messages, list) else [messages]
        converted = [PublicMessage._create_message(m) for m in raw]

        futures: List[asyncio.Future] = []
        async with self._lock:
            assert self._chooser is not None  # resolved by _init(), awaited above
            for message in converted:
                partition_id = self._chooser.choose_partition(message)
                writer = await self._get_or_create_writer(partition_id)
                self._last_write_at[partition_id] = self._loop.time()
                seqno = self._assign_seqno(partition_id, message)
                if seqno in self._inflight.get(partition_id, {}):
                    raise TopicWriterError("duplicate in-flight seqno %d for partition %d" % (seqno, partition_id))

                user_future: asyncio.Future = self._loop.create_future()
                entry = _InflightMessage(
                    message=message,
                    user_future=user_future,
                    seqno=seqno,
                    partition_id=partition_id,
                )
                # Record the message only after the sub-writer accepts it, so a failed
                # admission (buffer timeout, stopped writer) does not leak an in-flight entry
                # whose future would never resolve.
                sub_future = await writer.write_with_ack_future(message)
                assert not isinstance(sub_future, list)  # single message -> single future
                entry.sub_future = sub_future
                self._inflight.setdefault(partition_id, {})[seqno] = entry
                self._attach_ack(entry)
                futures.append(user_future)

        return futures[0] if input_single_message else futures

    async def write(self, messages: Union[Message, List[Message]]):
        await self.write_with_ack_future(messages)

    async def write_with_ack(
        self,
        messages: Union[Message, List[Message]],
    ) -> Union[PublicWriteResultTypes, List[PublicWriteResultTypes]]:
        futures = await self.write_with_ack_future(messages)
        future_list = futures if isinstance(futures, list) else [futures]
        await asyncio.wait(future_list)
        results = [f.result() for f in future_list]
        return results if isinstance(futures, list) else results[0]

    @staticmethod
    async def _idle_reaper(mw_ref: "weakref.ref", idle_timeout: float):
        interval = max(1.0, idle_timeout / 3)
        try:
            while True:
                await asyncio.sleep(interval)
                mw = mw_ref()
                if mw is None or mw._closed:
                    return
                try:
                    await mw._evict_idle_writers()
                except Exception:  # noqa: BLE001
                    logger.debug("multi-writer: idle eviction pass failed", exc_info=True)
                del mw  # drop the strong ref so the writer can be GC'd while we sleep
        except asyncio.CancelledError:
            pass

    async def _evict_idle_writers(self):
        # Close sub-writers with no in-flight messages that have not been written to for the idle
        # timeout; they are recreated on demand. Done under the lock so a concurrent write cannot
        # open a second session for the same producer while we close the old one.
        now = self._loop.time()
        async with self._lock:
            for partition_id in list(self._writers.keys()):
                if self._inflight.get(partition_id):
                    continue  # has un-acked messages -> not idle
                if now - self._last_write_at.get(partition_id, now) < self._idle_timeout:
                    continue
                writer = self._writers.pop(partition_id)
                self._last_write_at.pop(partition_id, None)
                logger.debug("multi-writer: evicting idle sub-writer for partition %d", partition_id)
                await self._safe_close(writer)

    def _pending_user_futures(self) -> List[asyncio.Future]:
        return [entry.user_future for part in self._inflight.values() for entry in part.values()]

    async def _flush_impl(self):
        await self.wait_init()
        async with self._lock:
            writers = list(self._writers.values())
            pending = self._pending_user_futures()
        await asyncio.gather(*(w.flush() for w in writers), return_exceptions=True)
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

    async def flush(self):
        self._check_closed()
        await self._flush_impl()

    async def close(self, *, flush: bool = True):
        if self._closed:
            return

        # Flush BEFORE marking closed (flush() itself refuses to run on a closed writer),
        # but only if init completed — otherwise nothing was written.
        init_done = self._init_task.done() and not self._init_task.cancelled() and self._init_task.exception() is None
        if flush and init_done:
            try:
                await self._flush_impl()
            except BaseException:
                logger.debug("multi-writer: flush during close failed", exc_info=True)

        self._closed = True
        if not self._init_task.done():
            self._init_task.cancel()
        if self._reaper_task is not None and not self._reaper_task.done():
            self._reaper_task.cancel()

        async with self._lock:
            writers = list(self._writers.values())
            self._writers.clear()
            pending = self._pending_user_futures()
            self._inflight.clear()
        await asyncio.gather(*(w.close(flush=False) for w in writers), return_exceptions=True)
        for future in pending:
            if not future.done():
                future.set_exception(TopicWriterStopped())
