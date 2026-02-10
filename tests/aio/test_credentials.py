import asyncio
import json
import os
import tempfile
import threading
import time
from unittest.mock import AsyncMock, MagicMock, patch

import grpc
import pytest

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
    t = await credentials.get_auth_token()
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


@pytest.mark.asyncio
async def test_token_lazy_refresh():
    credentials = ServiceAccountCredentialsForTest(
        tests.auth.test_credentials.SERVICE_ACCOUNT_ID,
        tests.auth.test_credentials.ACCESS_KEY_ID,
        tests.auth.test_credentials.PRIVATE_KEY,
        "localhost:0",
    )

    credentials._tp.submit = MagicMock()

    mock_response = {"access_token": "token_v1", "expires_in": 3600}
    credentials._make_token_request = AsyncMock(return_value=mock_response)

    with patch("time.time") as mock_time:
        mock_time.return_value = 1000

        token1 = await credentials.token()
        assert token1 == "token_v1"
        assert credentials._make_token_request.call_count == 1

        token2 = await credentials.token()
        assert token2 == "token_v1"
        assert credentials._make_token_request.call_count == 1

        mock_time.return_value = 1000 + 3600 - 30 + 1
        credentials._make_token_request.return_value = {"access_token": "token_v2", "expires_in": 3600}

        token3 = await credentials.token()
        assert token3 == "token_v2"
        assert credentials._make_token_request.call_count == 2


@pytest.mark.asyncio
async def test_token_double_check_locking():
    credentials = ServiceAccountCredentialsForTest(
        tests.auth.test_credentials.SERVICE_ACCOUNT_ID,
        tests.auth.test_credentials.ACCESS_KEY_ID,
        tests.auth.test_credentials.PRIVATE_KEY,
        "localhost:0",
    )

    credentials._tp.submit = MagicMock()

    call_count = 0

    async def mock_make_request():
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.01)
        return {"access_token": f"token_v{call_count}", "expires_in": 3600}

    credentials._make_token_request = mock_make_request

    with patch("time.time") as mock_time:
        mock_time.return_value = 1000

        tasks = [credentials.token() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(set(results)) == 1
        assert call_count == 1


@pytest.mark.asyncio
async def test_token_expiration_calculation():
    credentials = ServiceAccountCredentialsForTest(
        tests.auth.test_credentials.SERVICE_ACCOUNT_ID,
        tests.auth.test_credentials.ACCESS_KEY_ID,
        tests.auth.test_credentials.PRIVATE_KEY,
        "localhost:0",
    )

    credentials._tp.submit = MagicMock()

    with patch("time.time") as mock_time:
        mock_time.return_value = 1000

        credentials._make_token_request = AsyncMock(return_value={"access_token": "token", "expires_in": 3600})

        await credentials.token()

        expected_expires = 1000 + 3600 - 30
        assert credentials._expires_in == expected_expires


@pytest.mark.asyncio
async def test_token_refresh_error_handling():
    credentials = ServiceAccountCredentialsForTest(
        tests.auth.test_credentials.SERVICE_ACCOUNT_ID,
        tests.auth.test_credentials.ACCESS_KEY_ID,
        tests.auth.test_credentials.PRIVATE_KEY,
        "localhost:0",
    )

    credentials._tp.submit = MagicMock()

    credentials._make_token_request = AsyncMock(side_effect=Exception("Network error"))

    with pytest.raises(Exception) as exc_info:
        await credentials.token()

    assert "Network error" in str(exc_info.value)
    assert credentials.last_error == "Network error"


@pytest.mark.asyncio
async def test_hybrid_background_and_sync_refresh():
    credentials = ServiceAccountCredentialsForTest(
        tests.auth.test_credentials.SERVICE_ACCOUNT_ID,
        tests.auth.test_credentials.ACCESS_KEY_ID,
        tests.auth.test_credentials.PRIVATE_KEY,
        "localhost:0",
    )

    call_count = 0
    background_calls = []

    async def mock_make_request():
        nonlocal call_count
        call_count += 1
        return {"access_token": f"token_v{call_count}", "expires_in": 3600}

    def mock_submit(callback):
        background_calls.append(callback)

    credentials._make_token_request = mock_make_request
    credentials._tp.submit = mock_submit

    with patch("time.time") as mock_time:
        mock_time.return_value = 1000

        token1 = await credentials.token()
        assert token1 == "token_v1"
        assert call_count == 1
        assert len(background_calls) == 0

        mock_time.return_value = 1000 + min(1800, 3600 / 10) + 1
        token2 = await credentials.token()
        assert token2 == "token_v1"
        assert call_count == 1
        assert len(background_calls) == 1

        mock_time.return_value = 1000 + 3600 - 30 + 1
        token3 = await credentials.token()
        assert token3 == "token_v2"
        assert call_count == 2
