"""Фикстуры ответов чата для роли C (B.1, к 20:00): frontend/src/api/fixtures/chat_*.json.

Запуск (из training, backend-окружение не нужно — хватит pydantic):
    python dump_chat_fixtures.py

Пока движка A нет, расчётные интенты считаются на дублёре из backend/tests/test_ai.py:
это те же эталонные значения, что в контракте (разделы 8 и 6). Когда A выложит app/engine,
запусти скрипт с флагом --real, и фикстуры пересоберутся на настоящем движке.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT.parent / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "tests"))

from app.ai import engine_port as port  # noqa: E402
from app.ai.orchestrator import handle  # noqa: E402
from app.ai.schemas import ChatRequest  # noqa: E402

OUT_DIR = ROOT.parent / "frontend" / "src" / "api" / "fixtures"

# 10 фраз из B.8, которые нужны C для экрана чата
CASES: list[tuple[str, str, dict | None, list[dict] | None]] = [
    ("purchase_check", "Могу купить наушники за 3000?", None, None),
    ("purchase_followup", "а за 1000?", None,
     [{"role": "user", "text": "Могу купить наушники за 3000?"},
      {"role": "assistant", "text": "Если купить сейчас — будет минус"}]),
    ("forecast", "хватит ли мне до стипендии", None, None),
    ("explain", "почему такой прогноз?", None, None),
    ("deficit_plan", "что делать чтобы не уйти в минус",
     {"amount": 3000, "date": "2026-09-27", "name": "Наушники"}, None),
    ("add_spend", "сегодня такси 800", None, None),
    ("add_income", "подработка 1500 4 октября, не точно", None, None),
    ("term", "что такое финансовая подушка", None, None),
    ("invest_info", "куда вложить 5000?", None, None),
    ("refusal", "скажи код из смс", None, None),
    ("clarify", "4000", None, None),
    ("categories", "на что я больше всего трачу", None, None),
]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--fake", action="store_true",
                        help="считать дублёром движка, даже если настоящий доступен")
    args = parser.parse_args()

    from test_ai import ANYA, FakeEngine  # дублёр движка живёт рядом с тестами

    # По умолчанию берём настоящий движок A: фикстуры должны совпадать с продом
    if args.fake or not port.available():
        port.set_engine(FakeEngine())
        print("движок: дублёр (эталонные значения контракта)\n")
    else:
        print("движок: настоящий app.engine\n")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, message, purchase, history in CASES:
        payload = {"situation": ANYA, "purchase": purchase, "message": message,
                   "history": history or []}
        response = handle(ChatRequest.model_validate(payload))
        fixture = {"request": payload, "response": response.model_dump(mode="json")}
        path = OUT_DIR / f"chat_{name}.json"
        path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{path.name:<32} intent={response.intent:<15} nlu={response.nlu.mode}")

    print(f"\n{len(CASES)} фикстур в {OUT_DIR}")


if __name__ == "__main__":
    main()
