from app.engine.dates import H, date_at, day_index
from app.models import DayPoint, DaySeries, Purchase, SeriesStats, Situation


def series(sit: Situation, purchase: Purchase | None = None, reduce: int = 0,
           reduce_until: int = H - 1, pessimistic: bool = False) -> list[int]:
    """Остаток на конец каждого дня горизонта (раздел 7)."""
    moves = [0] * H
    for o in sit.obligations:
        d = day_index(sit, o.date)
        if 0 <= d < H:
            moves[d] -= o.amount
    for s in sit.spends:
        d = day_index(sit, s.date)
        if 0 <= d < H:
            moves[d] -= s.amount
    for i in sit.incomes:
        d = day_index(sit, i.date)
        if 0 <= d < H and (i.confirmed or not pessimistic):
            moves[d] += i.amount
    if purchase is not None:
        d = day_index(sit, purchase.date)
        if 0 <= d < H:
            moves[d] -= purchase.amount

    b = sit.balance
    out = []
    for d in range(H):
        b -= sit.daily - (reduce if d <= reduce_until else 0)
        b += moves[d]
        out.append(b)
    return out


def stats(sit: Situation, values: list[int]) -> SeriesStats:
    min_day = min(range(len(values)), key=lambda d: (values[d], d))
    negative = [d for d, v in enumerate(values) if v < 0]
    first_neg = negative[0] if negative else None
    last_neg = negative[-1] if negative else None
    low = values[min_day]
    return SeriesStats(
        min=low,
        min_date=date_at(sit, min_day),
        first_negative_date=date_at(sit, first_neg) if first_neg is not None else None,
        last_negative_date=date_at(sit, last_neg) if last_neg is not None else None,
        max_deficit=max(0, -low),
        first_negative_amount=-values[first_neg] if first_neg is not None else 0,
    )


def to_day_series(sit: Situation, values: list[int]) -> DaySeries:
    return DaySeries(
        days=[DayPoint(date=date_at(sit, d), balance=v) for d, v in enumerate(values)],
        stats=stats(sit, values),
    )
