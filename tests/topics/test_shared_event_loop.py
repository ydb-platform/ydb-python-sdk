from __future__ import annotations

import asyncio
import threading

from ydb._topic_common.common import _get_shared_event_loop, _shutdown_shared_event_loop


def _shared_loop_threads_alive() -> bool:
    return any(t.name == "Common ydb topic event loop" and t.is_alive() for t in threading.enumerate())


def test_shared_event_loop_shutdown_joins_thread():
    loop = _get_shared_event_loop()
    assert _shared_loop_threads_alive()

    fut = asyncio.run_coroutine_threadsafe(asyncio.sleep(0.01), loop)
    assert fut.result(1) is None

    _shutdown_shared_event_loop()
    assert not _shared_loop_threads_alive()

    # Loop can be recreated after shutdown (e.g. another client later in-process).
    loop2 = _get_shared_event_loop()
    fut2 = asyncio.run_coroutine_threadsafe(asyncio.sleep(0.01), loop2)
    assert fut2.result(1) is None

    _shutdown_shared_event_loop()
    assert not _shared_loop_threads_alive()
