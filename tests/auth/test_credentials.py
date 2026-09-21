import jwt
import concurrent.futures
import grpc
import io
import pytest
import time
import urllib.error
from unittest.mock import patch
from unittest.mock import MagicMock

import ydb.iam
import ydb.oidc
from ydb import issues
from ydb.oidc._common import OAuth2CredentialsBase
from ydb.oidc._common import bearer_token

from yandex.cloud.iam.v1 import iam_token_service_pb2_grpc
from yandex.cloud.iam.v1 import iam_token_service_pb2

SERVICE_ACCOUNT_ID = "sa_id"
ACCESS_KEY_ID = "key_id"
PRIVATE_KEY = "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC75/JS3rMcLJxv\nFgpOzF5+2gH+Yig3RE2MTl9uwC0BZKAv6foYr7xywQyWIK+W1cBhz8R4LfFmZo2j\nM0aCvdRmNBdW0EDSTnHLxCsFhoQWLVq+bI5f5jzkcoiioUtaEpADPqwgVULVtN/n\nnPJiZ6/dU30C3jmR6+LUgEntUtWt3eq3xQIn5lG3zC1klBY/HxtfH5Hu8xBvwRQT\nJnh3UpPLj8XwSmriDgdrhR7o6umWyVuGrMKlLHmeivlfzjYtfzO1MOIMG8t2/zxG\nR+xb4Vwks73sH1KruH/0/JMXU97npwpe+Um+uXhpldPygGErEia7abyZB2gMpXqr\nWYKMo02NAgMBAAECggEAO0BpC5OYw/4XN/optu4/r91bupTGHKNHlsIR2rDzoBhU\nYLd1evpTQJY6O07EP5pYZx9mUwUdtU4KRJeDGO/1/WJYp7HUdtxwirHpZP0lQn77\nuccuX/QQaHLrPekBgz4ONk+5ZBqukAfQgM7fKYOLk41jgpeDbM2Ggb6QUSsJISEp\nzrwpI/nNT/wn+Hvx4DxrzWU6wF+P8kl77UwPYlTA7GsT+T7eKGVH8xsxmK8pt6lg\nsvlBA5XosWBWUCGLgcBkAY5e4ZWbkdd183o+oMo78id6C+PQPE66PLDtHWfpRRmN\nm6XC03x6NVhnfvfozoWnmS4+e4qj4F/emCHvn0GMywKBgQDLXlj7YPFVXxZpUvg/\nrheVcCTGbNmQJ+4cZXx87huqwqKgkmtOyeWsRc7zYInYgraDrtCuDBCfP//ZzOh0\nLxepYLTPk5eNn/GT+VVrqsy35Ccr60g7Lp/bzb1WxyhcLbo0KX7/6jl0lP+VKtdv\nmto+4mbSBXSM1Y5BVVoVgJ3T/wKBgQDsiSvPRzVi5TTj13x67PFymTMx3HCe2WzH\nJUyepCmVhTm482zW95pv6raDr5CTO6OYpHtc5sTTRhVYEZoEYFTM9Vw8faBtluWG\nBjkRh4cIpoIARMn74YZKj0C/0vdX7SHdyBOU3bgRPHg08Hwu3xReqT1kEPSI/B2V\n4pe5fVrucwKBgQCNFgUxUA3dJjyMES18MDDYUZaRug4tfiYouRdmLGIxUxozv6CG\nZnbZzwxFt+GpvPUV4f+P33rgoCvFU+yoPctyjE6j+0aW0DFucPmb2kBwCu5J/856\nkFwCx3blbwFHAco+SdN7g2kcwgmV2MTg/lMOcU7XwUUcN0Obe7UlWbckzQKBgQDQ\nnXaXHL24GGFaZe4y2JFmujmNy1dEsoye44W9ERpf9h1fwsoGmmCKPp90az5+rIXw\nFXl8CUgk8lXW08db/r4r+ma8Lyx0GzcZyplAnaB5/6j+pazjSxfO4KOBy4Y89Tb+\nTP0AOcCi6ws13bgY+sUTa/5qKA4UVw+c5zlb7nRpgwKBgGXAXhenFw1666482iiN\ncHSgwc4ZHa1oL6aNJR1XWH+aboBSwR+feKHUPeT4jHgzRGo/aCNHD2FE5I8eBv33\nof1kWYjAO0YdzeKrW0rTwfvt9gGg+CS397aWu4cy+mTI+MNfBgeDAIVBeJOJXLlX\nhL8bFAuNNVrCOp79TNnNIsh7\n-----END PRIVATE KEY-----\n"  # noqa: E501
PUBLIC_KEY = "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAu+fyUt6zHCycbxYKTsxe\nftoB/mIoN0RNjE5fbsAtAWSgL+n6GK+8csEMliCvltXAYc/EeC3xZmaNozNGgr3U\nZjQXVtBA0k5xy8QrBYaEFi1avmyOX+Y85HKIoqFLWhKQAz6sIFVC1bTf55zyYmev\n3VN9At45kevi1IBJ7VLVrd3qt8UCJ+ZRt8wtZJQWPx8bXx+R7vMQb8EUEyZ4d1KT\ny4/F8Epq4g4Ha4Ue6OrplslbhqzCpSx5nor5X842LX8ztTDiDBvLdv88RkfsW+Fc\nJLO97B9Sq7h/9PyTF1Pe56cKXvlJvrl4aZXT8oBhKxImu2m8mQdoDKV6q1mCjKNN\njQIDAQAB\n-----END PUBLIC KEY-----\n"  # noqa: E501


def test_metadata_credentials():
    credentials = ydb.iam.MetadataUrlCredentials()
    raised = False
    try:
        credentials.auth_metadata()
    except Exception:
        raised = True

    assert raised


class IamTokenServiceForTest(iam_token_service_pb2_grpc.IamTokenServiceServicer):
    def Create(self, request, context):
        print("IAM token service request: {}".format(request))
        # Validate jwt:
        decoded = jwt.decode(
            request.jwt, key=PUBLIC_KEY, algorithms=["PS256"], audience="https://iam.api.cloud.yandex.net/iam/v1/tokens"
        )
        assert decoded["iss"] == SERVICE_ACCOUNT_ID
        assert decoded["aud"] == "https://iam.api.cloud.yandex.net/iam/v1/tokens"
        assert abs(decoded["iat"] - time.time()) <= 60
        assert abs(decoded["exp"] - time.time()) <= 3600

        response = iam_token_service_pb2.CreateIamTokenResponse(iam_token="test_token")
        response.expires_at.seconds = int(time.time() + 42)
        return response


class IamTokenServiceTestServer(object):
    def __init__(self):
        self.server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=2))
        iam_token_service_pb2_grpc.add_IamTokenServiceServicer_to_server(IamTokenServiceForTest(), self.server)
        self.server.add_insecure_port(self.get_endpoint())
        self.server.start()

    def stop(self):
        self.server.stop(1)
        self.server.wait_for_termination()

    def get_endpoint(self):
        return "localhost:54321"


class ServiceAccountCredentialsForTest(ydb.iam.ServiceAccountCredentials):
    def _channel_factory(self):
        return grpc.insecure_channel(self._iam_endpoint)

    def get_expire_time(self):
        return self._expires_in - time.time()


def test_yandex_service_account_credentials():
    server = IamTokenServiceTestServer()
    credentials = ServiceAccountCredentialsForTest(
        SERVICE_ACCOUNT_ID, ACCESS_KEY_ID, PRIVATE_KEY, server.get_endpoint()
    )
    t = credentials.get_auth_token()
    assert t == "test_token"
    assert credentials.get_expire_time() <= 42
    server.stop()


def test_oauth2_token_credentials():
    credentials = ydb.oidc.OAuth2TokenCredentials("access-token")

    assert credentials.auth_metadata() == [("x-ydb-auth-ticket", "Bearer access-token")]
    assert ydb.oidc.OAuth2TokenCredentials("Bearer access-token").get_auth_token() == "Bearer access-token"


def test_oauth2_client_credentials():
    issuer = "https://issuer.example"
    requests = []
    responses = iter(
        [
            (200, {"issuer": issuer, "token_endpoint": issuer + "/token"}),
            (200, {"access_token": "access-token", "token_type": "Bearer", "expires_in": 300}),
        ]
    )
    credentials = ydb.oidc.OAuth2ClientCredentials(
        issuer,
        "client-id",
        "client-secret",
        scope=["openid", "profile"],
        audience="ydb",
    )

    def request_json(url, data=None, headers=None):
        requests.append((url, data, headers))
        return next(responses)

    credentials._request_json = request_json

    assert credentials.get_auth_token() == "Bearer access-token"
    assert requests[0] == (issuer + "/.well-known/openid-configuration", None, None)
    assert requests[1][0] == issuer + "/token"
    assert requests[1][1] == {
        "grant_type": "client_credentials",
        "scope": "openid profile",
        "audience": "ydb",
    }
    assert requests[1][2]["Authorization"].startswith("Basic ")


def test_oauth2_device_credentials_poll_and_refresh():
    issuer = "https://issuer.example"
    callback_values = []
    responses = iter(
        [
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
                    "verification_uri_complete": issuer + "/verify?user_code=user-code",
                    "expires_in": 600,
                    "interval": 1,
                },
            ),
            (400, {"error": "authorization_pending"}),
            (400, {"error": "slow_down"}),
            (
                200,
                {
                    "access_token": "device-access-token",
                    "refresh_token": "refresh-token",
                    "token_type": "Bearer",
                    "expires_in": 300,
                },
            ),
            (
                200,
                {
                    "access_token": "refreshed-access-token",
                    "refresh_token": "new-refresh-token",
                    "token_type": "Bearer",
                    "expires_in": 300,
                },
            ),
        ]
    )
    requests = []
    credentials = ydb.oidc.OAuth2DeviceCredentials(
        issuer,
        "device-client",
        callback_values.append,
    )

    def request_json(url, data=None, headers=None):
        requests.append((url, data, headers))
        return next(responses)

    credentials._request_json = request_json

    with patch("ydb.oidc.credentials.time.sleep") as sleep:
        assert credentials.get_auth_token() == "Bearer device-access-token"

    assert callback_values[0].user_code == "user-code"
    assert [value.args[0] for value in sleep.call_args_list] == [1, 1, 6]
    assert credentials._make_token_request() == {
        "access_token": "Bearer refreshed-access-token",
        "expires_in": 300,
    }
    assert requests[-1][1]["grant_type"] == "refresh_token"
    assert requests[-1][1]["refresh_token"] == "refresh-token"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"issuer": ""},
        {"client_id": ""},
        {"request_timeout": 0},
        {"client_secret": ""},
    ],
)
def test_oauth2_client_credentials_validation(kwargs):
    arguments = {
        "issuer": "https://issuer.example",
        "client_id": "client-id",
        "client_secret": "client-secret",
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError):
        ydb.oidc.OAuth2ClientCredentials(**arguments)


@pytest.mark.parametrize("token", ["", None])
def test_oauth2_token_credentials_validation(token):
    with pytest.raises(ValueError):
        bearer_token(token)


def test_oauth2_common_response_processing():
    credentials = OAuth2CredentialsBase("https://issuer.example/", "client id", audience="ydb")

    with pytest.raises(issues.Error, match="invalid JSON"):
        credentials._decode_json(b"not-json", "https://issuer.example/token")
    with pytest.raises(issues.Error, match="non-object"):
        credentials._decode_json(b"[]", "https://issuer.example/token")

    credentials._raise_for_status(204, {})
    for status, response, error_type in (
        (401, {}, issues.Unauthenticated),
        (400, {"error": "invalid_client"}, issues.Unauthenticated),
        (503, {}, issues.Unavailable),
        (400, {"error": "bad_request", "error_description": "details"}, issues.BadRequest),
        (300, {}, issues.Error),
    ):
        with pytest.raises(error_type):
            credentials._raise_for_status(status, response)

    with pytest.raises(issues.Error, match="issuer mismatch"):
        credentials._process_discovery_response(
            200,
            {"issuer": "https://other.example", "token_endpoint": "https://issuer.example/token"},
        )
    with pytest.raises(issues.Error, match="token_endpoint"):
        credentials._process_discovery_response(200, {"issuer": "https://issuer.example"})

    for response, message in (
        ({}, "access_token"),
        ({"access_token": "token", "token_type": "Basic", "expires_in": 60}, "token_type"),
        ({"access_token": "token", "token_type": "Bearer", "expires_in": True}, "expires_in"),
    ):
        with pytest.raises(issues.Error, match=message):
            credentials._process_token_response(response)

    assert credentials._client_credentials_data() == {
        "grant_type": "client_credentials",
        "audience": "ydb",
    }
    assert credentials._device_authorization_data() == {
        "client_id": "client id",
        "audience": "ydb",
    }
    assert credentials._refresh_token_data("refresh-token") == {
        "grant_type": "refresh_token",
        "client_id": "client id",
        "refresh_token": "refresh-token",
    }
    assert (
        credentials._client_authorization_header("client id", "secret/value")
        == "Basic Y2xpZW50K2lkOnNlY3JldCUyRnZhbHVl"
    )


@pytest.mark.parametrize(
    "invalid_value, message",
    [
        ({"device_code": ""}, "device_code"),
        ({"user_code": ""}, "user_code"),
        ({"verification_uri": ""}, "verification_uri"),
        ({"verification_uri_complete": 42}, "verification_uri_complete"),
        ({"expires_in": 0}, "expires_in"),
        ({"interval": 0}, "interval"),
    ],
)
def test_oauth2_device_authorization_response_validation(invalid_value, message):
    response = {
        "device_code": "device-code",
        "user_code": "user-code",
        "verification_uri": "https://issuer.example/verify",
        "verification_uri_complete": "https://issuer.example/verify?user_code=user-code",
        "expires_in": 600,
        "interval": 5,
    }
    response.update(invalid_value)

    with pytest.raises(issues.Error, match=message):
        OAuth2CredentialsBase._process_device_authorization_response(response)


def test_oauth2_sync_http_requests_and_discovery_cache():
    credentials = ydb.oidc.OAuth2ClientCredentials(
        "https://issuer.example",
        "client-id",
        "client-secret",
    )
    response = MagicMock(status=200)
    response.read.return_value = b'{"issuer":"https://issuer.example","token_endpoint":"https://issuer.example/token"}'
    response_context = MagicMock()
    response_context.__enter__.return_value = response

    with patch("ydb.oidc.credentials.urllib.request.urlopen", return_value=response_context) as urlopen:
        first = credentials._discovery()
        second = credentials._discovery()

    assert first is second
    assert urlopen.call_count == 1

    http_error = urllib.error.HTTPError(
        "https://issuer.example/token",
        400,
        "Bad Request",
        {},
        io.BytesIO(b'{"error":"invalid_request"}'),
    )
    with patch("ydb.oidc.credentials.urllib.request.urlopen", side_effect=http_error):
        assert credentials._request_json("https://issuer.example/token", {"key": "value"}) == (
            400,
            {"error": "invalid_request"},
        )

    with patch(
        "ydb.oidc.credentials.urllib.request.urlopen",
        side_effect=urllib.error.URLError("unavailable"),
    ):
        with pytest.raises(issues.Unavailable):
            credentials._request_json("https://issuer.example/token")


def test_oauth2_sync_device_error_paths():
    with pytest.raises(ValueError):
        ydb.oidc.OAuth2DeviceCredentials("https://issuer.example", "client-id", None)
    with pytest.raises(ValueError):
        ydb.oidc.OAuth2DeviceCredentials(
            "https://issuer.example",
            "client-id",
            lambda info: None,
            device_flow_timeout=0,
        )

    credentials = ydb.oidc.OAuth2DeviceCredentials(
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
    assert credentials._save_token_response(
        {
            "access_token": "token",
            "token_type": "Bearer",
            "expires_in": 300,
        }
    ) == {"access_token": "Bearer token", "expires_in": 300}

    credentials._refresh_token_value = "refresh-token"
    credentials._request_json = MagicMock(return_value=(400, {"error": "invalid_grant"}))
    assert credentials._try_refresh("https://issuer.example/token") is None
    assert credentials._refresh_token_value is None

    credentials._discovery_document = {"token_endpoint": "https://issuer.example/token"}
    with pytest.raises(issues.Error, match="device_authorization_endpoint"):
        credentials._make_token_request()


@pytest.mark.parametrize(
    "token_response, expected_message",
    [
        ({"error": "expired_token"}, "expired"),
        ({"error": "access_denied"}, "access_denied"),
        (None, "timed out"),
    ],
)
def test_oauth2_sync_device_expiration(token_response, expected_message):
    credentials = ydb.oidc.OAuth2DeviceCredentials(
        "https://issuer.example",
        "client-id",
        lambda info: None,
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
    monotonic_values = [0, 2]
    if token_response is not None:
        responses.append((400, token_response))
        monotonic_values = [0, 0]
    credentials._request_json = MagicMock(side_effect=responses)

    with patch("ydb.oidc.credentials.time.monotonic", side_effect=monotonic_values), patch(
        "ydb.oidc.credentials.time.sleep"
    ):
        with pytest.raises(issues.Unauthenticated, match=expected_message):
            credentials._make_token_request()
