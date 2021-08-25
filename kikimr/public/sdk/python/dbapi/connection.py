from __future__ import absolute_import
from __future__ import unicode_literals

import os

from kikimr.public.sdk.python import iam, ydb

from kikimr.public.dbapi.cursor import Cursor
from kikimr.public.dbapi.errors import DatabaseError

_DRIVERS = {}


class Connection(object):
    isolation_level = ydb.SerializableReadWrite()
    driver = None

    def __init__(self, endpoint=None, host=None, port=None, db=None, database=None, autocommit=False):
        self.endpoint = endpoint or self._create_endpoint(host, port)
        self.database = database or db
        if not self.database.startswith('/'):
            self.database = '/' + self.database

        self.driver = self._create_driver(self.endpoint, self.database)
        self.session = ydb.retry_operation_sync(lambda: self.driver.table_client.session().create())
        self.tx = self.session.transaction(ydb.SerializableReadWrite())
        self.autocommit = autocommit

    def cursor(self):
        return Cursor(self)

    def execute(self, sql, parameters=None):
        return self.cursor().execute(sql, parameters)

    def executemany(self, sql, parameters):
        return self.cursor().executemany(sql, parameters)

    def commit(self):
        if self.tx.tx_id:
            self.tx.commit()
        self.tx = self.session.transaction(self.isolation_level)

    def rollback(self):
        if self.tx.tx_id:
            self.tx.rollback()
        self.tx = self.session.transaction(self.isolation_level)

    def close(self):
        pass

    @staticmethod
    def _create_endpoint(host, port):
        return '%s:%d' % (host, port)

    @staticmethod
    def _create_driver(endpoint, database):
        driver_id = (endpoint, database, )
        driver = _DRIVERS.get(driver_id)
        if not driver:
            driver_config = ydb.DriverConfig(
                endpoint, database=database, credentials=Connection._create_credentials())

            try:
                driver = ydb.Driver(driver_config)
                driver.wait(timeout=5)
            except Exception:
                raise DatabaseError('Failed to connect to YDB')

            _DRIVERS[driver_id] = driver

        return driver

    @staticmethod
    def _create_credentials():
        if os.getenv('YDB_TOKEN') is not None:
            return ydb.AuthTokenCredentials(os.getenv('YDB_TOKEN'))

        if os.getenv('SA_ID') is not None:
            with open(os.getenv('SA_PRIVATE_KEY_FILE')) as private_key_file:
                root_certificates_file = os.getenv('SSL_ROOT_CERTIFICATES_FILE', None)
                iam_channel_credentials = {}
                if root_certificates_file is not None:
                    with open(root_certificates_file, 'rb') as root_certificates_file:
                        root_certificates = root_certificates_file.read()
                    iam_channel_credentials = {'root_certificates': root_certificates}
                return iam.ServiceAccountCredentials(
                    iam_endpoint=os.getenv('IAM_ENDPOINT', 'iam.api.cloud.yandex.net:443'),
                    iam_channel_credentials=iam_channel_credentials,
                    access_key_id=os.getenv('SA_ACCESS_KEY_ID'),
                    service_account_id=os.getenv('SA_ID'),
                    private_key=private_key_file.read()
                )
