# -*- coding: utf-8 -*-
import ydb


def test_connect_secure(secure_endpoint, database):
    with ydb.Driver(
        endpoint="grpcs://localhost:2135",
        database="/local",
        root_certificates=ydb.load_ydb_root_certificate(),
    ) as driver:
        driver.wait(timeout=10)
        driver.scheme_client.make_directory("/local/test")
