import sqlalchemy.orm as orm
from sqlalchemy import Column, Integer, Unicode


Base = orm.declarative_base()


class Series(Base):
    __tablename__ = "series"

    series_id = Column(Integer, primary_key=True)
    title = Column(Unicode)
    series_info = Column(Unicode)
    release_date = Column(Integer)


class Seasons(Base):
    __tablename__ = "seasons"

    series_id = Column(Integer, primary_key=True)
    season_id = Column(Integer, primary_key=True)
    title = Column(Unicode)
    first_aired = Column(Integer)
    last_aired = Column(Integer)


class Episodes(Base):
    __tablename__ = "episodes"

    series_id = Column(Integer, primary_key=True)
    season_id = Column(Integer, primary_key=True)
    episode_id = Column(Integer, primary_key=True)
    title = Column(Unicode)
    air_date = Column(Integer)
