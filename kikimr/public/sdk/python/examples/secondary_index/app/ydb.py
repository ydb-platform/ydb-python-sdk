# -*- coding: UTF-8 -*-
import os
from threading import Lock

import kikimr.public.sdk.python.client as ydb
from concurrent.futures import TimeoutError


class YDBPreparedQueriesCache(object):

    def __init__(self, session, table_prefix):
        super(YDBPreparedQueriesCache, self).__init__()
        self._session = session
        self._table_prefix = table_prefix
        self._prepared_queries = dict()

    def __getitem__(self, query):
        if query in self._prepared_queries:
            return self._prepared_queries[query]
        prepared_query = self._session.prepare(query.format(table_prefix=self._table_prefix))
        self._prepared_queries[query] = prepared_query
        return prepared_query


class YDBCachedSession(object):

    def __init__(self, parent, ydb_session, table_prefix):
        super(YDBCachedSession, self).__init__()
        self._parent = parent
        self._session = ydb_session
        self._table_prefix = table_prefix
        self._prepared_queries = YDBPreparedQueriesCache(ydb_session, table_prefix)

    @property
    def table_prefix(self):
        return self._table_prefix

    @property
    def session(self):
        return self._session

    @property
    def queries(self):
        return self._prepared_queries

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._parent.free_session(self)


class YDBSessionCache(object):

    def __init__(self, app, endpoint, database, path, token):
        super(YDBSessionCache, self).__init__()
        self.app = app
        self._driver = None
        self._endpoint = endpoint
        self._database = database
        self._path = path
        self._token = token
        self._table_prefix = os.path.join(self._database, self._path.rstrip("/"))
        self._sessions = list()
        self._session_guard = Lock()
        self._driver_guard = Lock()

    @property
    def database(self):
        return self._database

    @property
    def path(self):
        return self._path

    @property
    def table_prefix(self):
        return self._table_prefix

    def _get_driver(self):
        driver = ydb.Driver(
            ydb.DriverConfig(
                self._endpoint,
                database=self._database,
                auth_token=self._token,
            )
        )
        try:
            driver.wait(timeout=5)
        except TimeoutError:
            raise RuntimeError("YDB connect error")
        return driver

    @property
    def driver(self):
        with self._driver_guard:
            if self._driver is None:
                self._driver = self._get_driver()
            return self._driver

    @property
    def session(self):
        """
        :rtype: YDBCachedSession
        """
        with self._session_guard:
            if len(self._sessions) == 0:
                return YDBCachedSession(
                    parent=self,
                    ydb_session=self.driver.table_client.session().create(),
                    table_prefix=self._table_prefix,
                )
            return self._sessions.pop()

    def free_session(self, session):
        with self._session_guard:
            self._sessions.append(session)
