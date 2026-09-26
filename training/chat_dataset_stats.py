"""Паспорт датасета генеративного пояснителя: объём, ветки, утечки (B.3).

Запуск:  python chat_dataset_stats.py
Пишет:   reports/chat_dataset_stats.json — цифры для docs/ai/model_card.md.

Главная проверка — утечка: ни один промпт из test и holdout не должен встречаться в train.
Формулировки вопросов делятся ещё в gen_dataset.py, здесь мы это подтверждаем на готовых парах.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
REPORTS = ROOT / "reports"
SPLITS = {"train": "chat_sft_train.jsonl", "test": "chat_sft_test.jsonl",
          "holdout": "chat_sft_holdout.jsonl"}


def load(name: str) -> list[dict]:
    path = DATA_DIR / name
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def question(row: dict) -> str:
    return row["messages"][1]["content"].splitlines()[0].removeprefix("ВОПРОС: ").strip().lower()


def stats(rows: list[dict]) -> dict:
    answers = [row["messages"][2]["content"] for row in rows]
    return {
        "size": len(rows),
        "unique_questions": len(set(question(row) for row in rows)),
        "unique_answers": len(set(answers)),
        "branches": dict(Counter(row["meta"]["branch"] for row in rows).most_common()),
        "intents": dict(Counter(row["meta"]["intent"] for row in rows).most_common()),
        "avg_answer_chars": round(sum(len(a) for a in answers) / max(len(answers), 1), 1),
        "avg_prompt_chars": round(
            sum(len(r["messages"][1]["content"]) for r in rows) / max(len(rows), 1), 1),
    }


def main() -> None:
    splits = {name: load(file) for name, file in SPLITS.items()}
    report = {name: stats(rows) for name, rows in splits.items() if rows}

    train_prompts = {row["messages"][1]["content"] for row in splits["train"]}
    train_questions = {question(row) for row in splits["train"]}
    for name in ("test", "holdout"):
        if not splits[name]:
            continue
        prompts = {row["messages"][1]["content"] for row in splits[name]}
        questions = {question(row) for row in splits[name]}
        report[name]["prompt_overlap_with_train"] = len(prompts & train_prompts)
        report[name]["question_overlap_with_train"] = len(questions & train_questions)

    digits_in_answers = sum(
        bool(re.search(r"\d", row["messages"][2]["content"])) for row in splits["train"])
    report["train"]["answers_with_numbers"] = digits_in_answers

    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "chat_dataset_stats.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
