import pytest
import time
import grpc
import threading

import tests.auth.test_credentials
import tests.oauth2_token_exchange
import tests.oauth2_token_exchange.test_token_exchange
import ydb.aio.iam
import ydb.aio.oauth2_token_exchange
import ydb.oauth2_token_exchange.token_source


class TestServiceAccountCredentials(ydb.aio.iam.ServiceAccountCredentials):
    def _channel_factory(self):
        return grpc.aio.insecure_channel(self._iam_endpoint)

    def get_expire_time(self):
        return self._expires_in - time.time()


class TestOauth2TokenExchangeCredentials(ydb.aio.oauth2_token_exchange.Oauth2TokenExchangeCredentials):
    def get_expire_time(self):
        return self._expires_in - time.time()


@pytest.mark.asyncio
async def test_yandex_service_account_credentials():
    server = tests.auth.test_credentials.IamTokenServiceTestServer()
    credentials = TestServiceAccountCredentials(
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

    credentials = TestOauth2TokenExchangeCredentials(
        server.endpoint(),
        ydb.oauth2_token_exchange.token_source.FixedTokenSource("test_src_token", "test_token_type"),
        audience=["a1", "a2"],
        scope=["s1", "s2"],
    )
    t = (await credentials.auth_metadata())[0][1]
    assert t == "Bearer test_dst_token"
    assert credentials.get_expire_time() <= 42

    serve_thread.join()
