import datetime as dt

from app.models import Purchase, PurchaseCheck, Situation


def earliest_safe_date(sit: Situation, amount: int) -> dt.date | None:
    raise NotImplementedError


def check_purchase(sit: Situation, purchase: Purchase) -> PurchaseCheck:
    raise NotImplementedError
