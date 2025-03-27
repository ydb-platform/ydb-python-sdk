import argparse
import logging
import ydb


def connect(endpoint: str, database: str) -> ydb.Driver:
    config = ydb.DriverConfig(endpoint=endpoint, database=database)
    config.credentials = ydb.credentials_from_env_variables()
    driver = ydb.Driver(config)
    driver.wait(5, fail_fast=True)
    return driver


def create_topic(driver: ydb.Driver, topic: str, consumer: str):
    try:
        driver.topic_client.drop_topic(topic)
    except ydb.SchemeError:
        pass

    driver.topic_client.create_topic(topic, consumers=[consumer])


def write_with_tx_example(driver: ydb.Driver, topic: str, message_count: int = 10):
    with ydb.QuerySessionPool(driver) as session_pool:

        def callee(tx: ydb.QueryTxContext):
            tx_writer: ydb.TopicTxWriter = driver.topic_client.tx_writer(tx, topic)

            for i in range(message_count):
                result_stream = tx.execute(query=f"select {i} as res;")
                for result_set in result_stream:
                    message = str(result_set.rows[0]["res"])
                    tx_writer.write(ydb.TopicWriterMessage(message))
                    print(f"Message {message} was written with tx.")

        session_pool.retry_tx_sync(callee)


def read_with_tx_example(driver: ydb.Driver, topic: str, consumer: str, message_count: int = 10):
    with driver.topic_client.reader(topic, consumer) as reader:
        with ydb.QuerySessionPool(driver) as session_pool:
            for _ in range(message_count):

                def callee(tx: ydb.QueryTxContext):
                    batch = reader.receive_batch_with_tx(tx, max_messages=1)
                    print(f"Message {batch.messages[0].data.decode()} was read with tx.")

                session_pool.retry_tx_sync(callee)


def main():
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

    with connect(args.endpoint, args.database) as driver:
        if not args.skip_drop_and_create_topic:
            create_topic(driver, args.path, args.consumer)

        write_with_tx_example(driver, args.path)
        read_with_tx_example(driver, args.path, args.consumer)


if __name__ == "__main__":
    main()
