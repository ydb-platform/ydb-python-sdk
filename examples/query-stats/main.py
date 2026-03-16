import os

import ydb

SESSION_QUERY = "SELECT 1"
TX_QUERY = "SELECT 1"


def get_query_stats_from_session(pool: ydb.QuerySessionPool):
    def callee(session: ydb.QuerySession):
        with session.execute(SESSION_QUERY, stats_mode=ydb.QueryStatsMode.PROFILE):
            pass

        print(session.last_query_stats)

    pool.retry_operation_sync(callee)


def get_query_stats_from_tx(pool: ydb.QuerySessionPool):
    def callee(tx: ydb.QueryTxContext):
        with tx.execute(TX_QUERY, stats_mode=ydb.QueryStatsMode.PROFILE):
            pass

        print(tx.last_query_stats)

    pool.retry_tx_sync(callee)


def main():
    driver = ydb.Driver(
        endpoint=os.getenv("YDB_ENDPOINT", "grpc://localhost:2136"),
        database=os.getenv("YDB_DATABASE", "/local"),
        credentials=ydb.AnonymousCredentials(),
    )

    with driver:
        # wait until driver become initialized
        driver.wait(fail_fast=True, timeout=5)
        with ydb.QuerySessionPool(driver) as pool:
            get_query_stats_from_session(pool)
            get_query_stats_from_tx(pool)


main()
