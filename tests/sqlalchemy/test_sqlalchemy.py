# import sqlalchemy as sa
# from sqlalchemy import MetaData, Table, Column, Integer, Unicode
#
# meta = MetaData()
#
#
# def clear_sql(stm):
#     return stm.replace("\n", " ").replace("  ", " ").strip()
#
#
# def test_sqlalchemy_core(connection):
#     # raw sql
#     rs = connection.execute("SELECT 1 AS value")
#     assert rs.fetchone()["value"] == 1
#
#     tb_test = Table(
#         "test",
#         meta,
#         Column("id", Integer, primary_key=True),
#         Column("text", Unicode),
#     )
#
#     stm = sa.select(tb_test)
#     assert clear_sql(str(stm)) == "SELECT test.id, test.text FROM test"
#
#     stm = sa.insert(tb_test).values(id=2, text="foo")
#     assert clear_sql(str(stm)) == "INSERT INTO test (id, text) VALUES (:id, :text)"
