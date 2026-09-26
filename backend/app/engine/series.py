from app.engine.dates import H
from app.models import DaySeries, Purchase, SeriesStats, Situation


def series(sit: Situation, purchase: Purchase | None = None, reduce: int = 0,
           reduce_until: int = H - 1, pessimistic: bool = False) -> list[int]:
    raise NotImplementedError


def stats(sit: Situation, values: list[int]) -> SeriesStats:
    raise NotImplementedError


def to_day_series(sit: Situation, values: list[int]) -> DaySeries:
    raise NotImplementedError
