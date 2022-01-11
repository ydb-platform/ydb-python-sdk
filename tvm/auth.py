# -*- coding: utf-8 -*-
import six
try:
    import tvmauth
except ImportError:
    tvmauth = None

from ydb import credentials


class TvmCredentialsProvider(credentials.Credentials):
    def __init__(self, self_client_id, self_secret, dsts, destination_alias):
        self._settings = tvmauth.TvmApiClientSettings(
            self_tvm_id=self_client_id, self_secret=self_secret, dsts=dsts
        )
        self._client = tvmauth.TvmClient(self._settings)
        self._destination_alias = destination_alias

    def _get_service_ticket(self):
        return six.text_type(self._client.get_service_ticket_for(self._destination_alias))

    def expired(self):
        return True

    def auth_metadata(self):
        return [
            (
                credentials.YDB_AUTH_TICKET_HEADER, self._get_service_ticket()
            )
        ]
