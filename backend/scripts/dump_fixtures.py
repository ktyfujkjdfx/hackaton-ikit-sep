"""Фикстуры для фронта: ответы API с правильными числами.

Запуск из backend/:  python -m scripts.dump_fixtures
"""
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.engine.personas import load_personas
from app.main import app

OUT = Path(__file__).resolve().parents[2] / "frontend" / "src" / "api" / "fixtures"
TODAY = "2026-09-27"


def main() -> None:
    client = TestClient(app)
    personas = load_personas()
    anya, danya = personas["anya"]["situation"], personas["danya"]["situation"]
    empty = {"today": TODAY, "balance": 0, "daily": 300, "incomes": [], "obligations": [],
             "spends": [], "goal": None, "categories": None, "history": []}

    def buy(amount: int) -> dict:
        return {"amount": amount, "date": TODAY, "name": "Наушники"}

    def dashboard(sit: dict, purchase: dict | None = None):
        return client.post("/api/dashboard", json={"situation": sit, "purchase": purchase})

    responses = {
        "persona_anya": client.get("/api/personas/anya"),
        "persona_danya": client.get("/api/personas/danya"),
        "dashboard_anya": dashboard(anya),
        "dashboard_anya_buy3000": dashboard(anya, buy(3000)),
        "dashboard_anya_buy1000": dashboard(anya, buy(1000)),
        "dashboard_danya": dashboard(danya),
        "dashboard_empty": dashboard(empty),
        "checks": client.get("/api/checks"),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for name, response in responses.items():
        response.raise_for_status()
        text = json.dumps(response.json(), ensure_ascii=False, indent=2) + "\n"
        (OUT / f"{name}.json").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
