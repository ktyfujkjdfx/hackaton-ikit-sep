import datetime as dt

from app.engine.dates import H, date_at
from app.engine.goal import goal_plan
from app.engine.plans import deficit_plan
from app.engine.series import series, stats
from app.models import Purchase, PurchaseCheck, Situation


def _safe_day(base: list[int], amount: int) -> int | None:
    """Первый день D, при котором покупка в день D не уводит ряд в минус."""
    for D in range(H):
        if all(v >= 0 for v in base[:D]) and all(v - amount >= 0 for v in base[D:]):
            return D
    return None


def earliest_safe_date(sit: Situation, amount: int) -> dt.date | None:
    D = _safe_day(series(sit), amount)
    return date_at(sit, D) if D is not None else None


def _verdict(sit: Situation, after_min: int) -> str:
    if after_min < 0:
        return "deficit"
    if after_min < 3 * sit.daily:
        return "tight"
    return "ok"


def check_purchase(sit: Situation, purchase: Purchase) -> PurchaseCheck:
    before = series(sit)
    after = series(sit, purchase=purchase)
    st_after = stats(sit, after)
    safe_day = _safe_day(before, purchase.amount)
    safe = date_at(sit, safe_day) if safe_day is not None else None
    depends = False
    if safe is not None:
        at_safe = Purchase(amount=purchase.amount, date=safe, name=purchase.name)
        depends = min(series(sit, purchase=at_safe, pessimistic=True)) < 0
    return PurchaseCheck(
        purchase=purchase,
        verdict=_verdict(sit, st_after.min),
        before=stats(sit, before),
        after=st_after,
        earliest_safe_date=safe,
        safe_depends_on_unconfirmed=depends,
        goal=goal_plan(sit, purchase.amount),
        plan=deficit_plan(sit, after, "purchase", safe),
    )
