# -*- coding: utf-8 -*-
import os
import random
import json
import base64
import ydb
from concurrent.futures import TimeoutError


def create_table(pool: ydb.SessionPool, db_path: str, path: str) -> str:
    columns = [
        ydb.Column("key", ydb.OptionalType(ydb.PrimitiveType.Int32)),
        ydb.Column("jsonb_value", ydb.OptionalType(ydb.PrimitiveType.JsonDocument)),
    ]
    table_path = os.path.join(path, "jsonb_table")
    ydb_path = os.path.join(db_path, table_path)
    def fun(session: ydb.Session):
        session.create_table(
            ydb_path,
            ydb.TableDescription()
            .with_primary_keys("key",)
            .with_columns(*columns)
        )
    pool.retry_operation_sync(fun)
    return table_path


def make_json(i: int) -> str:
    data = {
        "key": (i+1),
        "some_value": base64.b64encode(random.randbytes(12)).decode("utf-8"),
        "long_value": base64.b64encode(random.randbytes(51)).decode("utf-8"),
        "struct_value": {
            "a": random.randint(1, 1000),
            "b": "this is a text"
        }
    }
    return json.dumps(data)


def insert_json_rows(pool: ydb.SessionPool, table_path: str, num: int):
    inputData = []
    for i in range(0, num):
        inputData.append({"key": i+1, "jsonb_value": make_json(i)})
    qtext = """
DECLARE $input AS List<Struct<key: Int32, jsonb_value: JsonDocument>>;
UPSERT INTO `%s` SELECT * FROM AS_TABLE($input);""" % (table_path)
    def fun(session: ydb.Session):
        session.transaction(ydb.SerializableReadWrite()).execute(
            query=session.prepare(qtext),
            parameters={"$input": inputData},
            commit_tx=True,
        )
    pool.retry_operation_sync(fun)


def find_json_row(pool: ydb.SessionPool, table_path: str, id: int):
    def fun(session: ydb.Session):
        rs = session.transaction().execute(
            session.prepare("""
    DECLARE $key AS Int32; SELECT jsonb_value FROM `%s` WHERE key=$key;
            """ % (table_path)),
            {"$key": id},
        )
        if rs is None or len(rs)==0 or rs[0].rows is None or len(rs[0].rows)==0:
            return None
        return rs[0].rows[0].jsonb_value
    return pool.retry_operation_sync(fun)


def run(endpoint: str, database: str, path: str):
    driver_config = ydb.DriverConfig(
        endpoint, database=database,
        credentials=ydb.credentials_from_env_variables(),
        root_certificates=ydb.load_ydb_root_certificate(),
    )
    with ydb.Driver(driver_config) as driver:
        driver.wait(timeout=5, fail_fast=True)
        with ydb.SessionPool(driver) as pool:
            table_path = create_table(pool, database, path)
            insert_json_rows(pool, table_path, 100)
            for i in range(1, 10):
                key = random.randint(1, 99)
                x = find_json_row(pool, table_path, key)
                print("Lookup for key %d -> %s" % (key, str(x)))
