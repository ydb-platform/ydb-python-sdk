from ydb import _dbapi as dbapi


def test_dbapi(endpoint, database):
    conn = dbapi.connect(endpoint, database=database)
    assert conn

    conn.commit()
    conn.rollback()

    cur = conn.cursor()
    assert cur

    cur.execute(
        "CREATE TABLE test(id Int64 NOT NULL, text Utf8, PRIMARY KEY (id))",
        context={"isddl": True},
    )

    cur.execute('INSERT INTO test(id, text) VALUES (1, "foo")')

    cur.execute("SELECT id, text FROM test")
    assert cur.fetchone() == (1, "foo"), "fetchone is ok"

    cur.execute("SELECT id, text FROM test WHERE id = %(id)s", {"id": 1})
    assert cur.fetchone() == (1, "foo"), "parametrized query is ok"

    cur.execute(
        "INSERT INTO test(id, text) VALUES (%(id1)s, %(text1)s), (%(id2)s, %(text2)s)",
        {"id1": 2, "text1": "", "id2": 3, "text2": "bar"},
    )

    cur.execute("UPDATE test SET text = %(t)s WHERE id = %(id)s", {"id": 2, "t": "foo2"})

    cur.execute("SELECT id FROM test")
    assert cur.fetchall() == [(1,), (2,), (3,)], "fetchall is ok"

    cur.execute("SELECT id FROM test ORDER BY id DESC")
    assert cur.fetchmany(2) == [(3,), (2,)], "fetchmany is ok"
    assert cur.fetchmany(1) == [(1,)]

    cur.execute("SELECT id FROM test ORDER BY id LIMIT 2")
    assert cur.fetchall() == [(1,), (2,)], "limit clause without params is ok"

    # TODO: Failed to convert type: Int64 to Uint64
    # cur.execute("SELECT id FROM test ORDER BY id LIMIT %(limit)s", {"limit": 2})
    # assert cur.fetchall() == [(1,), (2,)], "limit clause with params is ok"

    cur2 = conn.cursor()
    cur2.execute("INSERT INTO test(id) VALUES (%(id1)s), (%(id2)s)", {"id1": 5, "id2": 6})

    cur.execute("SELECT id FROM test ORDER BY id")
    assert cur.fetchall() == [(1,), (2,), (3,), (5,), (6,)], "cursor2 commit changes"

    cur.execute("SELECT text FROM test WHERE id > %(min_id)s", {"min_id": 3})
    assert cur.fetchall() == [(None,), (None,)], "NULL returns as None"

    cur.execute("SELECT id, text FROM test WHERE text LIKE %(p)s", {"p": "foo%"})
    assert cur.fetchall() == [(1, "foo"), (2, "foo2")], "like clause works"

    cur.execute(
        # DECLARE statement (DECLARE $data AS List<Struct<id:Int64,text:Utf8>>)
        # will generate automatically
        """INSERT INTO test SELECT id, text FROM AS_TABLE($data);""",
        {
            "data": [
                {"id": 17, "text": "seventeen"},
                {"id": 21, "text": "twenty one"},
            ]
        },
    )

    cur.execute("SELECT id FROM test ORDER BY id")
    assert cur.rowcount == 7, "rowcount ok"
    assert cur.fetchall() == [(1,), (2,), (3,), (5,), (6,), (17,), (21,)], "ok"

    cur.execute("DROP TABLE test", context={"isddl": True})

    cur.close()
    cur2.close()
    conn.close()
