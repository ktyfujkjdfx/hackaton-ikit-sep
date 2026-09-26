"""Формат промпта генеративного пояснителя — один и тот же при обучении и в сервисе (B.6).

Обучение (`training/gen_chat_dataset.py`) и прод (`local_llm.py`) собирают текст одной
и той же функцией: если формат разъедется, модель на проде увидит не то, на чём училась.
Числа и даты сюда приходят уже готовыми строками из движка A — модель ничего не считает.
"""
from __future__ import annotations

from typing import Any

SYSTEM_PROMPT = (
    "Ты «ФинКом» — помощник студента по деньгам до следующего поступления.\n"
    "Отвечай на русском, простым языком, 1–3 коротких предложения, без эмодзи и приветствий.\n"
    "Все числа и даты бери ТОЛЬКО из блока ФАКТЫ и переписывай их дословно. "
    "Сам ничего не считай и новых чисел не придумывай.\n"
    "Не советуй, во что вкладывать деньги, не решай за пользователя и никогда не спрашивай "
    "пароли, коды из СМС, CVV и номер карты."
)

NO_FACTS = "нет — расчёта в этом ответе нет"


def facts_block(facts: list[dict] | None) -> str:
    """Факты движка как список строк «подпись: значение»."""
    lines = []
    for fact in facts or []:
        label = str(_field(fact, "label") or "").strip()
        value = str(_field(fact, "value") or "").strip()
        if label or value:
            lines.append(f"- {label}: {value}")
    return "\n".join(lines) if lines else NO_FACTS


def user_prompt(message: str, intent: str, headline: str, facts: list[dict] | None) -> str:
    return (
        f"ВОПРОС: {message.strip()}\n"
        f"НАМЕРЕНИЕ: {intent}\n"
        f"ЗАГОЛОВОК: {(headline or '').strip() or 'нет'}\n"
        f"ФАКТЫ:\n{facts_block(facts)}"
    )


def messages(message: str, intent: str, headline: str, facts: list[dict] | None) -> list[dict]:
    """Чат-разметка для tokenizer.apply_chat_template — и при обучении, и при выводе."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt(message, intent, headline, facts)},
    ]


def _field(item: Any, name: str) -> Any:
    if isinstance(item, dict):
        return item.get(name)
    return getattr(item, name, None)
