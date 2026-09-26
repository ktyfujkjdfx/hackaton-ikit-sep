"""Пересчёт метрик на holdout и обновление model card — одной командой.

Запуск:
    python update_holdout_report.py            # если фраз стало больше — пересчитать и обновить
    python update_holdout_report.py --check     # только сказать, кто уже прислал фразы

Нужен, потому что holdout приходит частями: A прислал 20, от D ждём 40. Скрипт считает обе
модели на всём файле и на части каждого автора, переписывает таблицу в docs/ai/model_card.md
и кладёт свежие матрицы ошибок в docs/ai/.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "backend"))

HOLDOUT = ROOT / "data" / "intents_holdout_team.jsonl"
REPORTS = ROOT / "reports"
DOCS = ROOT.parent / "docs" / "ai"
MODEL_CARD = DOCS / "model_card.md"
EXPECTED_FROM_D = 40
# Таблицу ищем строго под этим заголовком: в model card есть вторая таблица с такой же шапкой
HOLDOUT_HEADING = "### Holdout команды — главная цифра"
TABLE_HEADER = "| Набор | Фраз | sklearn | ONNX |"


def rows() -> list[dict]:
    if not HOLDOUT.exists():
        return []
    return [json.loads(line) for line in open(HOLDOUT, encoding="utf-8") if line.strip()]


def by_author(data: list[dict]) -> Counter:
    return Counter(row.get("author", "?") for row in data)


def score(data: list[dict], model_name: str) -> tuple[int, int, float]:
    """(верно, всего, macro-F1) одной модели на переданных строках."""
    from sklearn.metrics import f1_score

    from app.ai.parse import normalize

    texts = [normalize(row["text"]) for row in data]
    true = [row["label"] for row in data]
    if model_name == "sklearn":
        import joblib

        model = joblib.load(ROOT.parent / "backend" / "app" / "ai" / "models" / "intent_sklearn.joblib")
        predicted = list(model.predict(texts))
    else:
        from app.ai.nlu import onnx_nlu

        predicted = [(onnx_nlu.predict(text) or ("off_topic", 0.0))[0] for text in texts]
    correct = sum(int(p == t) for p, t in zip(predicted, true))
    return correct, len(true), f1_score(true, predicted, average="macro", zero_division=0)


def cell(data: list[dict], model_name: str) -> str:
    if not data:
        return "—"
    correct, total, macro_f1 = score(data, model_name)
    mark = "**" if correct == total else ""
    return f"{mark}{correct} из {total}{mark} (macro-F1 {macro_f1:.2f})".replace(".", ",")


def build_table(data: list[dict]) -> str:
    authors = by_author(data)
    lines = [TABLE_HEADER, "|---|---|---|---|"]
    for author in sorted(authors):
        part = [row for row in data if row.get("author") == author]
        lines.append(f"| holdout от {author} | {len(part)} | "
                     f"{cell(part, 'sklearn')} | {cell(part, 'onnx')} |")
    if "D" not in authors:
        lines.append(f"| holdout от D | ждём {EXPECTED_FROM_D} | — | — |")
    if len(authors) > 1:
        lines.append(f"| **всё вместе** | {len(data)} | "
                     f"{cell(data, 'sklearn')} | {cell(data, 'onnx')} |")
    return "\n".join(lines)


def replace_table(text: str, table: str) -> str:
    """Меняем таблицу под заголовком Holdout.

    Анкер — именно заголовок: в model card есть вторая таблица с такой же шапкой «| Набор | Фраз |»
    (про датасет), и её задевать нельзя.
    """
    pattern = re.compile(
        r"(?P<head>" + re.escape(HOLDOUT_HEADING) + r".*?)^\| Набор \| Фраз \|.*?(?=\n\n)",
        re.S | re.M,
    )
    if not pattern.search(text):
        raise SystemExit(f"в model_card.md нет таблицы под «{HOLDOUT_HEADING}» — обнови вручную")
    return pattern.sub(lambda match: match.group("head") + table, text, count=1)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="только показать, что уже есть")
    args = parser.parse_args()

    data = rows()
    authors = by_author(data)
    print(f"holdout: {len(data)} фраз — " +
          (", ".join(f"{a}: {n}" for a, n in sorted(authors.items())) or "файла нет"))
    if "D" not in authors:
        print(f"фраз от D ещё нет (ждём {EXPECTED_FROM_D}): честное сравнение моделей пока невозможно")
    if args.check:
        return
    if not data:
        raise SystemExit("нечего считать")

    subprocess.run([sys.executable, str(ROOT / "eval.py"), "--holdout", "--onnx"],
                   cwd=ROOT, check=True)

    MODEL_CARD.write_text(replace_table(MODEL_CARD.read_text(encoding="utf-8"), build_table(data)),
                          encoding="utf-8", newline="\n")
    for image in REPORTS.glob("confusion_*holdout*.png"):
        shutil.copy(image, DOCS / image.name)
    print(f"\nтаблица в {MODEL_CARD.name} обновлена, картинки скопированы в docs/ai/")
    print("проверь текст вокруг таблицы: выводы про «слишком мало фраз» могли устареть")


if __name__ == "__main__":
    main()
