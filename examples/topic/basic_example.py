import argparse
import asyncio
import logging

import ydb


async def connect(endpoint: str, database: str) -> ydb.aio.Driver:
    config = ydb.DriverConfig(endpoint=endpoint, database=database)
    config.credentials = ydb.credentials_from_env_variables()
    driver = ydb.aio.Driver(config)
    await driver.wait(15)
    return driver


async def create_topic(driver: ydb.aio.Driver, topic: str, consumer: str):
    try:
        await driver.topic_client.drop_topic(topic)
    except ydb.SchemeError:
        pass

    await driver.topic_client.create_topic(topic, consumers=[consumer])


async def write_messages(driver: ydb.aio.Driver, topic: str):
    async with driver.topic_client.writer(topic) as writer:
        for i in range(10):
            await writer.write(f"mess-{i}")
            await asyncio.sleep(1)


async def read_messages(driver: ydb.aio.Driver, topic: str, consumer: str):
    async with driver.topic_client.reader(topic, consumer) as reader:
        while True:
            try:
                mess = await asyncio.wait_for(reader.receive_message(), 5)
                print()
                print(mess.seqno)
                print(mess.created_at)
                print(mess.data.decode())
                reader.commit(mess)
            except asyncio.TimeoutError:
                return


async def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""YDB topic basic example.\n""",
    )
    parser.add_argument("-d", "--database", default="/local", help="Name of the database to use")
    parser.add_argument("-e", "--endpoint", default="grpc://localhost:2136", help="Endpoint url to use")
    parser.add_argument("-p", "--path",  default="test-topic", help="Topic name")
    parser.add_argument("-c", "--consumer", default="consumer", help="Consumer name")
    parser.add_argument("-v", "--verbose", default=False, action="store_true")
    parser.add_argument("-s", "--skip-drop-and-create-topic", default=False, action="store_true", help="Use existed topic, skip remove it and re-create")

    args = parser.parse_args()

    if args.verbose:
        logger = logging.getLogger("topicexample")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.StreamHandler())

    driver = await connect(args.endpoint, args.database)
    if not args.skip_drop_and_create_topic:
        await create_topic(driver, args.path, args.consumer)

    await asyncio.gather(
        write_messages(driver, args.path),
        read_messages(driver, args.path, args.consumer),
    )


if __name__ == '__main__':
    asyncio.run(main())