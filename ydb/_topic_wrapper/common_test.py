import asyncio

import pytest

from .common import callback_from_asyncio


@pytest.mark.asyncio
class Test:
    async def test_callback_from_asyncio(self):
        class TestError(Exception):
            pass

        def sync_success():
            return 1

        assert await callback_from_asyncio(sync_success) == 1

        def sync_failed():
            raise TestError()

        with pytest.raises(TestError):
            await callback_from_asyncio(sync_failed)

        async def async_success():
            await asyncio.sleep(0)
            return 1

        assert await callback_from_asyncio(async_success) == 1

        async def async_failed():
            await asyncio.sleep(0)
            raise TestError()

        with pytest.raises(TestError):
            await callback_from_asyncio(async_failed)
