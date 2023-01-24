from typing import List, Callable, Union, Mapping, Any

import ydb._topic_writer

from ydb._topic_reader import (
    Reader as TopicReader, ReaderAsyncIO as TopicReaderAsyncIO,
    Selector as TopicSelector,
)

from ydb._topic_writer.topic_writer import (
    Writer as TopicWriter,
    PublicWriterSettings as TopicWriterSettings,
    PublicMessage as TopicWriterMessage,
)

from ydb._topic_writer.topic_writer_asyncio import WriterAsyncIO as TopicWriterAsyncIO


class TopicClientAsyncIO:
    _driver: ydb.aio.Driver
    _credentials: Union[ydb.Credentials, None]

    def __init__(self, driver: ydb.aio.Driver, settings: "TopicClientSettings" = None):
        self._driver = driver

    def topic_reader(self, topic: Union[str, TopicSelector, List[Union[str, TopicSelector]]],
                     consumer: str,
                     commit_batch_time: Union[float, None] = 0.1,
                     commit_batch_count: Union[int, None] = 1000,
                     buffer_size_bytes: int = 50 * 1024 * 1024,
                     sync_commit: bool = False,  # reader.commit(...) will wait commit ack from server
                     on_commit: Callable[["OnCommitEvent"], None] = None,
                     on_get_partition_start_offset: Callable[
                         ["ydb._topic_reader.Events.OnPartitionGetStartOffsetRequest"], "ydb._topic_reader.Events.OnPartitionGetStartOffsetResponse"] = None,
                     on_init_partition: Callable[["StubEvent"], None] = None,
                     on_shutdown_partition: Callable[["StubEvent"], None] = None,
                     decoder: Union[Mapping[int, Callable[[bytes], bytes]], None] = None,
                     deserializer: Union[Callable[[bytes], Any], None] = None,
                     one_attempt_connection_timeout: Union[float, None] = 1,
                     connection_timeout: Union[float, None] = None,
                     retry_policy: Union["ydb._topic_reader.RetryPolicy", None] = None,
                     ) -> TopicReaderAsyncIO:
        raise NotImplementedError()

    def topic_writer(self, topic,
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
                     retry_policy: Union["ydb._topic_writer.RetryPolicy", None] = None,
                     ) -> TopicWriterAsyncIO:
        args = locals()
        del args['self']
        settings = TopicWriterSettings(**args)
        return TopicWriterAsyncIO(self._driver, settings)


class TopicClient:
    def __init__(self, driver, topic_client_settings: "TopicClientSettings" = None):
        pass

    def topic_reader(self, topic: Union[str, TopicSelector, List[Union[str, TopicSelector]]],
                     consumer: str,
                     commit_batch_time: Union[float, None] = 0.1,
                     commit_batch_count: Union[int, None] = 1000,
                     buffer_size_bytes: int = 50 * 1024 * 1024,
                     sync_commit: bool = False,  # reader.commit(...) will wait commit ack from server
                     on_commit: Callable[["OnCommitEvent"], None] = None,
                     on_get_partition_start_offset: Callable[
                         ["ydb._topic_reader.Events.OnPartitionGetStartOffsetRequest"], "ydb._topic_reader.Events.OnPartitionGetStartOffsetResponse"] = None,
                     on_init_partition: Callable[["StubEvent"], None] = None,
                     on_shutdown_partition: Callable[["StubEvent"], None] = None,
                     decoder: Union[Mapping[int, Callable[[bytes], bytes]], None] = None,
                     deserializer: Union[Callable[[bytes], Any], None] = None,
                     one_attempt_connection_timeout: Union[float, None] = 1,
                     connection_timeout: Union[float, None] = None,
                     retry_policy: Union["ydb._topic_reader.RetryPolicy", None] = None,
                     ) -> TopicReader:
        raise NotImplementedError()

    def topic_writer(self, topic,
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
                     retry_policy: Union["ydb._topic_writer.RetryPolicy", None] = None,
                     ) -> TopicWriter:
        raise NotImplementedError()


class TopicClientSettings:
    pass


class StubEvent:
    pass
