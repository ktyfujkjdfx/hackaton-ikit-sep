"""Парсер слотов: сумма, дата, название, категория. Только правила, без модели.

Ничего не считает в деньгах: достаёт из текста числа, даты и названия. Все расчёты — в app.engine.
Порт логики parseAmount/parseDay/addAnswer из docs/prototype.html, расширенный по B.3 (сленг, «3т.р.», «три тысячи»).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta

# --------------------------------------------------------------- словари

MONTHS = {
    "янв": 1, "фев": 2, "мар": 3, "апр": 4, "мая": 5, "май": 5, "июн": 6,
    "июл": 7, "авг": 8, "сен": 9, "окт": 10, "ноя": 11, "дек": 12,
}
MONTH_RE = "|".join(MONTHS)

WEEKDAYS = {
    "понедельник": 0, "вторник": 1, "среду": 2, "среда": 2, "четверг": 3,
    "пятницу": 4, "пятница": 4, "субботу": 5, "суббота": 5, "воскресенье": 6,
}
WEEKDAY_RE = "|".join(WEEKDAYS)

NUMERALS = {
    "полторы": 1.5, "полтора": 1.5, "один": 1, "одна": 1, "два": 2, "две": 2, "три": 3,
    "четыре": 4, "пять": 5, "шесть": 6, "семь": 7, "восемь": 8, "девять": 9, "десять": 10,
    "одиннадцать": 11, "двенадцать": 12, "тринадцать": 13, "четырнадцать": 14,
    "пятнадцать": 15, "шестнадцать": 16, "семнадцать": 17, "восемнадцать": 18,
    "девятнадцать": 19, "двадцать": 20, "тридцать": 30, "сорок": 40, "пятьдесят": 50,
    "шестьдесят": 60, "семьдесят": 70, "восемьдесят": 80, "девяносто": 90, "сто": 100,
    "двести": 200, "триста": 300, "четыреста": 400, "пятьсот": 500, "шестьсот": 600,
    "семьсот": 700, "восемьсот": 800, "девятьсот": 900,
}
THOUSAND_WORDS = ("тысяча", "тысячи", "тысяч", "тыщи", "тыща", "тыщ", "косарь", "косаря")

# «15 октября», «15.10», «15.10.2026» — вырезаем до поиска суммы, чтобы день не стал суммой
DATE_PATTERNS = (
    rf"\b\d{{1,2}}\s*(?:{MONTH_RE})\w*(?:\s+\d{{4}})?",
    r"\b\d{1,2}\.\d{1,2}(?:\.\d{2,4})?\b",
    r"\b\d{1,2}\s*числ\w*",
)

CATEGORY_RULES = (
    ("Транспорт", r"такси|автобус|метро|проезд|маршрутк|трамва|электричк|самокат"),
    ("Кафе и доставка", r"кафе|доставк|кофе|обед|ресторан|бар|пицц|шаурм|бургер|столовк|завтрак|фастфуд"),
    ("Еда", r"продукт|еда|пятероч|магнит|супермаркет|овощ|молок"),
)

INCOME_NAMES = (
    ("Стипендия", r"стипенд|стипух|стипа|стипы"),
    ("Подработка", r"подработ|халтур|смен|курьер|репетитор|листовк"),
    ("Зарплата", r"зарплат|зп\b|аванс|премия|премию"),
    ("Перевод от родителей", r"родител|родак|мама|мамы|папа|папы|бабушк|дедушк"),
)
SPEND_NAME_BY_CATEGORY = {
    "Транспорт": "Такси",
    "Кафе и доставка": "Кафе и доставка",
    "Еда": "Продукты",
    "Прочее": "Трата",
}

UNCONFIRMED_RE = r"не точно|неточно|может|не увер|наверн|вроде|не факт|если получится|обещал|возможно|мож быть"

# Название покупки: «купить наушники», «куплю кроссы», «взять куртку»
PURCHASE_NAME_RE = re.compile(
    r"(?:куп(?:ить|лю|ишь|им)|взять|возьму|брать|беру|заказать|заказыва\w+)\s+"
    r"(?!мне\b|себе\b|за\b|на\b|ли\b)([а-яёa-z][а-яёa-z-]+(?:\s+[а-яёa-z][а-яёa-z-]+)?)",
    re.IGNORECASE,
)


@dataclass
class Slots:
    """Что удалось достать из фразы. Никаких вычислений — только распознанные значения."""

    amount: int | None = None
    date: date | None = None
    date_explicit: bool = False
    name: str | None = None
    category: str | None = None
    confirmed: bool = True


# --------------------------------------------------------------- нормализация

def normalize(text: str) -> str:
    """Нижний регистр, «ё» → «е», склеенные тысячи («3 000» → «3000»), одиночные пробелы."""
    text = text.lower().replace("ё", "е").replace(" ", " ")
    text = re.sub(r"(\d)\s+(?=\d{3}\b)", r"\1", text)
    # «ыыыыыы» → «ыы»: тянутые буквы не должны перевешивать смысл фразы. Цифры не трогаем.
    text = re.sub(r"([^\W\d_])\1{2,}", r"\1\1", text)
    return re.sub(r"\s+", " ", text).strip()


def strip_dates(text: str) -> str:
    """Убирает даты, чтобы их числа не попали в сумму («куплю кроссы за 4к 15 октября»)."""
    for pattern in DATE_PATTERNS:
        text = re.sub(pattern, " ", text)
    return text


# --------------------------------------------------------------- сумма

def _amount_from_digits(text: str) -> int | None:
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(к\b|k\b|тыс\w*|т\.?\s*р\.?|т\b|косар\w*)?", text)
    if not match:
        return None
    value = float(match.group(1).replace(",", "."))
    if match.group(2):
        value *= 1000
    return round(value)


def _amount_from_words(text: str) -> int | None:
    thousands = "|".join(THOUSAND_WORDS)
    numerals = "|".join(sorted(NUMERALS, key=len, reverse=True))
    match = re.search(rf"\b({numerals})\s+({thousands})\b", text)
    if match:
        return round(NUMERALS[match.group(1)] * 1000)
    if re.search(rf"\b({thousands})\b", text):
        return 1000
    match = re.search(rf"\b({numerals})\b", text)
    if match and NUMERALS[match.group(1)] >= 100:
        return round(NUMERALS[match.group(1)])
    return None


def parse_amount(text: str) -> int | None:
    """Сумма в целых рублях или None. Даты в тексте игнорируются."""
    clean = strip_dates(normalize(text))
    amount = _amount_from_digits(clean)
    if amount is None:
        amount = _amount_from_words(clean)
    if amount is None or amount <= 0:
        return None
    return amount


# --------------------------------------------------------------- дата

def _with_year(today: date, day: int, month: int, allow_past: bool) -> date | None:
    """Год берём из today; если дата уже прошла — следующий год (B.10)."""
    for year in (today.year, today.year + 1):
        try:
            value = date(year, month, day)
        except ValueError:
            return None
        if allow_past or value >= today:
            return value
    return None


def parse_date(text: str, today: date, allow_past: bool = False) -> tuple[date | None, bool]:
    """Возвращает (дата, была ли она названа явно). Без даты — (today, False) решает вызывающий."""
    clean = normalize(text)

    if re.search(r"\bпослезавтра\b", clean):
        return today + timedelta(days=2), True
    if re.search(r"\bзавтра\b", clean):
        return today + timedelta(days=1), True
    if re.search(r"\bсегодня\b|\bсейчас\b|\bщас\b|\bпрямо сейчас\b", clean):
        return today, True
    if allow_past and re.search(r"\bвчера\b", clean):
        return today - timedelta(days=1), True
    if allow_past and re.search(r"\bпозавчера\b", clean):
        return today - timedelta(days=2), True

    match = re.search(rf"\b(\d{{1,2}})\s*({MONTH_RE})\w*(?:\s+(\d{{4}}))?", clean)
    if match:
        day, month = int(match.group(1)), MONTHS[match.group(2)]
        if match.group(3):
            try:
                return date(int(match.group(3)), month, day), True
            except ValueError:
                return None, False
        return _with_year(today, day, month, allow_past), True

    match = re.search(r"\b(\d{1,2})\.(\d{1,2})(?:\.(\d{2,4}))?\b", clean)
    if match:
        day, month = int(match.group(1)), int(match.group(2))
        if match.group(3):
            year = int(match.group(3))
            year += 2000 if year < 100 else 0
            try:
                return date(year, month, day), True
            except ValueError:
                return None, False
        return _with_year(today, day, month, allow_past), True

    if re.search(r"на выходных|в выходные|на выходные", clean):
        return today + timedelta(days=(5 - today.weekday()) % 7 or 7), True

    match = re.search(rf"\b({WEEKDAY_RE})\b", clean)
    if match:
        target = WEEKDAYS[match.group(1)]
        return today + timedelta(days=(target - today.weekday()) % 7 or 7), True

    match = re.search(r"\b(\d{1,2})\s*числ\w*", clean)
    if match:
        return _with_year(today, int(match.group(1)), today.month, allow_past), True

    return None, False


# --------------------------------------------------------------- названия и категории

def parse_category(text: str) -> str:
    clean = normalize(text)
    for category, pattern in CATEGORY_RULES:
        if re.search(pattern, clean):
            return category
    return "Прочее"


def parse_purchase_name(text: str) -> str | None:
    match = PURCHASE_NAME_RE.search(normalize(text))
    if not match:
        return None
    name = re.sub(r"\s+(за|на|до|в|к)$", "", match.group(1).strip())
    words = [w for w in name.split() if w not in {"за", "на", "мне", "себе", "ли", "это"}]
    if not words:
        return None
    name = " ".join(words[:2])
    return name[:1].upper() + name[1:]


def parse_income_name(text: str) -> str:
    clean = normalize(text)
    for name, pattern in INCOME_NAMES:
        if re.search(pattern, clean):
            return name
    return "Поступление"


def parse_confirmed(text: str) -> bool:
    return not re.search(UNCONFIRMED_RE, normalize(text))


# --------------------------------------------------------------- сборка

def parse(text: str, label: str, today: date) -> Slots:
    """Слоты под конкретную метку: у трат дата может быть в прошлом, у покупок — нет."""
    allow_past = label == "add_spend"
    parsed_date, explicit = parse_date(text, today, allow_past=allow_past)
    slots = Slots(
        amount=parse_amount(text),
        date=parsed_date if explicit else None,
        date_explicit=explicit,
    )
    if label == "purchase_check":
        slots.name = parse_purchase_name(text)
    elif label == "add_spend":
        slots.category = parse_category(text)
        slots.name = parse_purchase_name(text) or SPEND_NAME_BY_CATEGORY[slots.category]
    elif label == "add_income":
        slots.name = parse_income_name(text)
        slots.confirmed = parse_confirmed(text)
    return slots
