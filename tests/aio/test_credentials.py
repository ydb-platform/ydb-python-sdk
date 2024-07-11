import pytest
import time
import grpc
import threading
import tempfile
import os
import json

import tests.auth.test_credentials
import tests.oauth2_token_exchange
import tests.oauth2_token_exchange.test_token_exchange
import ydb.aio.iam
import ydb.aio.oauth2_token_exchange
import ydb.oauth2_token_exchange.token_source


class ServiceAccountCredentialsForTest(ydb.aio.iam.ServiceAccountCredentials):
    def _channel_factory(self):
        return grpc.aio.insecure_channel(self._iam_endpoint)

    def get_expire_time(self):
        return self._expires_in - time.time()


class Oauth2TokenExchangeCredentialsForTest(ydb.aio.oauth2_token_exchange.Oauth2TokenExchangeCredentials):
    def get_expire_time(self):
        return self._expires_in - time.time()


@pytest.mark.asyncio
async def test_yandex_service_account_credentials():
    server = tests.auth.test_credentials.IamTokenServiceTestServer()
    credentials = ServiceAccountCredentialsForTest(
        tests.auth.test_credentials.SERVICE_ACCOUNT_ID,
        tests.auth.test_credentials.ACCESS_KEY_ID,
        tests.auth.test_credentials.PRIVATE_KEY,
        server.get_endpoint(),
    )
    t = (await credentials.auth_metadata())[0][1]
    assert t == "test_token"
    assert credentials.get_expire_time() <= 42
    server.stop()


@pytest.mark.asyncio
async def test_oauth2_token_exchange_credentials():
    server = tests.oauth2_token_exchange.test_token_exchange.Oauth2TokenExchangeServiceForTest(40124)

    def serve(s):
        s.handle_request()

    serve_thread = threading.Thread(target=serve, args=(server,))
    serve_thread.start()

    credentials = Oauth2TokenExchangeCredentialsForTest(
        server.endpoint(),
        ydb.oauth2_token_exchange.token_source.FixedTokenSource("test_src_token", "test_token_type"),
        audience=["a1", "a2"],
        scope=["s1", "s2"],
    )
    t = (await credentials.auth_metadata())[0][1]
    assert t == "Bearer test_dst_token"
    assert credentials.get_expire_time() <= 42

    serve_thread.join()


@pytest.mark.asyncio
async def test_oauth2_token_exchange_credentials_file():
    server = tests.oauth2_token_exchange.test_token_exchange.Oauth2TokenExchangeServiceForTest(40124)

    def serve(s):
        s.handle_request()

    serve_thread = threading.Thread(target=serve, args=(server,))
    serve_thread.start()

    cfg = {
        "subject-credentials": {
            "type": "FIXED",
            "token": "test_src_token",
            "token-type": "test_token_type",
        },
        "aud": [
            "a1",
            "a2",
        ],
        "scope": [
            "s1",
            "s2",
        ],
    }

    temp_cfg_file = tempfile.NamedTemporaryFile(delete=False)
    cfg_file_name = temp_cfg_file.name

    try:
        temp_cfg_file.write(json.dumps(cfg, indent=4).encode("utf-8"))
        temp_cfg_file.close()

        credentials = Oauth2TokenExchangeCredentialsForTest.from_file(
            cfg_file=cfg_file_name, iam_endpoint=server.endpoint()
        )

        t = (await credentials.auth_metadata())[0][1]
        assert t == "Bearer test_dst_token"
        assert credentials.get_expire_time() <= 42

        serve_thread.join()
        os.remove(cfg_file_name)
    except Exception:
        os.remove(cfg_file_name)
        raise
