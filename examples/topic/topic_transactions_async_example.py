import asyncio
import argparse
import logging
import ydb


async def connect(endpoint: str, database: str) -> ydb.aio.Driver:
    config = ydb.DriverConfig(endpoint=endpoint, database=database)
    config.credentials = ydb.credentials_from_env_variables()
    driver = ydb.aio.Driver(config)
    await driver.wait(5, fail_fast=True)
    return driver


async def create_topic(driver: ydb.aio.Driver, topic: str, consumer: str):
    try:
        await driver.topic_client.drop_topic(topic)
    except ydb.SchemeError:
        pass

    await driver.topic_client.create_topic(topic, consumers=[consumer])


async def write_with_tx_example(driver: ydb.aio.Driver, topic: str, message_count: int = 10):
    async with ydb.aio.QuerySessionPool(driver) as session_pool:

        async def callee(tx: ydb.aio.QueryTxContext):
            tx_writer: ydb.TopicTxWriterAsyncIO = driver.topic_client.tx_writer(tx, topic)

            for i in range(message_count):
                async with await tx.execute(query=f"select {i} as res;") as result_stream:
                    async for result_set in result_stream:
                        message = str(result_set.rows[0]["res"])
                        await tx_writer.write(ydb.TopicWriterMessage(message))
                        print(f"Message {result_set.rows[0]['res']} was written with tx.")

        await session_pool.retry_tx_async(callee)


async def read_with_tx_example(driver: ydb.aio.Driver, topic: str, consumer: str, message_count: int = 10):
    async with driver.topic_client.reader(topic, consumer) as reader:
        async with ydb.aio.QuerySessionPool(driver) as session_pool:
            for _ in range(message_count):

                async def callee(tx: ydb.aio.QueryTxContext):
                    batch = await reader.receive_batch_with_tx(tx, max_messages=1)
                    print(f"Message {batch.messages[0].data.decode()} was read with tx.")

                await session_pool.retry_tx_async(callee)


async def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""YDB topic basic example.\n""",
    )
    parser.add_argument("-d", "--database", default="/local", help="Name of the database to use")
    parser.add_argument("-e", "--endpoint", default="grpc://localhost:2136", help="Endpoint url to use")
    parser.add_argument("-p", "--path", default="test-topic", help="Topic name")
    parser.add_argument("-c", "--consumer", default="consumer", help="Consumer name")
    parser.add_argument("-v", "--verbose", default=False, action="store_true")
    parser.add_argument(
        "-s",
        "--skip-drop-and-create-topic",
        default=False,
        action="store_true",
        help="Use existed topic, skip remove it and re-create",
    )

    args = parser.parse_args()

    if args.verbose:
        logger = logging.getLogger("topicexample")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.StreamHandler())

    async with await connect(args.endpoint, args.database) as driver:
        if not args.skip_drop_and_create_topic:
            await create_topic(driver, args.path, args.consumer)

        await write_with_tx_example(driver, args.path)
        await read_with_tx_example(driver, args.path, args.consumer)


if __name__ == "__main__":
    asyncio.run(main())
