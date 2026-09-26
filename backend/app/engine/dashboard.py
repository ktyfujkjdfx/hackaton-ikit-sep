from app.engine.dates import H, date_at
from app.engine.events import events
from app.engine.format import format_date_ru, format_rub
from app.engine.goal import goal_plan
from app.engine.headline import build_headline, has_unconfirmed
from app.engine.history import history_items
from app.engine.plans import deficit_plan
from app.engine.purchase import check_purchase
from app.engine.series import series, to_day_series
from app.engine.types import money_types
from app.models import Dashboard, Purchase, Scenarios, Situation


def _has_negative(values: list[int] | None) -> bool:
    return values is not None and min(values) < 0


def assumptions(sit: Situation, purchase: Purchase | None) -> list[str]:
    source = "по истории за 2 месяца" if sit.categories else "из анкеты"
    out = [f"Обычные траты — {format_rub(sit.daily)} в день, оценка {source}"]
    if any(i.confirmed for i in sit.incomes):
        out.append("Постоянный доход придёт в указанную дату и в указанной сумме")
    for i in sit.incomes:
        if not i.confirmed:
            out.append(f"«{i.name}» может не прийти — показываем прогноз и с ним, и без него")
    if sit.obligations:
        out.append("Обязательные платежи спишутся в указанные даты")
    if sit.spends:
        out.append("Разовые траты, которые ты записал, — это факт")
    if sit.history:
        out.append("Прошлые операции уже учтены в остатке на карте и в прогноз не входят")
    if purchase is not None:
        out.append("Покупка — только проверка: мы её не совершаем и ничего не списываем")
    return out


def unknowns(sit: Situation) -> list[str]:
    return [
        "Будущие необычные траты: подарки, поломки, внезапные поездки",
        "Придут ли деньги точно в срок. Если перевод задержится, график станет хуже",
        "Как изменятся твои привычки. Траты в день — это среднее, а не план",
        f"Что будет после {format_date_ru(date_at(sit, H - 1))}: прогноз строится на 30 дней",
    ]


def build_dashboard(sit: Situation, purchase: Purchase | None) -> Dashboard:
    base = series(sit)
    pess = series(sit, pessimistic=True) if has_unconfirmed(sit) else None
    buy = series(sit, purchase=purchase) if purchase is not None else None
    buy_pess = (series(sit, purchase=purchase, pessimistic=True)
                if purchase is not None and pess is not None else None)

    if _has_negative(base):
        plan = deficit_plan(sit, base, "base")
    elif _has_negative(pess):
        plan = deficit_plan(sit, pess, "pessimistic")
    else:
        plan = None

    return Dashboard(
        today=sit.today,
        horizon_days=H,
        headline=build_headline(sit, base, pess),
        scenarios=Scenarios(
            base=to_day_series(sit, base),
            pessimistic=to_day_series(sit, pess) if pess is not None else None,
            with_purchase=to_day_series(sit, buy) if buy is not None else None,
            with_purchase_pessimistic=to_day_series(sit, buy_pess) if buy_pess is not None else None,
        ),
        events=events(sit, purchase),
        money_types=money_types(sit),
        goal=goal_plan(sit, purchase.amount if purchase is not None else 0),
        purchase=check_purchase(sit, purchase) if purchase is not None else None,
        deficit_plan=plan,
        history=history_items(sit),
        show_learn_card=not (_has_negative(base) or _has_negative(buy) or _has_negative(pess)),
        assumptions=assumptions(sit, purchase),
        unknowns=unknowns(sit),
    )
