import iso8601

import sqlalchemy as sa
from models import Base, Series, Seasons, Episodes


def to_days(date):
    timedelta = iso8601.parse_date(date) - iso8601.parse_date("1970-1-1")
    return timedelta.days


def fill_series(conn):
    data = [
        (
            1,
            "IT Crowd",
            "The IT Crowd is a British sitcom produced by Channel 4, written by Graham Linehan, produced by "
            "Ash Atalla and starring Chris O'Dowd, Richard Ayoade, Katherine Parkinson, and Matt Berry.",
            to_days("2006-02-03"),
        ),
        (
            2,
            "Silicon Valley",
            "Silicon Valley is an American comedy television series created by Mike Judge, John Altschuler and "
            "Dave Krinsky. The series focuses on five young men who founded a startup company in Silicon Valley.",
            to_days("2014-04-06"),
        ),
    ]
    conn.execute(sa.insert(Series).values(data))


def fill_seasons(conn):
    data = [
        (1, 1, "Season 1", to_days("2006-02-03"), to_days("2006-03-03")),
        (1, 2, "Season 2", to_days("2007-08-24"), to_days("2007-09-28")),
        (1, 3, "Season 3", to_days("2008-11-21"), to_days("2008-12-26")),
        (1, 4, "Season 4", to_days("2010-06-25"), to_days("2010-07-30")),
        (2, 1, "Season 1", to_days("2014-04-06"), to_days("2014-06-01")),
        (2, 2, "Season 2", to_days("2015-04-12"), to_days("2015-06-14")),
        (2, 3, "Season 3", to_days("2016-04-24"), to_days("2016-06-26")),
        (2, 4, "Season 4", to_days("2017-04-23"), to_days("2017-06-25")),
        (2, 5, "Season 5", to_days("2018-03-25"), to_days("2018-05-13")),
    ]
    conn.execute(sa.insert(Seasons).values(data))


def fill_episodes(conn):
    data = [
        (1, 1, 1, "Yesterday's Jam", to_days("2006-02-03")),
        (1, 1, 2, "Calamity Jen", to_days("2006-02-03")),
        (1, 1, 3, "Fifty-Fifty", to_days("2006-02-10")),
        (1, 1, 4, "The Red Door", to_days("2006-02-17")),
        (1, 1, 5, "The Haunting of Bill Crouse", to_days("2006-02-24")),
        (1, 1, 6, "Aunt Irma Visits", to_days("2006-03-03")),
        (1, 2, 1, "The Work Outing", to_days("2006-08-24")),
        (1, 2, 2, "Return of the Golden Child", to_days("2007-08-31")),
        (1, 2, 3, "Moss and the German", to_days("2007-09-07")),
        (1, 2, 4, "The Dinner Party", to_days("2007-09-14")),
        (1, 2, 5, "Smoke and Mirrors", to_days("2007-09-21")),
        (1, 2, 6, "Men Without Women", to_days("2007-09-28")),
        (1, 3, 1, "From Hell", to_days("2008-11-21")),
        (1, 3, 2, "Are We Not Men?", to_days("2008-11-28")),
        (1, 3, 3, "Tramps Like Us", to_days("2008-12-05")),
        (1, 3, 4, "The Speech", to_days("2008-12-12")),
        (1, 3, 5, "Friendface", to_days("2008-12-19")),
        (1, 3, 6, "Calendar Geeks", to_days("2008-12-26")),
        (1, 4, 1, "Jen The Fredo", to_days("2010-06-25")),
        (1, 4, 2, "The Final Countdown", to_days("2010-07-02")),
        (1, 4, 3, "Something Happened", to_days("2010-07-09")),
        (1, 4, 4, "Italian For Beginners", to_days("2010-07-16")),
        (1, 4, 5, "Bad Boys", to_days("2010-07-23")),
        (1, 4, 6, "Reynholm vs Reynholm", to_days("2010-07-30")),
    ]
    conn.execute(sa.insert(Episodes).values(data))


def fill_all_tables(conn):
    Base.metadata.drop_all(conn.engine)
    Base.metadata.create_all(conn.engine)

    fill_series(conn)
    fill_seasons(conn)
    fill_episodes(conn)
