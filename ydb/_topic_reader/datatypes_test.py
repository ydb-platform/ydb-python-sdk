import asyncio
import copy
import functools
from collections import deque
from typing import List

import pytest

from ydb._topic_common.test_helpers import wait_condition
from ydb._topic_reader import topic_reader_asyncio
from ydb._topic_reader.datatypes import PartitionSession


@pytest.mark.asyncio
class TestPartitionSession:
    session_comitted_offset = 10

    @pytest.fixture
    def session(self) -> PartitionSession:
        return PartitionSession(
            id=1,
            state=PartitionSession.State.Active,
            topic_path="",
            partition_id=1,
            committed_offset=self.session_comitted_offset,
            reader_reconnector_id=1,
            reader_stream_id=1,
        )

    @pytest.mark.parametrize(
        "offsets_waited,notify_offset,offsets_notified,offsets_waited_rest",
        [
            ([1], 1, [1], []),
            ([1], 10, [1], []),
            ([1, 2, 3], 10, [1, 2, 3], []),
            ([1, 2, 10, 20], 10, [1, 2, 10], [20]),
            ([10, 20], 1, [], [10, 20]),
        ],
    )
    async def test_ack_notify(
        self,
        session,
        offsets_waited: List[int],
        notify_offset: int,
        offsets_notified: List[int],
        offsets_waited_rest: List[int],
    ):
        notified = []

        for offset in offsets_waited:
            fut = asyncio.Future()

            def add_notify(future, notified_offset):
                notified.append(notified_offset)

            fut.add_done_callback(functools.partial(add_notify, notified_offset=offset))
            waiter = PartitionSession.CommitAckWaiter(offset, fut)
            session._ack_waiters.append(waiter)

        session.ack_notify(notify_offset)
        assert session._ack_waiters == deque(
            [PartitionSession.CommitAckWaiter(offset, asyncio.Future()) for offset in offsets_waited_rest]
        )

        await wait_condition(lambda: len(notified) == len(offsets_notified))

        notified.sort()
        assert notified == offsets_notified
        assert session.committed_offset == notify_offset

    # noinspection PyTypeChecker
    @pytest.mark.parametrize(
        "original,add,is_done,result",
        [
            (
                [],
                session_comitted_offset - 5,
                True,
                [],
            ),
            (
                [PartitionSession.CommitAckWaiter(session_comitted_offset + 5, None)],
                session_comitted_offset + 0,
                True,
                [
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 5, None),
                ],
            ),
            (
                [],
                session_comitted_offset + 5,
                False,
                [
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 5, None),
                ],
            ),
            (
                [PartitionSession.CommitAckWaiter(session_comitted_offset + 5, None)],
                session_comitted_offset + 6,
                False,
                [
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 5, None),
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 6, None),
                ],
            ),
            (
                [PartitionSession.CommitAckWaiter(session_comitted_offset + 5, None)],
                session_comitted_offset + 4,
                False,
                [
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 4, None),
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 5, None),
                ],
            ),
            (
                [PartitionSession.CommitAckWaiter(session_comitted_offset + 5, None)],
                session_comitted_offset + 100,
                False,
                [
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 5, None),
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 100, None),
                ],
            ),
            (
                [
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 5, None),
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 100, None),
                ],
                session_comitted_offset + 50,
                False,
                [
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 5, None),
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 50, None),
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 100, None),
                ],
            ),
            (
                [
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 5, None),
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 7, None),
                ],
                session_comitted_offset + 6,
                False,
                [
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 5, None),
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 6, None),
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 7, None),
                ],
            ),
            (
                [
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 5, None),
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 100, None),
                ],
                session_comitted_offset + 6,
                False,
                [
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 5, None),
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 6, None),
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 100, None),
                ],
            ),
            (
                [
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 5, None),
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 100, None),
                ],
                session_comitted_offset + 99,
                False,
                [
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 5, None),
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 99, None),
                    PartitionSession.CommitAckWaiter(session_comitted_offset + 100, None),
                ],
            ),
        ],
    )
    async def test_add_waiter(
        self,
        session,
        original: List[PartitionSession.CommitAckWaiter],
        add: int,
        is_done: bool,
        result: List[PartitionSession.CommitAckWaiter],
    ):
        session._ack_waiters = copy.deepcopy(original)
        res = session.add_waiter(add)
        assert result == session._ack_waiters
        assert res.future.done() == is_done

    async def test_close_notify_waiters(self, session):
        waiter = session.add_waiter(session.committed_offset + 1)
        session.close()

        with pytest.raises(topic_reader_asyncio.TopicReaderCommitToExpiredPartition):
            waiter.future.result()

    async def test_close_twice(self, session):
        session.close()
        session.close()
