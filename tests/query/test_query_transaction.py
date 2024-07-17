import pytest

import ydb.query.session

class TestQuerySession:
    def test_transaction_begin(self, driver_sync):
        session = ydb.query.session.QuerySessionSync(driver_sync)

        session.create()

        tx = session.transaction()

        assert tx.tx_id == None

        tx.begin()

        assert tx.tx_id != None
