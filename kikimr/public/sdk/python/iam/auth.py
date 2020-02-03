# -*- coding: utf-8 -*-
from kikimr.public.sdk.python.client import credentials
import grpc
import time
from datetime import datetime
import json

try:
    from yandex.cloud.iam.v1 import iam_token_service_pb2_grpc
    from yandex.cloud.iam.v1 import iam_token_service_pb2
    import jwt
except ImportError:
    jwt = None
    iam_token_service_pb2_grpc = None
    iam_token_service_pb2 = None

try:
    import requests
except ImportError:
    requests = None


def get_jwt(service_account_id, access_key_id, private_key, jwt_expiration_timeout):
    now = time.time()
    now_utc = datetime.utcfromtimestamp(now)
    exp_utc = datetime.utcfromtimestamp(now + jwt_expiration_timeout)
    return jwt.encode(
        key=private_key, algorithm="PS256", headers={"typ": "JWT", "alg": "PS256", "kid": access_key_id},
        payload={
            "iss": service_account_id,
            "aud": "https://iam.api.cloud.yandex.net/iam/v1/tokens", "iat": now_utc, "exp": exp_utc
        }
    )


class ServiceAccountCredentials(credentials.Credentials):
    def __init__(self, service_account_id, access_key_id, private_key, iam_endpoint=None, iam_channel_credentials=None):
        super(ServiceAccountCredentials, self).__init__()
        if iam_token_service_pb2_grpc is None or jwt is None or iam_token_service_pb2 is None:
            raise RuntimeError(
                "Install jwt & yandex python cloud library to use service account credentials provider")
        iam_endpoint = 'iam.api.cloud.yandex.net:443' if iam_endpoint is None else iam_endpoint
        iam_channel_credentials = {} if iam_channel_credentials is None else iam_channel_credentials
        self._channel = grpc.secure_channel(iam_endpoint, grpc.ssl_channel_credentials(**iam_channel_credentials))
        self._channel_stub = iam_token_service_pb2_grpc.IamTokenServiceStub(self._channel)
        self._service_account_id = service_account_id
        self._jwt_expiration_timeout = 60. * 60
        self._get_token_request_timeout = 10
        self._token_expiration_timeout = 120
        self._access_key_id = access_key_id
        self._private_key = private_key
        self._token_timestamp = None
        self._token = None

    def set_token_expiration_timeout(self, value):
        self._token_expiration_timeout = value
        return self

    @property
    def expired(self):
        return self._token is None or (
            datetime.now() - self._token_timestamp).total_seconds() > self._token_expiration_timeout

    def _get_token_request(self):
        return iam_token_service_pb2.CreateIamTokenRequest(
            jwt=get_jwt(
                self._service_account_id, self._access_key_id, self._private_key, self._jwt_expiration_timeout
            )
        )

    def _save_token(self, future):
        self._token = future.result().iam_token
        self._token_timestamp = datetime.now()

    def _send_request(self):
        future = self._channel_stub.Create.future(self._get_token_request(), self._get_token_request_timeout)
        future.add_done_callback(self._save_token)
        return future

    def _update_token(self):
        self._send_request().result()

    @classmethod
    def from_file(cls, key_file, iam_endpoint=None, iam_channel_credentials=None):
        with open(key_file, 'r') as r:
            output = json.loads(r.read())
        return cls(
            output['service_account_id'],
            output['id'],
            output['private_key'],
            iam_endpoint=iam_endpoint,
            iam_channel_credentials=iam_channel_credentials
        )

    def auth_metadata(self):
        if self.expired:
            self._update_token()
        return [
            (credentials.YDB_AUTH_TICKET_HEADER, self._token)]


class MetadataUrlCredentials(credentials.AbstractCredentials):
    def __init__(self, metadata_url=None):
        if metadata_url is None:
            metadata_url = 'http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token'
        self._metadata_url = metadata_url
        self._hour = 60 * 60
        self._expires_in = 0
        self._iam_token = None
        if requests is None:
            raise RuntimeError(
                "Install requests library to use metadata credentials provider")

    def _auth_metadata(self):
        response = requests.get(self._metadata_url, headers={'Metadata-Flavor': 'Google'}, timeout=3)
        response.raise_for_status()
        return json.loads(response.text)

    @property
    def iam_token(self):
        if time.time() > self._expires_in:
            auth_metadata = self._auth_metadata()
            self._iam_token = auth_metadata['access_token']
            self._expires_in = time.time() + min(self._hour, auth_metadata['expires_in'] / 2)
        return self._iam_token

    def auth_metadata(self):
        return [
            (credentials.YDB_AUTH_TICKET_HEADER, self.iam_token)
        ]
