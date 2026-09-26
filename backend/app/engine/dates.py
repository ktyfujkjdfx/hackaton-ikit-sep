import datetime as dt

from app.models import Situation

H = 30


def day_index(sit: Situation, d: dt.date | str) -> int:
    raise NotImplementedError


def date_at(sit: Situation, d: int) -> dt.date:
    raise NotImplementedError
