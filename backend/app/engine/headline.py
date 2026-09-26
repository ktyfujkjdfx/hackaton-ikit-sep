from app.models import Headline, Income, Situation


def next_income(sit: Situation, only_confirmed: bool = False) -> Income | None:
    raise NotImplementedError


def has_unconfirmed(sit: Situation) -> bool:
    raise NotImplementedError


def headline(sit: Situation) -> Headline:
    raise NotImplementedError
