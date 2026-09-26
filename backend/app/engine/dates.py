import datetime as dt

from app.models import Situation

H = 30


def as_date(d: dt.date | str) -> dt.date:
    return d if isinstance(d, dt.date) else dt.date.fromisoformat(d)


def day_index(sit: Situation, d: dt.date | str) -> int:
    """Номер дня горизонта: 0 — сегодня, отрицательный — прошлое."""
    return (as_date(d) - sit.today).days


def date_at(sit: Situation, d: int) -> dt.date:
    return sit.today + dt.timedelta(days=d)


def in_horizon(sit: Situation, d: dt.date | str) -> bool:
    return 0 <= day_index(sit, d) < H
