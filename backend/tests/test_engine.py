import datetime as dt

from app import engine, models
from app.models import ChatRequest, ChatResponse, Situation
from tests.fixtures_personas import ANYA, DANYA

ENGINE_API = [
    "H", "day_index", "series", "stats", "to_day_series", "next_income", "has_unconfirmed",
    "earliest_safe_date", "deficit_plan", "goal_plan", "check_purchase", "headline",
    "money_types", "history_items", "events", "validate", "build_dashboard", "run_checks",
    "format_rub", "format_date_ru", "days_word",
]


def test_models_import():
    for name in ["Situation", "Purchase", "SeriesStats", "DaySeries", "Headline", "MoneyTypes",
                 "DeficitPlan", "GoalPlan", "PurchaseCheck", "Dashboard", "ValidationError",
                 "HistoryItem", "ChecksResult", "Income", "Event", "ChatRequest", "ChatResponse"]:
        assert hasattr(models, name), name


def test_engine_exports_contract_signatures():
    for name in ENGINE_API:
        assert hasattr(engine, name), name
    assert engine.H == 30


def test_anya_situation_validates():
    sit = Situation.model_validate(ANYA)
    assert sit.today == dt.date(2026, 9, 27)
    assert sit.balance == 6900
    assert sit.incomes[0].date == dt.date(2026, 10, 10)
    assert sit.goal.name == "Ноутбук"
    assert len(sit.history) == 8
    assert sit.model_dump(mode="json")["incomes"][0]["date"] == "2026-10-10"


def test_danya_situation_validates():
    sit = Situation.model_validate(DANYA)
    assert sit.incomes[0].confirmed is False


def test_situation_today_defaults_to_demo_today():
    sit = Situation.model_validate({k: v for k, v in ANYA.items() if k != "today"})
    assert sit.today == dt.date(2026, 9, 27)


def test_chat_models_validate():
    req = ChatRequest.model_validate({
        "situation": ANYA, "purchase": None, "message": "Могу купить наушники за 3000?",
        "history": [{"role": "user", "text": "привет"}],
    })
    assert req.situation.balance == 6900
    resp = ChatResponse.model_validate({
        "intent": "purchase_check",
        "tool_calls": [{"name": "check_purchase", "args": {"amount": 3000, "date": "2026-09-27"}}],
        "headline": "Если купить сейчас — будет минус", "tone": "bad",
        "facts": [{"label": "Первый день без денег", "value": "5 октября", "tone": None}],
        "text": "Решение за тобой.", "source": None,
        "purchase": {"amount": 3000, "date": "2026-09-27", "name": "Наушники"},
        "proposed_entry": None,
        "actions": [{"kind": "open_explain", "label": "Как посчитали?", "payload": {}}],
        "nlu": {"mode": "sklearn", "label": "purchase_check", "confidence": 0.94},
        "explainer": "templates", "guarded": False,
    })
    assert resp.purchase.amount == 3000
