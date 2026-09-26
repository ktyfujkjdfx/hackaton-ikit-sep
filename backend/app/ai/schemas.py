"""Схемы чата. Единственный источник — app/models.py (владелец A, разделы 5–6 контракта).

Пока A не выложил models.py, здесь лежат те же схемы слово в слово по контракту, чтобы AI-слой
и тесты собирались. Как только имя появляется в app.models — берём его оттуда, не дублируя.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field

try:  # A уже выложил models.py — берём всё оттуда
    import app.models as _models
except Exception:  # noqa: BLE001 — модуля ещё нет, работаем на своих схемах
    _models = None


def _shared(name: str):
    return getattr(_models, name, None) if _models is not None else None


class _Income(BaseModel):
    id: str | None = None
    name: str
    amount: int
    date: date
    confirmed: bool = True


class _Obligation(BaseModel):
    id: str | None = None
    name: str
    amount: int
    date: date


class _Spend(BaseModel):
    id: str | None = None
    name: str
    amount: int
    date: date
    category: str | None = None


class _Goal(BaseModel):
    name: str
    target: int
    current: int
    date: date


class _Category(BaseModel):
    name: str
    per_day: int


class _HistoryOp(BaseModel):
    date: date
    name: str
    amount: int
    category: str | None = None


class _Purchase(BaseModel):
    amount: int
    date: date
    name: str | None = None


class _Situation(BaseModel):
    today: date
    balance: int
    daily: int
    incomes: list[_Income] = Field(default_factory=list)
    obligations: list[_Obligation] = Field(default_factory=list)
    spends: list[_Spend] = Field(default_factory=list)
    goal: _Goal | None = None
    categories: list[_Category] | None = None
    history: list[_HistoryOp] = Field(default_factory=list)


Income = _shared("Income") or _Income
Obligation = _shared("Obligation") or _Obligation
Spend = _shared("Spend") or _Spend
Goal = _shared("Goal") or _Goal
Category = _shared("Category") or _Category
HistoryOp = _shared("HistoryOp") or _HistoryOp
Purchase = _shared("Purchase") or _Purchase
Situation = _shared("Situation") or _Situation

Intent = Literal[
    "purchase_check", "forecast", "explain", "deficit_plan", "categories",
    "term", "add_entry", "invest_info", "refusal", "clarify", "off_topic",
]
Tone = Literal["good", "bad", "neutral"]
ActionKind = Literal[
    "open_explain", "defer", "show_jobs", "save_entry", "open_learn",
    "check_purchase", "open_add_income",
]


class _Fact(BaseModel):
    label: str
    value: str
    tone: Literal["good", "bad"] | None = None


class _ToolCall(BaseModel):
    name: str
    args: dict[str, Any] = Field(default_factory=dict)


class _Action(BaseModel):
    kind: ActionKind
    label: str
    payload: dict[str, Any] = Field(default_factory=dict)


class _Source(BaseModel):
    title: str
    url: str


class _ProposedEntry(BaseModel):
    type: Literal["spend", "income"]
    name: str
    amount: int
    date: date
    confirmed: bool = True
    category: str | None = None


class _NluInfo(BaseModel):
    mode: str
    label: str | None = None
    confidence: float = 0.0


class _ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    text: str = ""
    label: str | None = None


class _ChatRequest(BaseModel):
    situation: _Situation
    purchase: _Purchase | None = None
    message: str = ""
    history: list[_ChatMessage] = Field(default_factory=list)


class _ChatResponse(BaseModel):
    intent: Intent
    tool_calls: list[_ToolCall] = Field(default_factory=list)
    headline: str = ""
    tone: Tone = "neutral"
    facts: list[_Fact] = Field(default_factory=list)
    text: str = ""
    source: _Source | None = None
    purchase: _Purchase | None = None
    proposed_entry: _ProposedEntry | None = None
    actions: list[_Action] = Field(default_factory=list)
    nlu: _NluInfo
    explainer: str = "templates"
    guarded: bool = False


Fact = _shared("Fact") or _Fact
ToolCall = _shared("ToolCall") or _ToolCall
Action = _shared("Action") or _Action
Source = _shared("Source") or _Source
ProposedEntry = _shared("ProposedEntry") or _ProposedEntry
NluInfo = _shared("NluInfo") or _NluInfo
ChatMessage = _shared("ChatMessage") or _ChatMessage
ChatRequest = _shared("ChatRequest") or _ChatRequest
ChatResponse = _shared("ChatResponse") or _ChatResponse
