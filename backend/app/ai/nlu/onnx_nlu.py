"""Наша нейросеть шага 2: rubert-tiny2, дообученная и экспортированная в ONNX (training/export_onnx.py).

На сервере только onnxruntime и tokenizers — ни torch, ни transformers (B.2).
Артефакты: app/ai/models/rubert_intent/{model.onnx, tokenizer.json, labels.json}.
"""
from __future__ import annotations

import json
import logging
import math
from pathlib import Path

from app.ai.nlu.labels import LABELS

log = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).resolve().parent.parent / "models" / "rubert_intent"
MAX_LENGTH = 64

_session = None
_tokenizer = None
_labels: list[str] = []
_loaded = False


def available() -> bool:
    _load()
    return _session is not None


def _load() -> None:
    global _session, _tokenizer, _labels, _loaded
    if _loaded:
        return
    _loaded = True
    model_path = MODEL_DIR / "model.onnx"
    tokenizer_path = MODEL_DIR / "tokenizer.json"
    labels_path = MODEL_DIR / "labels.json"
    if not (model_path.exists() and tokenizer_path.exists() and labels_path.exists()):
        log.info("onnx-модель не найдена в %s", MODEL_DIR)
        return
    try:
        import onnxruntime
        from tokenizers import Tokenizer

        _tokenizer = Tokenizer.from_file(str(tokenizer_path))
        _tokenizer.enable_truncation(MAX_LENGTH)
        _tokenizer.enable_padding(length=None)
        _session = onnxruntime.InferenceSession(
            str(model_path), providers=["CPUExecutionProvider"]
        )
        _labels = json.loads(labels_path.read_text(encoding="utf-8"))
        if list(_labels) != list(LABELS):
            log.error("labels.json не совпадает с labels.py — onnx отключён")
            _session = None
    except Exception:  # noqa: BLE001 — упасть в sklearn лучше, чем уронить сервер
        log.exception("не удалось загрузить onnx-модель")
        _session = None


def _softmax(values: list[float]) -> list[float]:
    top = max(values)
    exponents = [math.exp(v - top) for v in values]
    total = sum(exponents)
    return [e / total for e in exponents]


def predict(text: str) -> tuple[str, float] | None:
    """(label, confidence) или None, если модель недоступна."""
    _load()
    if _session is None or _tokenizer is None:
        return None
    text = text.strip()
    if not text:
        return None
    import numpy as np

    encoding = _tokenizer.encode(text)
    tensors = {
        "input_ids": encoding.ids,
        "attention_mask": encoding.attention_mask,
        "token_type_ids": encoding.type_ids,
    }
    feed = {
        model_input.name: np.array([tensors[model_input.name]], dtype=np.int64)
        for model_input in _session.get_inputs()
        if model_input.name in tensors
    }
    logits = _session.run(None, feed)[0][0]
    probabilities = _softmax([float(v) for v in logits])
    best = max(range(len(probabilities)), key=probabilities.__getitem__)
    return _labels[best], probabilities[best]
