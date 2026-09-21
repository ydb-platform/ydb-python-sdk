# -*- coding: utf-8 -*-
import asyncio
import inspect
import typing

import aiohttp

from ydb import issues
from ydb.aio.credentials import AbstractExpiringTokenCredentials
from ydb.oidc._common import DeviceAuthorizationInfo, OAuth2CredentialsBase
from ydb.oidc.credentials import OAuth2TokenCredentials


class _OAuth2Credentials(AbstractExpiringTokenCredentials, OAuth2CredentialsBase):
    def __init__(
        self,
        issuer: str,
        client_id: str,
        scope: typing.Union[str, typing.Sequence[str], None],
        audience: typing.Optional[str],
        ca_file: typing.Optional[str],
        request_timeout: float,
    ):
        AbstractExpiringTokenCredentials.__init__(self)
        OAuth2CredentialsBase.__init__(self, issuer, client_id, scope, audience, ca_file, request_timeout)

    async def _request_json(
        self,
        url: str,
        data: typing.Optional[typing.Mapping[str, str]] = None,
        headers: typing.Optional[typing.Mapping[str, str]] = None,
    ) -> typing.Tuple[int, typing.Dict[str, typing.Any]]:
        timeout = aiohttp.ClientTimeout(total=self._request_timeout)
        ssl_context = self._ssl_context if url.startswith("https://") else None
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.request(
                    "POST" if data is not None else "GET",
                    url,
                    data=data,
                    headers=headers,
                    ssl=ssl_context,
                ) as response:
                    return response.status, self._decode_json(await response.read(), url)
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as error:
            raise issues.Unavailable("OAuth 2.0 endpoint is unavailable at {}: {}".format(url, error))

    async def _discovery(self) -> typing.Dict[str, typing.Any]:
        if self._discovery_document is None:
            url = self._issuer.rstrip("/") + "/.well-known/openid-configuration"
            status, response = await self._request_json(url)
            self._discovery_document = self._process_discovery_response(status, response)
        return self._discovery_document


class OAuth2ClientCredentials(_OAuth2Credentials):
    """Asynchronous OAuth 2.0 Client Credentials Grant through OIDC discovery."""

    def __init__(
        self,
        issuer: str,
        client_id: str,
        client_secret: str,
        scope: typing.Union[str, typing.Sequence[str], None] = None,
        audience: typing.Optional[str] = None,
        ca_file: typing.Optional[str] = None,
        request_timeout: float = 10,
    ):
        if not client_secret:
            raise ValueError("OAuth 2.0 client secret must not be empty")
        super(OAuth2ClientCredentials, self).__init__(issuer, client_id, scope, audience, ca_file, request_timeout)
        self._client_secret = client_secret

    async def _make_token_request(self):
        token_endpoint = (await self._discovery())["token_endpoint"]
        headers = {"Authorization": self._client_authorization_header(self._client_id, self._client_secret)}
        status, response = await self._request_json(token_endpoint, self._client_credentials_data(), headers)
        self._raise_for_status(status, response)
        return self._process_token_response(response)


class OAuth2DeviceCredentials(_OAuth2Credentials):
    """Asynchronous OAuth 2.0 Device Authorization Grant through OIDC discovery."""

    def __init__(
        self,
        issuer: str,
        client_id: str,
        device_authorization_callback: typing.Callable[
            [DeviceAuthorizationInfo], typing.Union[typing.Awaitable[None], None]
        ],
        scope: typing.Union[str, typing.Sequence[str], None] = "openid",
        audience: typing.Optional[str] = None,
        client_secret: typing.Optional[str] = None,
        ca_file: typing.Optional[str] = None,
        request_timeout: float = 10,
        device_flow_timeout: typing.Optional[float] = None,
    ):
        if not callable(device_authorization_callback):
            raise ValueError("Device Authorization callback must be callable")
        if device_flow_timeout is not None and device_flow_timeout <= 0:
            raise ValueError("Device Authorization timeout must be positive")
        super(OAuth2DeviceCredentials, self).__init__(issuer, client_id, scope, audience, ca_file, request_timeout)
        self._device_authorization_callback = device_authorization_callback
        self._client_secret = client_secret
        self._device_flow_timeout = device_flow_timeout
        self._refresh_token_value: typing.Optional[str] = None

    def _client_headers(self) -> typing.Dict[str, str]:
        if self._client_secret is None:
            return {}
        return {"Authorization": self._client_authorization_header(self._client_id, self._client_secret)}

    def _save_token_response(self, response: typing.Mapping[str, typing.Any]) -> typing.Dict[str, typing.Any]:
        refresh_token = response.get("refresh_token")
        if refresh_token is not None:
            if not isinstance(refresh_token, str) or not refresh_token:
                raise issues.Error("OAuth 2.0 token response contains an invalid refresh_token")
            self._refresh_token_value = refresh_token
        return self._process_token_response(response)

    async def _try_refresh(self, token_endpoint: str) -> typing.Optional[typing.Dict[str, typing.Any]]:
        if self._refresh_token_value is None:
            return None
        status, response = await self._request_json(
            token_endpoint,
            self._refresh_token_data(self._refresh_token_value),
            self._client_headers(),
        )
        if status >= 400 and response.get("error") == "invalid_grant":
            self._refresh_token_value = None
            return None
        self._raise_for_status(status, response)
        return self._save_token_response(response)

    async def _make_token_request(self):
        discovery = await self._discovery()
        token_endpoint = discovery["token_endpoint"]
        refreshed = await self._try_refresh(token_endpoint)
        if refreshed is not None:
            return refreshed

        device_endpoint = discovery.get("device_authorization_endpoint")
        if not isinstance(device_endpoint, str) or not device_endpoint:
            raise issues.Error("OIDC discovery response does not contain a device_authorization_endpoint")

        status, response = await self._request_json(
            device_endpoint,
            self._device_authorization_data(),
            self._client_headers(),
        )
        self._raise_for_status(status, response)
        device_code, info = self._process_device_authorization_response(response)
        callback_result = self._device_authorization_callback(info)
        if inspect.isawaitable(callback_result):
            await callback_result

        timeout = info.expires_in
        if self._device_flow_timeout is not None:
            timeout = min(timeout, self._device_flow_timeout)
        deadline = asyncio.get_running_loop().time() + timeout
        interval = info.interval

        while asyncio.get_running_loop().time() < deadline:
            await asyncio.sleep(interval)
            status, response = await self._request_json(
                token_endpoint,
                self._device_token_data(device_code),
                self._client_headers(),
            )
            if 200 <= status < 300:
                return self._save_token_response(response)

            error = response.get("error")
            if error == "authorization_pending":
                continue
            if error == "slow_down":
                interval += 5
                continue
            if error == "expired_token":
                raise issues.Unauthenticated("OAuth 2.0 device code expired")
            self._raise_for_status(status, response)

        raise issues.Unauthenticated("OAuth 2.0 Device Authorization timed out")


__all__ = [
    "DeviceAuthorizationInfo",
    "OAuth2ClientCredentials",
    "OAuth2DeviceCredentials",
    "OAuth2TokenCredentials",
]
