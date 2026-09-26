from app.engine.dates import H, day_index
from app.engine.series import series, stats
from app.models import Headline, Income, NextIncome, Situation


def next_income(sit: Situation, only_confirmed: bool = False) -> Income | None:
    """Ближайшее поступление с 1 ≤ d ≤ 29 (сегодняшнее уже не «следующее»)."""
    found = [i for i in sit.incomes
             if 1 <= day_index(sit, i.date) < H and (i.confirmed or not only_confirmed)]
    return min(found, key=lambda i: day_index(sit, i.date), default=None)


def has_unconfirmed(sit: Situation) -> bool:
    return any(not i.confirmed and 0 <= day_index(sit, i.date) < H for i in sit.incomes)


def _next(sit: Situation, inc: Income | None) -> NextIncome | None:
    if inc is None:
        return None
    return NextIncome(name=inc.name, date=inc.date, days=day_index(sit, inc.date),
                      confirmed=inc.confirmed)


def build_headline(sit: Situation, base: list[int], pess: list[int] | None) -> Headline:
    st = stats(sit, base)
    ni = next_income(sit)
    if ni is None:
        state = "no_income"
    elif st.first_negative_date is not None:
        state = "deficit"
    elif pess is not None and min(pess) < 0:
        state = "depends"
    elif st.min < 3 * sit.daily:
        state = "tight"
    else:
        state = "ok"
    days_left = st.min // sit.daily if st.min >= 0 and sit.daily > 0 else None
    return Headline(
        state=state,
        next_income=_next(sit, ni),
        next_confirmed_income=_next(sit, next_income(sit, only_confirmed=True)),
        min_balance=st.min,
        min_date=st.min_date,
        first_negative_date=st.first_negative_date,
        max_deficit=st.max_deficit,
        days_of_spending_left=days_left,
    )


def headline(sit: Situation) -> Headline:
    pess = series(sit, pessimistic=True) if has_unconfirmed(sit) else None
    return build_headline(sit, series(sit), pess)
