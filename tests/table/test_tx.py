import pytest
from contextlib import suppress

import ydb.iam


def test_tx_commit(driver_sync, database):
    session = driver_sync.table_client.session().create()
    prepared = session.prepare(
        "DECLARE $param as Int32;\n SELECT $param as value",
    )

    tx = session.transaction()
    tx.execute(prepared, {"$param": 2})
    tx.commit()
    tx.commit()


def test_tx_rollback(driver_sync, database):
    session = driver_sync.table_client.session().create()
    prepared = session.prepare(
        "DECLARE $param as Int32;\n SELECT $param as value",
    )

    tx = session.transaction()
    tx.execute(prepared, {"$param": 2})
    tx.rollback()
    tx.rollback()


def test_tx_begin(driver_sync, database):
    session = driver_sync.table_client.session().create()
    session.create()

    tx = session.transaction()
    tx.begin()
    tx.begin()
    tx.rollback()


def test_credentials():
    credentials = ydb.iam.MetadataUrlCredentials()
    raised = False
    try:
        credentials.auth_metadata()
    except Exception:
        raised = True

    assert raised


def test_tx_snapshot_ro(driver_sync, database):
    session = driver_sync.table_client.session().create()
    description = (
        ydb.TableDescription()
        .with_primary_keys("key")
        .with_columns(
            ydb.Column("key", ydb.OptionalType(ydb.PrimitiveType.Uint64)),
            ydb.Column("value", ydb.OptionalType(ydb.PrimitiveType.Uint64)),
        )
    )
    tb_name = f"{database}/test"
    with suppress(ydb.issues.SchemeError):
        session.drop_table(tb_name)
    session.create_table(tb_name, description)
    session.transaction(ydb.SerializableReadWrite()).execute(
        """INSERT INTO `test` (`key`, `value`) VALUES (1, 1), (2, 2)""",
        commit_tx=True,
    )

    ro_tx = session.transaction(tx_mode=ydb.SnapshotReadOnly())
    data1 = ro_tx.execute("SELECT value FROM `test` WHERE key = 1")

    session.transaction(ydb.SerializableReadWrite()).execute(
        "UPDATE `test` SET value = value + 1", commit_tx=True
    )

    data2 = ro_tx.execute("SELECT value FROM `test` WHERE key = 1")
    assert data1[0].rows == data2[0].rows == [{"value": 1}]

    ro_tx.commit()

    ro_tx = session.transaction(tx_mode=ydb.SnapshotReadOnly())
    with pytest.raises(ydb.issues.GenericError) as exc_info:
        ro_tx.execute("UPDATE `test` SET value = value + 1")
    assert "read only transaction" in exc_info.value.message

    data = session.transaction(tx_mode=ydb.SnapshotReadOnly()).execute(
        "SELECT value FROM `test` WHERE key = 1",
        commit_tx=True,
    )
    assert data[0].rows == [{"value": 2}]


def test_split_transactions_deny_split(driver_sync, table_name):
    with ydb.SessionPool(driver_sync, 1) as pool:

        def check_transaction(s: ydb.table.Session):
            with s.transaction(deny_split_transactions=True) as tx:
                tx.execute("INSERT INTO %s (id) VALUES (1)" % table_name)
                tx.commit()

                with pytest.raises(RuntimeError):
                    tx.execute("INSERT INTO %s (id) VALUES (2)" % table_name)

                tx.commit()

            with s.transaction() as tx:
                rs = tx.execute("SELECT COUNT(*) as cnt FROM %s" % table_name)
                assert rs[0].rows[0].cnt == 1

        pool.retry_operation_sync(check_transaction)


def test_split_transactions_allow_split(driver_sync, table_name):
    with ydb.SessionPool(driver_sync, 1) as pool:

        def check_transaction(s: ydb.table.Session):
            with s.transaction(deny_split_transactions=False) as tx:
                tx.execute("INSERT INTO %s (id) VALUES (1)" % table_name)
                tx.commit()

                tx.execute("INSERT INTO %s (id) VALUES (2)" % table_name)
                tx.commit()

            with s.transaction() as tx:
                rs = tx.execute("SELECT COUNT(*) as cnt FROM %s" % table_name)
                assert rs[0].rows[0].cnt == 2

        pool.retry_operation_sync(check_transaction)


def test_split_transactions_default(driver_sync, table_name):
    with ydb.SessionPool(driver_sync, 1) as pool:

        def check_transaction(s: ydb.table.Session):
            with s.transaction() as tx:
                tx.execute("INSERT INTO %s (id) VALUES (1)" % table_name)
                tx.commit()

                tx.execute("INSERT INTO %s (id) VALUES (2)" % table_name)
                tx.commit()

            with s.transaction() as tx:
                rs = tx.execute("SELECT COUNT(*) as cnt FROM %s" % table_name)
                assert rs[0].rows[0].cnt == 2

        pool.retry_operation_sync(check_transaction)
