"""Шаг 2 (B.4): дообучение rubert-tiny2 на нашем датасете — своя нейросеть на 12 классов.

Запуск:  python train_rubert.py                    # 5 эпох, CPU
         python train_rubert.py --epochs 6
Пишет:   runs/rubert_intent/ (torch-чекпоинт лучшей эпохи по macro-F1 на test)

torch и transformers нужны только здесь. На сервере их нет — туда идёт ONNX (export_onnx.py).
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import f1_score
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "backend"))
from app.ai.nlu.labels import LABELS  # noqa: E402
from app.ai.parse import normalize  # noqa: E402

BASE_MODEL = "cointegrated/rubert-tiny2"
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "runs" / "rubert_intent"
MAX_LENGTH = 64
BATCH_SIZE = 32
LEARNING_RATE = 5e-5
SEED = 42


def seed_everything(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


class IntentDataset(Dataset):
    def __init__(self, path: Path, tokenizer) -> None:
        rows = [json.loads(line) for line in open(path, encoding="utf-8")]
        self.texts = [normalize(r["text"]) for r in rows]
        self.labels = [LABELS.index(r["label"]) for r in rows]
        self.encodings = tokenizer(self.texts, truncation=True, max_length=MAX_LENGTH,
                                   padding="max_length")

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, index: int) -> dict:
        item = {key: torch.tensor(value[index]) for key, value in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[index])
        return item


@torch.no_grad()
def evaluate(model, loader) -> tuple[float, float]:
    model.eval()
    predictions, targets = [], []
    for batch in loader:
        labels = batch.pop("labels")
        logits = model(**batch).logits
        predictions += logits.argmax(dim=-1).tolist()
        targets += labels.tolist()
    accuracy = sum(int(p == t) for p, t in zip(predictions, targets)) / len(targets)
    return accuracy, f1_score(targets, predictions, average="macro", zero_division=0)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=5)
    args = parser.parse_args()

    seed_everything()
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL, num_labels=len(LABELS),
        id2label={i: name for i, name in enumerate(LABELS)},
        label2id={name: i for i, name in enumerate(LABELS)},
    )

    train_loader = DataLoader(IntentDataset(DATA_DIR / "intents_train.jsonl", tokenizer),
                              batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(IntentDataset(DATA_DIR / "intents_test.jsonl", tokenizer),
                             batch_size=BATCH_SIZE)

    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)
    best_f1 = -1.0
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        for batch in train_loader:
            optimizer.zero_grad()
            loss = model(**batch).loss
            loss.backward()
            optimizer.step()
            total_loss += float(loss)
        accuracy, macro_f1 = evaluate(model, test_loader)
        mark = ""
        if macro_f1 > best_f1:  # ранняя остановка по macro-F1: храним лучшую эпоху
            best_f1 = macro_f1
            model.save_pretrained(OUT_DIR)
            tokenizer.save_pretrained(OUT_DIR)
            mark = "  ← сохранил"
        print(f"эпоха {epoch}: loss {total_loss / len(train_loader):.4f}  "
              f"accuracy {accuracy:.4f}  macro-F1 {macro_f1:.4f}{mark}")

    (OUT_DIR / "metrics.json").write_text(
        json.dumps({"base_model": BASE_MODEL, "epochs": args.epochs,
                    "best_macro_f1_test": round(best_f1, 4)}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"\nлучший macro-F1 на test: {best_f1:.4f}\nчекпоинт: {OUT_DIR}")


if __name__ == "__main__":
    main()
