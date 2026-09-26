from app.engine.dates import H, in_horizon
from app.models import IncomeGroup, MoneyTypes, ObligationGroup, Situation, VariableExpenses


def money_types(sit: Situation) -> MoneyTypes:
    """Постоянное и разовое за 30 дней горизонта."""
    stable = [i for i in sit.incomes if i.confirmed and in_horizon(sit, i.date)]
    unstable = [i for i in sit.incomes if not i.confirmed and in_horizon(sit, i.date)]
    obligations = [o for o in sit.obligations if in_horizon(sit, o.date)]
    one_off = [s for s in sit.spends if in_horizon(sit, s.date)]
    stable_total = sum(i.amount for i in stable)
    obligations_total = sum(o.amount for o in obligations)
    return MoneyTypes(
        stable_income=IncomeGroup(total=stable_total, items=stable),
        unstable_income=IncomeGroup(total=sum(i.amount for i in unstable), items=unstable),
        stable_expenses=ObligationGroup(total=obligations_total, items=obligations),
        variable_expenses=VariableExpenses(
            total=sit.daily * H + sum(s.amount for s in one_off),
            daily=sit.daily, days=H, one_off=one_off,
        ),
        reliable_total=sit.balance + stable_total - obligations_total,
    )
