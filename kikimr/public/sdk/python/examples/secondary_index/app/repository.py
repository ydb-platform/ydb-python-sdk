# -*- coding: UTF-8 -*-

import os

import kikimr.public.sdk.python.client as ydb

import model
import queries


class SeriesRepository(object):
    _table_description = (
        ydb.TableDescription()
        .with_column(ydb.Column("series_id", ydb.OptionalType(ydb.PrimitiveType.Uint64)))
        .with_column(ydb.Column("title", ydb.OptionalType(ydb.PrimitiveType.Utf8)))
        .with_column(ydb.Column("series_info", ydb.OptionalType(ydb.PrimitiveType.Utf8)))
        .with_column(ydb.Column("release_date", ydb.OptionalType(ydb.PrimitiveType.Uint32)))
        .with_column(ydb.Column("views", ydb.OptionalType(ydb.PrimitiveType.Uint64)))
        .with_primary_keys("series_id")
    )
    _table_rev_index_description = (
        ydb.TableDescription()
        .with_column(ydb.Column("rev_views", ydb.OptionalType(ydb.PrimitiveType.Uint64)))
        .with_column(ydb.Column("series_id", ydb.OptionalType(ydb.PrimitiveType.Uint64)))
        .with_primary_keys("rev_views", "series_id")
    )
    _table_name = "series"
    _table_rev_views_name = "series_rev_views"

    def __init__(self, ydb_session):
        """
        :type ydb_session: ydb.YDBCachedSession
        """
        super(SeriesRepository, self).__init__()
        self._session = ydb_session

    def create_tables(self):
        self._session.session.create_table(
            os.path.join(self._session.table_prefix, self._table_name),
            self._table_description
        )
        self._session.session.create_table(
            os.path.join(self._session.table_prefix, self._table_rev_views_name),
            self._table_rev_index_description
        )

    def drop_tables(self):
        self._session.session.drop_table(os.path.join(self._session.table_prefix, self._table_name))
        self._session.session.drop_table(os.path.join(self._session.table_prefix, self._table_rev_views_name))

    def insert(self, series):
        """
        :type series: Series
        """
        self._session.session.transaction(ydb.SerializableReadWrite()).execute(
            self._session.queries[queries.INSERT_QUERY], {
                "$seriesId": series.series_id,
                "$title": series.title,
                "$seriesInfo": series.series_info,
                "$releaseDate": model.to_days(series.release_date),
                "$views": series.views,
            },
            commit_tx=True
        )

    def delete(self, series_id):
        """
        :type series_id: int
        """
        result_sets = self._session.session.transaction(ydb.SerializableReadWrite()).execute(
            self._session.queries[queries.DELETE_QUERY], {
                "$seriesId": series_id,
            },
            commit_tx=True
        )
        if len(result_sets[0].rows) < 1:
            raise RuntimeError("Query count was not returned")
        return result_sets[0].rows[0].cnt

    def update_views(self, series_id, new_views):
        """
        :type series_id: int
        :type new_views: int
        """
        tx = self._session.session.transaction(ydb.SerializableReadWrite()).begin()
        result_sets = tx.execute(
            self._session.queries[queries.UPDATE_VIEWS_QUERY], {
                "$seriesId": series_id,
                "$newViews": new_views,
            },
            commit_tx=True
        )
        if len(result_sets[0].rows) < 1:
            raise RuntimeError("Query count was not returned")
        return result_sets[0].rows[0].cnt

    def find_by_id(self, series_id):
        """
        :type series_id: int
        :rtype: Series or None
        """
        tx = self._session.session.transaction(ydb.SerializableReadWrite()).begin()
        result_sets = tx.execute(
            self._session.queries[queries.FIND_BY_ID_QUERY], {
                "$seriesId": series_id,
            },
            commit_tx=True
        )
        if len(result_sets[0].rows) < 1:
            return None
        return self._extract_series(result_sets[0].rows[0])

    def find_all(self, limit, last_series_id=None):
        """
        :type limit: int
        :type last_series_id: int or None
        :rtype: list(Series)
        """
        tx = self._session.session.transaction(ydb.SerializableReadWrite()).begin()
        if last_series_id is None:
            result_sets = tx.execute(
                self._session.queries[queries.FIND_ALL_QUERY], {
                    "$limit": limit,
                },
                commit_tx=True
            )
        else:
            result_sets = tx.execute(
                self._session.queries[queries.FIND_ALL_NEXT_QUERY], {
                    "$limit": limit,
                    "$lastSeriesId": last_series_id

                },
                commit_tx=True
            )
        return [self._extract_series(row) for row in result_sets[0].rows]

    def find_most_viewed(self, limit, last_series_id=None, last_views=None):
        """
        :type limit: int
        :type last_series_id: int or None
        :type last_views: int or None
        :rtype: list(Series)
        """
        tx = self._session.session.transaction(ydb.SerializableReadWrite()).begin()
        if last_series_id is None or last_views is None:
            result_sets = tx.execute(
                self._session.queries[queries.FIND_MOST_VIEWED_QUERY], {
                    "$limit": limit,
                },
                commit_tx=True
            )
        else:
            result_sets = tx.execute(
                self._session.queries[queries.FIND_MOST_VIEWED_NEXT_QUERY], {
                    "$limit": limit,
                    "$lastSeriesId": last_series_id,
                    "$lastViews": last_views,

                },
                commit_tx=True
            )
        return [self._extract_series(row) for row in result_sets[0].rows]

    @staticmethod
    def _extract_series(row):
        """
        :rtype:  Series
        """
        series = model.Series()
        series.series_id = row.series_id
        series.title = row.title
        series.series_info = row.series_info
        series.release_date = model.from_days(row.release_date)
        series.views = row.views
        return series
