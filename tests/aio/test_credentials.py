import pytest
import time
import grpc
import threading
import tempfile
import os
import json
import asyncio
import aiohttp
from unittest.mock import patch, AsyncMock, MagicMock

import tests.auth.test_credentials
import tests.oauth2_token_exchange
import tests.oauth2_token_exchange.test_token_exchange
import ydb.aio.iam
import ydb.aio.oidc
import ydb.aio.oauth2_token_exchange
import ydb.oauth2_token_exchange.token_source
from ydb import issues


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


@pytest.mark.asyncio
async def test_oauth2_client_credentials():
    issuer = "https://issuer.example"
    credentials = ydb.aio.oidc.OAuth2ClientCredentials(issuer, "client-id", "client-secret")
    credentials._request_json = AsyncMock(
        side_effect=[
            (200, {"issuer": issuer, "token_endpoint": issuer + "/token"}),
            (200, {"access_token": "access-token", "token_type": "Bearer", "expires_in": 300}),
        ]
    )

    assert await credentials.get_auth_token() == "Bearer access-token"
    assert credentials._request_json.await_count == 2


@pytest.mark.asyncio
async def test_oauth2_device_credentials():
    issuer = "https://issuer.example"
    callback_values = []

    async def callback(info):
        callback_values.append(info)

    credentials = ydb.aio.oidc.OAuth2DeviceCredentials(issuer, "device-client", callback)
    credentials._request_json = AsyncMock(
        side_effect=[
            (
                200,
                {
                    "issuer": issuer,
                    "token_endpoint": issuer + "/token",
                    "device_authorization_endpoint": issuer + "/device",
                },
            ),
            (
                200,
                {
                    "device_code": "device-code",
                    "user_code": "user-code",
                    "verification_uri": issuer + "/verify",
                    "expires_in": 600,
                    "interval": 1,
                },
            ),
            (400, {"error": "authorization_pending"}),
            (400, {"error": "slow_down"}),
            (200, {"access_token": "access-token", "token_type": "Bearer", "expires_in": 300}),
        ]
    )

    with patch("ydb.aio.oidc.asyncio.sleep", new=AsyncMock()) as sleep:
        assert await credentials.get_auth_token() == "Bearer access-token"

    assert callback_values[0].user_code == "user-code"
    assert sleep.await_count == 3


@pytest.mark.asyncio
async def test_oauth2_async_http_requests_and_discovery_cache():
    credentials = ydb.aio.oidc.OAuth2ClientCredentials(
        "https://issuer.example",
        "client-id",
        "client-secret",
    )
    response = MagicMock(status=200)
    response.read = AsyncMock(
        return_value=b'{"issuer":"https://issuer.example","token_endpoint":"https://issuer.example/token"}'
    )
    request_context = MagicMock()
    request_context.__aenter__ = AsyncMock(return_value=response)
    request_context.__aexit__ = AsyncMock(return_value=None)
    session = MagicMock()
    session.request.return_value = request_context
    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=session)
    session_context.__aexit__ = AsyncMock(return_value=None)

    with patch("ydb.aio.oidc.aiohttp.ClientSession", return_value=session_context) as client_session:
        first = await credentials._discovery()
        second = await credentials._discovery()

    assert first is second
    assert client_session.call_count == 1
    assert session.request.call_args.kwargs["ssl"] is not None

    with patch(
        "ydb.aio.oidc.aiohttp.ClientSession",
        side_effect=aiohttp.ClientError("unavailable"),
    ):
        with pytest.raises(issues.Unavailable):
            await credentials._request_json("http://issuer.example/token", {"key": "value"})


@pytest.mark.asyncio
async def test_oauth2_async_device_refresh_and_error_paths():
    with pytest.raises(ValueError):
        ydb.aio.oidc.OAuth2ClientCredentials("https://issuer.example", "client-id", "")
    with pytest.raises(ValueError):
        ydb.aio.oidc.OAuth2DeviceCredentials("https://issuer.example", "client-id", None)
    with pytest.raises(ValueError):
        ydb.aio.oidc.OAuth2DeviceCredentials(
            "https://issuer.example",
            "client-id",
            lambda info: None,
            device_flow_timeout=0,
        )

    credentials = ydb.aio.oidc.OAuth2DeviceCredentials(
        "https://issuer.example",
        "client-id",
        lambda info: None,
        client_secret="client-secret",
    )
    assert credentials._client_headers()["Authorization"].startswith("Basic ")
    with pytest.raises(issues.Error, match="refresh_token"):
        credentials._save_token_response(
            {
                "access_token": "token",
                "token_type": "Bearer",
                "expires_in": 300,
                "refresh_token": "",
            }
        )

    credentials._refresh_token_value = "refresh-token"
    credentials._request_json = AsyncMock(
        return_value=(
            200,
            {
                "access_token": "refreshed-token",
                "token_type": "Bearer",
                "expires_in": 300,
                "refresh_token": "new-refresh-token",
            },
        )
    )
    credentials._discovery_document = {"token_endpoint": "https://issuer.example/token"}
    assert await credentials._make_token_request() == {
        "access_token": "Bearer refreshed-token",
        "expires_in": 300,
    }
    assert credentials._refresh_token_value == "new-refresh-token"

    credentials._request_json = AsyncMock(return_value=(400, {"error": "invalid_grant"}))
    assert await credentials._try_refresh("https://issuer.example/token") is None
    assert credentials._refresh_token_value is None

    credentials._discovery_document = {"token_endpoint": "https://issuer.example/token"}
    with pytest.raises(issues.Error, match="device_authorization_endpoint"):
        await credentials._make_token_request()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "token_response, expected_message",
    [
        ({"error": "expired_token"}, "expired"),
        ({"error": "access_denied"}, "access_denied"),
        (None, "timed out"),
    ],
)
async def test_oauth2_async_device_expiration(token_response, expected_message):
    callback_values = []
    credentials = ydb.aio.oidc.OAuth2DeviceCredentials(
        "https://issuer.example",
        "client-id",
        callback_values.append,
        device_flow_timeout=1,
    )
    credentials._discovery_document = {
        "token_endpoint": "https://issuer.example/token",
        "device_authorization_endpoint": "https://issuer.example/device",
    }
    device_response = {
        "device_code": "device-code",
        "user_code": "user-code",
        "verification_uri": "https://issuer.example/verify",
        "expires_in": 600,
        "interval": 1,
    }
    responses = [(200, device_response)]
    loop = MagicMock()
    loop.time.side_effect = [0, 2]
    if token_response is not None:
        responses.append((400, token_response))
        loop.time.side_effect = [0, 0]
    credentials._request_json = AsyncMock(side_effect=responses)

    with patch("ydb.aio.oidc.asyncio.get_running_loop", return_value=loop), patch(
        "ydb.aio.oidc.asyncio.sleep", new=AsyncMock()
    ):
        with pytest.raises(issues.Unauthenticated, match=expected_message):
            await credentials._make_token_request()

    assert callback_values[0].user_code == "user-code"
