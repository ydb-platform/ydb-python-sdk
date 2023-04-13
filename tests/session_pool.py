import pytest

import ydb


def test_close_basic_logic_case_1(driver_sync):
    pool = ydb.SessionPool(driver_sync, 1)
    s = pool.acquire()

    pool.stop()

    with pytest.raises(ValueError):
        pool.acquire()

    pool.release(s)
    assert pool._pool_impl._active_count == 0


def test_close_basic_logic_case_2(driver_sync):
    pool = ydb.SessionPool(driver_sync, 10)
    acquired = []

    for _ in range(10):
        acquired.append(pool.acquire())

    for _ in range(3):
        pool.release(acquired.pop(-1))

    pool.stop()
    assert pool._pool_impl._active_count == 7

    while acquired:
        pool.release(acquired.pop(-1))

    assert pool._pool_impl._active_count == 0

    with pytest.raises(ValueError):
        pool.acquire()

    pool.stop()
