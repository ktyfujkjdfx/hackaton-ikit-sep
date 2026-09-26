"""Единственная дверь AI-слоя к движку A (docs/CONTRACT.md, раздел 7.1).

Здесь нет ни одной формулы: только доступ к app.engine и форматирование его же функциями.
Пока движка нет, available() == False, и orchestrator честно говорит, что расчёт недоступен.
Тесты подменяют движок через set_engine().
"""
from __future__ import annotations

from datetime import date
from typing import Any

_override: Any = None


def set_engine(module: Any) -> None:
    """Подменить движок (используют тесты, пока A не выложил app/engine)."""
    global _override
    _override = module


REQUIRED = ("check_purchase", "headline", "series", "stats", "day_index")


def engine() -> Any:
    """Модуль движка. Бросает EngineUnavailable, если его ещё нет или он пока пустой."""
    if _override is not None:
        return _override
    try:
        from app import engine as real_engine
    except Exception as error:  # noqa: BLE001
        raise EngineUnavailable(str(error)) from error
    missing = [name for name in REQUIRED if not hasattr(real_engine, name)]
    if missing:
        raise EngineUnavailable(f"в app.engine ещё нет функций: {', '.join(missing)}")
    return real_engine


def available() -> bool:
    try:
        engine()
    except EngineUnavailable:
        return False
    return True


class EngineUnavailable(RuntimeError):
    """Движок A ещё не подключён — считать нечем."""


def _formatter(name: str):
    eng = engine()
    function = getattr(eng, name, None)
    if function is None:  # format.py может не быть реэкспортирован
        from importlib import import_module

        function = getattr(import_module(f"{eng.__name__}.format"), name)
    return function


def rub(value: int) -> str:
    """2400 → «2 400 ₽». Форматирует движок — иначе guard и текст увидят разные строки."""
    return _formatter("format_rub")(value)


def day(value: date | str, with_year_if_other: bool = True) -> str:
    """«5 октября», «4 июня 2027»."""
    return _formatter("format_date_ru")(value, with_year_if_other)


def days(count: int) -> str:
    """«1 день», «2 дня», «5 дней»."""
    return _formatter("days_word")(count)
