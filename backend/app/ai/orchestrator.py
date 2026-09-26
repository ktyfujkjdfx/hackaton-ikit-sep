"""Сборка ответа чата: nlu → parse → execute → explain → guard → ChatResponse (B.2).

Пользователю никогда не показываем исключение — только понятный текст (B.10).
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any

from app.ai import engine_port as port
from app.ai import guard, parse, templates, tools
from app.ai.explain import api_explainer
from app.ai.nlu import predict
from app.ai.schemas import ChatResponse

log = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 2000
# Метки, где текст пишет только шаблон: отказы, обучение и определения не отдаём в API
TEMPLATE_ONLY_INTENTS = ("refusal", "invest_info", "term", "clarify", "off_topic")


def _today(situation: Any) -> date:
    value = getattr(situation, "today", None)
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _response(execution: tools.Execution, mode: str, label: str,
              confidence: float, explainer: str = "templates",
              guarded: bool = False) -> ChatResponse:
    return ChatResponse.model_validate({
        "intent": execution.intent,
        "tool_calls": execution.tool_calls,
        "headline": execution.headline,
        "tone": execution.tone,
        "facts": execution.facts,
        "text": execution.text,
        "source": execution.source,
        "purchase": execution.purchase,
        "proposed_entry": execution.proposed_entry,
        "actions": execution.actions,
        "nlu": {"mode": mode, "label": label, "confidence": round(confidence, 4)},
        "explainer": explainer,
        "guarded": guarded,
    })


def _failure(mode: str, text: str) -> ChatResponse:
    return _response(
        tools.Execution("clarify", templates.HEADLINE_CLARIFY, text=text), mode, "off_topic", 0.0
    )


def handle(request: Any) -> ChatResponse:
    message = (getattr(request, "message", "") or "").strip()
    situation = getattr(request, "situation")
    active_purchase = getattr(request, "purchase", None)
    history = getattr(request, "history", None) or []

    if not message:
        return _failure("rules", templates.CLARIFY_UNKNOWN)
    if len(message) > MAX_MESSAGE_LENGTH:
        message = message[:MAX_MESSAGE_LENGTH]

    prediction = predict(message, history)
    slots = parse.parse(message, prediction.label or "", _today(situation))

    try:
        execution = tools.execute(prediction.label, slots, situation, active_purchase, message)
    except port.EngineUnavailable:
        log.error("движок A недоступен — отвечаю без расчёта")
        return _failure(prediction.mode, templates.ENGINE_UNAVAILABLE)
    except Exception:  # noqa: BLE001 — пользователю показываем текст, не трейс
        log.exception("ошибка выполнения намерения %s", prediction.label)
        return _failure(prediction.mode, templates.FAILURE)

    explainer, guarded = "templates", False
    if execution.intent not in TEMPLATE_ONLY_INTENTS and execution.facts:
        rephrased = api_explainer.rephrase(execution.intent, message, execution.facts)
        if rephrased is not None:
            if guard.check(rephrased, execution.facts, extra=[execution.headline]):
                execution.text = rephrased
                explainer = api_explainer.mode()
            else:
                guarded = True
                explainer = api_explainer.mode()

    return _response(execution, prediction.mode, prediction.reported_label,
                     prediction.confidence, explainer, guarded)
