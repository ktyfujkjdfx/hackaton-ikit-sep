"""Демо-персоны. Источник — app/data/personas.json (роль D), значения — раздел 8 CONTRACT.md."""
import json
from functools import lru_cache
from pathlib import Path

from app.models import Situation

PERSONAS_PATH = Path(__file__).resolve().parent.parent / "data" / "personas.json"

# Копия раздела 8 на случай, если personas.json ещё не в ветке. Значения менять нельзя.
_FALLBACK = {
    "anya": {
        "who": "Аня · 1 курс · общежитие", "title": "Аня",
        "subtitle": "1 курс, общежитие, 2 месяца истории",
        "situation": {
            "today": "2026-09-27", "balance": 6900, "daily": 300,
            "incomes": [
                {"id": "i1", "name": "Стипендия", "amount": 3200, "date": "2026-10-10", "confirmed": True},
                {"id": "i2", "name": "Перевод от родителей", "amount": 10000, "date": "2026-10-15",
                 "confirmed": True},
            ],
            "obligations": [
                {"id": "o1", "name": "Подписка на музыку", "amount": 200, "date": "2026-10-01"},
                {"id": "o2", "name": "Связь", "amount": 400, "date": "2026-10-03"},
                {"id": "o3", "name": "Общежитие", "amount": 1800, "date": "2026-10-05"},
            ],
            "spends": [],
            "goal": {"name": "Ноутбук", "target": 40000, "current": 25000, "date": "2027-06-01"},
            "categories": [
                {"name": "Еда", "per_day": 180}, {"name": "Транспорт", "per_day": 60},
                {"name": "Кафе и доставка", "per_day": 40}, {"name": "Прочее", "per_day": 20},
            ],
            "history": [
                {"date": "2026-09-24", "name": "Продукты у общежития", "amount": -640, "category": "Еда"},
                {"date": "2026-09-22", "name": "Доставка еды", "amount": -520, "category": "Кафе и доставка"},
                {"date": "2026-09-19", "name": "Кроссовки", "amount": -4200, "category": "Прочее"},
                {"date": "2026-09-15", "name": "Перевод от родителей", "amount": 10000, "category": "Доход"},
                {"date": "2026-09-10", "name": "Стипендия", "amount": 3200, "category": "Доход"},
                {"date": "2026-09-05", "name": "Общежитие", "amount": -1800, "category": "Обязательное"},
                {"date": "2026-09-03", "name": "Связь", "amount": -400, "category": "Обязательное"},
                {"date": "2026-09-01", "name": "Подписка на музыку", "amount": -200, "category": "Обязательное"},
            ],
        },
    },
    "danya": {
        "who": "Даня · 2 курс · подработка курьером", "title": "Даня",
        "subtitle": "доход без графика — прогноз в двух вариантах",
        "situation": {
            "today": "2026-09-27", "balance": 5000, "daily": 280,
            "incomes": [
                {"id": "i1", "name": "Подработка курьером", "amount": 4000, "date": "2026-10-03",
                 "confirmed": False},
                {"id": "i2", "name": "Стипендия", "amount": 2800, "date": "2026-10-20", "confirmed": True},
            ],
            "obligations": [
                {"id": "o1", "name": "Проездной", "amount": 900, "date": "2026-09-30"},
                {"id": "o2", "name": "Связь", "amount": 350, "date": "2026-10-02"},
                {"id": "o3", "name": "Подписка на кино", "amount": 150, "date": "2026-10-08"},
            ],
            "spends": [],
            "goal": {"name": "Билет домой на Новый год", "target": 12000, "current": 3000,
                     "date": "2026-12-20"},
            "categories": [
                {"name": "Еда", "per_day": 170}, {"name": "Кафе и доставка", "per_day": 50},
                {"name": "Транспорт", "per_day": 30}, {"name": "Прочее", "per_day": 30},
            ],
            "history": [
                {"date": "2026-09-25", "name": "Подработка курьером", "amount": 2600, "category": "Доход"},
                {"date": "2026-09-23", "name": "Кафе с друзьями", "amount": -1900,
                 "category": "Кафе и доставка"},
                {"date": "2026-09-20", "name": "Стипендия", "amount": 2800, "category": "Доход"},
                {"date": "2026-09-18", "name": "Продукты", "amount": -760, "category": "Еда"},
                {"date": "2026-09-11", "name": "Подработка курьером", "amount": 1500, "category": "Доход"},
                {"date": "2026-09-08", "name": "Подписка на кино", "amount": -150, "category": "Обязательное"},
                {"date": "2026-09-02", "name": "Связь", "amount": -350, "category": "Обязательное"},
            ],
        },
    },
}


@lru_cache
def load_personas() -> dict:
    if PERSONAS_PATH.exists():
        return json.loads(PERSONAS_PATH.read_text(encoding="utf-8"))
    return _FALLBACK


def persona_situation(persona_id: str) -> Situation:
    """Новая копия ситуации персоны — её можно менять в сценарии."""
    return Situation.model_validate(load_personas()[persona_id]["situation"])
