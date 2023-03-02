import os.path

import pytest

from ydb import issues


@pytest.mark.asyncio
class TestTopicClientControlPlaneAsyncIO:
    async def test_create_topic(self, driver, database):
        client = driver.topic_client

        topic_path = database + "/my-test-topic"

        await client.create_topic(topic_path)

        with pytest.raises(issues.SchemeError):
            # double create is ok - try create topic with bad path
            await client.create_topic(database)

    async def test_drop_topic(self, driver, topic_path):
        client = driver.topic_client

        await client.drop_topic(topic_path)

        with pytest.raises(issues.SchemeError):
            await client.drop_topic(topic_path)

    async def test_describe_topic(self, driver, topic_path: str, topic_consumer):
        res = await driver.topic_client.describe_topic(topic_path)

        assert res.self.name == os.path.basename(topic_path)

        has_consumer = False
        for consumer in res.consumers:
            if consumer.name == topic_consumer:
                has_consumer = True
                break

        assert has_consumer


class TestTopicClientControlPlane:
    def test_create_topic(self, driver_sync, database):
        client = driver_sync.topic_client

        topic_path = database + "/my-test-topic"

        client.create_topic(topic_path)

        with pytest.raises(issues.SchemeError):
            # double create is ok - try create topic with bad path
            client.create_topic(database)

    def test_drop_topic(self, driver_sync, topic_path):
        client = driver_sync.topic_client

        client.drop_topic(topic_path)

        with pytest.raises(issues.SchemeError):
            client.drop_topic(topic_path)

    def test_describe_topic(self, driver_sync, topic_path: str, topic_consumer):
        res = driver_sync.topic_client.describe_topic(topic_path)

        assert res.self.name == os.path.basename(topic_path)

        has_consumer = False
        for consumer in res.consumers:
            if consumer.name == topic_consumer:
                has_consumer = True
                break

        assert has_consumer
