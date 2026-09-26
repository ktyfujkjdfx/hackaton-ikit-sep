import datetime as dt

from app.models import demo_today

NBSP = " "
MINUS = "−"
MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа",
          "сентября", "октября", "ноября", "декабря"]


def format_rub(v: int) -> str:
    """2400 -> "2 400 ₽", -200 -> "−200 ₽" (неразрывный пробел)."""
    n = round(v)
    digits = f"{abs(n):,}".replace(",", NBSP)
    return f"{MINUS if n < 0 else ''}{digits}{NBSP}₽"


def format_date_ru(d: dt.date | str, with_year_if_other: bool = True) -> str:
    """"5 октября", "4 июня 2027" — год пишем, если он не текущий."""
    d = d if isinstance(d, dt.date) else dt.date.fromisoformat(d)
    text = f"{d.day} {MONTHS[d.month - 1]}"
    if with_year_if_other and d.year != demo_today().year:
        text += f" {d.year}"
    return text


def plural(n: int, one: str, few: str, many: str) -> str:
    n = abs(n) % 100
    n1 = n % 10
    if 10 < n < 20:
        return many
    if 1 < n1 < 5:
        return few
    if n1 == 1:
        return one
    return many


def days_word(n: int) -> str:
    """"1 день", "2 дня", "5 дней"."""
    return f"{n} {plural(n, 'день', 'дня', 'дней')}"
