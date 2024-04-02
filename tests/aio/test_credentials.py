import pytest
import time
import grpc
import threading

import tests.auth.test_credentials
import ydb.aio.iam


class TestServiceAccountCredentials(ydb.aio.iam.ServiceAccountCredentials):
    def _channel_factory(self):
        return grpc.aio.insecure_channel(
            self._iam_endpoint
        )

    def get_expire_time(self):
        return self._expires_in - time.time()


class TestNebiusServiceAccountCredentials(ydb.aio.iam.NebiusServiceAccountCredentials):
    def get_expire_time(self):
        return self._expires_in - time.time()


@pytest.mark.asyncio
async def test_yandex_service_account_credentials():
    server = tests.auth.test_credentials.IamTokenServiceTestServer()
    credentials = TestServiceAccountCredentials(tests.auth.test_credentials.SERVICE_ACCOUNT_ID, tests.auth.test_credentials.ACCESS_KEY_ID, tests.auth.test_credentials.PRIVATE_KEY, server.get_endpoint())
    t = (await credentials.auth_metadata())[0][1]
    assert t == "test_token"
    assert credentials.get_expire_time() <= 42
    server.stop()


@pytest.mark.asyncio
async def test_nebius_service_account_credentials():
    server = tests.auth.test_credentials.NebiusTokenServiceForTest()

    def serve(s):
        s.handle_request()

    serve_thread = threading.Thread(target=serve, args=(server,))
    serve_thread.start()

    credentials = TestNebiusServiceAccountCredentials(tests.auth.test_credentials.SERVICE_ACCOUNT_ID, tests.auth.test_credentials.ACCESS_KEY_ID, tests.auth.test_credentials.PRIVATE_KEY, server.endpoint())
    t = (await credentials.auth_metadata())[0][1]
    assert t == "test_nebius_token"
    assert credentials.get_expire_time() <= 42

    serve_thread.join()
