from unittest import mock

import pytest

from . import issues, topic


class _CapturedWriter:
    """Records what the client factory built, so the test can check the wiring only."""

    last = None

    def __init__(self, driver, settings, _parent=None):
        self.driver = driver
        self.settings = settings
        self.parent = _parent
        type(self).last = self


@pytest.fixture
def async_client():
    client = topic.TopicClientAsyncIO(mock.Mock())
    yield client
    client._closed = True  # skip the real close: nothing was actually opened


@pytest.fixture
def sync_client():
    # The sync client takes settings positionally, unlike the async one.
    client = topic.TopicClient(mock.Mock(), None)
    yield client
    client._closed = True


@pytest.mark.parametrize(
    "client_fixture, patched", [("async_client", "TopicWriterMultiAsyncIO"), ("sync_client", "TopicWriterMulti")]
)
def test_multiwriter_factory_passes_settings_through(client_fixture, patched, request, monkeypatch):
    """The factory is the only place the caller's arguments turn into writer settings.

    A silently dropped argument here (a codec, a chooser, a buffer limit) would leave the writer
    running on defaults while the caller believes otherwise, so every one of them is checked.
    """
    client = request.getfixturevalue(client_fixture)
    monkeypatch.setattr(topic, patched, _CapturedWriter)

    chooser = topic.TopicWriterPartitionByKeyKafka()
    writer = client.multiwriter(
        "/local/topic",
        producer_id_prefix="pfx",
        partition_chooser=chooser,
        auto_seqno=False,
        auto_created_at=False,
        codec=topic.TopicCodec.RAW,
        max_buffer_size_bytes=1024,
        max_buffer_messages=10,
        buffer_wait_timeout_sec=1.5,
        writer_idle_timeout_sec=30,
    )

    assert writer is _CapturedWriter.last
    assert writer.parent is client, "the writer must keep the client alive"

    settings = writer.settings
    assert settings.topic == "/local/topic"
    assert settings.producer_id_prefix == "pfx"
    assert settings.partition_chooser is chooser
    assert settings.auto_seqno is False
    assert settings.auto_created_at is False
    assert settings.codec == topic.TopicCodec.RAW
    assert settings.max_buffer_size_bytes == 1024
    assert settings.max_buffer_messages == 10
    assert settings.buffer_wait_timeout_sec == 1.5
    assert settings.writer_idle_timeout_sec == 30
    # Encoding runs on the client's shared pool unless the caller brought its own.
    assert settings.encoder_executor is client._executor


@pytest.mark.parametrize(
    "client_fixture, patched", [("async_client", "TopicWriterMultiAsyncIO"), ("sync_client", "TopicWriterMulti")]
)
def test_multiwriter_keeps_a_caller_supplied_executor(client_fixture, patched, request, monkeypatch):
    client = request.getfixturevalue(client_fixture)
    monkeypatch.setattr(topic, patched, _CapturedWriter)
    executor = mock.Mock()

    writer = client.multiwriter("/local/topic", encoder_executor=executor)

    assert writer.settings.encoder_executor is executor


@pytest.mark.parametrize("client_fixture", ["async_client", "sync_client"])
def test_multiwriter_refuses_a_closed_client(client_fixture, request):
    client = request.getfixturevalue(client_fixture)
    client._closed = True

    with pytest.raises(issues.Error):
        client.multiwriter("/local/topic")


def test_unclosed_sync_client_is_closed_on_delete():
    """__del__ is the last chance to release the executor a forgotten client still holds."""
    client = topic.TopicClient(mock.Mock(), None)
    with mock.patch.object(topic.TopicClient, "close") as close:
        client.__del__()
    close.assert_called_once()
    client._closed = True


def test_delete_of_a_closed_sync_client_does_nothing():
    client = topic.TopicClient(mock.Mock(), None)
    client._closed = True
    with mock.patch.object(topic.TopicClient, "close") as close:
        client.__del__()
    close.assert_not_called()
