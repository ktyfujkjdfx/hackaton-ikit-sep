"""Финальная проверка API: 13 эталонов раздела 8 + крайние случаи. Только HTTP, без импорта движка.

Запуск из backend/:
    python -m scripts.final_check                                  # прод
    python -m scripts.final_check --base http://localhost:8000     # локально
    python -m scripts.final_check --out ../docs/final_check_log.txt
"""
import argparse
import datetime as dt
import json
import sys
import time
import urllib.error
import urllib.request

PROD = "https://dotyanu-api.onrender.com"
TODAY = "2026-09-27"


class Api:
    def __init__(self, base: str):
        self.base = base.rstrip("/") + "/api"

    def call(self, path: str, body: dict | None = None) -> tuple[int, dict]:
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(self.base + path, data=data,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            return e.code, json.load(e)

    def dashboard(self, sit: dict, purchase: dict | None = None) -> tuple[int, dict]:
        return self.call("/dashboard", {"situation": sit, "purchase": purchase})

    def purchase(self, sit: dict, purchase: dict) -> tuple[int, dict]:
        return self.call("/purchase/check", {"situation": sit, "purchase": purchase})

    def chat(self, sit: dict, message: str) -> dict:
        return self.call("/chat", {"situation": sit, "message": message, "history": []})[1]


def buy(amount, date=TODAY):
    return {"amount": amount, "date": date, "name": "Наушники"}


def reduce_of(plan: dict) -> dict:
    return next(o for o in plan["options"] if o["kind"] == "reduce")


def first_error(resp: tuple[int, dict]) -> tuple:
    status, body = resp
    e = body.get("errors", [{}])[0]
    return status, e.get("field"), e.get("index"), e.get("subfield"), e.get("message")


def reference_checks(api: Api, anya: dict, danya: dict):
    """13 эталонов (раздел 8 CONTRACT.md), каждый — через обычные эндпоинты."""
    empty = {"today": TODAY, "balance": 0, "daily": 300}

    def c1():
        h = api.dashboard(anya)[1]["headline"]
        got = (h["min_balance"], h["min_date"], h["state"], h["next_income"]["name"], h["next_income"]["days"])
        return got, (600, "2026-10-09", "tight", "Стипендия", 13)

    def c2():
        p = api.purchase(anya, buy(3000))[1]
        r = reduce_of(p["plan"])
        got = (p["after"]["first_negative_date"], p["after"]["max_deficit"], p["earliest_safe_date"],
               r["per_day"], r["until"], r["days"])
        return got, ("2026-10-05", 2400, "2026-10-15", 185, "2026-10-14", 18)

    def c3():
        p = api.purchase(anya, buy(1000))[1]
        got = (p["after"]["first_negative_date"], p["after"]["max_deficit"], p["earliest_safe_date"],
               reduce_of(p["plan"])["per_day"])
        return got, ("2026-10-08", 400, "2026-10-10", 31)

    def c4():
        d = api.dashboard(empty)[1]
        return (d["scenarios"]["base"]["stats"]["first_negative_date"], d["headline"]["state"]), \
            (TODAY, "no_income")

    def c5():
        return first_error(api.dashboard({**empty, "balance": -500}))[:2], (422, "balance")

    def c6():
        bad = json.loads(json.dumps(anya))
        bad["incomes"][0]["date"] = "2026-09-20"
        return first_error(api.dashboard(bad))[:4], (422, "incomes", 0, "date")

    def c7():
        return api.purchase(anya, buy(6900))[1]["after"]["first_negative_date"], TODAY

    def c8():
        sit = {"today": TODAY, "balance": 1000, "daily": 100,
               "incomes": [{"id": "x", "name": "Доход", "amount": 2000, "date": "2026-09-30", "confirmed": True}],
               "obligations": [{"id": "y", "name": "Платёж", "amount": 3000, "date": "2026-09-30"}]}
        st = api.dashboard(sit)[1]["scenarios"]["base"]["stats"]
        return (st["first_negative_date"], st["first_negative_amount"]), ("2026-09-30", 400)

    def c9():
        return api.purchase(anya, buy(50000))[1]["earliest_safe_date"], None

    def c10():
        d = api.dashboard(danya)[1]
        b, p = d["scenarios"]["base"]["stats"], d["scenarios"]["pessimistic"]["stats"]
        got = (b["min"], b["min_date"], d["headline"]["state"], p["first_negative_date"], p["max_deficit"])
        return got, (1160, "2026-10-19", "depends", "2026-10-09", 2840)

    def c11():
        taxi = {**anya, "spends": [{"id": "s", "name": "Такси", "amount": 800, "date": TODAY,
                                    "category": "Транспорт"}]}
        d = api.dashboard(taxi)[1]
        return (d["headline"]["min_balance"], reduce_of(d["deficit_plan"])["per_day"]), (-200, 16)

    def c12():
        g = api.dashboard(anya)[1]["goal"]
        return (g["monthly_surplus"], g["eta"], g["late_days"]), (1800, "2027-06-04", 3)

    def c13():
        g = api.dashboard(anya, buy(3000))[1]["goal"]
        return (g["eta_with_purchase"], g["shift_days"]), ("2027-07-24", 50)

    return [
        ("Аня без покупок", c1), ("Аня: покупка 3 000 сегодня", c2),
        ("Аня: покупка 1 000 сегодня (сумма от жюри)", c3), ("Пусто: 0 ₽, 300 ₽/день, без поступлений", c4),
        ("На карте −500 ₽", c5), ("Дата стипендии в прошлом (20 сентября)", c6),
        ("Покупка на весь остаток (6 900 ₽)", c7), ("Доход +2 000 и платёж −3 000 в один день", c8),
        ("Покупка 50 000 ₽", c9), ("Даня: подработка может не прийти", c10),
        ("Аня + такси 800 ₽ сегодня", c11), ("Цель «Ноутбук» без покупки", c12),
        ("Цель «Ноутбук» с покупкой 3 000 ₽", c13),
    ]


def edge_checks(api: Api, anya: dict):
    """Крайние случаи, которых нет среди 13 эталонов."""
    goal = anya["goal"]

    def spend(amount):
        return {**anya, "spends": [{"id": "s", "name": "Трата", "amount": amount, "date": TODAY,
                                    "category": "Прочее"}]}

    def with_first(section, amount):
        items = [{**anya[section][0], "amount": amount}] + anya[section][1:]
        return {**anya, section: items}

    def e_unreachable():
        s, d = api.dashboard({**anya, "daily": 359, "goal": {**goal, "target": 10_000_000}}, buy(3000))
        return (s, d["goal"]["monthly_surplus"], d["goal"]["eta"], d["goal"]["eta_with_purchase"]), \
            (200, 30, None, None)

    def e_fraction():
        return first_error(api.dashboard({**anya, "daily": 250.5})), \
            (422, "daily", None, None, "Укажите сумму в целых рублях, без копеек.")

    def err(field, sub, msg, index=0):
        return (422, field, index, sub, msg)

    cases = [
        ("Недостижимая цель: 30 ₽ в месяц на 10 000 000 ₽", e_unreachable),
        ("Дробная сумма: 250,5 ₽ в день", e_fraction),
        ("Трата 0 ₽", lambda: (first_error(api.dashboard(spend(0))),
                               err("spends", "amount", "Сумма траты должна быть больше нуля."))),
        ("Трата −5 000 ₽", lambda: (first_error(api.dashboard(spend(-5000))),
                                    err("spends", "amount", "Сумма траты должна быть больше нуля."))),
        ("Доход 0 ₽", lambda: (first_error(api.dashboard(with_first("incomes", 0))),
                               err("incomes", "amount", "Сумма поступления должна быть больше нуля."))),
        ("Доход −3 200 ₽", lambda: (first_error(api.dashboard(with_first("incomes", -3200))),
                                    err("incomes", "amount", "Сумма поступления должна быть больше нуля."))),
        ("Платёж −1 800 ₽", lambda: (first_error(api.dashboard(with_first("obligations", -1800))),
                                     err("obligations", "amount", "Сумма платежа должна быть больше нуля."))),
        ("Покупка 0 ₽", lambda: (first_error(api.purchase(anya, buy(0))),
                                 err("purchase", "amount", "Сумма покупки должна быть больше нуля.", None))),
        ("Покупка за горизонтом (27 октября)", lambda: (
            first_error(api.purchase(anya, buy(100, "2026-10-27"))),
            err("purchase", "date", "Можно проверить покупку в ближайшие 30 дней.", None))),
        ("Покупка в последний день горизонта (26 октября)", lambda: (
            (lambda r: (r[0], r[1]["verdict"]))(api.purchase(anya, buy(100, "2026-10-26"))), (200, "tight"))),
        ("Цель уже накоплена", lambda: (first_error(api.dashboard({**anya, "goal": {**goal, "current": 40000}}))[:2],
                                        (422, "goal"))),
        ("Текст вместо суммы", lambda: (first_error(api.dashboard({**anya, "balance": "много"}))[:2],
                                        (422, "balance"))),
        ("Траты 0 ₽ в день", lambda: ((lambda d: (d["headline"]["state"], d["headline"]["days_of_spending_left"]))(
            api.dashboard({**anya, "daily": 0})[1]), ("ok", None))),
        ("Нет платежей и цели", lambda: ((lambda d: (d["money_types"]["stable_expenses"]["total"], d["goal"]))(
            api.dashboard({**anya, "obligations": [], "goal": None})[1]), (0, None))),
        ("Все поступления «может не прийти»", lambda: ((lambda h: (h["state"], h["next_confirmed_income"]))(
            api.dashboard({**anya, "incomes": [{**i, "confirmed": False} for i in anya["incomes"]]})[1]["headline"]),
            ("depends", None))),
        ("Большие суммы: 10 000 000 ₽ на карте, покупка 9 000 000 ₽", lambda: (
            (lambda p: (p["verdict"], p["after"]["min"]))(
                api.purchase({**anya, "balance": 10_000_000}, buy(9_000_000))[1]), ("ok", 1_000_600 - 6900))),
        ("Чат: код из СМС при битых данных → отказ", lambda: (
            (lambda r: (r["intent"], r["nlu"]["label"]))(api.chat(spend(-50000), "мне прислали код из смс куда его ввести")),
            ("refusal", "credentials"))),
        ("Чат: прогноз при битых данных → просит исправить", lambda: (
            (lambda r: (r["intent"], r["text"]))(api.chat(spend(-50000), "хватит ли мне до стипендии")),
            ("clarify", "Сумма траты должна быть больше нуля."))),
    ]
    return cases


def run(title: str, cases, lines: list[str]) -> tuple[int, int]:
    lines.append(f"\n== {title} ==")
    passed = 0
    for n, (name, fn) in enumerate(cases, 1):
        try:
            got, want = fn()
            ok = got == want
        except Exception as exc:  # в лог, а не падение всего прогона
            got, want, ok = f"ошибка: {exc!r}", "—", False
        passed += ok
        lines.append(f"{n:>2}. {'OK  ' if ok else 'FAIL'} {name}")
        lines.append(f"      получили: {got}")
        if not ok:
            lines.append(f"      ждали:    {want}")
    lines.append(f"-- итого: {passed}/{len(cases)}")
    return passed, len(cases)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=PROD)
    parser.add_argument("--out")
    args = parser.parse_args()
    api = Api(args.base)

    start = time.monotonic()
    status, health = api.call("/health")
    wake = time.monotonic() - start
    anya = api.call("/personas/anya")[1]["situation"]
    danya = api.call("/personas/danya")[1]["situation"]

    lines = [
        "Финальная проверка API «ФинКом»",
        f"Сервер:  {args.base}",
        f"Время:   {dt.datetime.now().astimezone():%Y-%m-%d %H:%M %Z}",
        f"health:  {status} {json.dumps(health, ensure_ascii=False)} (первый ответ за {wake:.1f} с)",
    ]
    p1, t1 = run("13 эталонных сценариев (раздел 8 CONTRACT.md) — через /dashboard и /purchase/check",
                 reference_checks(api, anya, danya), lines)
    checks = api.call("/checks")[1]
    lines.append(f"/api/checks (самопроверка сервера): {checks['passed']}/{checks['total']}")
    p2, t2 = run("Крайние случаи", edge_checks(api, anya), lines)
    ok = p1 == t1 and p2 == t2 and checks["passed"] == checks["total"]
    lines.append(f"\nИТОГ: эталоны {p1}/{t1}, крайние случаи {p2}/{t2} — {'ВСЁ СОВПАЛО' if ok else 'ЕСТЬ РАСХОЖДЕНИЯ'}")

    text = "\n".join(lines) + "\n"
    sys.stdout.write(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
