from __future__ import absolute_import
from __future__ import unicode_literals

import logging

from kikimr.public.dbapi.errors import DatabaseError


class Cursor(object):
    last_result_sets = []
    current_index = 0

    def __init__(self, connection):
        self.connection = connection
        self.description = []
        self.arraysize = 1
        self.logger = logging.getLogger(__name__)

    def execute(self, sql, parameters=None):
        if parameters:
            if isinstance(parameters, tuple) or isinstance(parameters, list):
                for parameter in parameters:
                    if parameter is None:
                        sql = sql.replace('?', 'NULL', 1)
                    else:
                        if isinstance(parameter, bytes):
                            parameter = parameter.decode('utf-8')
                        sql = sql.replace('?', repr(parameter), 1)
            else:
                raise DatabaseError(
                    'Unsupported parameters type: ' + str(type(parameters)))

        self.current_index = 0
        if 'create table' in sql.lower():
            self.connection.session.execute_scheme(sql)
            self.last_result_sets = []
        else:
            self.last_result_sets = self.connection.tx.execute(sql, commit_tx=self.connection.autocommit)

        if self.last_result_sets:
            self.description = [
                (name.name, None, None, None, None, None, None,) for name in self.last_result_sets[0].columns]

    def executemany(self, sql, seq_of_parameters):
        for parameters in seq_of_parameters:
            self.execute(sql, parameters)

    def executescript(self, script):
        return self.execute(script)

    def fetchone(self):
        if self.last_result_sets:
            last_result = self.last_result_sets[0].rows
            if len(last_result) > self.current_index:
                row = last_result[self.current_index]
                self.current_index += 1
                return row

        else:
            raise DatabaseError('No result set available')

    def fetchmany(self, size=None):
        if size is None:
            size = self.arraysize

        result = []
        while size > 0:
            row = self.fetchone()
            if row is not None:
                result.append(row)
            size -= 1
        return result

    def fetchall(self):
        result = []
        while True:
            row = self.fetchone()
            if row is not None:
                result.append(row)
            else:
                break
        return result

    def nextset(self):
        if self.last_result_sets:
            self.last_result_sets = self.last_result_sets[1:]

    def setinputsizes(self, sizes):
        pass

    def setoutputsize(self, column=None):
        pass

    def close(self):
        self.last_result_sets = []

    @property
    def rowcount(self):
        if self.last_result_sets:
            return len(self.last_result_sets[0])
        else:
            return -1
