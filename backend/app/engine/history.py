from app.models import HistoryItem, Situation

REGULAR_CATEGORY = "Обязательное"
LARGE_DAYS = 5


def history_items(sit: Situation) -> list[HistoryItem]:
    """История с метками «регулярный» и «крупная трата»."""
    confirmed_names = {i.name for i in sit.incomes if i.confirmed}
    items = []
    for op in sit.history:
        regular = op.category == REGULAR_CATEGORY or (op.amount > 0 and op.name in confirmed_names)
        large = op.amount < 0 and not regular and -op.amount >= LARGE_DAYS * sit.daily
        items.append(HistoryItem(**op.model_dump(), regular=regular, large=large))
    return items
