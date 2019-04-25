# -*- coding: UTF-8 -*-

from flask import Flask

from ydb import YDBSessionCache

app = Flask(__name__)
app.config.from_object("app.settings")
app.ydb = YDBSessionCache(
    app=app,
    endpoint=app.config["YDB_ENDPOINT"],
    database=app.config["YDB_DATABASE"],
    path=app.config["YDB_PATH"],
    token=app.config["YDB_TOKEN"],
)

from .views import bp  # noqa
app.register_blueprint(bp, url_prefix="/series")
