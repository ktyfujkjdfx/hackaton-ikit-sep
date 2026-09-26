"""Поговорить с помощником в консоли — тем же кодом, что и сайт (B.9).

Запуск (окружение .venv-llm, модель уже обучена):
    python chat_llm.py                      # персона Аня, ответы пишет наша модель
    python chat_llm.py --persona danya
    python chat_llm.py --templates          # для сравнения: те же ответы шаблонами

Это не отдельный «чат-бот»: вопрос идёт через настоящий /api/chat — классификатор намерений,
движок A считает суммы, наша модель только пересказывает готовые факты, guard проверяет числа.
Видно, чем ответила модель (explainer) и не отрезал ли её guard.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "backend"))

DEFAULT_ADAPTER = ROOT / "runs" / "dotyanu_llm"
MERGED = ROOT / "runs" / "dotyanu_llm_merged"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--persona", default="anya")
    parser.add_argument("--templates", action="store_true", help="без модели, только шаблоны")
    parser.add_argument("--adapter", default=str(DEFAULT_ADAPTER))
    parser.add_argument("--load-4bit", action="store_true", help="для слабой видеокарты")
    args = parser.parse_args()

    if args.templates:
        os.environ["EXPLAIN_MODE"] = "templates"
    else:
        os.environ["EXPLAIN_MODE"] = "local"
        if MERGED.exists():
            os.environ["LLM_MODEL_PATH"] = str(MERGED)
        else:
            os.environ["LLM_ADAPTER_PATH"] = args.adapter
        os.environ["LLM_TIMEOUT_S"] = os.getenv("LLM_TIMEOUT_S", "60")
        if args.load_4bit:
            os.environ["LLM_LOAD_4BIT"] = "1"

    from app.ai.orchestrator import handle
    from app.ai.schemas import ChatRequest
    from app.engine.personas import persona_situation

    situation = persona_situation(args.persona).model_dump(mode="json")
    history: list[dict] = []
    print(f"персона: {args.persona} · пояснитель: {os.environ['EXPLAIN_MODE']}"
          "\nпиши вопрос, «выход» — закончить\n")

    while True:
        try:
            message = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not message or message.lower() in ("выход", "exit", "quit"):
            break

        response = handle(ChatRequest.model_validate(
            {"situation": situation, "message": message, "history": history[-6:]}))

        print(f"\n[{response.headline or response.intent}]")
        for fact in response.facts:
            print(f"   {fact.label}: {fact.value}")
        print(f"\n{response.text}")
        print(f"   · намерение {response.nlu.label} ({response.nlu.mode}, "
              f"{response.nlu.confidence:.2f}) · пояснитель {response.explainer}"
              f"{' · guard отрезал модель' if response.guarded else ''}\n")

        history.append({"role": "user", "text": message})
        history.append({"role": "assistant", "text": response.text, "label": response.nlu.label})


if __name__ == "__main__":
    main()
