"""Выполнение намерения: вызвать движок A и собрать готовые факты (B.5).

Правило слоя: здесь нет ни одной денежной формулы. Все числа приходят из app.engine и
форматируются его же функциями через engine_port. Исключение — показ категорий: контракт (B.5)
сам отдаёт эту витрину чату, считая её оформлением уже известных `situation.categories`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.ai import engine_port as port
from app.ai import knowledge, templates
from app.ai.parse import Slots

TONE_GOOD, TONE_BAD, TONE_NEUTRAL = "good", "bad", "neutral"


@dataclass
class Execution:
    intent: str
    headline: str = ""
    tone: str = TONE_NEUTRAL
    facts: list[dict] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    actions: list[dict] = field(default_factory=list)
    text: str = ""
    source: dict | None = None
    purchase: dict | None = None
    proposed_entry: dict | None = None


def _get(obj: Any, name: str, default: Any = None) -> Any:
    """Движок может отдать pydantic-модель или dict — читаем одинаково."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _fact(label: str, value: str, tone: str | None = None) -> dict:
    return {"label": label, "value": value, "tone": tone}


def _iso(value: Any) -> str:
    return value.isoformat() if isinstance(value, date) else str(value)


# ------------------------------------------------------------------ purchase_check

def _purchase_check(slots: Slots, sit: Any, active: Any) -> Execution:
    amount = slots.amount if slots.amount is not None else _get(active, "amount")
    if not amount:
        return Execution("clarify", templates.HEADLINE_CLARIFY,
                         text=templates.CLARIFY_PURCHASE_AMOUNT)

    today = _get(sit, "today")
    when = slots.date or today
    eng = port.engine()
    horizon_index = eng.day_index(sit, when)
    if horizon_index < 0:
        when = today
        horizon_index = 0
    if horizon_index >= getattr(eng, "H", 30):
        return Execution("purchase_check", text=templates.PURCHASE_OUT_OF_HORIZON)

    from app.ai.schemas import Purchase

    name = slots.name or _get(active, "name")
    purchase = {"amount": int(amount), "date": _iso(when), "name": name}
    result = eng.check_purchase(sit, Purchase.model_validate(purchase))

    before, after = _get(result, "before"), _get(result, "after")
    safe_date = _get(result, "earliest_safe_date")
    goal = _get(result, "goal")
    execution = Execution(
        "purchase_check",
        tool_calls=[{"name": "check_purchase", "args": {"amount": int(amount), "date": _iso(when)}}],
        purchase=purchase,
    )

    if _get(after, "first_negative_date") is None:
        execution.headline = templates.HEADLINE_PURCHASE_OK
        execution.tone = TONE_GOOD
        execution.facts = [
            _fact("Самый низкий остаток после покупки", port.rub(_get(after, "min")), TONE_GOOD),
            _fact("Когда", port.day(_get(after, "min_date"))),
        ]
        tight = _get(result, "verdict") == "tight"
        execution.text = templates.PURCHASE_TIGHT if tight else templates.PURCHASE_FITS
    else:
        base_bad = _get(before, "first_negative_date") is not None
        execution.tone = TONE_BAD
        execution.headline = (
            templates.HEADLINE_PURCHASE_WORSE if base_bad
            else templates.HEADLINE_PURCHASE_BAD.format(
                when="сейчас" if horizon_index == 0 else port.day(when))
        )
        execution.facts = [
            _fact("Первый день без денег", port.day(_get(after, "first_negative_date"))),
            _fact("Самый большой минус", port.rub(_get(after, "max_deficit")), TONE_BAD),
        ]
        if base_bad:
            execution.facts.append(_fact(
                "Без покупки минус был",
                f"{port.rub(_get(before, 'max_deficit'))} с {port.day(_get(before, 'first_negative_date'))}",
            ))
        execution.facts.append(_fact(
            "Без минуса можно купить",
            f"с {port.day(safe_date)}" if safe_date else "не в ближайшие 30 дней",
            TONE_GOOD if safe_date else None,
        ))
        if goal is not None and _get(goal, "eta") and _get(goal, "shift_days"):
            goal_name = _get(_get(sit, "goal"), "name", "Цель")
            execution.facts.append(
                _fact(f"Цель «{goal_name}» сдвинется", f"на {port.days(_get(goal, 'shift_days'))}")
            )
        if safe_date:
            unconfirmed = (templates.UNCONFIRMED_NOTE
                           if _get(result, "safe_depends_on_unconfirmed") else "")
            execution.text = templates.PURCHASE_WAIT.format(
                safe_date=port.day(safe_date), unconfirmed=unconfirmed) + templates.PURCHASE_TAIL
        else:
            execution.text = templates.PURCHASE_NO_SAFE_DATE + templates.PURCHASE_TAIL
        execution.facts += _plan_facts(_get(result, "plan"))

    execution.actions = [{"kind": "open_explain", "label": "Как посчитали?", "payload": {}}]
    if safe_date and _get(after, "first_negative_date") is not None:
        execution.actions.append({"kind": "defer", "label": f"Отложить до {port.day(safe_date)}",
                                  "payload": {"date": _iso(safe_date)}})
        execution.actions.append({"kind": "show_jobs", "label": "Где искать подработку",
                                  "payload": {"amount": _get(after, "max_deficit")}})
    return execution


def _plan_facts(plan: Any) -> list[dict]:
    """Варианты выхода из минуса как факты: «что сделать» → «легко/сложно» (B.5)."""
    if plan is None:
        return []
    facts: list[dict] = []
    for option in _get(plan, "options", []) or []:
        kind = _get(option, "kind")
        ease = "легко" if _get(option, "ease") == "easy" else "сложно"
        if kind == "postpone":
            label = f"Перенести покупку на {port.day(_get(option, 'date'))}"
        elif kind == "reduce":
            if not _get(option, "possible", True):
                facts.append(_fact("Тратить меньше", "не хватит даже без обычных трат", TONE_BAD))
                continue
            label = f"Тратить на {port.rub(_get(option, 'per_day'))} в день меньше"
            ease = (f"{ease} · до {port.day(_get(option, 'until'))}, "
                    f"{port.days(_get(option, 'days'))}")
        elif kind == "earn":
            label = (f"Найти {port.rub(_get(option, 'amount'))} "
                     f"до {port.day(_get(option, 'by_date'))}")
        else:
            continue
        facts.append(_fact(label, ease, TONE_GOOD if _get(option, "ease") == "easy" else None))
    return facts


# ------------------------------------------------------------------ forecast

def _forecast(sit: Any) -> Execution:
    eng = port.engine()
    head = eng.headline(sit)
    next_income = _get(head, "next_income")
    execution = Execution(
        "forecast",
        headline=templates.HEADLINE_FORECAST,
        tool_calls=[{"name": "headline", "args": {"horizon_days": 30}}],
    )
    if next_income is None:
        execution.text = templates.NO_INCOME
        execution.actions = [{"kind": "open_add_income", "label": "Указать поступление", "payload": {}}]
        return execution

    execution.facts = [
        _fact(f"До «{_get(next_income, 'name')}»", port.days(_get(next_income, "days"))),
        _fact("Самый низкий остаток",
              f"{port.rub(_get(head, 'min_balance'))}, {port.day(_get(head, 'min_date'))}"),
    ]
    first_negative = _get(head, "first_negative_date")
    if first_negative:
        execution.facts.append(_fact("Минус начнётся", port.day(first_negative), TONE_BAD))
        execution.tone = TONE_BAD
        execution.text = templates.FORECAST_RISK + templates.FORECAST_TAIL
    else:
        execution.tone = TONE_GOOD if _get(head, "state") == "ok" else TONE_NEUTRAL
        execution.text = templates.FORECAST_OK + templates.FORECAST_TAIL
    return execution


# ------------------------------------------------------------------ explain

def _explain(sit: Any) -> Execution:
    eng = port.engine()
    values = eng.series(sit)
    stats = eng.stats(sit, values)
    min_date = _get(stats, "min_date")
    day_count = eng.day_index(sit, min_date) + 1
    money = eng.money_types(sit)

    facts = [
        _fact("Сейчас на карте (факт)", port.rub(_get(sit, "balance"))),
        _fact("Обычные траты (оценка)", f"{port.rub(_get(sit, 'daily'))} × {day_count}"),
        _fact("Обязательные платежи (постоянные)",
              port.rub(_get(_get(money, "stable_expenses"), "total"))),
    ]
    expected = _get(_get(money, "stable_income"), "total")
    if expected:
        facts.append(_fact("Поступления (ожидается)", port.rub(expected)))
    facts.append(_fact("Итог — самый низкий остаток",
                       f"{port.rub(_get(stats, 'min'))}, {port.day(min_date)}"))

    return Execution(
        "explain",
        headline=templates.HEADLINE_EXPLAIN,
        facts=facts,
        text=templates.EXPLAIN_TAIL,
        tool_calls=[{"name": "series", "args": {"horizon_days": 30, "explain": True}}],
        actions=[{"kind": "open_explain", "label": "Открыть «Как посчитали?»", "payload": {}}],
    )


# ------------------------------------------------------------------ deficit_plan

def _deficit_plan(sit: Any, active: Any) -> Execution:
    eng = port.engine()
    note = ""
    plan = None
    based_on = "base"
    safe_date = None

    if active is not None:
        check = eng.check_purchase(sit, active)
        if _get(_get(check, "after"), "first_negative_date") is not None:
            plan, based_on = _get(check, "plan"), "purchase"
            safe_date = _get(check, "earliest_safe_date")

    if plan is None:
        values = eng.series(sit)
        stats = eng.stats(sit, values)
        if _get(stats, "first_negative_date") is None and eng.has_unconfirmed(sit):
            values = eng.series(sit, pessimistic=True)
            stats = eng.stats(sit, values)
            based_on = "pessimistic"
            note = templates.DEFICIT_PESSIMISTIC_NOTE
        if _get(stats, "first_negative_date") is None:
            return Execution("deficit_plan", headline=templates.HEADLINE_NO_DEFICIT,
                             tone=TONE_GOOD, text=templates.NO_DEFICIT_TEXT,
                             tool_calls=[{"name": "series", "args": {"horizon_days": 30}}])
        plan = eng.deficit_plan(sit, values, based_on, safe_date)

    if plan is None:
        return Execution("deficit_plan", headline=templates.HEADLINE_NO_DEFICIT,
                         tone=TONE_GOOD, text=templates.NO_DEFICIT_TEXT)

    deficit = port.rub(_get(plan, "deficit"))
    return Execution(
        "deficit_plan",
        headline=templates.HEADLINE_DEFICIT.format(deficit=deficit),
        tone=TONE_BAD,
        facts=_plan_facts(plan) + [
            _fact("Нужно к первому дню без денег",
                  f"{port.rub(_get(plan, 'first_needed_amount'))} "
                  f"до {port.day(_get(plan, 'first_needed_date'))}"),
        ],
        text=note + templates.DEFICIT_TAIL,
        tool_calls=[{"name": "deficit_plan", "args": {"based_on": based_on}}],
        actions=[{"kind": "show_jobs", "label": "Где искать подработку",
                  "payload": {"amount": _get(plan, "deficit")}}],
    )


# ------------------------------------------------------------------ categories

def _categories(sit: Any) -> Execution:
    categories = _get(sit, "categories") or []
    if not categories:
        return Execution("categories", headline=templates.HEADLINE_CATEGORIES,
                         text=templates.NO_CATEGORIES)

    # Витрина уже известных per_day из situation (B.5): месяц = 30 дней, доля — от суммы per_day
    ordered = sorted(categories, key=lambda c: _get(c, "per_day", 0), reverse=True)
    total = sum(_get(c, "per_day", 0) for c in ordered) or 1
    facts = [
        _fact(_get(c, "name", ""),
              f"{port.rub(_get(c, 'per_day', 0) * 30)}/мес · {round(_get(c, 'per_day', 0) / total * 100)}%")
        for c in ordered
    ]
    top = _get(ordered[0], "name", "").lower()
    return Execution(
        "categories",
        headline=templates.HEADLINE_CATEGORIES,
        facts=facts,
        text=f"Больше всего уходит на «{top}». {templates.CATEGORIES_TAIL}",
        tool_calls=[{"name": "categories", "args": {"period": "2 месяца"}}],
    )


# ------------------------------------------------------------------ add_entry

def _add_entry(label: str, slots: Slots, sit: Any) -> Execution:
    if not slots.amount:
        return Execution("clarify", templates.HEADLINE_CLARIFY, text=templates.CLARIFY_AMOUNT)

    kind = "income" if label == "add_income" else "spend"
    when = slots.date or _get(sit, "today")
    entry = {
        "type": kind,
        "name": slots.name or ("Поступление" if kind == "income" else "Трата"),
        "amount": int(slots.amount),
        "date": _iso(when),
        "confirmed": bool(slots.confirmed) if kind == "income" else True,
        "category": slots.category if kind == "spend" else None,
    }
    facts = [
        _fact("Тип", "Доход" if kind == "income" else "Разовая трата"),
        _fact("Сумма", port.rub(int(slots.amount))),
        _fact("Дата", port.day(when)),
    ]
    if kind == "income":
        facts.append(_fact("Надёжность",
                           "точно придёт" if slots.confirmed else "может не прийти",
                           None if slots.confirmed else TONE_BAD))
    else:
        facts.append(_fact("Категория", slots.category or "Прочее"))

    return Execution(
        "add_entry",
        headline=templates.HEADLINE_ENTRY,
        facts=facts,
        text=templates.ENTRY_TAIL,
        tool_calls=[{"name": "parse_entry", "args": {"type": kind, "amount": int(slots.amount),
                                                    "date": _iso(when)}}],
        actions=[{"kind": "save_entry", "label": "Сохранить", "payload": entry}],
        proposed_entry=entry,
    )


# ------------------------------------------------------------------ остальное

def _term(message: str) -> Execution:
    found = knowledge.find(message)
    if found is None:
        return Execution("term", text=templates.TERM_NOT_FOUND)
    return Execution(
        "term",
        headline=found.term,
        text=found.definition,
        source=found.source,
        tool_calls=[{"name": "knowledge_search", "args": {"term": found.term}}],
    )


def _invest() -> Execution:
    return Execution(
        "invest_info",
        text=templates.INVEST_INFO,
        tool_calls=[{"name": "policy_check", "args": {"topic": "инвестиции"}}],
        actions=[{"kind": "open_learn", "label": "Как устроены накопления и инвестиции?",
                  "payload": {}}],
    )


def _refusal(label: str) -> Execution:
    text = (templates.REFUSAL_CREDENTIALS if label == "credentials"
            else templates.REFUSAL_MONEY_OPERATION)
    return Execution(
        "refusal",
        headline=templates.HEADLINE_REFUSAL,
        text=text,
        tool_calls=[{"name": "policy_check", "args": {"risk": label}}],
    )


def execute(label: str | None, slots: Slots, sit: Any, purchase: Any = None,
            message: str = "") -> Execution:
    """label + слоты → готовый ответ. Единственная точка входа для orchestrator."""
    if label == "purchase_check":
        return _purchase_check(slots, sit, purchase)
    if label == "forecast":
        return _forecast(sit)
    if label == "explain":
        return _explain(sit)
    if label == "deficit_plan":
        return _deficit_plan(sit, purchase)
    if label == "categories":
        return _categories(sit)
    if label in ("add_spend", "add_income"):
        return _add_entry(label, slots, sit)
    if label == "invest_advice":
        return _invest()
    if label in ("credentials", "money_operation"):
        return _refusal(label)
    if label == "off_topic":
        return Execution("off_topic", text=templates.OFF_TOPIC)
    if label == "term":
        return _term(message)
    # label is None — модель и правила не уверены
    text = templates.CLARIFY_AMOUNT if slots.amount else templates.CLARIFY_UNKNOWN
    return Execution("clarify", headline=templates.HEADLINE_CLARIFY, text=text)
