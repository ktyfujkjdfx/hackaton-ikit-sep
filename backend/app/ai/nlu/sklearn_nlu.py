"""Наша модель шага 1: TF-IDF (char_wb) + логистическая регрессия, обученная в training/train_sklearn.py.

Артефакт: app/ai/models/intent_sklearn.joblib. На сервере нужны только scikit-learn, joblib и numpy.
"""
from __future__ import annotations

import logging
from pathlib import Path

from app.ai.nlu.labels import LABELS
from app.ai.parse import normalize

log = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "intent_sklearn.joblib"

_pipeline = None
_loaded = False


def available() -> bool:
    return _load() is not None


def _load():
    """Ленивая загрузка: без модели или без scikit-learn просто отдаём None, сервер живёт дальше."""
    global _pipeline, _loaded
    if _loaded:
        return _pipeline
    _loaded = True
    if not MODEL_PATH.exists():
        log.warning("sklearn-модель не найдена: %s", MODEL_PATH)
        return None
    try:
        import joblib

        _pipeline = joblib.load(MODEL_PATH)
    except Exception:  # noqa: BLE001 — на демо важнее живой сервер, чем точная причина
        log.exception("не удалось загрузить sklearn-модель")
        _pipeline = None
    return _pipeline


def predict(text: str) -> tuple[str, float] | None:
    """(label, confidence) или None, если модель недоступна."""
    pipeline = _load()
    if pipeline is None:
        return None
    clean = normalize(text)
    if not clean:
        return None
    probabilities = pipeline.predict_proba([clean])[0]
    best = int(probabilities.argmax())
    label = str(pipeline.classes_[best])
    if label not in LABELS:
        log.error("модель вернула неизвестную метку %r", label)
        return None
    return label, float(probabilities[best])
