# -*- coding: UTF-8 -*-

import datetime

_EPOCH = datetime.datetime.utcfromtimestamp(0).date()


def to_days(date):
    return (date - _EPOCH).days


def from_days(days):
    return _EPOCH + datetime.timedelta(days=days)


class Series(object):

    def __init__(self, series_id=None, title=None, series_info=None, release_date=None, views=None):
        super(Series, self).__init__()
        self.series_id = series_id
        self.title = title
        self.series_info = series_info
        self.release_date = release_date
        self.views = views

    def export(self):
        return dict(
            seriesId=self.series_id,
            title=self.title,
            seriesInfo=self.series_info,
            views=self.views,
            releaseDate=self.release_date.strftime("%Y-%m-%d") if self.release_date is not None else None
        )

    @staticmethod
    def from_dict(data):
        obj = Series()
        obj.series_id = data["seriesId"]
        obj.title = data["title"]
        obj.series_info = data["seriesInfo"]
        obj.views = data["views"]
        obj.release_date = datetime.datetime.strptime(data["releaseDate"], "%Y-%m-%d").date()
        return obj
