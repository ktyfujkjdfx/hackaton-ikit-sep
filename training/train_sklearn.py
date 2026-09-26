"""Обучение модели шага 1 (docs/plans/ROLE_B_ai.md, B.4): TF-IDF char_wb + логистическая регрессия.

Запуск:  python train_sklearn.py
Пишет:   ../backend/app/ai/models/intent_sklearn.joblib

Нормализация текста берётся из backend/app/ai/parse.py — ровно та же, что в проде.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "backend"))
from app.ai.parse import normalize  # noqa: E402

DATA_DIR = ROOT / "data"
MODEL_PATH = ROOT.parent / "backend" / "app" / "ai" / "models" / "intent_sklearn.joblib"
SEED = 42


def load(name: str) -> tuple[list[str], list[str]]:
    rows = [json.loads(line) for line in open(DATA_DIR / name, encoding="utf-8")]
    return [normalize(r["text"]) for r in rows], [r["label"] for r in rows]


def build_pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=2000, C=5, class_weight="balanced", random_state=SEED)),
    ])


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    x_train, y_train = load("intents_train.jsonl")
    x_test, y_test = load("intents_test.jsonl")

    pipeline = build_pipeline()
    pipeline.fit(x_train, y_train)

    predicted = pipeline.predict(x_test)
    accuracy = accuracy_score(y_test, predicted)
    macro_f1 = f1_score(y_test, predicted, average="macro")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH, compress=3)
    size_mb = MODEL_PATH.stat().st_size / 1024 / 1024

    print(f"train: {len(x_train)}  test: {len(x_test)}")
    print(f"accuracy: {accuracy:.4f}  macro-F1: {macro_f1:.4f}")
    print(f"модель: {MODEL_PATH}  ({size_mb:.2f} МБ)")


if __name__ == "__main__":
    main()
