# -*- coding: utf-8 -*-
import time
import http.server
import urllib
import json
import threading
import tempfile
import os
import jwt
import base64
from ydb.oauth2_token_exchange import Oauth2TokenExchangeCredentials, FixedTokenSource
from ydb.driver import credentials_from_env_variables


TEST_RSA_PRIVATE_KEY_CONTENT = "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC75/JS3rMcLJxv\nFgpOzF5+2gH+Yig3RE2MTl9uwC0BZKAv6foYr7xywQyWIK+W1cBhz8R4LfFmZo2j\nM0aCvdRmNBdW0EDSTnHLxCsFhoQWLVq+bI5f5jzkcoiioUtaEpADPqwgVULVtN/n\nnPJiZ6/dU30C3jmR6+LUgEntUtWt3eq3xQIn5lG3zC1klBY/HxtfH5Hu8xBvwRQT\nJnh3UpPLj8XwSmriDgdrhR7o6umWyVuGrMKlLHmeivlfzjYtfzO1MOIMG8t2/zxG\nR+xb4Vwks73sH1KruH/0/JMXU97npwpe+Um+uXhpldPygGErEia7abyZB2gMpXqr\nWYKMo02NAgMBAAECggEAO0BpC5OYw/4XN/optu4/r91bupTGHKNHlsIR2rDzoBhU\nYLd1evpTQJY6O07EP5pYZx9mUwUdtU4KRJeDGO/1/WJYp7HUdtxwirHpZP0lQn77\nuccuX/QQaHLrPekBgz4ONk+5ZBqukAfQgM7fKYOLk41jgpeDbM2Ggb6QUSsJISEp\nzrwpI/nNT/wn+Hvx4DxrzWU6wF+P8kl77UwPYlTA7GsT+T7eKGVH8xsxmK8pt6lg\nsvlBA5XosWBWUCGLgcBkAY5e4ZWbkdd183o+oMo78id6C+PQPE66PLDtHWfpRRmN\nm6XC03x6NVhnfvfozoWnmS4+e4qj4F/emCHvn0GMywKBgQDLXlj7YPFVXxZpUvg/\nrheVcCTGbNmQJ+4cZXx87huqwqKgkmtOyeWsRc7zYInYgraDrtCuDBCfP//ZzOh0\nLxepYLTPk5eNn/GT+VVrqsy35Ccr60g7Lp/bzb1WxyhcLbo0KX7/6jl0lP+VKtdv\nmto+4mbSBXSM1Y5BVVoVgJ3T/wKBgQDsiSvPRzVi5TTj13x67PFymTMx3HCe2WzH\nJUyepCmVhTm482zW95pv6raDr5CTO6OYpHtc5sTTRhVYEZoEYFTM9Vw8faBtluWG\nBjkRh4cIpoIARMn74YZKj0C/0vdX7SHdyBOU3bgRPHg08Hwu3xReqT1kEPSI/B2V\n4pe5fVrucwKBgQCNFgUxUA3dJjyMES18MDDYUZaRug4tfiYouRdmLGIxUxozv6CG\nZnbZzwxFt+GpvPUV4f+P33rgoCvFU+yoPctyjE6j+0aW0DFucPmb2kBwCu5J/856\nkFwCx3blbwFHAco+SdN7g2kcwgmV2MTg/lMOcU7XwUUcN0Obe7UlWbckzQKBgQDQ\nnXaXHL24GGFaZe4y2JFmujmNy1dEsoye44W9ERpf9h1fwsoGmmCKPp90az5+rIXw\nFXl8CUgk8lXW08db/r4r+ma8Lyx0GzcZyplAnaB5/6j+pazjSxfO4KOBy4Y89Tb+\nTP0AOcCi6ws13bgY+sUTa/5qKA4UVw+c5zlb7nRpgwKBgGXAXhenFw1666482iiN\ncHSgwc4ZHa1oL6aNJR1XWH+aboBSwR+feKHUPeT4jHgzRGo/aCNHD2FE5I8eBv33\nof1kWYjAO0YdzeKrW0rTwfvt9gGg+CS397aWu4cy+mTI+MNfBgeDAIVBeJOJXLlX\nhL8bFAuNNVrCOp79TNnNIsh7\n-----END PRIVATE KEY-----\n"  # noqa: E501
TEST_RSA_PUBLIC_KEY_CONTENT = "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAu+fyUt6zHCycbxYKTsxe\nftoB/mIoN0RNjE5fbsAtAWSgL+n6GK+8csEMliCvltXAYc/EeC3xZmaNozNGgr3U\nZjQXVtBA0k5xy8QrBYaEFi1avmyOX+Y85HKIoqFLWhKQAz6sIFVC1bTf55zyYmev\n3VN9At45kevi1IBJ7VLVrd3qt8UCJ+ZRt8wtZJQWPx8bXx+R7vMQb8EUEyZ4d1KT\ny4/F8Epq4g4Ha4Ue6OrplslbhqzCpSx5nor5X842LX8ztTDiDBvLdv88RkfsW+Fc\nJLO97B9Sq7h/9PyTF1Pe56cKXvlJvrl4aZXT8oBhKxImu2m8mQdoDKV6q1mCjKNN\njQIDAQAB\n-----END PUBLIC KEY-----\n"  # noqa: E501
TEST_EC_PRIVATE_KEY_CONTENT = "-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEIB6fv25gf7P/7fkjW/2kcKICUhHeOygkFeUJ/ylyU3hloAoGCCqGSM49\nAwEHoUQDQgAEvkKy92hpLiT0GEpzFkYBEWWnkAGTTA6141H0oInA9X30eS0RObAa\nmVY8yD39NI7Nj03hBxEa4Z0tOhrq9cW8eg==\n-----END EC PRIVATE KEY-----\n"  # noqa: E501
TEST_EC_PUBLIC_KEY_CONTENT = "-----BEGIN PUBLIC KEY-----\nMFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEvkKy92hpLiT0GEpzFkYBEWWnkAGT\nTA6141H0oInA9X30eS0RObAamVY8yD39NI7Nj03hBxEa4Z0tOhrq9cW8eg==\n-----END PUBLIC KEY-----\n"  # noqa: E501
TEST_HMAC_SECRET_KEY_BASE64_CONTENT = "VGhlIHdvcmxkIGhhcyBjaGFuZ2VkLgpJIHNlZSBpdCBpbiB0aGUgd2F0ZXIuCkkgZmVlbCBpdCBpbiB0aGUgRWFydGguCkkgc21lbGwgaXQgaW4gdGhlIGFpci4KTXVjaCB0aGF0IG9uY2Ugd2FzIGlzIGxvc3QsCkZvciBub25lIG5vdyBsaXZlIHdobyByZW1lbWJlciBpdC4K"  # noqa: E501


def get_expire_time(creds):
    return creds._expires_in - time.time()


TOKEN_EXCHANGE_RESPONSES = {
    "test_src_token": [
        200,
        {
            "access_token": "test_dst_token",
            "issued_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "token_type": "BeareR",
            "expires_in": 42,
        },
    ],
    "test_http_code": [
        403,
        {
            "err": "err_42",
            "access_token": "test_dst_token",
            "issued_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "token_type": "BeareR",
            "expires_in": 42,
        },
    ],
    "test_wrong_token_type": [
        200,
        {
            "access_token": "test_dst_token",
            "issued_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "token_type": "basic",
            "expires_in": 42,
        },
    ],
    "test_wrong_expiration_time": [
        200,
        {
            "access_token": "test_dst_token",
            "issued_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "token_type": "BeareR",
            "expires_in": -42,
        },
    ],
    "test_different_scope": [
        200,
        {
            "access_token": "test_dst_token",
            "issued_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "token_type": "BeareR",
            "expires_in": 42,
            "scope": "s1",
        },
    ],
}


class FixedTokenSourceChecker:
    def __init__(
        self,
        token,
        token_type,
    ):
        self.token = token
        self.token_type = token_type

    def check(self, token, token_type):
        assert token == self.token
        assert token_type == self.token_type


class AnyTokenSourceChecker:
    def check(self, token, token_type):
        assert token != ""
        assert token_type != ""


class JwtTokenSourceChecker:
    def __init__(
        self,
        alg,
        public_key,
        key_id=None,
        issuer=None,
        subject=None,
        aud=None,
        id=None,
        ttl_seconds=3600,
    ):
        self.alg = alg
        self.public_key = public_key
        self.key_id = key_id
        self.issuer = issuer
        self.subject = subject
        self.aud = aud
        self.id = id
        self.ttl_seconds = ttl_seconds

    def check(self, token, token_type):
        assert token_type == "urn:ietf:params:oauth:token-type:jwt"
        decoded = jwt.decode(
            token,
            key=self.public_key,
            algorithms=[self.alg],
            options={
                "require": ["iat", "exp"],
                "verify_signature": True,
                "verify_aud": False,
                "verify_iss": False,
            },
        )
        header = jwt.get_unverified_header(token)
        assert header.get("kid") == self.key_id
        assert header.get("alg") == self.alg
        assert decoded.get("iss") == self.issuer
        assert decoded.get("sub") == self.subject
        assert decoded.get("aud") == self.aud
        assert decoded.get("jti") == self.id
        assert abs(decoded["iat"] - time.time()) <= 60
        assert abs(decoded["exp"] - decoded["iat"]) == self.ttl_seconds


class Oauth2ExchangeServiceChecker:
    def __init__(
        self,
        subject_token_source=None,
        actor_token_source=None,
        audience=None,
        scope=None,
        resource=None,
        requested_token_type="urn:ietf:params:oauth:token-type:access_token",
        grant_type="urn:ietf:params:oauth:grant-type:token-exchange",
    ):
        self.subject_token_source = subject_token_source
        self.actor_token_source = actor_token_source
        self.audience = audience
        self.scope = scope
        self.resource = resource
        self.requested_token_type = requested_token_type
        self.grant_type = grant_type

    def check(self, handler, parsed_request) -> None:
        assert handler.headers["Content-Type"] == "application/x-www-form-urlencoded"
        assert handler.path == "/token/exchange"

        assert len(parsed_request["grant_type"]) == 1
        assert parsed_request["grant_type"][0] == self.grant_type

        assert len(parsed_request["requested_token_type"]) == 1
        assert parsed_request["requested_token_type"][0] == self.requested_token_type

        if self.audience is None or len(self.audience) == 0:
            assert len(parsed_request.get("audience", [])) == 0
        else:
            assert len(parsed_request["audience"]) == len(self.audience)
            for i in range(len(self.audience)):
                assert parsed_request["audience"][i] == self.audience[i]

        if self.scope is None or len(self.scope) == 0:
            assert len(parsed_request.get("scope", [])) == 0
        else:
            assert len(parsed_request.get("scope", [])) == 1
            assert parsed_request["scope"][0] == " ".join(self.scope)

        if self.resource is None or len(self.resource) == 0:
            assert len(parsed_request.get("resource", [])) == 0
        else:
            assert len(parsed_request["resource"]) == len(self.resource)
            for i in range(len(self.resource)):
                assert parsed_request["resource"][i] == self.resource[i]

        if self.subject_token_source is None:
            assert len(parsed_request.get("subject_token", [])) == 0
            assert len(parsed_request.get("subject_token_type", [])) == 0
        else:
            assert len(parsed_request.get("subject_token", [])) == 1
            assert len(parsed_request.get("subject_token_type", [])) == 1
            self.subject_token_source.check(parsed_request["subject_token"][0], parsed_request["subject_token_type"][0])

        if self.actor_token_source is None:
            assert len(parsed_request.get("actor_token", [])) == 0
            assert len(parsed_request.get("actor_token_type", [])) == 0
        else:
            assert len(parsed_request.get("actor_token", [])) == 1
            assert len(parsed_request.get("actor_token_type", [])) == 1
            self.actor_token_source.check(parsed_request["actor_token"][0], parsed_request["actor_token_type"][0])


class TokenExchangeResponseBySubjectToken:
    def __init__(self, responses=TOKEN_EXCHANGE_RESPONSES):
        self.responses = responses

    def get_response(self, parsed_request):
        assert len(parsed_request["subject_token"]) == 1
        responses = self.responses.get(parsed_request["subject_token"][0])
        assert responses is not None
        response_code = responses[0]
        response = responses[1]
        return response_code, response


class Oauth2TokenExchangeResponse:
    def __init__(
        self,
        response_code,
        response,
    ):
        self.response_code = response_code
        self.response = response

    def get_response(self, parsed_request):
        return self.response_code, self.response


class OauthExchangeServiceHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length).decode("utf8")
        print("OauthExchangeServiceHandler.POST data: {}".format(post_data))
        parsed_request = urllib.parse.parse_qs(str(post_data))
        try:
            self.server.checker.check(self, parsed_request)
            self.server.checker.check_successful = True
            response_code, response = self.server.response.get_response(parsed_request)

            self.send_response(response_code)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf8"))
        except Exception as ex:
            self.send_response(500)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write("Exception during text check: {}".format(ex).encode("utf8"))


class Oauth2TokenExchangeServiceForTest(http.server.HTTPServer):
    def __init__(self, port, checker=None, response=None):
        http.server.HTTPServer.__init__(self, ("localhost", port), OauthExchangeServiceHandler)
        self.checker = checker
        if self.checker is None:
            self.checker = Oauth2ExchangeServiceChecker(
                subject_token_source=AnyTokenSourceChecker(),
                audience=["a1", "a2"],
                scope=["s1", "s2"],
            )
        self.response = response
        if self.response is None:
            self.response = TokenExchangeResponseBySubjectToken()
        self.port = port

    def endpoint(self):
        return "http://localhost:{}/token/exchange".format(self.port)


class DataForTest:
    def __init__(self, src_token, dst_token, error_text):
        self.src_token = src_token
        self.dst_token = dst_token
        self.error_text = error_text

    def run_check(self, server):
        try:
            credentials = Oauth2TokenExchangeCredentials(
                server.endpoint(),
                subject_token_source=FixedTokenSource(self.src_token, "test_token_type"),
                audience=["a1", "a2"],
                scope=["s1", "s2"],
            )
            t = credentials.get_auth_token()
            assert not self.error_text, "Exception is expected. Test: {}".format(self.src_token)
            assert t == self.dst_token
            assert get_expire_time(credentials) <= 42
        except AssertionError:
            raise
        except Exception as ex:
            if self.error_text:
                assert self.error_text in str(ex)
            else:
                assert False, "Exception is not expected. Test: {}. Exception text: {}".format(self.src_token, ex)


def test_oauth2_token_exchange_credentials():
    server = Oauth2TokenExchangeServiceForTest(40123)

    tests = [
        DataForTest(
            "test_src_token",
            "Bearer test_dst_token",
            "",
        ),
        DataForTest(
            "test_http_code",
            "",
            "err_42",
        ),
        DataForTest(
            "test_wrong_token_type",
            "",
            "unsupported token type: basic",
        ),
        DataForTest(
            "test_wrong_expiration_time",
            "",
            "incorrect expiration time: -42",
        ),
        DataForTest(
            "test_different_scope",
            "",
            'different scope. Expected: "s1 s2", but got: "s1"',
        ),
    ]

    def serve(s):
        for _ in tests:
            # one request per test
            s.handle_request()

    serve_thread = threading.Thread(target=serve, args=(server,))
    serve_thread.start()

    try:
        for t in tests:
            t.run_check(server)
    except Exception:
        raise

    serve_thread.join()


class DataForConfigTest:
    def __init__(
        self,
        cfg=None,  # cfg or cfg text
        cfg_file=None,
        checker=None,
        response=None,
        init_error_text_part=None,
        get_token_error_text_part=None,
        dst_token=None,
        dst_expire_time=42,
        http_request_is_expected=None,
        init_from_env=False,
    ):
        self.cfg = cfg
        self.cfg_file = cfg_file
        self.checker = checker
        self.response = response
        self.init_error_text_part = init_error_text_part
        self.get_token_error_text_part = get_token_error_text_part
        self.dst_token = dst_token
        self.dst_expire_time = dst_expire_time
        self.http_request_is_expected = http_request_is_expected
        self.init_from_env = init_from_env

    def get_cfg(self):
        if isinstance(self.cfg, str):
            return self.cfg
        else:
            return json.dumps(self.cfg, indent=4)

    def expect_http_request(self):
        if self.http_request_is_expected is not None:
            return self.http_request_is_expected

        if self.init_error_text_part is not None:
            return False
        return True

    def run_check(self, server):
        server.checker = self.checker
        if server.checker is not None:
            server.checker.check_successful = False
        server.response = self.response

        if self.cfg_file:
            cfg_file = self.cfg_file

            def rm_file():
                pass

        else:
            temp_cfg_file = tempfile.NamedTemporaryFile(delete=False)
            cfg_file = temp_cfg_file.name
            temp_cfg_file.write(self.get_cfg().encode("utf-8"))
            temp_cfg_file.close()

            def rm_file():
                os.remove(cfg_file)
                if self.init_from_env:
                    del os.environ["YDB_OAUTH2_KEY_FILE"]

        try:
            if self.init_from_env:
                os.environ["YDB_OAUTH2_KEY_FILE"] = cfg_file
                credentials = credentials_from_env_variables()
            else:
                credentials = Oauth2TokenExchangeCredentials.from_file(
                    cfg_file,
                    iam_endpoint=server.endpoint(),
                )
            assert self.init_error_text_part is None, "Init exception is expected. Test:\n{}".format(self.get_cfg())

            t = credentials.get_auth_token()
            assert not self.get_token_error_text_part, "Exception is expected. Test:\n{}".format(self.get_cfg())
            if self.expect_http_request() and server.checker is not None:
                assert server.checker.check_successful

            assert t == self.dst_token
            assert get_expire_time(credentials) <= self.dst_expire_time
            rm_file()
        except AssertionError:
            rm_file()
            raise
        except Exception as ex:
            rm_file()
            err_text = self.init_error_text_part if self.init_error_text_part else self.get_token_error_text_part
            if err_text:
                assert err_text in str(ex)
            else:
                assert False, "Exception is not expected. Test:\n{}. Exception text: {}".format(self.get_cfg(), ex)


def test_oauth2_token_exchange_credentials_file():
    server = Oauth2TokenExchangeServiceForTest(40124)

    tests = [
        DataForConfigTest(cfg="not json config", init_error_text_part="Failed to parse json config"),
        DataForConfigTest(
            init_from_env=True,
            cfg={
                "res": "tEst",
                "grant-type": "grant",
                "requested-token-type": "access_token",
                "subject-credentials": {
                    "type": "fixed",
                    "token": "test-token",
                    "token-type": "test-token-type",
                },
            },
            init_error_text_part="no token endpoint specified",
        ),
        DataForConfigTest(
            init_from_env=True,
            cfg={
                "token-endpoint": server.endpoint(),
                "res": "tEst",
                "grant-type": "grant",
                "requested-token-type": "access_token",
                "subject-credentials": {
                    "type": "fixed",
                    "token": "test-token",
                    "token-type": "test-token-type",
                },
            },
            checker=Oauth2ExchangeServiceChecker(
                subject_token_source=FixedTokenSourceChecker(
                    token="test-token",
                    token_type="test-token-type",
                ),
                grant_type="grant",
                requested_token_type="access_token",
                resource=["tEst"],
            ),
            response=Oauth2TokenExchangeResponse(
                200,
                {
                    "access_token": "test_dst_token",
                    "issued_token_type": "urn:ietf:params:oauth:token-type:access_token",
                    "token_type": "Bearer",
                    "expires_in": 42,
                },
            ),
            dst_token="Bearer test_dst_token",
        ),
        DataForConfigTest(
            cfg={
                "aud": "test-aud",
                "scope": [
                    "s1",
                    "s2",
                ],
                "res": ["r1", "r2"],
                "unknown-field": [123],
                "actor-credentials": {
                    "type": "fixed",
                    "token": "test-token",
                    "token-type": "test-token-type",
                },
            },
            checker=Oauth2ExchangeServiceChecker(
                actor_token_source=FixedTokenSourceChecker(
                    token="test-token",
                    token_type="test-token-type",
                ),
                audience=["test-aud"],
                scope=["s1", "s2"],
                resource=["r1", "r2"],
            ),
            response=Oauth2TokenExchangeResponse(
                200,
                {
                    "access_token": "test_dst_token",
                    "issued_token_type": "urn:ietf:params:oauth:token-type:access_token",
                    "token_type": "Bearer",
                    "expires_in": 42,
                },
            ),
            dst_token="Bearer test_dst_token",
        ),
        DataForConfigTest(
            cfg={
                "requested-token-type": "access_token",
                "subject-credentials": {
                    "type": "JWT",
                    "alg": "ps256",
                    "private-key": TEST_RSA_PRIVATE_KEY_CONTENT,
                    "aud": ["a1", "a2"],
                    "jti": "123",
                    "sub": "test_subject",
                    "iss": "test_issuer",
                    "kid": "test_key_id",
                    "ttl": "24h",
                    "unknown_field": "hello!",
                },
            },
            checker=Oauth2ExchangeServiceChecker(
                subject_token_source=JwtTokenSourceChecker(
                    alg="PS256",
                    public_key=TEST_RSA_PUBLIC_KEY_CONTENT,
                    aud=["a1", "a2"],
                    id="123",
                    subject="test_subject",
                    issuer="test_issuer",
                    key_id="test_key_id",
                    ttl_seconds=24 * 3600,
                ),
                requested_token_type="access_token",
            ),
            response=Oauth2TokenExchangeResponse(
                200,
                {
                    "access_token": "test_dst_token",
                    "issued_token_type": "urn:ietf:params:oauth:token-type:access_token",
                    "token_type": "bearer",
                    "expires_in": 42,
                },
            ),
            dst_token="Bearer test_dst_token",
        ),
        DataForConfigTest(
            cfg={
                "actor-credentials": {
                    "type": "JWT",
                    "alg": "es256",
                    "private-key": TEST_EC_PRIVATE_KEY_CONTENT,
                    "ttl": "3m",
                    "unknown_field": "hello!",
                },
            },
            checker=Oauth2ExchangeServiceChecker(
                actor_token_source=JwtTokenSourceChecker(
                    alg="ES256",
                    public_key=TEST_EC_PUBLIC_KEY_CONTENT,
                    ttl_seconds=180,
                ),
            ),
            response=Oauth2TokenExchangeResponse(
                200,
                {
                    "access_token": "test_dst_token",
                    "issued_token_type": "urn:ietf:params:oauth:token-type:access_token",
                    "token_type": "bearer",
                    "expires_in": 42,
                },
            ),
            dst_token="Bearer test_dst_token",
        ),
        DataForConfigTest(
            cfg={
                "subject-credentials": {
                    "type": "JWT",
                    "alg": "hs512",
                    "private-key": TEST_HMAC_SECRET_KEY_BASE64_CONTENT,
                },
            },
            checker=Oauth2ExchangeServiceChecker(
                subject_token_source=JwtTokenSourceChecker(
                    alg="HS512",
                    public_key=base64.b64decode(TEST_HMAC_SECRET_KEY_BASE64_CONTENT),
                ),
            ),
            response=Oauth2TokenExchangeResponse(
                200,
                {
                    "access_token": "test_dst_token",
                    "issued_token_type": "urn:ietf:params:oauth:token-type:access_token",
                    "token_type": "bearer",
                    "expires_in": 42,
                },
            ),
            dst_token="Bearer test_dst_token",
        ),
        DataForConfigTest(
            cfg={
                "subject-credentials": {
                    "type": "JWT",
                    "alg": "rs512",
                    "private-key": TEST_HMAC_SECRET_KEY_BASE64_CONTENT,
                },
            },
            http_request_is_expected=False,
            get_token_error_text_part="Could not deserialize key data.",
        ),
        DataForConfigTest(
            cfg={
                "subject-credentials": {
                    "type": "JWT",
                    "alg": "es512",
                    "private-key": TEST_HMAC_SECRET_KEY_BASE64_CONTENT,
                },
            },
            http_request_is_expected=False,
            get_token_error_text_part="Could not deserialize key data.",
        ),
        DataForConfigTest(
            cfg={
                "subject-credentials": {
                    "type": "JWT",
                    "alg": "es512",
                    "private-key": TEST_RSA_PRIVATE_KEY_CONTENT,
                },
            },
            http_request_is_expected=False,
            get_token_error_text_part="sign() missing 1 required positional argument",
        ),
        DataForConfigTest(
            cfg_file="~/unknown-file.cfg",
            init_error_text_part="No such file or directory",
        ),
        DataForConfigTest(
            cfg={
                "actor-credentials": "",
            },
            init_error_text_part='Key "actor-credentials" is expected to be a json map',
        ),
        DataForConfigTest(
            cfg={
                "subject-credentials": {
                    "type": "JWT",
                    "alg": "RS256",
                    "private-key": "123",
                    "ttl": 123,
                },
            },
            init_error_text_part='Key "ttl" is expected to be a string',
        ),
        DataForConfigTest(
            cfg={
                "subject-credentials": {
                    "type": "JWT",
                    "alg": "RS256",
                    "private-key": "123",
                    "ttl": "-3h",
                },
            },
            init_error_text_part="-3: negative duration is not allowed",
        ),
        DataForConfigTest(
            cfg={
                "subject-credentials": {
                    "type": "JWT",
                    "private-key": "123",
                },
            },
            init_error_text_part='Key "alg" is expected to be a nonempty string',
        ),
        DataForConfigTest(
            cfg={
                "subject-credentials": {
                    "type": "JWT",
                    "alg": "HS384",
                },
            },
            init_error_text_part='Key "private-key" is expected to be a nonempty string',
        ),
        DataForConfigTest(
            cfg={
                "subject-credentials": {
                    "type": "JWT",
                    "alg": "unknown",
                    "private-key": "123",
                },
            },
            http_request_is_expected=False,
            get_token_error_text_part="Algorithm not supported.",
        ),
        DataForConfigTest(
            cfg={
                "aud": {
                    "value": "wrong_format of aud: not string and not list",
                },
                "subject-credentials": {
                    "type": "FIXED",
                    "token": "test-token",
                    "token-type": "test-token-type",
                },
            },
            init_error_text_part='Key "aud" is expected to be a single string or list of nonempty strings',
        ),
        DataForConfigTest(
            cfg={
                "subject-credentials": {
                    "type": "JWT",
                    "alg": "RS256",
                    "private-key": "123",
                    "aud": {
                        "value": "wrong_format of aud: not string and not list",
                    },
                },
            },
            init_error_text_part='Key "aud" is expected to be a single string or list of nonempty strings',
        ),
        DataForConfigTest(
            cfg={
                "subject-credentials": {
                    "type": "unknown",
                },
            },
            init_error_text_part='"subject-credentials": unknown token source type: "unknown"',
        ),
        DataForConfigTest(
            cfg={
                "subject-credentials": {
                    "token": "test",
                },
            },
            init_error_text_part='Key "type" is expected to be a nonempty string',
        ),
        DataForConfigTest(
            cfg={
                "subject-credentials": {
                    "type": "FIXED",
                    "token": "test",
                },
            },
            init_error_text_part='Key "token-type" is expected to be a nonempty string',
        ),
        DataForConfigTest(
            cfg={
                "subject-credentials": {
                    "type": "FIXED",
                    "token-type": "test",
                },
            },
            init_error_text_part='Key "token" is expected to be a nonempty string',
        ),
    ]

    def serve(s):
        for t in tests:
            # one request per test
            if t.expect_http_request():
                s.handle_request()

    serve_thread = threading.Thread(target=serve, args=(server,))
    serve_thread.start()

    for t in tests:
        t.run_check(server)

    serve_thread.join()
