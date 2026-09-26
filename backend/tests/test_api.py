import datetime as dt

import pytest
from fastapi.testclient import TestClient

from app.engine.personas import load_personas
from app.main import app
from app.models import ChecksResult, Dashboard, PersonaDetail, PurchaseCheck

client = TestClient(app)
ANYA = load_personas()["anya"]["situation"]
DANYA = load_personas()["danya"]["situation"]
BUY_3000 = {"amount": 3000, "date": "2026-09-27", "name": "Наушники"}


def test_health():
    body = client.get("/api/health").json()
    assert body["ok"] is True
    assert body["nlu"] in ("onnx", "sklearn", "rules")
    assert body["explain"] in ("templates", "yandex", "anthropic")


def test_personas_list():
    body = client.get("/api/personas").json()
    assert [p["id"] for p in body] == ["anya", "danya"]
    assert set(body[0]) == {"id", "title", "subtitle"}


def test_persona_detail():
    r = client.get("/api/personas/anya")
    assert r.status_code == 200
    p = PersonaDetail.model_validate(r.json())
    assert p.who == "Аня · 1 курс · общежитие" and p.situation.balance == 6900
    assert r.json()["situation"]["incomes"][0]["date"] == "2026-10-10"


def test_persona_unknown_404():
    assert client.get("/api/personas/nobody").status_code == 404


def test_validate_ok_and_errors():
    assert client.post("/api/validate", json={"situation": ANYA}).json() == {"ok": True, "errors": []}
    body = client.post("/api/validate", json={"situation": {**ANYA, "balance": -500}}).json()
    assert body["ok"] is False and body["errors"][0]["field"] == "balance"


def test_dashboard_anya():
    r = client.post("/api/dashboard", json={"situation": ANYA, "purchase": None})
    assert r.status_code == 200
    d = Dashboard.model_validate(r.json())
    assert d.headline.min_balance == 600 and d.headline.state == "tight"
    assert r.json()["scenarios"]["base"]["days"][0] == {"date": "2026-09-27", "balance": 6600}


def test_dashboard_without_purchase_field():
    assert client.post("/api/dashboard", json={"situation": DANYA}).status_code == 200


def test_dashboard_with_purchase():
    r = client.post("/api/dashboard", json={"situation": ANYA, "purchase": BUY_3000})
    body = r.json()
    assert body["purchase"]["earliest_safe_date"] == "2026-10-15"
    assert body["purchase"]["plan"]["options"][1] == {
        "kind": "reduce", "per_day": 185, "new_daily": 115, "until": "2026-10-14", "days": 18,
        "possible": True, "ease": "hard", "flexible_per_day": 60}


def test_dashboard_422_errors_format():
    r = client.post("/api/dashboard", json={"situation": {**ANYA, "balance": -500}})
    assert r.status_code == 422
    assert r.json() == {"errors": [{
        "field": "balance", "index": None, "subfield": None,
        "message": "Сумма не может быть отрицательной. Если на карте минус по кредитке — "
                   "укажи 0 и добавь долг как платёж."}]}


def test_purchase_check():
    r = client.post("/api/purchase/check", json={"situation": ANYA, "purchase": BUY_3000})
    assert r.status_code == 200
    pc = PurchaseCheck.model_validate(r.json())
    assert pc.verdict == "deficit" and pc.after.max_deficit == 2400
    assert pc.goal.eta_with_purchase == dt.date(2027, 7, 24)


@pytest.mark.parametrize("amount", [0, -100])
def test_purchase_check_non_positive_amount(amount):
    r = client.post("/api/purchase/check",
                    json={"situation": ANYA, "purchase": {**BUY_3000, "amount": amount}})
    assert r.status_code == 422
    assert r.json()["errors"][0]["field"] == "purchase"
    assert "больше нуля" in r.json()["errors"][0]["message"]


def test_purchase_check_beyond_horizon():
    r = client.post("/api/purchase/check",
                    json={"situation": ANYA, "purchase": {**BUY_3000, "date": "2026-11-15"}})
    assert r.status_code == 422
    assert r.json()["errors"][0]["message"] == "Можно проверить покупку в ближайшие 30 дней."


def test_purchase_check_requires_purchase():
    r = client.post("/api/purchase/check", json={"situation": ANYA})
    assert r.status_code == 422
    assert r.json()["errors"][0]["field"] == "purchase"


def test_malformed_body_uses_errors_format():
    bad = {**ANYA, "incomes": [{**ANYA["incomes"][0], "amount": "много"}]}
    r = client.post("/api/dashboard", json={"situation": bad})
    assert r.status_code == 422
    err = r.json()["errors"][0]
    assert (err["field"], err["index"], err["subfield"]) == ("incomes", 0, "amount")


def test_dashboard_goal_already_reached_422():
    sit = {**ANYA, "goal": {**ANYA["goal"], "current": 40000}}
    r = client.post("/api/dashboard", json={"situation": sit})
    assert r.status_code == 422 and r.json()["errors"][0]["field"] == "goal"


def test_checks_endpoint_13_of_13():
    r = client.get("/api/checks")
    result = ChecksResult.model_validate(r.json())
    assert (result.passed, result.total) == (13, 13)
    assert result.items[0].got == "600 ₽, 9 октября; впритык; Стипендия, 13 дней"


def test_cors_allows_frontend_origin():
    r = client.options("/api/checks", headers={"Origin": "http://localhost:5173",
                                              "Access-Control-Request-Method": "GET"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_fractional_amount_asks_for_whole_rubles():
    r = client.post("/api/dashboard", json={"situation": {**ANYA, "daily": 250.5}})
    assert r.status_code == 422
    assert r.json()["errors"][0]["field"] == "daily"
    assert "целых рублях" in r.json()["errors"][0]["message"]


def test_unreachable_goal_is_not_500():
    sit = {**ANYA, "daily": 359, "goal": {**ANYA["goal"], "target": 10_000_000}}
    r = client.post("/api/dashboard", json={"situation": sit, "purchase": BUY_3000})
    assert r.status_code == 200
    assert r.json()["goal"]["eta"] is None


def test_empty_body_is_422_errors():
    r = client.post("/api/dashboard", json={})
    assert r.status_code == 422 and "errors" in r.json()


SPEND = {"id": "s1", "name": "Такси", "amount": 800, "date": "2026-09-27", "category": "Транспорт"}


@pytest.mark.parametrize("amount", [0, -5000])
def test_negative_spend_is_422_not_extra_money(amount):
    sit = {**ANYA, "spends": [{**SPEND, "amount": amount}]}
    for path, body in [("/api/dashboard", {"situation": sit}),
                       ("/api/purchase/check", {"situation": sit, "purchase": BUY_3000})]:
        r = client.post(path, json=body)
        assert r.status_code == 422, path
        err = r.json()["errors"][0]
        assert (err["field"], err["index"], err["subfield"]) == ("spends", 0, "amount")
    body = client.post("/api/validate", json={"situation": sit}).json()
    assert body["ok"] is False and body["errors"][0]["field"] == "spends"


def test_positive_spend_still_works():
    r = client.post("/api/dashboard", json={"situation": {**ANYA, "spends": [SPEND]}})
    assert r.status_code == 200 and r.json()["headline"]["min_balance"] == -200


@pytest.mark.parametrize("field,amount", [("incomes", 0), ("incomes", -3200),
                                          ("obligations", 0), ("obligations", -1800)])
def test_non_positive_income_or_obligation_is_422(field, amount):
    items = [{**ANYA[field][0], "amount": amount}] + ANYA[field][1:]
    r = client.post("/api/dashboard", json={"situation": {**ANYA, field: items}})
    assert r.status_code == 422
    err = r.json()["errors"][0]
    assert (err["field"], err["index"], err["subfield"]) == (field, 0, "amount")


def test_malformed_spend_maps_to_spends_field():
    sit = {**ANYA, "spends": [{**SPEND, "amount": "много"}]}
    err = client.post("/api/dashboard", json={"situation": sit}).json()["errors"][0]
    assert (err["field"], err["index"], err["subfield"]) == ("spends", 0, "amount")
