from app.engine.dates import H, day_index
from app.models import Purchase, Situation, ValidationError


def validate(sit: Situation, purchase: Purchase | None = None) -> list[ValidationError]:
    """Ошибки ввода простыми словами. Пустой список — всё в порядке."""
    errors: list[ValidationError] = []

    def err(field, message, index=None, subfield=None):
        errors.append(ValidationError(field=field, index=index, subfield=subfield, message=message))

    if sit.balance < 0:
        err("balance", "Сумма не может быть отрицательной. Если на карте минус по кредитке — "
                       "укажи 0 и добавь долг как платёж.")
    if sit.daily < 0:
        err("daily", "Траты не могут быть отрицательными.")

    for k, i in enumerate(sit.incomes):
        if i.amount <= 0:
            err("incomes", "Сумма поступления должна быть больше нуля.", k, "amount")
        if day_index(sit, i.date) < 0:
            err("incomes", "Дата поступления уже прошла. Укажи следующую.", k, "date")

    for k, o in enumerate(sit.obligations):
        if o.amount <= 0:
            err("obligations", "Сумма платежа должна быть больше нуля.", k, "amount")
        if day_index(sit, o.date) < 0:
            err("obligations", "Дата платежа уже прошла.", k, "date")

    g = sit.goal
    if g is not None:
        if g.target <= 0:
            err("goal", "Укажи, сколько нужно на цель.", subfield="amount")
        elif g.current < 0:
            err("goal", "Сколько уже накоплено — число от 0.", subfield="amount")
        elif g.current >= g.target:
            err("goal", "Цель уже накоплена — поздравляем! Убери её или увеличь сумму.",
                subfield="amount")
        if day_index(sit, g.date) <= 0:
            err("goal", "Дата цели должна быть в будущем.", subfield="date")

    if purchase is not None:
        if purchase.amount <= 0:
            err("purchase", "Сумма покупки должна быть больше нуля.", subfield="amount")
        if not 0 <= day_index(sit, purchase.date) < H:
            err("purchase", "Можно проверить покупку в ближайшие 30 дней.", subfield="date")

    return errors
