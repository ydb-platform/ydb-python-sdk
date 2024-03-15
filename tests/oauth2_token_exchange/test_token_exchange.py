# -*- coding: utf-8 -*-
import time
import http.server
import urllib
import json
import threading
from ydb.oauth2_token_exchange import Oauth2TokenExchangeCredentials, FixedTokenSource


class TestOauth2TokenExchangeCredentials(Oauth2TokenExchangeCredentials):
    def get_expire_time(self):
        return self._expires_in - time.time()


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


class OauthExchangeServiceHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        assert self.headers["Content-Type"] == "application/x-www-form-urlencoded"
        assert self.path == "/token/exchange"
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length).decode("utf8")
        print("OauthExchangeServiceHandler.POST data: {}".format(post_data))
        parsed_request = urllib.parse.parse_qs(str(post_data))
        assert len(parsed_request["grant_type"]) == 1
        assert parsed_request["grant_type"][0] == "urn:ietf:params:oauth:grant-type:token-exchange"

        assert len(parsed_request["requested_token_type"]) == 1
        assert parsed_request["requested_token_type"][0] == "urn:ietf:params:oauth:token-type:access_token"

        assert len(parsed_request["subject_token_type"]) == 1
        assert parsed_request["subject_token_type"][0] == "test_token_type"

        assert len(parsed_request["subject_token"]) == 1
        responses = TOKEN_EXCHANGE_RESPONSES.get(parsed_request["subject_token"][0])
        assert responses is not None
        response_code = responses[0]
        response = responses[1]

        assert len(parsed_request["audience"]) == 2
        assert parsed_request["audience"][0] == "a1"
        assert parsed_request["audience"][1] == "a2"

        assert len(parsed_request["scope"]) == 1
        assert parsed_request["scope"][0] == "s1 s2"

        self.send_response(response_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode("utf8"))


class Oauth2TokenExchangeServiceForTest(http.server.HTTPServer):
    def __init__(self, port):
        http.server.HTTPServer.__init__(self, ("localhost", port), OauthExchangeServiceHandler)
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
            credentials = TestOauth2TokenExchangeCredentials(
                server.endpoint(),
                subject_token_source=FixedTokenSource(self.src_token, "test_token_type"),
                audience=["a1", "a2"],
                scope=["s1", "s2"],
            )
            t = credentials.get_auth_token()
            assert not self.error_text, "Exception is expected. Test: {}".format(self.src_token)
            assert t == self.dst_token
            assert credentials.get_expire_time() <= 42
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
