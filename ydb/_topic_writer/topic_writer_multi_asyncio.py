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

# A writer opened against a partition that is no longer active never finishes its init handshake.
# Since sub-writers are created while the orchestrator lock is held, an unbounded wait there stalls
# every write, flush and repartition, so the wait is capped.
_WRITER_INIT_TIMEOUT = 30.0


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
        # One sequence for the whole writer, seeded above the last_seqno of every producer we
        # open, so a message keeps its number when a split moves it to another partition.
        self._seqno: int = 0
        # partition_id -> last persisted seqno reported by the current sub-writer's init.
        self._server_init_seqno: Dict[int, int] = {}
        # partition_id -> server's last persisted seqno for a retired producer. Final once read:
        # nothing writes under that producer id again.
        self._retired_max_seqno: Dict[int, int] = {}
        # partition_id -> its parents, learned from every DescribeTopic. Needed to ask the whole
        # lineage for the dedup cut, since a message changes producer id as it is migrated.
        self._parents: Dict[int, List[int]] = {}
        # partition_id -> highest acked seqno (fallback maxSeqNo if a probe fails).
        self._max_acked: Dict[int, int] = {}
        # Partitions whose sub-writer is being torn down for a repartition or a recovery. Ack
        # failures from such a writer are expected and must not reach the user.
        self._retiring: set = set()
        # partition_id -> in-progress repartition task, so repeated OVERLOADED for one partition
        # coalesce and close() can cancel and await them.
        self._repartition_tasks: Dict[int, asyncio.Future] = {}
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
        description = res.to_public()
        # Remember parent links while we have them: once a partition is retired it disappears
        # from our routing view, but the dedup cut still has to be able to walk back to it.
        for partition in description.partitions:
            if partition.parent_partition_ids:
                self._parents[partition.partition_id] = list(partition.parent_partition_ids)
        return description

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

    def _build_writer_settings(
        self,
        partition_id: int,
        with_split_hook: bool,
        pin_partition: bool = True,
    ) -> PublicWriterSettings:
        return PublicWriterSettings(
            topic=self._settings.topic,
            producer_id="%s-%d" % (self._prefix, partition_id),
            # Unpinned (pin_partition=False) leaves the session routed by message group instead,
            # which is the only way to reach a partition that is no longer active.
            partition_id=partition_id if pin_partition else None,
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
            # Seed the seqno cursor from the producer's last persisted seqno so a
            # stable producer_id_prefix resumes numbering instead of colliding. The wait is
            # bounded: a partition that went inactive between the routing decision and this call
            # never completes init, and we hold the orchestrator lock here.
            try:
                init_info = await asyncio.wait_for(writer.wait_init(), timeout=_WRITER_INIT_TIMEOUT)
            except BaseException:
                # Do not register a writer that never became usable, and do not leak its stream.
                await self._safe_close(writer)
                raise
            self._writers[partition_id] = writer
            self._last_write_at[partition_id] = self._loop.time()
            last_seqno = init_info.last_seqno or 0
            self._server_init_seqno[partition_id] = last_seqno
            # Lift the shared cursor above every producer we have opened: each partition has its
            # own producer_id and therefore its own persisted history, and a seqno we hand out
            # must be new in whichever partition the message ends up in.
            self._seqno = max(self._seqno, last_seqno)
        return writer

    def _assign_seqno(self, message: PublicMessage) -> int:
        """Draw the message's sequence number from the writer-wide cursor.

        One counter for the whole multi-writer, not one per partition: that is what lets a
        message keep its seqno when a split moves it to a child. A per-partition number would
        mean nothing in another partition's sequence, so it would have to be reassigned -- and a
        message that changes identity mid-flight cannot be reconciled with the attempt that may
        already have been persisted. Both reference implementations do the same (C++
        `TProducer` `CurrentSeqNo`, Go `orchestrator.currentSeqNo`).
        """
        if self._settings.auto_seqno:
            self._seqno += 1
            message.seqno = self._seqno
            return self._seqno

        if message.seqno is None:
            # Bad input, not a stopped writer: the caller disabled auto_seqno and owes us
            # a seqno. Reporting this as TopicWriterStopped misleads retry handling.
            raise TopicWriterError("message seqno is required when auto_seqno is disabled")
        self._seqno = max(self._seqno, message.seqno)
        return message.seqno

    def _schedule_repartition(self, partition_id: int) -> None:
        """Start (or join) the repartition of one partition.

        A burst of OVERLOADED for the same partition must not start several concurrent
        recoveries of it, and the writer must own the task so close() can cancel and await it
        instead of leaving it to describe topics and open sub-writers after shutdown.
        """
        if self._closed:
            return
        running = self._repartition_tasks.get(partition_id)
        if running is not None and not running.done():
            return

        task = self._loop.create_task(self._on_partition_overloaded(partition_id))
        task.set_name("multiwriter repartition %d" % partition_id)
        self._repartition_tasks[partition_id] = task

        def _forget(finished: asyncio.Future) -> None:
            if self._repartition_tasks.get(partition_id) is finished:
                del self._repartition_tasks[partition_id]

        task.add_done_callback(_forget)

    def _make_overloaded_hook(self, partition_id: int):
        def hook(err: BaseException) -> bool:
            if _is_overloaded(err):
                logger.debug("multi-writer: partition %d overloaded, re-describing (split/merge)", partition_id)
                self._schedule_repartition(partition_id)
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
        if exc is not None:
            if isinstance(exc, TopicWriterPartitionSplitError) or partition_id in self._retiring:
                # Expected while the partition is torn down: leave the message in flight so the
                # repartition (or the in-place recovery) resends it.
                return
            self._inflight.get(partition_id, {}).pop(seqno, None)
            if not entry.user_future.done():
                entry.user_future.set_exception(exc)
            return

        # A success is always honoured, including one that lands while the sub-writer is being
        # closed: the server persisted the message, and ignoring the ack would leave the dedup
        # cut too low and resend an already-written message to the child.
        self._inflight.get(partition_id, {}).pop(seqno, None)
        self._max_acked[partition_id] = max(self._max_acked.get(partition_id, 0), seqno)
        if not entry.user_future.done():
            entry.user_future.set_result(sub_future.result())

    async def _quiesce_writer(self, partition_id: int) -> None:
        """Close the partition's sub-writer and settle the acks it was still holding.

        Closing fails every pending ack, which must not reach the user because those messages
        are about to be resent. ``_retiring`` suppresses exactly those failures while letting
        successes through, and the yield below gives already-scheduled ack callbacks a chance to
        run before the caller reads the dedup cut.
        """
        self._retiring.add(partition_id)
        writer = self._writers.pop(partition_id, None)
        if writer is not None:
            await self._safe_close(writer)
        await asyncio.sleep(0)

    @staticmethod
    async def _safe_close(writer: WriterAsyncIO) -> None:
        # A sub-writer stopped by the split hook re-raises TopicWriterPartitionSplitError from
        # close(); closing a writer we are discarding must never abort a repartition.
        try:
            await writer.close(flush=False)
        except Exception:  # noqa: BLE001
            logger.debug("multi-writer: ignoring error while closing a discarded sub-writer", exc_info=True)

    async def _probe_server_seqno(self, partition_id: int) -> int:
        """Ask the server how far this partition's producer actually got.

        The answer must come from the server, not from the acks we happened to receive: a message
        can be persisted and its ack lost when the session dies, and treating it as unwritten is
        exactly what produces a duplicate on resend.

        The session is opened WITHOUT a partition id. By the time we ask, the partition is
        usually inactive, and a session pinned to an inactive partition never completes its init
        handshake -- it would hang here holding the orchestrator lock. Unpinned, the session is
        routed by message group and still reports this producer's persisted seqno. Both reference
        implementations read the cut the same way (C++ `CreateWriteSession(..., false)` sets only
        ProducerId/MessageGroupId, Go `createNonDirectWriter` only WithProducerID).

        Results are cached: a retired producer receives no further writes, so its value is final.
        """
        cached = self._retired_max_seqno.get(partition_id)
        if cached is not None:
            return cached

        probe = WriterAsyncIO(
            self._driver,
            self._build_writer_settings(partition_id, with_split_hook=False, pin_partition=False),
        )
        try:
            init_info = await asyncio.wait_for(probe.wait_init(), timeout=_WRITER_INIT_TIMEOUT)
        finally:
            await self._safe_close(probe)

        last_seqno = init_info.last_seqno or 0
        self._retired_max_seqno[partition_id] = last_seqno
        logger.debug("multi-writer: partition %d persisted up to seqno %d (server)", partition_id, last_seqno)
        return last_seqno

    def _lineage(self, partition_id: int) -> List[int]:
        """The partition plus every ancestor we know of.

        A message carries one seqno for its whole life, but it is written under the producer id of
        whichever partition held it at the time -- and a repartition moves it on. So "was seqno N
        already persisted?" has to be asked of the entire lineage, not just the partition we are
        retiring now. Merge children have two parents, so this walks a graph, not a chain.
        """
        chain = [partition_id]
        seen = {partition_id}
        frontier = [partition_id]
        while frontier:
            for parent in self._parents.get(frontier.pop(), ()):
                if parent in seen:
                    continue
                seen.add(parent)
                chain.append(parent)
                frontier.append(parent)
        return chain

    async def _max_seqno_cut(self, partition_id: int) -> int:
        """Dedup cut for a repartition: messages at or below it were persisted to the retiring
        lineage and must not be resent to the child.

        Raises if the server cannot be asked. Falling back to the highest ack we saw would look
        like it worked while quietly reopening the duplicate window this exists to close; the
        caller turns the failure into terminal errors on the affected messages instead.
        """
        acked = self._max_acked.get(partition_id, 0)
        lineage = self._lineage(partition_id)
        cut = acked
        for ancestor in lineage:
            cut = max(cut, await self._probe_server_seqno(ancestor))
        # Worth seeing: this number alone decides resend vs. drop, so a cut below `acked` would
        # mean duplicates and one above it would mean loss.
        logger.debug(
            "multi-writer: dedup cut for partition %d is %d (lineage %s, highest ack seen %d)",
            partition_id,
            cut,
            lineage,
            acked,
        )
        return cut

    @staticmethod
    def _children_cover_parent(parent, children: List[_PartitionInfo]) -> bool:
        """True if the children's key ranges tile the parent's range with no gap.

        A split becomes visible in DescribeTopic one child at a time, so a mid-split describe can
        report a single child of two. Retiring the parent on that view would leave the rest of its
        key space unowned, and routing -- which locates a partition by the greatest from_bound at
        or below the key -- would then send those keys to the left sibling instead: one key on two
        branches of the partition graph.
        """
        parent_range = getattr(parent, "key_range", None)
        if parent_range is None:
            return True  # topic without key ranges: nothing to verify (and nothing that splits)

        ranges = []
        for child in children:
            child_range = getattr(child, "key_range", None)
            if child_range is None:
                return False  # inconsistent with a bounded parent -> treat the view as incomplete
            ranges.append((child_range.from_bound, child_range.to_bound))
        ranges.sort(key=lambda r: r[0])

        # Coverage is "at least the parent's range", not "exactly": a merge child owns the ranges
        # of both its parents, so it legitimately covers more than the parent we started from.
        parent_end = parent_range.to_bound  # empty == end of the key space
        cursor = parent_range.from_bound  # covered up to here, exclusive
        for from_bound, to_bound in ranges:
            if from_bound > cursor:
                return False  # gap between the covered prefix and this child
            if not to_bound:
                return True  # this child runs to the end of the key space
            if to_bound > cursor:
                cursor = to_bound
            if parent_end and cursor >= parent_end:
                return True
        return False

    async def _discover_children(self, partition_id: int) -> List[_PartitionInfo]:
        """Re-describe until the split/merge children of ``partition_id`` appear.

        Returns an empty list if none appear (ordinary transient overload), or if the children
        that did appear never covered the parent's key range -- an incomplete graph is a
        retry-later state, not a topology we may commit to.
        """
        parent = self._partitions.get(partition_id)
        children: List[_PartitionInfo] = []
        for attempt in range(_REPARTITION_DISCOVER_ATTEMPTS):
            description = await self._describe()
            children = [
                p
                for p in description.partitions
                if p.active and not p.child_partition_ids and partition_id in p.parent_partition_ids
            ]
            if children and self._children_cover_parent(parent, children):
                return children
            if attempt + 1 < _REPARTITION_DISCOVER_ATTEMPTS:
                await asyncio.sleep(_REPARTITION_DISCOVER_DELAY)
        if children:
            logger.warning(
                "multi-writer: children of partition %d never covered its key range; keeping the"
                " partition instead of routing keys into the uncovered range",
                partition_id,
            )
        return []

    def _fail_partition_inflight(self, partition_id: int, err: BaseException) -> None:
        """Give every in-flight message of an unusable partition a terminal outcome.

        Once repartition and recovery have both failed there is no sub-writer left to ack these
        messages, so their futures would never resolve and flush()/close(flush=True) would wait
        on them forever. An accepted message must always end in success or failure.
        """
        entries = self._inflight.pop(partition_id, {})
        if not entries:
            return
        logger.error(
            "multi-writer: partition %d is unusable, failing %d in-flight messages: %s",
            partition_id,
            len(entries),
            err,
        )
        for entry in entries.values():
            entry.sub_future = None
            if not entry.user_future.done():
                entry.user_future.set_exception(err)

    async def _on_partition_overloaded(self, partition_id: int):
        """Entry point for the OVERLOADED hook: handle a repartition, or recover on failure.

        The hook force-stops the sub-writer, so if handling fails we must not leave the
        partition's messages stranded — recreate the writer and resend them. If that fails too,
        the messages are failed explicitly rather than left without an owner.
        """
        try:
            await self._handle_repartition(partition_id)
            return
        except asyncio.CancelledError:
            raise
        except Exception as err:
            logger.exception("multi-writer: repartition of partition %d failed; recovering", partition_id)
            failure: BaseException = err

        try:
            async with self._lock:
                if partition_id in self._partitions:
                    await self._recover_partition(partition_id)
                    return
        except asyncio.CancelledError:
            raise
        except Exception as err:
            logger.exception("multi-writer: recovery of partition %d failed", partition_id)
            failure = err

        async with self._lock:
            self._fail_partition_inflight(partition_id, failure)

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
            try:
                for old in retired:
                    await self._quiesce_writer(old)

                for old in retired:
                    if self._inflight.get(old):
                        await self._migrate_messages(old, await self._max_seqno_cut(old))
                    else:
                        self._inflight.pop(old, None)
            finally:
                self._retiring.difference_update(retired)

    async def _recover_partition(self, partition_id: int):
        # The hook stopped the sub-writer; drop it and resend the partition's in-flight
        # messages to a fresh writer for the SAME partition, keeping their seqnos.
        await self._quiesce_writer(partition_id)
        try:
            writer = await self._get_or_create_writer(partition_id)

            # The partition is still active, so this writer's init carries the server's real last
            # persisted seqno -- an exact dedup cut, unlike the split case. Messages at or below it
            # were written and their ack was lost with the stream; resending one is not idempotent
            # here, because the writer rejects a seqno it has already seen ("Message seqno is
            # duplicated") before the server ever gets a chance to deduplicate it, and that error
            # would abort the resend of every message after it.
            cut = max(self._server_init_seqno.get(partition_id, 0), self._max_acked.get(partition_id, 0))
            for seqno, entry in sorted(self._inflight.get(partition_id, {}).items()):
                if seqno <= cut:
                    self._inflight.get(partition_id, {}).pop(seqno, None)
                    self._max_acked[partition_id] = max(self._max_acked.get(partition_id, 0), seqno)
                    if not entry.user_future.done():
                        entry.user_future.set_result(PublicWriteResult.Written(offset=-1))
                    continue
                entry.message.seqno = seqno
                sub_future = await writer.write_with_ack_future(entry.message)
                assert not isinstance(sub_future, list)  # single message -> single future
                entry.sub_future = sub_future
                self._attach_ack(entry)
        finally:
            self._retiring.discard(partition_id)

    def _migration_conflict(
        self,
        child_id: int,
        seqno: int,
        target: Dict[int, _InflightMessage],
    ) -> Optional[BaseException]:
        """Why this seqno cannot be carried into ``child_id``, or None if it can.

        Carrying the number over is only safe while it is free in the child's sequence, and two
        things can take it: another in-flight message (manual seqnos are checked for uniqueness
        only within one partition, so a merge can bring two equal ones into the same child), or
        the child's own producer, if a stable ``producer_id_prefix`` already wrote that far in an
        earlier run. In the second case the sub-writer would reject the resend as a duplicate
        seqno and take down the migration of every message behind it.
        """
        if seqno in target:
            return TopicWriterError(
                "seqno %d is already in flight on partition %d: manual seqnos must be unique"
                " across partitions to survive a repartition" % (seqno, child_id)
            )
        server_seqno = self._server_init_seqno.get(child_id, 0)
        if seqno <= server_seqno:
            return TopicWriterError(
                "seqno %d cannot be resent to partition %d: its producer has already persisted"
                " up to %d" % (seqno, child_id, server_seqno)
            )
        return None

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

            assert self._chooser is not None
            try:
                child_id = self._chooser.choose_partition(entry.message)
                child_writer = await self._get_or_create_writer(child_id)
            except Exception as err:  # noqa: BLE001
                # The message cannot be placed: no ready leaf owns its key, or the child itself
                # went inactive (splits cascade). Fail it and everything after it -- dropping
                # would lose the message silently, and skipping ahead would reorder the key.
                logger.warning(
                    "multi-writer: cannot migrate messages of partition %d, failing seqno >= %d: %s",
                    partition_id,
                    seqno,
                    err,
                )
                for pending_seqno, pending in sorted(entries.items()):
                    if pending_seqno < seqno:
                        continue
                    self._inflight.get(partition_id, {}).pop(pending_seqno, None)
                    if not pending.user_future.done():
                        pending.user_future.set_exception(err)
                break

            if self._inflight.get(partition_id, {}).get(seqno) is not entry:
                continue  # acked while the child writer was being opened -> nothing to resend

            # The message keeps its seqno: only its target partition changes. The number comes
            # from the writer-wide sequence, so it stays valid -- and unchanged identity is what
            # lets the child's cut still describe this exact message.
            target = self._inflight.setdefault(child_id, {})
            conflict = self._migration_conflict(child_id, seqno, target)
            if conflict is not None:
                logger.error("multi-writer: %s", conflict)
                self._inflight.get(partition_id, {}).pop(seqno, None)
                if not entry.user_future.done():
                    entry.user_future.set_exception(conflict)
                continue

            self._inflight.get(partition_id, {}).pop(seqno, None)
            entry.partition_id = child_id
            entry.message.seqno = seqno
            target[seqno] = entry
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
                seqno = self._assign_seqno(message)
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

        # Stop repartitions before touching the writers: an in-flight one holds the lock, opens
        # sub-writers and mutates the topology, none of which may outlive the multi-writer.
        repartitions = list(self._repartition_tasks.values())
        self._repartition_tasks.clear()
        for task in repartitions:
            if not task.done():
                task.cancel()
        if repartitions:
            await asyncio.gather(*repartitions, return_exceptions=True)

        async with self._lock:
            writers = list(self._writers.values())
            self._writers.clear()
            pending = self._pending_user_futures()
            self._inflight.clear()
        await asyncio.gather(*(w.close(flush=False) for w in writers), return_exceptions=True)
        for future in pending:
            if not future.done():
                future.set_exception(TopicWriterStopped())
