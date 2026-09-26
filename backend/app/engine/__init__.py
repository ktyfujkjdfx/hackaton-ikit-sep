"""Движок расчётов. Сигнатуры — docs/CONTRACT.md, раздел 7.1."""
from app.engine.checks import run_checks
from app.engine.dashboard import build_dashboard
from app.engine.dates import H, date_at, day_index
from app.engine.events import events
from app.engine.format import days_word, format_date_ru, format_rub
from app.engine.goal import goal_plan
from app.engine.headline import has_unconfirmed, headline, next_income
from app.engine.history import history_items
from app.engine.plans import deficit_plan
from app.engine.purchase import check_purchase, earliest_safe_date
from app.engine.series import series, stats, to_day_series
from app.engine.types import money_types
from app.engine.validate import validate

__all__ = [
    "H", "day_index", "date_at", "series", "stats", "to_day_series", "next_income",
    "has_unconfirmed", "earliest_safe_date", "deficit_plan", "goal_plan", "check_purchase",
    "headline", "money_types", "history_items", "events", "validate", "build_dashboard",
    "run_checks", "format_rub", "format_date_ru", "days_word",
]
