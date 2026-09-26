import datetime as dt


def format_rub(v: int) -> str:
    """2400 -> "2 400 ₽", -200 -> "−200 ₽" (неразрывный пробел)."""
    raise NotImplementedError


def format_date_ru(d: dt.date | str, with_year_if_other: bool = True) -> str:
    """"5 октября", "4 июня 2027"."""
    raise NotImplementedError


def days_word(n: int) -> str:
    """"1 день", "2 дня", "5 дней"."""
    raise NotImplementedError
