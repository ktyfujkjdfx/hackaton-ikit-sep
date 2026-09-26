"""Pydantic-схемы API. Источник истины — docs/CONTRACT.md, разделы 5–6."""
import datetime as dt
import os
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field


def demo_today() -> dt.date:
    return dt.date.fromisoformat(os.getenv("DEMO_TODAY", "2026-09-27"))


# ---------- Раздел 5. Модель данных ----------

class Income(BaseModel):
    id: str
    name: str
    amount: int
    date: dt.date
    confirmed: bool


class Obligation(BaseModel):
    id: str
    name: str
    amount: int
    date: dt.date


class Spend(BaseModel):
    id: str
    name: str
    amount: int
    date: dt.date
    category: str


class Goal(BaseModel):
    name: str
    target: int
    current: int
    date: dt.date


class Category(BaseModel):
    name: str
    per_day: int


class HistoryOp(BaseModel):
    date: dt.date
    name: str
    amount: int
    category: str


class Situation(BaseModel):
    today: dt.date = Field(default_factory=demo_today)
    balance: int
    daily: int
    incomes: list[Income] = []
    obligations: list[Obligation] = []
    spends: list[Spend] = []
    goal: Goal | None = None
    categories: list[Category] | None = None
    history: list[HistoryOp] = []


class Purchase(BaseModel):
    amount: int
    date: dt.date
    name: str | None = None


# ---------- Раздел 6. API ----------

class ValidationError(BaseModel):
    field: Literal["balance", "daily", "incomes", "obligations", "spends", "goal", "purchase"]
    index: int | None = None
    subfield: Literal["amount", "date"] | None = None
    message: str


class SeriesStats(BaseModel):
    min: int
    min_date: dt.date
    first_negative_date: dt.date | None
    last_negative_date: dt.date | None
    max_deficit: int
    first_negative_amount: int


class DayPoint(BaseModel):
    date: dt.date
    balance: int


class DaySeries(BaseModel):
    days: list[DayPoint]
    stats: SeriesStats


class NextIncome(BaseModel):
    name: str
    date: dt.date
    days: int
    confirmed: bool


class Headline(BaseModel):
    state: Literal["ok", "tight", "deficit", "depends", "no_income"]
    next_income: NextIncome | None
    next_confirmed_income: NextIncome | None
    min_balance: int
    min_date: dt.date
    first_negative_date: dt.date | None
    max_deficit: int
    days_of_spending_left: int | None


class Event(BaseModel):
    date: dt.date
    kind: Literal["income", "obligation", "spend", "purchase"]
    name: str
    amount: int
    confirmed: bool | None


class IncomeGroup(BaseModel):
    total: int
    items: list[Income]


class ObligationGroup(BaseModel):
    total: int
    items: list[Obligation]


class VariableExpenses(BaseModel):
    total: int
    daily: int
    days: int
    one_off: list[Spend]


class MoneyTypes(BaseModel):
    stable_income: IncomeGroup
    unstable_income: IncomeGroup
    stable_expenses: ObligationGroup
    variable_expenses: VariableExpenses
    reliable_total: int


Ease = Literal["easy", "hard"]


class PostponeOption(BaseModel):
    kind: Literal["postpone"] = "postpone"
    date: dt.date
    ease: Literal["easy"] = "easy"


class ReduceOption(BaseModel):
    kind: Literal["reduce"] = "reduce"
    per_day: int
    new_daily: int
    until: dt.date
    days: int
    possible: bool
    ease: Ease
    flexible_per_day: int


class EarnOption(BaseModel):
    kind: Literal["earn"] = "earn"
    amount: int
    by_date: dt.date
    first_amount: int
    first_date: dt.date
    ease: Ease


PlanOption = Annotated[Union[PostponeOption, ReduceOption, EarnOption], Field(discriminator="kind")]


class DeficitPlan(BaseModel):
    deficit: int
    by_date: dt.date
    first_needed_amount: int
    first_needed_date: dt.date
    based_on: Literal["base", "pessimistic", "purchase"]
    options: list[PlanOption]


class GoalPlan(BaseModel):
    monthly_surplus: int
    per_day: float
    remaining: int
    eta: dt.date | None
    late_days: int | None
    need_monthly: int | None
    eta_with_purchase: dt.date | None
    shift_days: int | None


class PurchaseCheck(BaseModel):
    purchase: Purchase
    verdict: Literal["ok", "tight", "deficit"]
    before: SeriesStats
    after: SeriesStats
    earliest_safe_date: dt.date | None
    safe_depends_on_unconfirmed: bool
    goal: GoalPlan | None
    plan: DeficitPlan | None


class HistoryItem(HistoryOp):
    regular: bool
    large: bool


class Scenarios(BaseModel):
    base: DaySeries
    pessimistic: DaySeries | None
    with_purchase: DaySeries | None
    with_purchase_pessimistic: DaySeries | None


class Dashboard(BaseModel):
    today: dt.date
    horizon_days: int = 30
    headline: Headline
    scenarios: Scenarios
    events: list[Event]
    money_types: MoneyTypes
    goal: GoalPlan | None
    purchase: PurchaseCheck | None
    deficit_plan: DeficitPlan | None
    history: list[HistoryItem]
    show_learn_card: bool
    assumptions: list[str]
    unknowns: list[str]


class CheckItem(BaseModel):
    id: int
    title: str
    expected: str
    got: str
    ok: bool


class ChecksResult(BaseModel):
    passed: int
    total: int
    items: list[CheckItem]


# ---------- Запросы и ответы эндпоинтов ----------

class HealthResponse(BaseModel):
    ok: bool
    nlu: Literal["onnx", "sklearn", "rules"]
    explain: Literal["templates", "local", "yandex", "anthropic"]


class PersonaSummary(BaseModel):
    id: str
    title: str
    subtitle: str


class PersonaDetail(BaseModel):
    id: str
    who: str
    situation: Situation


class ValidateRequest(BaseModel):
    situation: Situation


class ValidateResponse(BaseModel):
    ok: bool
    errors: list[ValidationError]


class DashboardRequest(BaseModel):
    situation: Situation
    purchase: Purchase | None = None


class PurchaseCheckRequest(BaseModel):
    situation: Situation
    purchase: Purchase


# ---------- Чат (эндпоинт — роль B) ----------

class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    text: str


class ChatRequest(BaseModel):
    situation: Situation
    purchase: Purchase | None = None
    message: str
    history: list[ChatTurn] = []


class ToolCall(BaseModel):
    name: str
    args: dict[str, Any] = {}


class Fact(BaseModel):
    label: str
    value: str
    tone: Literal["good", "bad", "neutral"] | None = None


class Source(BaseModel):
    title: str
    url: str


class ProposedEntry(BaseModel):
    type: Literal["spend", "income"]
    name: str
    amount: int
    date: dt.date
    confirmed: bool = True
    category: str | None = None


class ChatAction(BaseModel):
    kind: Literal["open_explain", "defer", "show_jobs", "save_entry", "open_learn",
                  "check_purchase", "open_add_income"]
    label: str
    payload: dict[str, Any] = {}


class NluInfo(BaseModel):
    mode: Literal["onnx", "sklearn", "rules"]
    label: str
    confidence: float


class ChatResponse(BaseModel):
    intent: Literal["purchase_check", "forecast", "explain", "deficit_plan", "categories",
                    "term", "add_entry", "invest_info", "refusal", "clarify", "off_topic"]
    tool_calls: list[ToolCall] = []
    headline: str
    tone: Literal["good", "bad", "neutral"]
    facts: list[Fact] = []
    text: str
    source: Source | None = None
    purchase: Purchase | None = None
    proposed_entry: ProposedEntry | None = None
    actions: list[ChatAction] = []
    nlu: NluInfo
    explainer: Literal["templates", "local", "yandex", "anthropic"]
    guarded: bool = False
