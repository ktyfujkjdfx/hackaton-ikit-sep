"""Выбор модели и предсказание намерения (docs/plans/ROLE_B_ai.md, B.2).

1. NLU_MODE=onnx и модель загрузилась → ONNX; иначе sklearn; иначе rules.
2. confidence < NLU_MIN_CONFIDENCE → спрашиваем правила; сработали → берём их (mode="rules").
3. Никто не уверен → label=None, orchestrator отвечает clarify.
4. Контекст: фраза без глагола, но с суммой («а за 1000?»), а прошлый intent — purchase_check → purchase_check.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

from app.ai.nlu import onnx_nlu, rules, sklearn_nlu
from app.ai.nlu.labels import LABELS, LABEL_TO_ID, LABEL_TO_INTENT  # noqa: F401 — реэкспорт
from app.ai.parse import normalize, parse_amount

DEFAULT_MIN_CONFIDENCE = 0.6

# «а за 1000?», «а если 500», «а 2000?» — уточнение суммы к прошлому вопросу
FOLLOW_UP_RE = re.compile(r"^(?:а|ну|и)?\s*(?:если|за|на|по)?\s*[\d\s.,]+(?:к|k|тыс\w*|т\.?р\.?|р|руб\w*|₽)?\s*\??$")


@dataclass
class Prediction:
    label: str | None
    confidence: float
    mode: str  # onnx | sklearn | rules | context


def min_confidence() -> float:
    try:
        return float(os.getenv("NLU_MIN_CONFIDENCE", DEFAULT_MIN_CONFIDENCE))
    except ValueError:
        return DEFAULT_MIN_CONFIDENCE


def current_mode() -> str:
    """Каким слоем реально отвечаем сейчас — это же показывает /api/health."""
    requested = os.getenv("NLU_MODE", "sklearn").strip().lower()
    if requested == "rules":
        return "rules"
    if requested == "onnx" and onnx_nlu.available():
        return "onnx"
    if sklearn_nlu.available():
        return "sklearn"
    return "rules"


def _model_predict(text: str, mode: str) -> tuple[str, float] | None:
    if mode == "onnx":
        return onnx_nlu.predict(text)
    if mode == "sklearn":
        return sklearn_nlu.predict(text)
    return None


def _field(item, name: str):
    return item.get(name) if isinstance(item, dict) else getattr(item, name, None)


def _last_intent(history: list | None) -> str | None:
    """О чём шла речь до этого.

    Фронт по контракту присылает только {role, text}, поэтому метку берём из ассистента,
    если она есть, а иначе распознаём прошлый вопрос пользователя правилами.
    """
    for item in reversed(history or []):
        if _field(item, "role") == "assistant":
            label = _field(item, "label") or _field(item, "intent")
            if label:
                return str(label)
    for item in reversed(history or []):
        if _field(item, "role") == "user":
            previous = rules.predict(str(_field(item, "text") or ""))
            return previous[0] if previous else None
    return None


def _is_follow_up(text: str) -> bool:
    clean = normalize(text)
    return bool(clean) and bool(FOLLOW_UP_RE.match(clean)) and parse_amount(text) is not None


def predict(text: str, history: list | None = None) -> Prediction:
    mode = current_mode()

    # Контекст сильнее модели: «а за 1000?» после проверки покупки — снова проверка покупки
    if _is_follow_up(text) and _last_intent(history) in ("purchase_check", "add_spend", "add_income"):
        return Prediction(_last_intent(history), 1.0, "context")

    # Только сумма и ничего больше («4000») — всегда уточняем, как в прототипе
    if _is_follow_up(text):
        return Prediction(None, 0.0, mode)

    guess = _model_predict(text, mode)
    if guess is not None and guess[1] >= min_confidence():
        return Prediction(guess[0], guess[1], mode)

    fallback = rules.predict(text)
    if fallback is not None:
        return Prediction(fallback[0], fallback[1], "rules")

    # Никто не уверен: label=None → orchestrator ответит clarify (B.2, шаг 3)
    return Prediction(None, guess[1] if guess else 0.0, mode)
