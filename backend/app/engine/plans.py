import datetime as dt

from app.engine.dates import day_index
from app.engine.series import stats
from app.models import DeficitPlan, EarnOption, PostponeOption, ReduceOption, Situation

FLEXIBLE_CATEGORIES = ("кафе", "прочее")
EASY_EARN_LIMIT = 1500


def _ceil_div(a: int, b: int) -> int:
    return -(-a // b)


def flexible_per_day(sit: Situation) -> int:
    """Сколько в день уходит на то, от чего проще отказаться: кафе, доставка, прочее."""
    return sum(c.per_day for c in sit.categories or []
               if any(word in c.name.lower() for word in FLEXIBLE_CATEGORIES))


def deficit_plan(sit: Situation, values: list[int], based_on: str,
                 safe_date: dt.date | None = None) -> DeficitPlan | None:
    """Три варианта выхода из минуса. None, если минуса нет."""
    st = stats(sit, values)
    if st.first_negative_date is None:
        return None

    options = []
    if safe_date is not None:
        options.append(PostponeOption(date=safe_date))

    per_day = max(_ceil_div(-v, d + 1) for d, v in enumerate(values) if v < 0)
    flexible = flexible_per_day(sit)
    options.append(ReduceOption(
        per_day=per_day,
        new_daily=sit.daily - per_day,
        until=st.last_negative_date,
        days=day_index(sit, st.last_negative_date) + 1,
        possible=per_day <= sit.daily,
        ease="easy" if per_day <= max(flexible, 0.2 * sit.daily) else "hard",
        flexible_per_day=flexible,
    ))
    options.append(EarnOption(
        amount=st.max_deficit,
        by_date=st.min_date,
        first_amount=st.first_negative_amount,
        first_date=st.first_negative_date,
        ease="easy" if st.max_deficit <= EASY_EARN_LIMIT else "hard",
    ))
    return DeficitPlan(
        deficit=st.max_deficit,
        by_date=st.min_date,
        first_needed_amount=st.first_negative_amount,
        first_needed_date=st.first_negative_date,
        based_on=based_on,
        options=options,
    )
