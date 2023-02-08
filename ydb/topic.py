import datetime
import warnings
from typing import List, Callable, Union, Mapping, Any, Optional, Dict

from . import aio, Credentials, _apis

from . import scheme

from ._grpc.grpcwrapper.ydb_topic_public_types import (
    DropTopicRequestParams as _DropTopicRequestParams,
    PublicCodec as TopicCodec,
    PublicConsumer as TopicConsumer,
    PublicMeteringMode as TopicMeteringMode,
    DescribeTopicRequestParams as _DescribeTopicRequestParams,
)

from ._topic_reader.topic_reader import (
    PublicReaderSettings as TopicReaderSettings,
    Reader as TopicReader,
    Selector as TopicSelector,
    Events as TopicReaderEvents,
    RetryPolicy as TopicReaderRetryPolicy,
    StubEvent as TopicReaderStubEvent,
)

from ._topic_reader.topic_reader_asyncio import (
    PublicAsyncIOReader as TopicReaderAsyncIO,
)

from ._topic_writer.topic_writer import (  # noqa: F401
    Writer as TopicWriter,
    PublicWriterSettings as TopicWriterSettings,
    PublicMessage as TopicWriterMessage,
    RetryPolicy as TopicWriterRetryPolicy,
)

from ._topic_common.common import (
    wrap_operation as _wrap_operation,
    create_result_wrapper as _create_result_wrapper,
)

from ydb._topic_writer.topic_writer_asyncio import WriterAsyncIO as TopicWriterAsyncIO

from ._grpc.grpcwrapper import ydb_topic as _ydb_topic
from ._grpc.grpcwrapper import ydb_topic_public_types as _ydb_topic_public_types


class TopicClientAsyncIO:
    _driver: aio.Driver
    _credentials: Union[Credentials, None]

    def __init__(self, driver: aio.Driver, settings: "TopicClientSettings" = None):
        self._driver = driver

    async def create_topic(
        self,
        path: str,
        min_active_partitions: Optional[
            int
        ] = None,  # Minimum partition count auto merge would stop working at.
        partition_count_limit: Optional[
            int
        ] = None,  # Limit for total partition count, including active (open for write) and read-only partitions.
        retention_period: Optional[
            datetime.timedelta
        ] = None,  # How long data in partition should be stored
        retention_storage_mb: Optional[
            int
        ] = None,  # How much data in partition should be stored
        # List of allowed codecs for writers.
        # Writes with codec not from this list are forbidden.
        supported_codecs: Optional[List[Union[TopicCodec, int]]] = None,
        partition_write_speed_bytes_per_second: Optional[
            int
        ] = None,  # Partition write speed in bytes per second
        partition_write_burst_bytes: Optional[
            int
        ] = None,  # Burst size for write in partition, in bytes
        # User and server attributes of topic. Server attributes starts from "_" and will be validated by server.
        attributes: Optional[Dict[str, str]] = None,
        # List of consumers for this topic
        consumers: Optional[List[Union[TopicConsumer, str]]] = None,
        # Metering mode for the topic in a serverless database
        metering_mode: Optional[TopicMeteringMode] = None,
    ):
        args = locals().copy()
        del args["self"]
        req = _ydb_topic_public_types.CreateTopicRequestParams(**args)
        req = _ydb_topic.CreateTopicRequest.from_public(req)
        await self._driver(
            req.to_proto(),
            _apis.TopicService.Stub,
            _apis.TopicService.CreateTopic,
            _wrap_operation,
        )

    async def describe(self, path: str, include_stats: bool = False):
        args = locals().copy()
        del args["self"]
        req = _DescribeTopicRequestParams(**args)
        res = await self._driver(
            req.to_proto(),
            _apis.TopicService.Stub,
            _apis.TopicService.DescribeTopic,
            _create_result_wrapper(_ydb_topic.DescribeTopicResult),
        )  # type: _ydb_topic.DescribeTopicResult
        return res.to_public()

    async def drop_topic(self, path: str):
        req = _DropTopicRequestParams(path=path)
        await self._driver(
            req.to_proto(),
            _apis.TopicService.Stub,
            _apis.TopicService.DropTopic,
            _wrap_operation,
        )

    def topic_reader(
        self,
        consumer: str,
        topic: str,
        buffer_size_bytes: int = 50 * 1024 * 1024,
        # on_commit: Callable[["Events.OnCommit"], None] = None
        # on_get_partition_start_offset: Callable[
        #     ["Events.OnPartitionGetStartOffsetRequest"],
        #     "Events.OnPartitionGetStartOffsetResponse",
        # ] = None
        # on_partition_session_start: Callable[["StubEvent"], None] = None
        # on_partition_session_stop: Callable[["StubEvent"], None] = None
        # on_partition_session_close: Callable[["StubEvent"], None] = None  # todo?
        # decoder: Union[Mapping[int, Callable[[bytes], bytes]], None] = None
        # deserializer: Union[Callable[[bytes], Any], None] = None
        # one_attempt_connection_timeout: Union[float, None] = 1
        # connection_timeout: Union[float, None] = None
        # retry_policy: Union["RetryPolicy", None] = None
    ) -> TopicReaderAsyncIO:
        args = locals()
        del args["self"]
        settings = TopicReaderSettings(**args)
        return TopicReaderAsyncIO(self._driver, settings)

    def topic_writer(
        self,
        topic,
        *,
        producer_and_message_group_id: str,
        session_metadata: Mapping[str, str] = None,
        encoders: Union[Mapping[int, Callable[[bytes], bytes]], None] = None,
        serializer: Union[Callable[[Any], bytes], None] = None,
        send_buffer_count: Union[int, None] = 10000,
        send_buffer_bytes: Union[int, None] = 100 * 1024 * 1024,
        partition_id: Union[int, None] = None,
        codec: Union[int, None] = None,
        codec_autoselect: bool = True,
        auto_seqno: bool = True,
        auto_created_at: bool = True,
        get_last_seqno: bool = False,
        retry_policy: Union["TopicWriterRetryPolicy", None] = None,
    ) -> TopicWriterAsyncIO:
        args = locals()
        del args["self"]
        settings = TopicWriterSettings(**args)
        return TopicWriterAsyncIO(self._driver, settings)


class TopicClient:
    def __init__(self, driver, topic_client_settings: "TopicClientSettings" = None):
        pass

    def topic_reader(
        self,
        topic: Union[str, TopicSelector, List[Union[str, TopicSelector]]],
        consumer: str,
        commit_batch_time: Union[float, None] = 0.1,
        commit_batch_count: Union[int, None] = 1000,
        buffer_size_bytes: int = 50 * 1024 * 1024,
        sync_commit: bool = False,  # reader.commit(...) will wait commit ack from server
        on_commit: Callable[["TopicReaderStubEvent"], None] = None,
        on_get_partition_start_offset: Callable[
            ["TopicReaderEvents.OnPartitionGetStartOffsetRequest"],
            "TopicReaderEvents.OnPartitionGetStartOffsetResponse",
        ] = None,
        on_init_partition: Callable[["StubEvent"], None] = None,
        on_shutdown_partition: Callable[["StubEvent"], None] = None,
        decoder: Union[Mapping[int, Callable[[bytes], bytes]], None] = None,
        deserializer: Union[Callable[[bytes], Any], None] = None,
        one_attempt_connection_timeout: Union[float, None] = 1,
        connection_timeout: Union[float, None] = None,
        retry_policy: Union["TopicReaderRetryPolicy", None] = None,
    ) -> TopicReader:
        raise NotImplementedError()

    def topic_writer(
        self,
        topic,
        producer_and_message_group_id: str,
        session_metadata: Mapping[str, str] = None,
        encoders: Union[Mapping[int, Callable[[bytes], bytes]], None] = None,
        serializer: Union[Callable[[Any], bytes], None] = None,
        send_buffer_count: Union[int, None] = 10000,
        send_buffer_bytes: Union[int, None] = 100 * 1024 * 1024,
        partition_id: Union[int, None] = None,
        codec: Union[int, None] = None,
        codec_autoselect: bool = True,
        auto_seqno: bool = True,
        auto_created_at: bool = True,
        get_last_seqno: bool = False,
        retry_policy: Union["TopicWriterRetryPolicy", None] = None,
    ) -> TopicWriter:
        raise NotImplementedError()


class TopicClientSettings:
    pass


class StubEvent:
    pass
