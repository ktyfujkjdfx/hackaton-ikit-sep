"""Датасет для генеративного пояснителя (шаг 3 роли B).

Запуск:  python gen_chat_dataset.py
Пишет:   data/chat_sft_train.jsonl, data/chat_sft_test.jsonl, data/chat_sft_holdout.jsonl

Как собирается один пример:
  1. вопрос берём из уже готового корпуса намерений (`data/intents_*.jsonl`, его делает
     gen_dataset.py) — фразы train и test там не пересекаются, так что сплит честный;
  2. ситуацию берём синтетическую: две демо-персоны плюс случайные варианты (seed 42);
  3. факты считает НАСТОЯЩИЙ движок A через app.ai.tools.execute — цифры в датасете
     ровно те же, что придут модели в проде;
  4. ответ собираем из банка формулировок answer_variants.py, подставляя строки фактов;
  5. каждый готовый ответ прогоняем через app.ai.guard.check — пример, где появилось
     «своё» число, в датасет не попадает. Поэтому модель учится только переписывать факты.

Персональных данных здесь нет и быть не может: все ситуации сгенерированы кодом.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "backend"))
sys.path.insert(0, str(ROOT))

import answer_variants as av  # noqa: E402
from app.ai import guard, parse, templates, tools  # noqa: E402
from app.ai.explain import prompt as prompt_format  # noqa: E402
from app.ai.schemas import Situation  # noqa: E402

SEED = 42
DATA_DIR = ROOT / "data"
SLOT_RE = re.compile(r"\{(\w+)\}")

# Сколько примеров на метку в train. Веса — по тому, как часто это спрашивают в демо.
TRAIN_PER_LABEL: dict[str, int] = {
    "purchase_check": 1300,
    "forecast": 900,
    "explain": 550,
    "deficit_plan": 700,
    "categories": 450,
    "add_spend": 450,
    "add_income": 400,
    "term": 400,
    "invest_advice": 220,
    "credentials": 220,
    "money_operation": 220,
    "off_topic": 300,
}
TEST_SHARE = 0.12
N_SMALLTALK_TRAIN = 420
N_SMALLTALK_TEST = 60

# ------------------------------------------------------------------ ситуации

INCOME_NAMES = ["Стипендия", "Перевод от родителей", "Подработка курьером", "Зарплата",
                "Деньги от мамы", "Аванс", "Повышенная стипендия", "Подработка репетитором"]
OBLIGATION_NAMES = ["Общежитие", "Связь", "Подписка на музыку", "Проездной", "Интернет",
                    "Подписка на кино", "Абонемент в зал", "Аренда комнаты"]
GOAL_NAMES = ["Ноутбук", "Билет домой на Новый год", "Велосипед", "Телефон", "Поездка к морю"]
CATEGORY_NAMES = ["Еда", "Транспорт", "Кафе и доставка", "Прочее", "Учёба", "Здоровье"]


def _persona_situations() -> list[dict]:
    """Демо-персоны роли D — их видит жюри, поэтому они всегда в датасете."""
    from app.engine.personas import load_personas

    return [dict(p["situation"]) for p in load_personas().values()]


def random_situation(rng: random.Random) -> dict:
    """Случайная, но правдоподобная студенческая ситуация. Только синтетика."""
    today = date(2026, 9, 27) + timedelta(days=rng.randint(0, 40))
    balance = rng.choice([300, 700, 1200, 2000, 3000, 4500, 6900, 9000, 12000, 18000,
                          25000, 35000])
    daily = rng.choice([150, 200, 250, 280, 300, 350, 400, 500])

    incomes = []
    for i in range(rng.randint(1, 3)):
        incomes.append({
            "id": f"i{i + 1}",
            "name": rng.choice(INCOME_NAMES),
            "amount": rng.choice([2500, 2800, 3200, 4000, 5000, 7000, 10000, 12000]),
            "date": (today + timedelta(days=rng.randint(2, 28))).isoformat(),
            "confirmed": rng.random() > 0.3,
        })

    obligations = []
    for i in range(rng.randint(0, 4)):
        obligations.append({
            "id": f"o{i + 1}",
            "name": rng.choice(OBLIGATION_NAMES),
            "amount": rng.choice([150, 200, 350, 400, 900, 1500, 1800, 2500]),
            "date": (today + timedelta(days=rng.randint(1, 27))).isoformat(),
        })

    goal = None
    if rng.random() > 0.35:
        target = rng.choice([12000, 20000, 30000, 40000, 60000])
        goal = {
            "name": rng.choice(GOAL_NAMES),
            "target": target,
            "current": rng.randrange(0, target - 1000, 1000),
            "date": (today + timedelta(days=rng.randint(60, 500))).isoformat(),
        }

    categories = None
    if rng.random() > 0.15:
        names = rng.sample(CATEGORY_NAMES, rng.randint(3, 5))
        categories = [{"name": n, "per_day": rng.choice([20, 30, 40, 60, 90, 120, 180])}
                      for n in names]

    return {
        "today": today.isoformat(), "balance": balance, "daily": daily,
        "incomes": incomes, "obligations": obligations, "spends": [],
        "goal": goal, "categories": categories, "history": [],
    }


def situation_pool(rng: random.Random, count: int) -> list[Situation]:
    raw = _persona_situations() + [random_situation(rng) for _ in range(count)]
    pool = []
    for item in raw:
        try:
            pool.append(Situation.model_validate(item))
        except Exception:  # noqa: BLE001 — кривой случайный набор просто пропускаем
            continue
    return pool


# ------------------------------------------------------------------ слоты из фактов

def _facts_map(facts: list[dict]) -> dict[str, str]:
    return {str(f.get("label", "")): str(f.get("value", "")) for f in facts}


def _plan_slots(facts: list[dict]) -> dict[str, str]:
    """Варианты плана движка → слоты {postpone} {reduce} {earn} человеческим языком."""
    slots: dict[str, str] = {}
    for fact in facts:
        label, value = str(fact.get("label", "")), str(fact.get("value", ""))
        ease = value.split(" · ")[0]
        lowered = label[:1].lower() + label[1:]
        if label.startswith("Перенести покупку"):
            slots["postpone"] = f"{lowered} ({ease})"
        elif label.startswith("Тратить на"):
            slots["reduce"] = f"{lowered} ({ease})"
        elif label == "Тратить меньше":
            slots["reduce"] = "меньше тратить уже не выйдет — " + value
        elif label.startswith("Найти "):
            slots["earn"] = f"{lowered} ({ease})"
        elif label.startswith("Цель «"):
            slots["goal_shift"] = value
    return slots


def _quoted(text: str) -> str:
    inner = re.search(r"«([^»]+)»", text)
    return inner.group(1) if inner else text


def slots_for(execution: tools.Execution, label: str) -> tuple[str, dict[str, str]]:
    """Ветка ответа и её слоты. Значения — только готовые строки движка."""
    facts = execution.facts
    by_label = _facts_map(facts)
    text = execution.text
    intent = execution.intent

    if intent == "purchase_check":
        if text == templates.PURCHASE_OUT_OF_HORIZON:
            return "purchase_out_of_horizon", {}
        if text in (templates.PURCHASE_FITS, templates.PURCHASE_TIGHT):
            branch = "purchase_tight" if text == templates.PURCHASE_TIGHT else "purchase_fits"
            return branch, {"min": by_label.get("Самый низкий остаток после покупки", ""),
                            "min_date": by_label.get("Когда", "")}
        slots = {
            "neg_date": by_label.get("Первый день без денег", ""),
            "deficit": by_label.get("Самый большой минус", ""),
        }
        safe = by_label.get("Без минуса можно купить", "")
        slots.update(_plan_slots(facts))
        if text.startswith(templates.PURCHASE_NO_SAFE_DATE):
            return "purchase_no_safe", slots
        slots["safe_date"] = safe[2:] if safe.startswith("с ") else safe
        branch = ("purchase_wait_unconfirmed" if templates.UNCONFIRMED_NOTE in text
                  else "purchase_wait")
        return branch, slots

    if intent == "forecast":
        if text == templates.NO_INCOME:
            return "forecast_no_income", {}
        income_label = next((k for k in by_label if k.startswith("До «")), "")
        slots = {
            "income_name": _quoted(income_label),
            "to_income": by_label.get(income_label, ""),
            "min": by_label.get("Самый низкий остаток", ""),
        }
        if "Минус начнётся" in by_label:
            slots["neg_date"] = by_label["Минус начнётся"]
            return "forecast_risk", slots
        return "forecast_ok", slots

    if intent == "explain":
        return "explain", {
            "balance": by_label.get("Сейчас на карте (факт)", ""),
            "daily": by_label.get("Обычные траты (оценка)", ""),
            "obligations": by_label.get("Обязательные платежи (постоянные)", ""),
            "income": by_label.get("Поступления (ожидается)", ""),
            "min": by_label.get("Итог — самый низкий остаток", ""),
        }

    if intent == "deficit_plan":
        if execution.headline == templates.HEADLINE_NO_DEFICIT:
            return "no_deficit", {}
        slots = _plan_slots(facts)
        slots["deficit"] = execution.headline.split("закрыть ")[-1]
        slots["need"] = by_label.get("Нужно к первому дню без денег", "")
        return "deficit_plan", slots

    if intent == "categories":
        if text == templates.NO_CATEGORIES:
            return "categories_none", {}
        slots = {"top_name": str(facts[0]["label"]), "top_value": str(facts[0]["value"])}
        if len(facts) > 1:
            slots["second_name"] = str(facts[1]["label"])
            slots["second_value"] = str(facts[1]["value"])
        return "categories", slots

    if intent == "add_entry":
        slots = {"amount": by_label.get("Сумма", ""), "date": by_label.get("Дата", ""),
                 "category": by_label.get("Категория", "")}
        if label == "add_income":
            branch = ("add_income_confirmed" if by_label.get("Надёжность") == "точно придёт"
                      else "add_income_unconfirmed")
            return branch, slots
        return "add_spend", slots

    if intent == "clarify":
        if text == templates.CLARIFY_PURCHASE_AMOUNT:
            return "clarify_purchase_amount", {}
        return ("clarify_amount" if text == templates.CLARIFY_AMOUNT else "clarify_unknown"), {}

    if intent == "term":
        return ("term_not_found" if text == templates.TERM_NOT_FOUND else "term"), {}
    if intent == "invest_info":
        return "invest_info", {}
    if intent == "refusal":
        return ("credentials" if label == "credentials" else "money_operation"), {}
    return "off_topic", {}


# ------------------------------------------------------------------ сборка ответа

BRANCH_VARIANTS: dict[str, list[str]] = {
    "purchase_fits": av.PURCHASE_FITS,
    "purchase_tight": av.PURCHASE_TIGHT,
    "purchase_wait": av.PURCHASE_WAIT,
    "purchase_wait_unconfirmed": av.PURCHASE_WAIT_UNCONFIRMED,
    "purchase_no_safe": av.PURCHASE_NO_SAFE,
    "purchase_out_of_horizon": av.PURCHASE_OUT_OF_HORIZON,
    "forecast_ok": av.FORECAST_OK,
    "forecast_risk": av.FORECAST_RISK,
    "forecast_no_income": av.FORECAST_NO_INCOME,
    "explain": av.EXPLAIN,
    "deficit_plan": av.DEFICIT_PLAN + av.DEFICIT_SHORT,
    "no_deficit": av.NO_DEFICIT,
    "categories": av.CATEGORIES,
    "categories_none": av.CATEGORIES_NONE,
    "add_spend": av.ADD_SPEND,
    "add_income_confirmed": av.ADD_INCOME_CONFIRMED,
    "add_income_unconfirmed": av.ADD_INCOME_UNCONFIRMED,
    "credentials": av.REFUSAL_CREDENTIALS,
    "money_operation": av.REFUSAL_MONEY_OPERATION,
    "invest_info": av.INVEST_INFO,
    "off_topic": av.OFF_TOPIC,
    "clarify_amount": av.CLARIFY_AMOUNT,
    "clarify_unknown": av.CLARIFY_UNKNOWN,
    "clarify_purchase_amount": av.CLARIFY_PURCHASE_AMOUNT,
    "term_not_found": av.TERM_NOT_FOUND,
}


def _fits(template: str, slots: dict[str, str]) -> bool:
    return all(slots.get(name) for name in SLOT_RE.findall(template))


def _pick(variants: list[str], slots: dict[str, str], rng: random.Random) -> str | None:
    usable = [v for v in variants if _fits(v, slots)]
    return rng.choice(usable).format(**slots) if usable else None


def build_answer(execution: tools.Execution, label: str, rng: random.Random) -> str | None:
    branch, slots = slots_for(execution, label)

    if branch == "term":
        # Определение термина переписывать нельзя: модель учится отдавать его как есть.
        return rng.choice(av.TERM_LEAD) + execution.text

    text = _pick(BRANCH_VARIANTS.get(branch, []), slots, rng)
    if text is None:
        return None

    if branch in ("purchase_wait", "purchase_wait_unconfirmed", "purchase_no_safe"):
        if rng.random() < 0.55:
            tail = _pick(av.PURCHASE_PLAN_TAIL, slots, rng)
            text += tail or ""
        if rng.random() < 0.3:
            text += _pick(av.PURCHASE_EARN_TAIL, slots, rng) or ""
        if rng.random() < 0.25:
            text += _pick(av.PURCHASE_GOAL_TAIL, slots, rng) or ""
    elif branch == "deficit_plan":
        if templates.DEFICIT_PESSIMISTIC_NOTE in execution.text:
            text = rng.choice(av.DEFICIT_PESSIMISTIC) + text
        if rng.random() < 0.35:
            text += _pick(av.DEFICIT_EARN_TAIL, slots, rng) or ""
    elif branch == "categories" and rng.random() < 0.5:
        text += _pick(av.CATEGORIES_SECOND_TAIL, slots, rng) or ""
    elif branch == "explain" and slots.get("income") and rng.random() < 0.5:
        text += _pick(av.EXPLAIN_INCOME_TAIL, slots, rng) or ""
    return text


# ------------------------------------------------------------------ сборка примеров

def load_questions(path: Path) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        grouped.setdefault(row["label"], []).append(row["text"])
    return grouped


def make_example(message: str, label: str, situation: Situation,
                 rng: random.Random) -> dict | None:
    """Один обучающий пример или None, если движок или guard его забраковали."""
    today = situation.today if isinstance(situation.today, date) else date.fromisoformat(
        str(situation.today))
    slots = parse.parse(message, label, today)
    try:
        execution = tools.execute(label, slots, situation, None, message)
    except Exception:  # noqa: BLE001 — случайная ситуация вне горизонта движка
        return None

    answer = build_answer(execution, label, rng)
    if answer is None:
        return None
    # Главная проверка датасета: в ответе нет ни одного числа и месяца мимо фактов.
    if not guard.check(answer, execution.facts, extra=[execution.headline]):
        return None

    return {
        "messages": [
            {"role": "system", "content": prompt_format.SYSTEM_PROMPT},
            {"role": "user", "content": prompt_format.user_prompt(
                message, execution.intent, execution.headline, execution.facts)},
            {"role": "assistant", "content": answer},
        ],
        "meta": {"label": label, "intent": execution.intent,
                 "branch": slots_for(execution, label)[0]},
    }


def smalltalk_pairs(split: str) -> list[tuple[str, list[str]]]:
    """Фразы «о помощнике», разделённые по сплитам.

    Последняя формулировка каждой группы уходит только в test: иначе одна и та же фраза
    оказалась бы и в обучении, и в проверке — и test перестал бы что-либо мерить.
    """
    pairs = []
    for questions, answers in av.SMALLTALK:
        chosen = questions[-1:] if split == "test" else questions[:-1]
        pairs += [(question, answers) for question in chosen]
    return pairs


def smalltalk_examples(count: int, rng: random.Random, split: str = "train") -> list[dict]:
    """Простые фразы «о помощнике»: расчёта нет, факты пустые."""
    examples = []
    pairs = smalltalk_pairs(split)
    for _ in range(count):
        question, answers = rng.choice(pairs)
        examples.append({
            "messages": [
                {"role": "system", "content": prompt_format.SYSTEM_PROMPT},
                {"role": "user", "content": prompt_format.user_prompt(
                    question, "off_topic", "", [])},
                {"role": "assistant", "content": rng.choice(answers)},
            ],
            "meta": {"label": "off_topic", "intent": "off_topic", "branch": "smalltalk"},
        })
    return examples


def build_split(questions: dict[str, list[str]], pool: list[Situation],
                per_label: dict[str, int], smalltalk: int, rng: random.Random,
                floor_scale: float = 1.0, split: str = "train") -> list[dict]:
    examples: list[dict] = []
    seen: set[str] = set()
    for label, target in per_label.items():
        bank = questions.get(label, [])
        if not bank:
            continue
        made, attempts = 0, 0
        while made < target and attempts < target * 12:
            attempts += 1
            message = rng.choice(bank)
            example = make_example(message, label, rng.choice(pool), rng)
            if example is None:
                continue
            key = example["messages"][1]["content"] + "|" + example["messages"][2]["content"]
            if key in seen:
                continue
            seen.add(key)
            examples.append(example)
            made += 1
    examples += balance_branches(questions, pool, examples, seen, rng, floor_scale)
    examples += smalltalk_examples(smalltalk, rng, split)
    rng.shuffle(examples)
    return examples


# Ветки, которые редко выпадают на случайных ситуациях, но важны в демо.
# «purchase_wait» — это киллер-фича «когда можно купить без минуса», её должно быть много.
BRANCH_FLOOR: dict[str, tuple[str, int]] = {
    "purchase_wait": ("purchase_check", 420),
    "purchase_wait_unconfirmed": ("purchase_check", 150),
    "purchase_tight": ("purchase_check", 150),
    "purchase_fits": ("purchase_check", 280),
    "forecast_risk": ("forecast", 300),
    "deficit_plan": ("deficit_plan", 350),
    "add_income_unconfirmed": ("add_income", 150),
}


def balance_branches(questions: dict[str, list[str]], pool: list[Situation],
                     made: list[dict], seen: set[str], rng: random.Random,
                     floor_scale: float = 1.0) -> list[dict]:
    """Добираем редкие ветки: те же вопросы, но ситуации подбираем, пока ветка не выпадет."""
    have = Counter(row["meta"]["branch"] for row in made)
    extra: list[dict] = []
    for branch, (label, floor) in BRANCH_FLOOR.items():
        bank = questions.get(label, [])
        target = max(6, round(floor * floor_scale))
        attempts = 0
        while have[branch] < target and attempts < target * 60:
            attempts += 1
            example = make_example(rng.choice(bank), label, rng.choice(pool), rng) if bank else None
            if example is None or example["meta"]["branch"] != branch:
                continue
            key = example["messages"][1]["content"] + "|" + example["messages"][2]["content"]
            if key in seen:
                continue
            seen.add(key)
            extra.append(example)
            have[branch] += 1
    return extra


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def report(name: str, rows: list[dict]) -> None:
    branches = Counter(row["meta"]["branch"] for row in rows)
    print(f"{name}: {len(rows)} примеров, веток {len(branches)}")
    for branch, count in branches.most_common():
        print(f"   {branch:28} {count}")


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    rng = random.Random(SEED)
    pool = situation_pool(rng, 240)
    print(f"ситуаций в пуле: {len(pool)} (2 персоны + случайные, seed {SEED})")

    train_questions = load_questions(DATA_DIR / "intents_train.jsonl")
    test_questions = load_questions(DATA_DIR / "intents_test.jsonl")

    train = build_split(train_questions, pool, TRAIN_PER_LABEL, N_SMALLTALK_TRAIN, rng)
    test_per_label = {k: max(8, int(v * TEST_SHARE)) for k, v in TRAIN_PER_LABEL.items()}
    test = build_split(test_questions, pool, test_per_label, N_SMALLTALK_TEST, rng,
                       TEST_SHARE, split="test")

    holdout_path = DATA_DIR / "intents_holdout_team.jsonl"
    holdout: list[dict] = []
    if holdout_path.exists():
        holdout = build_split(load_questions(holdout_path), pool,
                              {label: 6 for label in TRAIN_PER_LABEL}, 0, rng, 0.02)

    write_jsonl(DATA_DIR / "chat_sft_train.jsonl", train)
    write_jsonl(DATA_DIR / "chat_sft_test.jsonl", test)
    if holdout:
        write_jsonl(DATA_DIR / "chat_sft_holdout.jsonl", holdout)

    report("train", train)
    report("test", test)
    if holdout:
        report("holdout (фразы команды)", holdout)


if __name__ == "__main__":
    main()
