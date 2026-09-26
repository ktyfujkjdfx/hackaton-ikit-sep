import datetime as dt

from app.models import DeficitPlan, Situation


def deficit_plan(sit: Situation, values: list[int], based_on: str,
                 safe_date: dt.date | None = None) -> DeficitPlan | None:
    raise NotImplementedError
