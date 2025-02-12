import argparse
import asyncio
import datetime
import logging

import ydb

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def connect(endpoint: str, database: str) -> ydb.aio.Driver:
    config = ydb.DriverConfig(endpoint=endpoint, database=database)
    config.credentials = ydb.credentials_from_env_variables()
    driver = ydb.aio.Driver(config)
    await driver.wait(5, fail_fast=True)
    return driver


async def recreate_topic(driver: ydb.aio.Driver, topic: str, consumer: str):
    try:
        await driver.topic_client.drop_topic(topic)
    except ydb.SchemeError:
        pass

    await driver.topic_client.create_topic(
        topic,
        consumers=[consumer],
        max_active_partitions=100,
        auto_partitioning_settings=ydb.TopicAutoPartitioningSettings(
            strategy=ydb.TopicAutoPartitioningStrategy.SCALE_UP,
            up_utilization_percent=1,
            down_utilization_percent=1,
            stabilization_window=datetime.timedelta(seconds=1),
        ),
    )


async def write_messages(driver: ydb.aio.Driver, topic: str, id: int = 0):
    async with driver.topic_client.writer(topic) as writer:
        for i in range(100):
            mess = ydb.TopicWriterMessage(data=f"[{id}] mess-{i}", metadata_items={"index": f"{i}"})
            await writer.write(mess)
            await asyncio.sleep(0.01)


async def read_messages(driver: ydb.aio.Driver, topic: str, consumer: str):
    async with driver.topic_client.reader(topic, consumer, auto_partitioning_support=True) as reader:
        count = 0
        while True:
            try:
                mess = await asyncio.wait_for(reader.receive_message(), 5)
                count += 1
                print(mess.data.decode())
                reader.commit(mess)
            except asyncio.TimeoutError:
                assert count == 200
                return


async def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""YDB topic basic example.\n""",
    )
    parser.add_argument("-d", "--database", default="/local", help="Name of the database to use")
    parser.add_argument("-e", "--endpoint", default="grpc://localhost:2136", help="Endpoint url to use")
    parser.add_argument("-p", "--path", default="test-topic", help="Topic name")
    parser.add_argument("-c", "--consumer", default="consumer", help="Consumer name")
    parser.add_argument("-v", "--verbose", default=True, action="store_true")

    args = parser.parse_args()

    if args.verbose:
        logger.addHandler(logging.StreamHandler())

    driver = await connect(args.endpoint, args.database)

    await recreate_topic(driver, args.path, args.consumer)

    await asyncio.gather(
        write_messages(driver, args.path, 0),
        write_messages(driver, args.path, 1),
        read_messages(driver, args.path, args.consumer),
    )


if __name__ == "__main__":
    asyncio.run(main())
