"""Проверка терминов на живом проде: определение нашлось и ссылка ведёт на статью (B.9).

Запуск:  python check_prod_terms.py
         python check_prod_terms.py --url http://localhost:8000

Для каждого термина из knowledge.json спрашиваем прод через POST /api/chat и проверяем:
  * intent == "term" — вопрос распознан, а не ушёл в off_topic;
  * есть source.url, это fincult.info и это КОНКРЕТНАЯ статья, а не главная страница;
  * ссылка открывается (код 200), то есть статью не переименовали и не удалили.

Прод на бесплатном тарифе засыпает: первый запрос может идти до минуты.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KNOWLEDGE = ROOT.parent / "backend" / "app" / "data" / "knowledge.json"
PROD = "https://dotyanu-api.onrender.com"
TIMEOUT = 90

SITUATION = {
    "today": "2026-09-27", "balance": 6900, "daily": 300,
    "incomes": [{"id": "i1", "name": "Стипендия", "amount": 3200,
                 "date": "2026-10-10", "confirmed": True}],
    "obligations": [], "spends": [], "goal": None, "categories": None, "history": [],
}


def ask(base: str, message: str) -> dict:
    body = json.dumps({"situation": SITUATION, "message": message}).encode("utf-8")
    request = urllib.request.Request(f"{base}/api/chat", data=body,
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return json.loads(response.read())


def link_alive(url: str) -> tuple[bool, str]:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=40) as response:
            return response.status == 200, str(response.status)
    except urllib.error.HTTPError as error:
        return False, f"HTTP {error.code}"
    except Exception as error:  # noqa: BLE001 — сеть может отвалиться, это тоже результат
        return False, type(error).__name__


def question_for(title: str) -> str:
    clean = title.split("(")[0].strip().strip("«»").strip().lower()
    return f"что такое {clean}?"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=PROD)
    args = parser.parse_args()

    terms = json.loads(KNOWLEDGE.read_text(encoding="utf-8"))
    print(f"{args.url} · терминов в knowledge.json: {len(terms)}\n")

    failures = []
    for term in terms:
        title = term.get("title", "?")
        message = question_for(title)
        try:
            answer = ask(args.url, message)
        except Exception as error:  # noqa: BLE001
            failures.append((title, f"запрос не прошёл: {error}"))
            print(f"[СБОЙ] {title}: {error}")
            continue

        intent = answer.get("intent")
        source = answer.get("source") or {}
        url = str(source.get("url", ""))
        problems = []
        if intent != "term":
            problems.append(f"intent={intent}, а не term")
        if not url:
            problems.append("нет ссылки")
        elif "fincult.info" not in url:
            problems.append(f"ссылка не на fincult.info: {url}")
        elif url.rstrip("/").endswith("fincult.info"):
            problems.append("ссылка на главную, а не на статью")
        else:
            alive, code = link_alive(url)
            if not alive:
                problems.append(f"ссылка не открывается ({code})")

        mark = "OK  " if not problems else "ПЛОХО"
        print(f"[{mark}] {title}\n        вопрос: «{message}»\n        {url or '—'}")
        if problems:
            failures.append((title, "; ".join(problems)))
            print(f"        проблемы: {'; '.join(problems)}")

    print(f"\nитог: {len(terms) - len(failures)} из {len(terms)}")
    for title, reason in failures:
        print(f"  ! {title} — {reason}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
