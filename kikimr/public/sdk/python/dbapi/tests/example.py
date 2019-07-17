from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
import os
import logging
logging.basicConfig(level=logging.DEBUG)

import kikimr.public.dbapi

con = kikimr.public.dbapi.connect(
    endpoint=os.getenv('YDB_ENDPOINT'),
    database=os.getenv('YDB_DATABASE')
)
cur = con.cursor()
cur.execute('select "foo" as foo;')
print(cur.fetchone()[0])
