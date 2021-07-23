from . import pool, scheme, table
from kikimr.public.sdk.python.client.driver import get_config


class Driver(pool.ConnectionPool):
    def __init__(self, driver_config=None, connection_string=None, endpoint=None, database=None, root_certificates=None, credentials=None, **kwargs):
        config = get_config(driver_config, connection_string, endpoint, database, root_certificates, credentials)

        super(Driver, self).__init__(config)

        self.scheme_client = scheme.SchemeClient(self)
        self.table_client = table.TableClient(self, config.table_client_settings)
