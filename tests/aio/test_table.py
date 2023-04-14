import pytest
import ydb.aio


@pytest.mark.asyncio
class TestSessionPool:
    async def test_checkout_from_stopped_pool(self, driver):
        pool = ydb.aio.SessionPool(driver, 1)
        await pool.stop()

        with pytest.raises(ValueError):
            await pool.acquire()
