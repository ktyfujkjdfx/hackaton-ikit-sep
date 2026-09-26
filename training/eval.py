"""Оценка модели (B.4): accuracy, macro-F1, отчёт по классам, матрица ошибок в png.

Запуск:  python eval.py                       # на intents_test.jsonl
         python eval.py --holdout             # ещё и на intents_holdout_team.jsonl, если он есть
Пишет:   reports/confusion_<набор>.png, reports/metrics.json

Holdout пишут A и D, он никогда не попадает в train — это главная метрика для жюри (B.10).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import matplotlib
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix, f1_score)

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "backend"))
from app.ai.nlu.labels import LABELS  # noqa: E402
from app.ai.parse import normalize  # noqa: E402

DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"
MODEL_PATH = ROOT.parent / "backend" / "app" / "ai" / "models" / "intent_sklearn.joblib"
HOLDOUT_NAME = "intents_holdout_team.jsonl"


def load(path: Path) -> tuple[list[str], list[str]]:
    rows = [json.loads(line) for line in open(path, encoding="utf-8")]
    return [normalize(r["text"]) for r in rows], [r["label"] for r in rows]


def draw_confusion(y_true: list[str], y_pred: list[str], title: str, path: Path) -> None:
    matrix = confusion_matrix(y_true, y_pred, labels=list(LABELS))
    fig, ax = plt.subplots(figsize=(9, 8))
    ax.imshow(matrix, cmap="Blues")
    ax.set_xticks(range(len(LABELS)), LABELS, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(LABELS)), LABELS, fontsize=8)
    ax.set_xlabel("предсказано")
    ax.set_ylabel("на самом деле")
    ax.set_title(title)
    limit = matrix.max() or 1
    for i in range(len(LABELS)):
        for j in range(len(LABELS)):
            value = matrix[i][j]
            if value:
                ax.text(j, i, str(value), ha="center", va="center", fontsize=8,
                        color="white" if value > limit / 2 else "black")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


class OnnxModel:
    """Обёртка над app.ai.nlu.onnx_nlu — чтобы считать метрики тем же кодом, что в проде."""

    name = "onnx"

    def __init__(self) -> None:
        from app.ai.nlu import onnx_nlu

        if not onnx_nlu.available():
            raise SystemExit("нет models/rubert_intent — сначала запусти export_onnx.py")
        self._onnx = onnx_nlu

    def predict(self, texts: list[str]) -> list[str]:
        return [(self._onnx.predict(text) or ("off_topic", 0.0))[0] for text in texts]


def evaluate(pipeline, path: Path, name: str) -> dict:
    x, y_true = load(path)
    y_pred = list(pipeline.predict(x))
    accuracy = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)

    print(f"\n=== {name} ({len(x)} фраз) ===")
    print(f"accuracy: {accuracy:.4f}   macro-F1: {macro_f1:.4f}")
    print(classification_report(y_true, y_pred, labels=list(LABELS), zero_division=0, digits=3))

    errors = [(t, a, p) for t, a, p in zip(x, y_true, y_pred) if a != p]
    if errors:
        print(f"ошибок: {len(errors)}; первые 15:")
        for text, actual, predicted in errors[:15]:
            print(f"  {actual:>16} → {predicted:<16} {text}")

    draw_confusion(y_true, y_pred, f"Матрица ошибок — {name}", REPORTS_DIR / f"confusion_{name}.png")
    return {"set": name, "size": len(x), "accuracy": round(accuracy, 4),
            "macro_f1": round(macro_f1, 4), "errors": len(errors)}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--holdout", action="store_true", help="оценить ещё и на holdout от A и D")
    parser.add_argument("--onnx", action="store_true", help="те же наборы для нейросети в ONNX")
    args = parser.parse_args()

    models: list[tuple[str, object]] = []
    if MODEL_PATH.exists():
        models.append(("sklearn", joblib.load(MODEL_PATH)))
    elif not args.onnx:
        raise SystemExit(f"нет модели {MODEL_PATH} — сначала запусти train_sklearn.py")
    if args.onnx:
        models.append(("onnx", OnnxModel()))

    sets = [("test", DATA_DIR / "intents_test.jsonl")]
    holdout = DATA_DIR / HOLDOUT_NAME
    if args.holdout:
        if holdout.exists():
            sets.append(("holdout_team", holdout))
        else:
            print(f"\n{HOLDOUT_NAME} ещё не прислали A и D — пропускаю")

    results = []
    for model_name, model in models:
        for set_name, path in sets:
            label = set_name if len(models) == 1 else f"{model_name}_{set_name}"
            result = evaluate(model, path, label)
            result["model"] = model_name
            results.append(result)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "metrics.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nотчёты: {REPORTS_DIR}")


if __name__ == "__main__":
    main()
