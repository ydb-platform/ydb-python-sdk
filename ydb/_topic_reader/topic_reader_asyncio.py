from __future__ import annotations

import asyncio
from typing import Optional

from ydb._topic_wrapper.common import TokenGetterFuncType, IGrpcWrapperAsyncIO
from ydb._topic_wrapper.reader import StreamReadMessage


class PublicAsyncIOReader:
    pass


class ReaderReconnector:
    pass


class ReaderStream:
    _token_getter: Optional[TokenGetterFuncType]
    _session_id: str
    _init_completed: asyncio.Future[None]

    def __init__(self, token_getter: Optional[TokenGetterFuncType]):
        self._token_getter = token_getter
        self._session_id = "not initialized"

    async def start(self, stream: IGrpcWrapperAsyncIO, init_message: StreamReadMessage.InitRequest):
        stream.write(StreamReadMessage.FromClient(client_message=init_message))
        init_response = await stream.receive()  # type: StreamReadMessage.FromServer
        if isinstance(init_response.server_message, StreamReadMessage.InitResponse):
            self._session_id = init_response.server_message.session_id


