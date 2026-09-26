"""Пояснитель (B.6): кто-то переписывает готовые факты движка в 1–2 предложения.

EXPLAIN_MODE выбирает кто:
    templates — никто, текст берётся из шаблонов (по умолчанию и на Render);
    local     — наша дообученная модель, локально, без интернета и ключей (local_llm.py);
    yandex | anthropic — готовый API.

Ошибка, таймаут, нет ключа или нет модели → возвращаем None, и orchestrator берёт шаблон.
Числа пояснитель не придумывает: за этим следит guard.py.
"""
from __future__ import annotations

import logging
import os

log = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Ты пишешь 1–2 коротких предложения простым языком для студента по готовому результату расчёта.\n"
    "Используй ТОЛЬКО числа и даты из списка фактов, дословно. Новых чисел не придумывай.\n"
    "Не советуй, куда вкладывать. Не решай за пользователя. Без приветствий и эмодзи."
)
USER_PROMPT = "Интент: {intent}. Вопрос: «{message}». Факты: {facts}"


def mode() -> str:
    return os.getenv("EXPLAIN_MODE", "templates").strip().lower()


def timeout_seconds() -> float:
    try:
        return float(os.getenv("LLM_TIMEOUT_S", "6"))
    except ValueError:
        return 6.0


def _facts_line(facts: list[dict]) -> str:
    return "; ".join(f"{f.get('label')}: {f.get('value')}" for f in facts or [])


def _yandex(prompt: str) -> str | None:
    api_key, folder_id = os.getenv("YANDEX_API_KEY"), os.getenv("YANDEX_FOLDER_ID")
    if not (api_key and folder_id):
        return None
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url="https://llm.api.cloud.yandex.net/v1",
                    timeout=timeout_seconds())
    completion = client.chat.completions.create(
        model=f"gpt://{folder_id}/yandexgpt/latest",
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=200,
    )
    return completion.choices[0].message.content


def _anthropic(prompt: str) -> str | None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    from anthropic import Anthropic

    client = Anthropic(api_key=api_key, timeout=timeout_seconds())
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in message.content if block.type == "text")


def rephrase(intent: str, message: str, facts: list[dict],
             headline: str = "") -> str | None:
    """Текст пояснителя или None. None — это норма: значит, показываем шаблон."""
    explain_mode = mode()
    if explain_mode == "local":
        from app.ai.explain import local_llm

        return local_llm.generate(message, intent, headline, facts, timeout_seconds())
    if explain_mode not in ("yandex", "anthropic"):
        return None
    prompt = USER_PROMPT.format(intent=intent, message=message, facts=_facts_line(facts))
    try:
        text = _yandex(prompt) if explain_mode == "yandex" else _anthropic(prompt)
    except Exception:  # noqa: BLE001 — любая ошибка API не должна ломать ответ
        log.exception("пояснитель %s недоступен — беру шаблон", explain_mode)
        return None
    return (text or "").strip() or None
