"""12 меток модели (docs/CONTRACT.md, раздел 9). Порядок фиксирован: он же порядок выходов модели.

Менять только через чат команды.
"""

LABELS: tuple[str, ...] = (
    "purchase_check",
    "forecast",
    "explain",
    "deficit_plan",
    "categories",
    "term",
    "add_spend",
    "add_income",
    "invest_advice",
    "credentials",
    "money_operation",
    "off_topic",
)

LABEL_TO_ID: dict[str, int] = {label: i for i, label in enumerate(LABELS)}

# Метка модели -> ChatResponse.intent (раздел 9). Нет суммы там, где она нужна, — clarify (решает tools.py).
LABEL_TO_INTENT: dict[str, str] = {
    "purchase_check": "purchase_check",
    "forecast": "forecast",
    "explain": "explain",
    "deficit_plan": "deficit_plan",
    "categories": "categories",
    "term": "term",
    "add_spend": "add_entry",
    "add_income": "add_entry",
    "invest_advice": "invest_info",
    "credentials": "refusal",
    "money_operation": "refusal",
    "off_topic": "off_topic",
}
