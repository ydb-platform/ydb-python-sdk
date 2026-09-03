import datetime
from pydantic import BaseModel


class Reservation(BaseModel):
    phone: str | str | None = None
    description: bytes | str | None = None
    table_id: int
    dt: datetime.datetime


class Table(BaseModel):
    table_id: int = None
    description: bytes | str | None = None
    cnt: int


class ReservationCreateRequest(BaseModel):
    dt: datetime.datetime
    cnt: int
    description: bytes | str | None = None
    phone: bytes | str | None


class ReservationCreateResponse(BaseModel):
    success: bool
    table_id: int | None = None


class ReservationCancelRequest(BaseModel):
    phone: bytes | str | None
    dt: datetime.datetime


class ReservationCancelResponse(BaseModel):
    success: bool
