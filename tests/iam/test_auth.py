from ydb.iam.auth import BaseJWTCredentials
from unittest.mock import patch, mock_open

CONTENT1 = '{"service_account_id":"my_sa", "id":"123", "private_key":"pppp", "user_account_id":"ua_id"}'
CONTENT2 = '{"id":"123", "private_key":"pppp", "user_account_id":"ua_id"}'


class FakeAuth(BaseJWTCredentials):
    def __init__(self, account_id, key_id, private_key, iam_endpoint=None, iam_channel_credentials=None):
        self.account_id = account_id
        self.key_id = key_id
        self.private_key = private_key
        self.iam_endpoint = iam_endpoint
        self.iam_channel_credentials = iam_channel_credentials

    def __eq__(self, other):
        return self.__dict__ == other.__dict__ if type(self) == type(other) else False


@patch("builtins.open", new_callable=mock_open, read_data=CONTENT1)
def test_auth_from_file(mock_file):
    r1 = FakeAuth.from_file("my_file.json", iam_endpoint="my_iam_address", iam_channel_credentials="my_creds")
    mock_file.assert_called_with("my_file.json", "r")

    r2 = FakeAuth.from_content(CONTENT1, iam_endpoint="my_iam_address", iam_channel_credentials="my_creds")
    assert r1 == r2
    assert r1.__dict__ == {
        "account_id": "my_sa",
        "key_id": "123",
        "private_key": "pppp",
        "iam_endpoint": "my_iam_address",
        "iam_channel_credentials": "my_creds",
    }

    r3 = FakeAuth.from_content(CONTENT2)

    assert r3.__dict__ == {
        "account_id": "ua_id",
        "key_id": "123",
        "private_key": "pppp",
        "iam_endpoint": None,
        "iam_channel_credentials": None,
    }
