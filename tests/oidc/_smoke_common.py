import asyncio
import base64
import http.cookiejar
import json
import os
import ssl
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import Dict, List, Optional

import ydb


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError("Missing {}: run prepare.sh and load .state/oidc.env".format(name))
    return value


def oidc_settings() -> Dict[str, str]:
    return {
        "issuer": required_env("YDB_OIDC_ISSUER"),
        "audience": required_env("YDB_OIDC_AUDIENCE"),
        "ca_file": required_env("YDB_OIDC_CA_FILE"),
    }


def client_credentials() -> ydb.oidc.OAuth2ClientCredentials:
    return ydb.oidc.OAuth2ClientCredentials(
        client_id=required_env("YDB_OIDC_CLIENT_ID"),
        client_secret=required_env("YDB_OIDC_CLIENT_SECRET"),
        **oidc_settings(),
    )


def raw_access_token() -> str:
    token = os.getenv("YDB_ACCESS_TOKEN")
    if token:
        return token.removeprefix("Bearer ")
    return client_credentials().get_auth_token().removeprefix("Bearer ")


def assert_token_claims(token: str) -> None:
    encoded_payload = token.split(".")[1]
    padding = "=" * (-len(encoded_payload) % 4)
    claims = json.loads(base64.urlsafe_b64decode(encoded_payload + padding))
    audience = claims.get("aud", [])
    if isinstance(audience, str):
        audience = [audience]
    if claims.get("iss") != required_env("YDB_OIDC_ISSUER"):
        raise RuntimeError("Unexpected issuer: {!r}".format(claims.get("iss")))
    if required_env("YDB_OIDC_AUDIENCE") not in audience:
        raise RuntimeError("Unexpected audience: {!r}".format(audience))


def execute_sync(credentials, label: str) -> None:
    with ydb.Driver(
        endpoint=required_env("YDB_ENDPOINT"),
        database=required_env("YDB_DATABASE"),
        credentials=credentials,
    ) as driver:
        driver.wait(timeout=10, fail_fast=True)
        with ydb.QuerySessionPool(driver) as pool:
            result_sets = pool.execute_with_retries("SELECT 42 AS answer")
    answer = result_sets[0].rows[0].answer
    if answer != 42:
        raise RuntimeError("{} returned {!r}".format(label, answer))
    print("{} sync query succeeded: answer=42".format(label))


async def execute_async(credentials, label: str) -> None:
    async with ydb.aio.Driver(
        endpoint=required_env("YDB_ENDPOINT"),
        database=required_env("YDB_DATABASE"),
        credentials=credentials,
    ) as driver:
        await driver.wait(timeout=10, fail_fast=True)
        async with ydb.aio.QuerySessionPool(driver) as pool:
            result_sets = await pool.execute_with_retries("SELECT 42 AS answer")
    answer = result_sets[0].rows[0].answer
    if answer != 42:
        raise RuntimeError("{} returned {!r}".format(label, answer))
    print("{} async query succeeded: answer=42".format(label))


class _Form:
    def __init__(self, form_id: Optional[str], action: str):
        self.form_id = form_id
        self.action = action
        self.inputs: Dict[str, str] = {}


class _FormParser(HTMLParser):
    def __init__(self):
        super(_FormParser, self).__init__()
        self.forms: List[_Form] = []
        self._current: Optional[_Form] = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "form":
            action = attributes.get("action")
            if action:
                self._current = _Form(attributes.get("id"), action)
                self.forms.append(self._current)
        elif tag == "input" and self._current is not None:
            name = attributes.get("name")
            if name:
                self._current.inputs[name] = attributes.get("value", "")

    def handle_endtag(self, tag):
        if tag == "form":
            self._current = None


def _forms(content: bytes) -> List[_Form]:
    parser = _FormParser()
    parser.feed(content.decode("utf-8"))
    return parser.forms


def approve_keycloak_device(info: ydb.oidc.DeviceAuthorizationInfo) -> None:
    if not info.verification_uri_complete:
        raise RuntimeError("Keycloak did not return verification_uri_complete")

    context = ssl.create_default_context(cafile=required_env("YDB_OIDC_CA_FILE"))
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=context),
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
    )

    with opener.open(info.verification_uri_complete, timeout=10) as response:
        current_url = response.geturl()
        login_forms = [form for form in _forms(response.read()) if form.form_id == "kc-form-login"]
    if len(login_forms) != 1:
        raise RuntimeError("Expected one Keycloak login form")

    login = login_forms[0]
    login.inputs.update(
        {
            "username": required_env("YDB_OIDC_DEVICE_USERNAME"),
            "password": required_env("YDB_OIDC_DEVICE_PASSWORD"),
            "credentialId": "",
        }
    )
    request = urllib.request.Request(
        urllib.parse.urljoin(current_url, login.action),
        data=urllib.parse.urlencode(login.inputs).encode("utf-8"),
    )
    with opener.open(request, timeout=10) as response:
        current_url = response.geturl()
        consent_forms = [form for form in _forms(response.read()) if "login-actions/consent" in form.action]
    if len(consent_forms) != 1:
        raise RuntimeError("Expected one Keycloak device consent form")

    consent = consent_forms[0]
    consent.inputs["accept"] = "Yes"
    request = urllib.request.Request(
        urllib.parse.urljoin(current_url, consent.action),
        data=urllib.parse.urlencode(consent.inputs).encode("utf-8"),
    )
    with opener.open(request, timeout=10) as response:
        content = response.read()
    if b"Device Login Successful" not in content:
        raise RuntimeError("Keycloak did not confirm Device Authorization")


async def approve_keycloak_device_async(info: ydb.oidc.DeviceAuthorizationInfo) -> None:
    await asyncio.to_thread(approve_keycloak_device, info)
