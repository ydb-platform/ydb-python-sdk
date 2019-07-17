# -*- coding: UTF-8 -*-

import datetime
import random

import flask

from model import Series
from repository import SeriesRepository

bp = flask.Blueprint("series_example", __name__)


@bp.route("/create_tables", methods=["POST"])
def create_tables():
    with flask.current_app.ydb.session as session:
        SeriesRepository(session).create_tables()
    return "OK"


@bp.route("/drop_tables", methods=["POST"])
def drop_tables():
    with flask.current_app.ydb.session as session:
        SeriesRepository(session).drop_tables()
    return "OK"


@bp.route("/list", methods=["GET"])
def list_series():
    with flask.current_app.ydb.session as session:
        series = SeriesRepository(session).find_all(
            limit=flask.request.args.get("limit", default=10, type=int),
            last_series_id=flask.request.args.get("lastSeriesId", type=int),
        )
    return flask.jsonify(series=[item.export() for item in series])


@bp.route("/most_viewed", methods=["GET"])
def most_viewed():
    with flask.current_app.ydb.session as session:
        series = SeriesRepository(session).find_most_viewed(
            limit=flask.request.args.get("limit", default=10, type=int),
            last_series_id=flask.request.args.get("lastSeriesId", type=int),
            last_views=flask.request.args.get("lastViews", type=int),
        )
    return flask.jsonify(series=[item.export() for item in series])


@bp.route("/delete/<int:series_id>", methods=["POST"])
def delete(series_id):
    with flask.current_app.ydb.session as session:
        return str(SeriesRepository(session).delete(series_id))


@bp.route("/insert", methods=["POST"])
def insert():
    try:
        series = Series.from_dict(flask.request.get_json())
    except (ValueError, KeyError):
        return "ERROR Invalid Series object"
    with flask.current_app.ydb.session as session:
        SeriesRepository(session).insert(series)
    return "OK"


@bp.route("/update_views/<int:series_id>/<int:new_views>", methods=["POST"])
def update_views(series_id, new_views):
    with flask.current_app.ydb.session as session:
        return str(SeriesRepository(session).update_views(series_id, new_views))


@bp.route("/generate_random", methods=["POST"])
def generate_random():
    start_id = flask.request.args.get("startId", type=int)
    count = flask.request.args.get("count", type=int)
    with flask.current_app.ydb.session as session:
        series_repository = SeriesRepository(session)
        for series_id in xrange(start_id, start_id + count):
            series_repository.insert(Series(
                series_id=series_id,
                title="Name " + str(series_id),
                series_info="Info " + str(series_id),
                release_date=datetime.datetime.now().date(),
                views=random.randint(0, 1000000)
            ))
    return "OK"
