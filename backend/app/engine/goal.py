import datetime as dt
import math
from fractions import Fraction

from app.engine.dates import H, day_index, in_horizon
from app.models import GoalPlan, Situation

# Дальше 100 лет срок не показываем: при таком темпе цель недостижима (и дата бы переполнилась).
MAX_GOAL_DAYS = 100 * 365


def goal_plan(sit: Situation, extra: int = 0) -> GoalPlan | None:
    """Когда накопится на цель при текущем темпе; extra — сумма покупки."""
    g = sit.goal
    if g is None:
        return None
    incomes = sum(i.amount for i in sit.incomes if in_horizon(sit, i.date))
    obligations = sum(o.amount for o in sit.obligations if in_horizon(sit, o.date))
    one_off = sum(s.amount for s in sit.spends if in_horizon(sit, s.date))
    monthly = incomes - obligations - sit.daily * H
    remaining = max(0, g.target - g.current)
    days_to_goal = max(1, day_index(sit, g.date))
    need_monthly = math.ceil(Fraction(remaining * H, days_to_goal))

    plan = GoalPlan(monthly_surplus=monthly, per_day=monthly / H, remaining=remaining,
                    eta=None, late_days=None, need_monthly=need_monthly,
                    eta_with_purchase=None, shift_days=None)
    if monthly <= 0:
        return plan

    # ceil(x / per_day) при per_day = monthly / H, без ошибок округления float
    days = math.ceil(Fraction((remaining + one_off) * H, monthly))
    if days > MAX_GOAL_DAYS:
        return plan
    plan.eta = sit.today + dt.timedelta(days=days)
    plan.late_days = (plan.eta - g.date).days
    if extra:
        days_x = math.ceil(Fraction((remaining + one_off + extra) * H, monthly))
        if days_x > MAX_GOAL_DAYS:
            return plan
        plan.eta_with_purchase = sit.today + dt.timedelta(days=days_x)
        plan.shift_days = days_x - days
    return plan
