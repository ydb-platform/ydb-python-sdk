import ydb


def writer_example(driver: ydb.Driver, topic: str):
    session_pool = ydb.QuerySessionPool(driver)

    def callee(tx: ydb.QueryTxContext):
        tx_writer: ydb.TopicTxWriter = driver.topic_client.tx_writer(tx, topic)
        # нужно ли внутри ретраить ? нужно разрешать ретраи с дедупликацией
        # дефолт - без дедупликации, без ретраев и без producer_id. договорились.

        with tx.execute(query="select 1") as result_sets:
            messages = [result_set.rows[0] for result_set in result_sets]

        tx_writer.write(messages)

    session_pool.retry_tx_sync(callee)


def reader_example(driver: ydb.Driver, reader: ydb.TopicReader):
    session_pool = ydb.QuerySessionPool(driver)

    def callee(tx: ydb.QueryTxContext):
        batch = reader.receive_batch_with_tx(tx, max_messages=5)

        with tx.execute(query="INSERT INTO max_values(val) VALUES ($val)", parameters={"$val": max(batch)}) as _:
            pass

        # коммитим при выходе из лямбды

    session_pool.retry_tx_sync(callee)
