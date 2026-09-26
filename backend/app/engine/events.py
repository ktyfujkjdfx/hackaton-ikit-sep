from app.engine.dates import in_horizon
from app.models import Event, Purchase, Situation

DEFAULT_PURCHASE_NAME = "Покупка"


def events(sit: Situation, purchase: Purchase | None) -> list[Event]:
    """События горизонта по датам: для графика и списка «Ближайшие»."""
    out = [Event(date=i.date, kind="income", name=i.name, amount=i.amount, confirmed=i.confirmed)
           for i in sit.incomes if in_horizon(sit, i.date)]
    out += [Event(date=o.date, kind="obligation", name=o.name, amount=o.amount, confirmed=None)
            for o in sit.obligations if in_horizon(sit, o.date)]
    out += [Event(date=s.date, kind="spend", name=s.name, amount=s.amount, confirmed=None)
            for s in sit.spends if in_horizon(sit, s.date)]
    if purchase is not None and in_horizon(sit, purchase.date):
        out.append(Event(date=purchase.date, kind="purchase",
                         name=purchase.name or DEFAULT_PURCHASE_NAME,
                         amount=purchase.amount, confirmed=None))
    return sorted(out, key=lambda e: e.date)
