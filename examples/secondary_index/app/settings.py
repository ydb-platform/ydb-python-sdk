# -*- coding: UTF-8 -*-
#

from os import environ


DEBUG = True

YDB_ENDPOINT = environ.get("YDB_ENDPOINT")
YDB_DATABASE = environ.get("YDB_DATABASE", "")
YDB_PATH = environ.get("YDB_PATH", "")
YDB_TOKEN = environ.get("YDB_TOKEN")
