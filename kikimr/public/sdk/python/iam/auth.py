# -*- coding: utf-8 -*-
from kikimr.public.sdk.python.client import credentials
import grpc
import time
import abc
import six
from datetime import datetime
import json
import threading
from concurrent import futures
import logging
from kikimr.public.sdk.python.client import issues

logger = logging.getLogger(__name__)

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


DEFAULT_METADATA_URL = 'http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token'


def get_jwt(account_id, access_key_id, private_key, jwt_expiration_timeout):
    now = time.time()
    now_utc = datetime.utcfromtimestamp(now)
    exp_utc = datetime.utcfromtimestamp(now + jwt_expiration_timeout)
    return jwt.encode(
        key=private_key, algorithm="PS256", headers={"typ": "JWT", "alg": "PS256", "kid": access_key_id},
        payload={
            "iss": account_id,
            "aud": "https://iam.api.cloud.yandex.net/iam/v1/tokens", "iat": now_utc, "exp": exp_utc
        }
    )


class OneToManyValue(object):
    def __init__(self):
        self._value = None
        self._condition = threading.Condition()

    def consume(self, timeout=3):
        with self._condition:
            if self._value is None:
                self._condition.wait(timeout=timeout)
            return self._value

    def update(self, n_value):
        with self._condition:
            prev_value = self._value
            self._value = n_value
            if prev_value is None:
                self._condition.notify_all()


class AtMostOneExecution(object):
    def __init__(self):
        self._can_schedule = True
        self._lock = threading.Lock()
        self._tp = futures.ThreadPoolExecutor(1)

    def wrapped_execution(self, callback):
        try:
            callback()
        except Exception:
            pass

        finally:
            self.cleanup()

    def submit(self, callback):
        with self._lock:
            if self._can_schedule:
                self._tp.submit(self.wrapped_execution, callback)
                self._can_schedule = False

    def cleanup(self):
        with self._lock:
            self._can_schedule = True


@six.add_metaclass(abc.ABCMeta)
class IamTokenCredentials(credentials.Credentials):
    def __init__(self):
        super(IamTokenCredentials, self).__init__()
        self._expires_in = 0
        self._refresh_in = 0
        self._hour = 60 * 60
        self._iam_token = OneToManyValue()
        self._tp = AtMostOneExecution()
        self.logger = logger.getChild(self.__class__.__name__)
        self.last_error = None
        self.extra_error_message = ""

    @abc.abstractmethod
    def _get_iam_token(self):
        pass

    def _refresh(self):
        current_time = time.time()
        self.logger.debug("Start refresh token from metadata")
        if current_time > self._refresh_in:
            self.logger.info("Cached token reached refresh_in deadline, current time %s, deadline %s", current_time, self._refresh_in)

        if current_time > self._expires_in and self._expires_in > 0:
            self.logger.error("Cached token reached expires_in deadline, current time %s, deadline %s", current_time, self._expires_in)

        try:
            auth_metadata = self._get_iam_token()
            self._iam_token.update(auth_metadata['access_token'])
            self._expires_in = time.time() + min(self._hour, auth_metadata['expires_in'] / 2)
            self._refresh_in = time.time() + min(self._hour / 2, auth_metadata['expires_in'] / 4)
            self.logger.info("Token refresh successful. current_time %s, refresh_in %s", current_time, self._refresh_in)

        except (KeyboardInterrupt, SystemExit):
            return

        except Exception as e:
            self.last_error = str(e)
            time.sleep(1)
            self._tp.submit(self._refresh)

    @property
    def iam_token(self):
        current_time = time.time()
        if current_time > self._refresh_in:
            self._tp.submit(self._refresh)

        iam_token = self._iam_token.consume(timeout=3)
        if iam_token is None:
            if self.last_error is None:
                raise issues.ConnectionError("%s: timeout occurred while waiting for token.\n%s" % self.__class__.__name__, self.extra_error_message)
            raise issues.ConnectionError("%s: %s.\n%s" % (self.__class__.__name__, self.last_error, self.extra_error_message))
        return iam_token

    def auth_metadata(self):
        return [
            (credentials.YDB_AUTH_TICKET_HEADER, self.iam_token)
        ]


@six.add_metaclass(abc.ABCMeta)
class TokenServiceCredentials(IamTokenCredentials):
    def __init__(self, iam_endpoint=None, iam_channel_credentials=None):
        super(TokenServiceCredentials, self).__init__()
        self._iam_endpoint = 'iam.api.cloud.yandex.net:443' if iam_endpoint is None else iam_endpoint
        self._iam_channel_credentials = {} if iam_channel_credentials is None else iam_channel_credentials
        self._get_token_request_timeout = 10
        if iam_token_service_pb2_grpc is None or jwt is None or iam_token_service_pb2 is None:
            raise RuntimeError(
                "Install jwt & yandex python cloud library to use service account credentials provider")

    def _channel_factory(self):
        return grpc.secure_channel(self._iam_endpoint, grpc.ssl_channel_credentials(**self._iam_channel_credentials))

    @abc.abstractmethod
    def _get_token_request(self):
        pass

    def _get_iam_token(self):
        with self._channel_factory() as channel:
            stub = iam_token_service_pb2_grpc.IamTokenServiceStub(channel)
            response = stub.Create(self._get_token_request(), timeout=self._get_token_request_timeout)
            expires_in = max(0, response.expires_at.seconds - int(time.time()))
            return {'access_token': response.iam_token, 'expires_in': expires_in}


class JWTIamCredentials(TokenServiceCredentials):
    def __init__(self, account_id, access_key_id, private_key, iam_endpoint=None, iam_channel_credentials=None):
        super(JWTIamCredentials, self).__init__(iam_endpoint, iam_channel_credentials)
        self._account_id = account_id
        self._jwt_expiration_timeout = 60. * 60
        self._token_expiration_timeout = 120
        self._access_key_id = access_key_id
        self._private_key = private_key

    def set_token_expiration_timeout(self, value):
        self._token_expiration_timeout = value
        return self

    def _get_token_request(self):
        return iam_token_service_pb2.CreateIamTokenRequest(
            jwt=get_jwt(
                self._account_id, self._access_key_id, self._private_key, self._jwt_expiration_timeout
            )
        )

    @classmethod
    def from_file(cls, key_file, iam_endpoint=None, iam_channel_credentials=None):
        with open(key_file, 'r') as r:
            output = json.loads(r.read())
        account_id = output.get('service_account_id', None)
        if account_id is None:
            account_id = output.get('user_account_id', None)
        return cls(
            account_id,
            output['id'],
            output['private_key'],
            iam_endpoint=iam_endpoint,
            iam_channel_credentials=iam_channel_credentials
        )


class YandexPassportOAuthIamCredentials(TokenServiceCredentials):
    def __init__(self, yandex_passport_oauth_token, iam_endpoint=None, iam_channel_credentials=None):
        self._yandex_passport_oauth_token = yandex_passport_oauth_token
        super(YandexPassportOAuthIamCredentials, self).__init__(iam_endpoint, iam_channel_credentials)

    def _get_token_request(self):
        return iam_token_service_pb2.CreateIamTokenRequest(yandex_passport_oauth_token=self._yandex_passport_oauth_token)


class MetadataUrlCredentials(IamTokenCredentials):
    def __init__(self, metadata_url=None):
        super(MetadataUrlCredentials, self).__init__()
        if requests is None:
            raise RuntimeError(
                "Install requests library to use metadata credentials provider")
        self._metadata_url = DEFAULT_METADATA_URL if metadata_url is None else metadata_url
        self._tp.submit(self._refresh)
        self.extra_error_message = "Check that metadata service configured properly and application deployed in VM or function at Yandex.Cloud."

    def _get_iam_token(self):
        response = requests.get(self._metadata_url, headers={'Metadata-Flavor': 'Google'}, timeout=3)
        response.raise_for_status()
        return json.loads(response.text)


class ServiceAccountCredentials(JWTIamCredentials):
    def __init__(self, service_account_id, access_key_id, private_key, iam_endpoint=None, iam_channel_credentials=None):
        super(ServiceAccountCredentials, self).__init__(service_account_id, access_key_id, private_key, iam_endpoint, iam_channel_credentials)
