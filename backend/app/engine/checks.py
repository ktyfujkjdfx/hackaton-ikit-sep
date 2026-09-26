"""13 эталонных проверок (раздел 8 CONTRACT.md). Ту же таблицу импортирует tests/test_checks.py."""
import datetime as dt
from dataclasses import dataclass
from typing import Callable

from app.engine.format import days_word, format_date_ru, format_rub
from app.engine.goal import goal_plan
from app.engine.headline import headline, next_income
from app.engine.personas import persona_situation
from app.engine.plans import deficit_plan
from app.engine.purchase import check_purchase
from app.engine.series import series, stats
from app.engine.validate import validate
from app.models import CheckItem, ChecksResult, Purchase, Situation, Spend

TODAY = dt.date(2026, 9, 27)
STATE_RU = {"ok": "хватает", "tight": "впритык", "deficit": "минус", "depends": "зависит от подработки",
            "no_income": "нет даты дохода"}


@dataclass(frozen=True)
class Check:
    id: int
    title: str
    expected: str
    run: Callable[[], tuple[str, bool]]


def D(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def fd(d: dt.date | None) -> str:
    return format_date_ru(d) if d is not None else "нет"


def anya() -> Situation:
    return persona_situation("anya")


def danya() -> Situation:
    return persona_situation("danya")


def empty() -> Situation:
    return Situation(today=TODAY, balance=0, daily=300)


def buy(amount: int) -> Purchase:
    return Purchase(amount=amount, date=TODAY, name="Наушники")


def reduce_option(plan):
    return next(o for o in plan.options if o.kind == "reduce")


def check_1():
    sit = anya()
    st = stats(sit, series(sit))
    h = headline(sit)
    ni = h.next_income
    got = f"{format_rub(st.min)}, {fd(st.min_date)}; {STATE_RU[h.state]}; {ni.name}, {days_word(ni.days)}"
    ok = (st.min == 600 and st.min_date == D("2026-10-09") and h.state == "tight"
          and ni.name == "Стипендия" and ni.days == 13)
    return got, ok


def check_2():
    r = check_purchase(anya(), buy(3000))
    red = reduce_option(r.plan)
    got = (f"минус с {fd(r.after.first_negative_date)}, до {format_rub(r.after.max_deficit)}; "
           f"с {fd(r.earliest_safe_date)}; {red.per_day} ₽/день до {fd(red.until)}, {days_word(red.days)}")
    ok = (r.after.first_negative_date == D("2026-10-05") and r.after.max_deficit == 2400
          and r.earliest_safe_date == D("2026-10-15") and red.per_day == 185
          and red.until == D("2026-10-14") and red.days == 18)
    return got, ok


def check_3():
    r = check_purchase(anya(), buy(1000))
    red = reduce_option(r.plan)
    got = (f"минус с {fd(r.after.first_negative_date)}, до {format_rub(r.after.max_deficit)}; "
           f"с {fd(r.earliest_safe_date)}; {red.per_day} ₽/день")
    ok = (r.after.first_negative_date == D("2026-10-08") and r.after.max_deficit == 400
          and r.earliest_safe_date == D("2026-10-10") and red.per_day == 31)
    return got, ok


def check_4():
    sit = empty()
    st = stats(sit, series(sit))
    h = headline(sit)
    got = f"минус с {fd(st.first_negative_date)}; {STATE_RU[h.state]}"
    ok = st.first_negative_date == TODAY and h.state == "no_income" and next_income(sit) is None
    return got, ok


def check_5():
    sit = empty()
    sit.balance = -500
    errors = validate(sit)
    got = f"ошибка: {errors[0].field}" if errors else "принято"
    return got, bool(errors) and errors[0].field == "balance"


def check_6():
    sit = anya()
    sit.incomes[0].date = D("2026-09-20")
    errors = validate(sit)
    hit = any(e.field == "incomes" and e.index == 0 and e.subfield == "date" for e in errors)
    return ("ошибка: incomes[0].date" if hit else "принято"), hit


def check_7():
    r = check_purchase(anya(), buy(6900))
    return f"минус с {fd(r.after.first_negative_date)}", r.after.first_negative_date == TODAY


def check_8():
    sit = Situation(
        today=TODAY, balance=1000, daily=100,
        incomes=[{"id": "x", "name": "Доход", "amount": 2000, "date": "2026-09-30", "confirmed": True}],
        obligations=[{"id": "y", "name": "Платёж", "amount": 3000, "date": "2026-09-30"}],
    )
    st = stats(sit, series(sit))
    got = f"минус {format_rub(st.first_negative_amount)} с {fd(st.first_negative_date)}"
    return got, st.first_negative_date == D("2026-09-30") and st.first_negative_amount == 400


def check_9():
    r = check_purchase(anya(), buy(50000))
    got = "даты нет" if r.earliest_safe_date is None else f"с {fd(r.earliest_safe_date)}"
    return got, r.earliest_safe_date is None


def check_10():
    sit = danya()
    base = stats(sit, series(sit))
    pess = stats(sit, series(sit, pessimistic=True))
    h = headline(sit)
    got = (f"с подработкой: мин {format_rub(base.min)}, {fd(base.min_date)}; {STATE_RU[h.state]}; "
           f"без: минус с {fd(pess.first_negative_date)}, до {format_rub(pess.max_deficit)}")
    ok = (base.min == 1160 and base.min_date == D("2026-10-19") and h.state == "depends"
          and pess.first_negative_date == D("2026-10-09") and pess.max_deficit == 2840)
    return got, ok


def check_11():
    sit = anya()
    sit.spends.append(Spend(id="s1", name="Такси", amount=800, date=TODAY, category="Транспорт"))
    values = series(sit)
    st = stats(sit, values)
    red = reduce_option(deficit_plan(sit, values, "base"))
    got = f"мин {format_rub(st.min)}; {red.per_day} ₽/день"
    return got, st.min == -200 and red.per_day == 16


def check_12():
    g = goal_plan(anya())
    got = f"{format_rub(g.monthly_surplus)}/мес, к {fd(g.eta)}, опоздание {days_word(g.late_days)}"
    return got, g.monthly_surplus == 1800 and g.eta == D("2027-06-04") and g.late_days == 3


def check_13():
    g = goal_plan(anya(), 3000)
    got = f"к {fd(g.eta_with_purchase)}, сдвиг на {days_word(g.shift_days)}"
    return got, g.eta_with_purchase == D("2027-07-24") and g.shift_days == 50


CHECKS: list[Check] = [
    Check(1, "Аня без покупок",
          "минимум 600 ₽, 9 октября; «впритык»; до стипендии 13 дней", check_1),
    Check(2, "Аня покупает наушники за 3 000 ₽ сегодня",
          "минус с 5 октября, до 2 400 ₽; без минуса — с 15 октября; тратить на 185 ₽/день меньше "
          "до 14 октября, 18 дней", check_2),
    Check(3, "Жюри: покупка за 1 000 ₽ сегодня",
          "минус с 8 октября, до 400 ₽; без минуса — с 10 октября; тратить на 31 ₽/день меньше",
          check_3),
    Check(4, "Пустой остаток: 0 ₽, траты 300 ₽/день, поступлений нет",
          "минус с сегодняшнего дня, нет даты дохода", check_4),
    Check(5, "Отрицательная сумма на карте (−500 ₽)",
          "анкета не принимается: ошибка в сумме на карте", check_5),
    Check(6, "Дата стипендии в прошлом (20 сентября)",
          "анкета не принимается: ошибка в дате поступления", check_6),
    Check(7, "Покупка ровно на весь остаток Ани (6 900 ₽)", "минус с сегодняшнего дня", check_7),
    Check(8, "Платёж и поступление в один день: 1 000 ₽, 100 ₽/день, 30 сентября +2 000 и −3 000",
          "минус 400 ₽ с 30 сентября", check_8),
    Check(9, "Покупка за 50 000 ₽ — больше всех денег за 30 дней", "безопасной даты нет", check_9),
    Check(10, "Даня: подработка может не прийти",
          "с подработкой минимум 1 160 ₽ (19 октября); без неё минус с 9 октября, до 2 840 ₽",
          check_10),
    Check(11, "Аня записала «такси 800» сегодня", "минимум −200 ₽; тратить на 16 ₽/день меньше",
          check_11),
    Check(12, "Цель «Ноутбук» без покупки",
          "1 800 ₽ в месяц, накопит к 4 июня 2027 — на 3 дня позже срока", check_12),
    Check(13, "Цель «Ноутбук» с наушниками за 3 000 ₽",
          "накопит к 24 июля 2027, сдвиг на 50 дней", check_13),
]


def run_check(check: Check) -> CheckItem:
    try:
        got, ok = check.run()
    except Exception as exc:  # проверка не должна ронять всю страницу
        got, ok = f"ошибка: {exc}", False
    return CheckItem(id=check.id, title=check.title, expected=check.expected, got=got, ok=ok)


def run_checks() -> ChecksResult:
    items = [run_check(c) for c in CHECKS]
    return ChecksResult(passed=sum(i.ok for i in items), total=len(items), items=items)
