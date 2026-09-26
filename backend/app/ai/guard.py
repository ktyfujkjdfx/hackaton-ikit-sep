"""Guard (B.6): все числа и даты из текста API должны встречаться в facts, иначе берём шаблон.

Проверка идёт по строкам, которые видит пользователь: facts уже отформатированы движком,
поэтому «2 400 ₽» в тексте и в факте — это одна и та же строка.
"""
from __future__ import annotations

import logging
import re

log = logging.getLogger(__name__)

# 1–2 цифры подряд с любыми разделителями внутри: «2 400», «2400», «15.10», «600»
NUMBER_RE = re.compile(r"\d[\d\s .,:-]*\d|\d")
MONTH_WORDS = (
    "январ", "феврал", "март", "апрел", "мая", "май", "июн", "июл",
    "август", "сентябр", "октябр", "ноябр", "декабр",
)


def _normalize(text: str) -> str:
    """Пробелы всех видов → один, «−» и «–» → «-», нижний регистр."""
    text = text.replace(" ", " ").replace("−", "-").replace("–", "-")
    return re.sub(r"\s+", " ", text).lower()


def _numbers(text: str) -> set[str]:
    """Числа без пробелов внутри: «2 400» и «2400» — одно и то же."""
    found = set()
    for match in NUMBER_RE.findall(_normalize(text)):
        digits = re.sub(r"[^\d]", "", match)
        if digits:
            found.add(digits.lstrip("0") or "0")
    return found


def _month_words(text: str) -> set[str]:
    clean = _normalize(text)
    return {word for word in MONTH_WORDS if word in clean}


def allowed_strings(facts: list[dict], extra: list[str] | None = None) -> list[str]:
    """Что считается «известным»: подписи и значения фактов плюс явно разрешённые строки."""
    allowed = []
    for fact in facts or []:
        allowed.append(str(fact.get("label", "")))
        allowed.append(str(fact.get("value", "")))
    allowed += extra or []
    return allowed


def check(text: str, facts: list[dict], extra: list[str] | None = None) -> bool:
    """True, если в тексте нет ни одного числа и месяца, которых нет в facts."""
    if not text.strip():
        return False
    source = " ".join(allowed_strings(facts, extra))
    known_numbers = _numbers(source)
    known_months = _month_words(source)

    unknown_numbers = _numbers(text) - known_numbers
    unknown_months = _month_words(text) - known_months
    if unknown_numbers or unknown_months:
        log.warning("guard отбросил текст: числа %s, месяцы %s", unknown_numbers, unknown_months)
        return False
    return True
