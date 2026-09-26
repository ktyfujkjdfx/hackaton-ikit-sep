import datetime as dt

import pytest

from app import engine, models
from app.engine import (build_dashboard, check_purchase, day_index, days_word, deficit_plan, events,
                        format_date_ru, format_rub, goal_plan, has_unconfirmed, headline,
                        history_items, money_types, next_income, series, stats, to_day_series,
                        validate)
from app.engine.dates import date_at
from app.models import ChatRequest, ChatResponse, Purchase, Situation, Spend
from app.engine.personas import load_personas

ANYA = load_personas()["anya"]["situation"]
DANYA = load_personas()["danya"]["situation"]

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


# ---------- Движок: юнит-тесты ----------

TODAY = dt.date(2026, 9, 27)
NBSP = " "


def anya() -> Situation:
    return Situation.model_validate(ANYA)


def danya() -> Situation:
    return Situation.model_validate(DANYA)


def sit_of(**kw) -> Situation:
    return Situation(today=TODAY, **{"balance": 1000, "daily": 100, **kw})


def buy(amount: int, date: str = "2026-09-27") -> Purchase:
    return Purchase(amount=amount, date=date, name="Наушники")


def test_day_index_and_date_at():
    sit = anya()
    assert day_index(sit, "2026-09-27") == 0
    assert day_index(sit, dt.date(2026, 10, 10)) == 13
    assert day_index(sit, "2026-09-20") == -7
    assert date_at(sit, 12) == dt.date(2026, 10, 9)


def test_series_day_zero_already_spends_daily():
    values = series(anya())
    assert len(values) == engine.H
    assert values[0] == 6600
    assert values[12] == 600


def test_series_ignores_items_outside_horizon():
    sit = sit_of(obligations=[{"id": "o", "name": "Далёкий", "amount": 500, "date": "2026-10-27"}],
                 incomes=[{"id": "i", "name": "Далёкий", "amount": 500, "date": "2026-12-01",
                           "confirmed": True}])
    assert series(sit) == series(sit_of())


def test_series_reduce_only_until_day():
    sit = sit_of()
    values = series(sit, reduce=50, reduce_until=1)
    assert values[:3] == [950, 900, 800]


def test_series_pessimistic_drops_unconfirmed():
    sit = danya()
    assert series(sit)[6] - series(sit, pessimistic=True)[6] == 4000


def test_series_purchase_on_its_day():
    values = series(anya(), purchase=buy(1000, "2026-09-28"))
    assert values[0] == 6600
    assert values[1] == 5300


def test_stats_min_date_is_first_minimum():
    st = stats(sit_of(), [5, 1, 1, 3])
    assert st.min == 1
    assert st.min_date == dt.date(2026, 9, 28)
    assert st.first_negative_date is None
    assert st.max_deficit == 0 and st.first_negative_amount == 0


def test_stats_negative_range():
    st = stats(sit_of(), [5, -2, -7, 3, -1, 4])
    assert st.first_negative_date == dt.date(2026, 9, 28)
    assert st.last_negative_date == dt.date(2026, 10, 1)
    assert st.max_deficit == 7
    assert st.first_negative_amount == 2


def test_to_day_series():
    ds = to_day_series(anya(), series(anya()))
    assert len(ds.days) == 30
    assert ds.days[0].date == TODAY and ds.days[0].balance == 6600
    assert ds.days[-1].date == dt.date(2026, 10, 26)
    assert ds.stats.min == 600


def test_next_income_skips_today_and_respects_confirmed():
    sit = danya()
    assert next_income(sit).name == "Подработка курьером"
    assert next_income(sit, only_confirmed=True).name == "Стипендия"
    today_income = sit_of(incomes=[{"id": "i", "name": "Сегодня", "amount": 100,
                                    "date": "2026-09-27", "confirmed": True}])
    assert next_income(today_income) is None


def test_has_unconfirmed():
    assert has_unconfirmed(danya()) is True
    assert has_unconfirmed(anya()) is False


@pytest.mark.parametrize("kw,state", [
    ({"balance": 100000, "daily": 100, "incomes": [
        {"id": "i", "name": "Стипендия", "amount": 100, "date": "2026-10-10", "confirmed": True}]}, "ok"),
    ({"balance": 100, "daily": 100, "incomes": [
        {"id": "i", "name": "Стипендия", "amount": 100, "date": "2026-10-10", "confirmed": True}]},
     "deficit"),
    ({"balance": 0, "daily": 300}, "no_income"),
])
def test_headline_states(kw, state):
    assert headline(sit_of(**kw)).state == state


def test_headline_anya_and_danya():
    h = headline(anya())
    assert h.state == "tight"
    assert h.next_income.days == 13 and h.next_income.confirmed is True
    assert h.min_balance == 600 and h.min_date == dt.date(2026, 10, 9)
    assert h.days_of_spending_left == 2
    assert headline(danya()).state == "depends"


def test_headline_daily_zero():
    h = headline(sit_of(daily=0, incomes=[
        {"id": "i", "name": "Стипендия", "amount": 100, "date": "2026-10-10", "confirmed": True}]))
    assert h.state == "ok"
    assert h.days_of_spending_left is None


def test_check_purchase_anya_3000():
    r = check_purchase(anya(), buy(3000))
    assert r.verdict == "deficit"
    assert r.before.min == 600
    assert r.after.first_negative_date == dt.date(2026, 10, 5)
    assert r.earliest_safe_date == dt.date(2026, 10, 15)
    assert r.safe_depends_on_unconfirmed is False
    assert [o.kind for o in r.plan.options] == ["postpone", "reduce", "earn"]
    assert r.goal.shift_days == 50


def test_check_purchase_verdicts():
    assert check_purchase(anya(), buy(100)).verdict == "tight"
    rich = anya()
    rich.balance = 100000
    r = check_purchase(rich, buy(100))
    assert r.verdict == "ok" and r.plan is None


def test_safe_date_depends_on_unconfirmed_income():
    r = check_purchase(danya(), buy(1000))
    assert r.earliest_safe_date == TODAY
    assert r.safe_depends_on_unconfirmed is True


def test_deficit_plan_anya_3000_exact():
    sit = anya()
    plan = deficit_plan(sit, series(sit, purchase=buy(3000)), "purchase", dt.date(2026, 10, 15))
    assert plan.deficit == 2400 and plan.by_date == dt.date(2026, 10, 9)
    assert plan.first_needed_amount == 1200 and plan.first_needed_date == dt.date(2026, 10, 5)
    postpone, reduce, earn = plan.options
    assert postpone.date == dt.date(2026, 10, 15) and postpone.ease == "easy"
    assert (reduce.per_day, reduce.new_daily, reduce.days) == (185, 115, 18)
    assert reduce.possible is True and reduce.ease == "hard" and reduce.flexible_per_day == 60
    assert earn.amount == 2400 and earn.first_amount == 1200 and earn.ease == "hard"


def test_deficit_plan_none_without_minus_and_no_postpone_without_safe_date():
    sit = anya()
    assert deficit_plan(sit, series(sit), "base") is None
    plan = deficit_plan(sit, series(sit, purchase=buy(50000)), "purchase")
    assert [o.kind for o in plan.options] == ["reduce", "earn"]
    assert plan.options[0].possible is False


def test_deficit_plan_easy_rules():
    sit = anya()
    sit.spends.append(Spend(id="s", name="Такси", amount=800, date=TODAY, category="Транспорт"))
    plan = deficit_plan(sit, series(sit), "base")
    reduce, earn = plan.options
    assert reduce.per_day == 16 and reduce.ease == "easy"
    assert earn.amount == 200 and earn.ease == "easy"


def test_deficit_plan_without_categories_uses_20_percent():
    sit = anya()
    sit.categories = None
    sit.spends.append(Spend(id="s", name="Такси", amount=800, date=TODAY, category="Транспорт"))
    reduce = deficit_plan(sit, series(sit), "base").options[0]
    assert reduce.flexible_per_day == 0
    assert reduce.ease == "easy"  # 16 ≤ 0.2 × 300


def test_goal_plan_anya():
    g = goal_plan(anya())
    assert g.monthly_surplus == 1800 and g.per_day == 60 and g.remaining == 15000
    assert g.eta == dt.date(2027, 6, 4) and g.late_days == 3 and g.need_monthly == 1822
    assert g.eta_with_purchase is None and g.shift_days is None


def test_goal_plan_no_goal_and_no_surplus():
    sit = anya()
    sit.goal = None
    assert goal_plan(sit) is None
    poor = anya()
    poor.daily = 1000
    g = goal_plan(poor)
    assert g.monthly_surplus < 0 and g.eta is None and g.late_days is None


def test_goal_plan_counts_one_off_spends():
    sit = anya()
    sit.spends.append(Spend(id="s", name="Такси", amount=600, date=TODAY, category="Транспорт"))
    assert goal_plan(sit).eta == dt.date(2027, 6, 14)


def test_validate_ok_for_personas():
    assert validate(anya()) == []
    assert validate(danya()) == []


def test_validate_collects_errors():
    sit = anya()
    sit.daily = -1
    sit.incomes[1].amount = 0
    sit.obligations[2].date = dt.date(2026, 9, 1)
    errors = {(e.field, e.index, e.subfield) for e in validate(sit)}
    assert errors == {("daily", None, None), ("incomes", 1, "amount"), ("obligations", 2, "date")}


@pytest.mark.parametrize("goal,msg", [
    ({"name": "x", "target": 0, "current": 0, "date": "2027-01-01"}, "сколько нужно"),
    ({"name": "x", "target": 100, "current": 100, "date": "2027-01-01"}, "уже накоплена"),
    ({"name": "x", "target": 100, "current": -1, "date": "2027-01-01"}, "от 0"),
    ({"name": "x", "target": 100, "current": 0, "date": "2026-09-27"}, "в будущем"),
])
def test_validate_goal(goal, msg):
    errors = validate(sit_of(goal=goal))
    assert errors and errors[0].field == "goal" and msg in errors[0].message


@pytest.mark.parametrize("purchase,subfield", [
    (Purchase(amount=0, date="2026-09-27"), "amount"),
    (Purchase(amount=-5, date="2026-09-27"), "amount"),
    (Purchase(amount=100, date="2026-10-27"), "date"),
    (Purchase(amount=100, date="2026-09-26"), "date"),
])
def test_validate_purchase(purchase, subfield):
    errors = validate(anya(), purchase)
    assert [(e.field, e.subfield) for e in errors] == [("purchase", subfield)]


def test_money_types_anya():
    mt = money_types(anya())
    assert mt.stable_income.total == 13200 and len(mt.stable_income.items) == 2
    assert mt.unstable_income.total == 0
    assert mt.stable_expenses.total == 2400
    assert mt.variable_expenses.total == 9000 and mt.variable_expenses.days == 30
    assert mt.reliable_total == 17700


def test_money_types_danya_and_spends():
    mt = money_types(danya())
    assert mt.unstable_income.total == 4000 and mt.stable_income.total == 2800
    sit = anya()
    sit.spends.append(Spend(id="s", name="Такси", amount=800, date=TODAY, category="Транспорт"))
    assert money_types(sit).variable_expenses.total == 9800


def test_history_flags():
    items = {h.name: h for h in history_items(anya())}
    assert items["Общежитие"].regular is True
    assert items["Стипендия"].regular is True
    assert items["Кроссовки"].large is True and items["Кроссовки"].regular is False
    assert items["Доставка еды"].large is False
    danya_items = {h.name: h for h in history_items(danya())}
    assert danya_items["Подработка курьером"].regular is False  # доход не confirmed


def test_events_sorted_with_purchase():
    evs = events(anya(), buy(3000))
    assert [e.date for e in evs] == sorted(e.date for e in evs)
    assert evs[0].kind == "purchase" and evs[0].name == "Наушники"
    kinds = {e.kind for e in evs}
    assert kinds == {"income", "obligation", "purchase"}
    assert all(e.confirmed is not None for e in evs if e.kind == "income")


def test_dashboard_anya_without_purchase():
    d = build_dashboard(anya(), None)
    assert d.horizon_days == 30 and d.today == TODAY
    assert d.headline.state == "tight"
    assert d.scenarios.pessimistic is None and d.scenarios.with_purchase is None
    assert d.purchase is None and d.deficit_plan is None
    assert d.show_learn_card is True
    assert "300 ₽" in d.assumptions[0]
    assert d.unknowns[-1].startswith("Что будет после 26 октября")


def test_dashboard_anya_with_purchase():
    d = build_dashboard(anya(), buy(3000))
    assert d.scenarios.with_purchase.stats.max_deficit == 2400
    assert d.scenarios.with_purchase_pessimistic is None
    assert d.purchase.earliest_safe_date == dt.date(2026, 10, 15)
    assert d.goal.shift_days == 50
    assert d.show_learn_card is False
    assert d.deficit_plan is None  # base без минуса, pessimistic нет


def test_dashboard_danya_uses_pessimistic_plan():
    d = build_dashboard(danya(), buy(500))
    assert d.headline.state == "depends"
    assert d.scenarios.pessimistic.stats.first_negative_date == dt.date(2026, 10, 9)
    assert d.scenarios.with_purchase_pessimistic is not None
    assert d.deficit_plan.based_on == "pessimistic" and d.deficit_plan.deficit == 2840
    assert d.show_learn_card is False
    assert any("Подработка курьером" in a for a in d.assumptions)


def test_dashboard_all_unconfirmed_and_no_obligations():
    sit = sit_of(balance=500, incomes=[{"id": "i", "name": "Подработка", "amount": 3000,
                                        "date": "2026-10-01", "confirmed": False}])
    d = build_dashboard(sit, None)
    assert d.headline.next_income.name == "Подработка"
    assert d.headline.next_confirmed_income is None
    assert d.headline.state == "depends"
    assert d.money_types.stable_expenses.total == 0


def test_dashboard_empty():
    d = build_dashboard(Situation(today=TODAY, balance=0, daily=300), None)
    assert d.headline.state == "no_income"
    assert d.deficit_plan.based_on == "base"
    assert d.goal is None and d.history == []
    assert any("из анкеты" in a for a in d.assumptions)


def test_dashboard_huge_amounts():
    sit = anya()
    sit.balance = 10_000_000
    d = build_dashboard(sit, buy(9_000_000))
    assert d.purchase.verdict == "ok"
    assert d.scenarios.with_purchase.stats.min == 600 + 10_000_000 - 6900 - 9_000_000
    assert format_rub(10_000_000) == f"10{NBSP}000{NBSP}000{NBSP}₽"


# ---------- format.py ----------

def test_format_rub():
    assert format_rub(2400) == f"2{NBSP}400{NBSP}₽"
    assert format_rub(-200) == f"−200{NBSP}₽"
    assert format_rub(0) == f"0{NBSP}₽"
    assert format_rub(999) == f"999{NBSP}₽"


def test_format_date_ru():
    assert format_date_ru("2027-06-04") == "4 июня 2027"
    assert format_date_ru(dt.date(2026, 10, 5)) == "5 октября"
    assert format_date_ru("2027-06-04", with_year_if_other=False) == "4 июня"


@pytest.mark.parametrize("n,text", [(1, "1 день"), (2, "2 дня"), (5, "5 дней"), (11, "11 дней"),
                                    (21, "21 день"), (22, "22 дня"), (50, "50 дней")])
def test_days_word(n, text):
    assert days_word(n) == text


def test_goal_plan_unreachable_goal_has_no_eta():
    sit = anya()
    sit.daily = 359  # в месяц остаётся 30 ₽
    sit.goal.target = 10_000_000
    g = goal_plan(sit, 3000)
    assert g.monthly_surplus == 30
    assert g.eta is None and g.late_days is None and g.eta_with_purchase is None


def test_goal_plan_early_goal_has_negative_late_days():
    sit = anya()
    sit.goal.date = dt.date(2027, 12, 1)
    assert goal_plan(sit).late_days < 0


def test_purchase_on_last_horizon_day():
    r = check_purchase(anya(), buy(100, "2026-10-26"))
    assert r.after.min == 600 and r.verdict == "tight"


def test_income_today_counts_in_series_but_is_not_next():
    sit = sit_of(daily=100, incomes=[
        {"id": "i", "name": "Сегодня", "amount": 500, "date": "2026-09-27", "confirmed": True},
        {"id": "j", "name": "Потом", "amount": 500, "date": "2026-10-26", "confirmed": True},
        {"id": "k", "name": "За горизонтом", "amount": 500, "date": "2026-10-27", "confirmed": True}])
    assert series(sit)[0] == 1400
    assert next_income(sit).name == "Потом"


@pytest.mark.parametrize("amount", [0, -5000])
def test_validate_spend_amount_must_be_positive(amount):
    sit = anya()
    sit.spends.append(Spend(id="s0", name="Такси", amount=800, date=TODAY, category="Транспорт"))
    sit.spends.append(Spend(id="s1", name="Возврат", amount=amount, date=TODAY, category="Прочее"))
    errors = validate(sit)
    assert [(e.field, e.index, e.subfield) for e in errors] == [("spends", 1, "amount")]
    assert "больше нуля" in errors[0].message


@pytest.mark.parametrize("field,amount", [("incomes", 0), ("incomes", -3200),
                                          ("obligations", 0), ("obligations", -1800)])
def test_validate_income_and_obligation_amount_must_be_positive(field, amount):
    sit = anya()
    getattr(sit, field)[0].amount = amount
    errors = validate(sit)
    assert [(e.field, e.index, e.subfield) for e in errors] == [(field, 0, "amount")]
