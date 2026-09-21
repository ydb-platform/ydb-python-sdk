# -*- coding: utf-8 -*-
import base64
import json
import os
import ssl
import typing
from dataclasses import dataclass
from urllib.parse import quote_plus, urlsplit

from ydb import issues


DEVICE_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"


@dataclass(frozen=True)
class DeviceAuthorizationInfo:
    verification_uri: str
    user_code: str
    verification_uri_complete: typing.Optional[str]
    expires_in: int
    interval: int


class OAuth2CredentialsBase:
    def __init__(
        self,
        issuer: str,
        client_id: str,
        scope: typing.Union[str, typing.Sequence[str], None] = None,
        audience: typing.Optional[str] = None,
        ca_file: typing.Optional[str] = None,
        request_timeout: float = 10,
    ):
        if not issuer:
            raise ValueError("OAuth 2.0 issuer must not be empty")
        if not client_id:
            raise ValueError("OAuth 2.0 client ID must not be empty")
        if request_timeout <= 0:
            raise ValueError("OAuth 2.0 request timeout must be positive")

        if not self._is_https_url(issuer, issuer=True):
            raise ValueError("OAuth 2.0 issuer must be an absolute HTTPS URL without userinfo, query, or fragment")

        self._issuer = issuer
        self._client_id = client_id
        self._scope = self._scope_parameter(scope)
        self._audience = audience
        self._request_timeout = request_timeout
        self._discovery_document: typing.Optional[typing.Dict[str, typing.Any]] = None
        self._ssl_context = ssl.create_default_context(cafile=os.path.expanduser(ca_file) if ca_file else None)

    @staticmethod
    def _scope_parameter(scope: typing.Union[str, typing.Sequence[str], None]) -> str:
        if scope is None:
            scopes = []
        elif isinstance(scope, str):
            scopes = scope.split()
        else:
            scopes = list(scope)
        if "openid" not in scopes:
            scopes.append("openid")
        return " ".join(scopes)

    @staticmethod
    def _is_https_url(value: str, issuer: bool = False) -> bool:
        if not isinstance(value, str) or any(ord(character) <= 0x20 or ord(character) == 0x7F for character in value):
            return False
        try:
            parsed = urlsplit(value)
            parsed.port
        except ValueError:
            return False
        return (
            parsed.scheme == "https"
            and parsed.hostname is not None
            and parsed.username is None
            and parsed.password is None
            and not parsed.fragment
            and (not issuer or not parsed.query)
        )

    @staticmethod
    def _decode_json(content: bytes, url: str) -> typing.Dict[str, typing.Any]:
        try:
            value = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise issues.Error("OAuth 2.0 endpoint returned invalid JSON from {}: {}".format(url, error))
        if not isinstance(value, dict):
            raise issues.Error("OAuth 2.0 endpoint returned a non-object JSON response from {}".format(url))
        return value

    @staticmethod
    def _raise_for_status(status: int, response: typing.Mapping[str, typing.Any]) -> None:
        if 200 <= status < 300:
            return

        error = response.get("error", "unknown_error")
        description = response.get("error_description")
        message = "OAuth 2.0 request failed: {}".format(error)
        if description:
            message += ": {}".format(description)

        if status in (401, 403) or error in ("invalid_client", "access_denied"):
            raise issues.Unauthenticated(message)
        if status >= 500:
            raise issues.Unavailable(message)
        if status >= 400:
            raise issues.BadRequest(message)
        raise issues.Error(message)

    def _process_discovery_response(
        self, status: int, response: typing.Dict[str, typing.Any]
    ) -> typing.Dict[str, typing.Any]:
        self._raise_for_status(status, response)
        discovered_issuer = response.get("issuer")
        if discovered_issuer != self._issuer:
            raise issues.Error(
                "OIDC discovery issuer mismatch: expected {!r}, got {!r}".format(self._issuer, discovered_issuer)
            )
        token_endpoint = response.get("token_endpoint")
        if not isinstance(token_endpoint, str) or not token_endpoint:
            raise issues.Error("OIDC discovery response does not contain a token_endpoint")
        if not self._is_https_url(token_endpoint):
            raise issues.Error("OIDC discovery response contains an invalid token_endpoint URL")
        device_endpoint = response.get("device_authorization_endpoint")
        if device_endpoint is not None and (
            not isinstance(device_endpoint, str) or not self._is_https_url(device_endpoint)
        ):
            raise issues.Error("OIDC discovery response contains an invalid device_authorization_endpoint URL")
        return response

    @staticmethod
    def _process_token_response(response: typing.Mapping[str, typing.Any]) -> typing.Dict[str, typing.Any]:
        access_token = response.get("access_token")
        token_type = response.get("token_type")
        expires_in = response.get("expires_in")

        if not isinstance(access_token, str) or not access_token:
            raise issues.Error("OAuth 2.0 token response does not contain an access_token")
        if not isinstance(token_type, str) or token_type.lower() != "bearer":
            raise issues.Error("OAuth 2.0 token response contains an unsupported token_type: {!r}".format(token_type))
        if isinstance(expires_in, bool) or not isinstance(expires_in, (int, float)) or expires_in <= 0:
            raise issues.Error("OAuth 2.0 token response contains an invalid expires_in: {!r}".format(expires_in))

        return {"access_token": "Bearer " + access_token, "expires_in": expires_in}

    @staticmethod
    def _client_authorization_header(client_id: str, client_secret: str) -> str:
        encoded_id = quote_plus(client_id)
        encoded_secret = quote_plus(client_secret)
        value = base64.b64encode("{}:{}".format(encoded_id, encoded_secret).encode("utf-8")).decode("ascii")
        return "Basic " + value

    def _client_credentials_data(self) -> typing.Dict[str, str]:
        data = {"grant_type": "client_credentials", "scope": self._scope}
        if self._audience:
            data["audience"] = self._audience
        return data

    def _device_authorization_data(self) -> typing.Dict[str, str]:
        data = {"client_id": self._client_id, "scope": self._scope}
        if self._audience:
            data["audience"] = self._audience
        return data

    def _device_token_data(self, device_code: str) -> typing.Dict[str, str]:
        return {
            "grant_type": DEVICE_GRANT_TYPE,
            "client_id": self._client_id,
            "device_code": device_code,
        }

    def _refresh_token_data(self, refresh_token: str) -> typing.Dict[str, str]:
        data = {
            "grant_type": "refresh_token",
            "client_id": self._client_id,
            "refresh_token": refresh_token,
            "scope": self._scope,
        }
        return data

    @staticmethod
    def _process_device_authorization_response(
        response: typing.Mapping[str, typing.Any],
    ) -> typing.Tuple[str, DeviceAuthorizationInfo]:
        device_code = response.get("device_code")
        user_code = response.get("user_code")
        verification_uri = response.get("verification_uri")
        verification_uri_complete = response.get("verification_uri_complete")
        expires_in = response.get("expires_in")
        interval = response.get("interval", 5)

        if not isinstance(device_code, str) or not device_code:
            raise issues.Error("Device Authorization response does not contain a device_code")
        if not isinstance(user_code, str) or not user_code:
            raise issues.Error("Device Authorization response does not contain a user_code")
        if not isinstance(verification_uri, str) or not verification_uri:
            raise issues.Error("Device Authorization response does not contain a verification_uri")
        if not OAuth2CredentialsBase._is_https_url(verification_uri):
            raise issues.Error("Device Authorization response contains an invalid verification_uri URL")
        if verification_uri_complete is not None and not isinstance(verification_uri_complete, str):
            raise issues.Error("Device Authorization response contains an invalid verification_uri_complete")
        if verification_uri_complete is not None and not OAuth2CredentialsBase._is_https_url(verification_uri_complete):
            raise issues.Error("Device Authorization response contains an invalid verification_uri_complete URL")
        if isinstance(expires_in, bool) or not isinstance(expires_in, int) or expires_in <= 0:
            raise issues.Error("Device Authorization response contains an invalid expires_in: {!r}".format(expires_in))
        if isinstance(interval, bool) or not isinstance(interval, int) or interval <= 0:
            raise issues.Error("Device Authorization response contains an invalid interval: {!r}".format(interval))

        info = DeviceAuthorizationInfo(
            verification_uri=verification_uri,
            user_code=user_code,
            verification_uri_complete=verification_uri_complete,
            expires_in=expires_in,
            interval=interval,
        )
        return device_code, info


def bearer_token(token: str) -> str:
    if not isinstance(token, str) or not token:
        raise ValueError("OAuth 2.0 access token must not be empty")
    if token.lower().startswith("bearer "):
        if not token[7:].strip():
            raise ValueError("OAuth 2.0 access token must not be empty")
        return token
    if not token.strip():
        raise ValueError("OAuth 2.0 access token must not be empty")
    return "Bearer " + token
