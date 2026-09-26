"""Поиск финансового термина в backend/app/data/knowledge.json (владелец D).

Пока файла нет, работает встроенный минимум из docs/prototype.html (словарь TERMS),
чтобы демо отвечало на «что такое финансовая подушка» без зависимости от чужой задачи.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.ai.parse import normalize

log = logging.getLogger(__name__)

KNOWLEDGE_PATH = Path(__file__).resolve().parent.parent / "data" / "knowledge.json"
DEFAULT_SOURCE = {"title": "fincult.info — сайт Банка России", "url": "https://fincult.info"}

# Запасной словарь = TERMS из прототипа
FALLBACK_TERMS: list[dict] = [
    {"term": "Финансовая подушка",
     "aliases": ["подушка", "подушка безопасности", "финансовая подушка"],
     "definition": "Запас денег на случай, если доход пропал или случилась непредвиденная трата. "
                   "Её держат отдельно от денег на каждый день и не тратят на покупки."},
    {"term": "Кассовый разрыв",
     "aliases": ["кассовый разрыв", "кассовый"],
     "definition": "Ситуация, когда деньги в итоге придут, но в какие-то дни их не хватает на расходы. "
                   "Именно его показывает красная зона на графике."},
    {"term": "Рассрочка",
     "aliases": ["рассрочка"],
     "definition": "Покупка, которую оплачиваешь частями. Каждый будущий платёж — это обязательный расход, "
                   "его нужно добавить в платежи."},
    {"term": "Кредитный лимит",
     "aliases": ["кредитный лимит", "кредитка", "кредитная карта"],
     "definition": "Деньги банка, которые можно потратить и потом вернуть, часто с процентами. "
                   "Это не твой остаток: в прогнозе мы его не учитываем."},
    {"term": "Вклад",
     "aliases": ["вклад", "депозит"],
     "definition": "Деньги, которые ты кладёшь в банк на срок под процент. Снять раньше срока обычно можно, "
                   "но проценты при этом теряются."},
    {"term": "Инфляция",
     "aliases": ["инфляция"],
     "definition": "Рост цен со временем: на ту же сумму через год купишь меньше. Поэтому деньги, "
                   "которые просто лежат, постепенно обесцениваются."},
    {"term": "Кэшбэк",
     "aliases": ["кэшбэк", "кешбэк"],
     "definition": "Возврат части суммы покупки на карту. Это скидка задним числом, а не доход: "
                   "тратить больше ради кэшбэка невыгодно."},
]


@dataclass
class Term:
    term: str
    definition: str
    source: dict


def _source_of(raw: dict) -> dict:
    """Источник из knowledge.json, если он уже заполнен; иначе fincult.info по умолчанию."""
    source = raw.get("source")
    if isinstance(source, dict) and str(source.get("url", "")).startswith("http"):
        return {"title": source.get("title", DEFAULT_SOURCE["title"]), "url": source["url"]}
    url = str(raw.get("source_url", ""))
    if url.startswith("http"):
        return {"title": raw.get("source_title") or DEFAULT_SOURCE["title"], "url": url}
    return DEFAULT_SOURCE


def _title_aliases(title: str) -> list[str]:
    """Разбивает составной заголовок на самостоятельные синонимы.

    «Вклад и накопительный счёт» → «вклад», «накопительный счёт»: иначе вопрос
    «что такое накопительный счёт» не находит термин, хотя он описан.
    «Сплит» (оплата частями) → «сплит», «оплата частями».
    """
    aliases = [title]
    inside = re.findall(r"[«(]([^»)]+)[»)]", title)
    aliases += inside
    outside = re.sub(r"[«(][^»)]*[»)]", " ", title)
    for part in [outside, *inside]:
        for piece in re.split(r"\s+и\s+|\s*[/,;]\s*", part):
            piece = piece.strip(" «»()\"'")
            if len(piece) >= 5:
                aliases.append(piece)
    return aliases


def _normalize_entry(raw: dict) -> dict | None:
    term = raw.get("term") or raw.get("title") or raw.get("name")
    definition = raw.get("definition") or raw.get("text") or raw.get("description") or raw.get("d")
    if not term or not definition:
        return None
    # D пишет корень слова в "key" («вклад», «подушк») — это и есть главный синоним
    aliases = list(raw.get("aliases") or raw.get("keys") or raw.get("synonyms") or [])
    if raw.get("key"):
        aliases.append(raw["key"])
    return {
        "term": str(term),
        "definition": str(definition),
        "aliases": [str(a) for a in aliases] + _title_aliases(str(term)),
        "source": _source_of(raw),
    }


@lru_cache(maxsize=1)
def _entries() -> list[dict]:
    """knowledge.json от D, если он есть; иначе встроенный словарь прототипа."""
    raw_entries: list[dict] = []
    if KNOWLEDGE_PATH.exists():
        try:
            data = json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data = data.get("terms", data.get("items", list(data.values())))
            raw_entries = [item for item in data if isinstance(item, dict)]
        except Exception:  # noqa: BLE001
            log.exception("не удалось прочитать %s — беру встроенный словарь", KNOWLEDGE_PATH)
    entries = [e for e in (_normalize_entry(r) for r in raw_entries) if e]
    for entry in entries:
        entry["aliases"] = sorted({normalize(a) for a in entry["aliases"]}, key=len, reverse=True)

    # Встроенные термины прототипа добавляем только там, где у D пока пусто:
    # так чат отвечает и про кэшбэк с депозитом, а тексты D всегда в приоритете.
    covered = {alias for entry in entries for alias in entry["aliases"]}
    for raw in FALLBACK_TERMS:
        entry = _normalize_entry(raw)
        aliases = [normalize(a) for a in entry["aliases"]]
        # оставляем только те синонимы, которых у D нет: «вклад» уже описан, а «депозит» ещё нет
        free = {a for a in aliases if not any(a in known or known in a for known in covered)}
        if free:
            entry["aliases"] = sorted(free, key=len, reverse=True)
            entries.append(entry)
    return entries


def reload() -> None:
    """Сбросить кэш (нужно тестам и после того, как D выложит файл)."""
    _entries.cache_clear()


def find(text: str) -> Term | None:
    """Термин, упомянутый во фразе, или None."""
    clean = normalize(text)
    if not clean:
        return None
    best: tuple[int, dict] | None = None
    for entry in _entries():
        for alias in entry["aliases"]:
            if alias and alias in clean and (best is None or len(alias) > best[0]):
                best = (len(alias), entry)
                break
    if best is None:
        return None
    entry = best[1]
    return Term(entry["term"], entry["definition"], entry["source"])
