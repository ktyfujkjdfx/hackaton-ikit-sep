"""Все эндпоинты раздела 6, кроме /api/chat (роль B)."""
import os

from fastapi import APIRouter, HTTPException

from app.engine import build_dashboard, check_purchase, run_checks, validate
from app.engine.personas import load_personas
from app.models import (ChecksResult, Dashboard, DashboardRequest, HealthResponse, PersonaDetail,
                        PersonaSummary, Purchase, PurchaseCheck, PurchaseCheckRequest, Situation,
                        ValidateRequest, ValidateResponse)

router = APIRouter(prefix="/api")


def _nlu_mode() -> str:
    try:
        from app.ai.nlu import current_mode
    except ImportError:
        return os.getenv("NLU_MODE", "sklearn")
    return current_mode()


def _ensure_valid(sit: Situation, purchase: Purchase | None) -> None:
    errors = validate(sit, purchase)
    if errors:
        raise HTTPException(422, {"errors": [e.model_dump(mode="json") for e in errors]})


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(ok=True, nlu=_nlu_mode(), explain=os.getenv("EXPLAIN_MODE", "templates"))


@router.get("/personas", response_model=list[PersonaSummary])
def personas():
    return [PersonaSummary(id=pid, title=p["title"], subtitle=p["subtitle"])
            for pid, p in load_personas().items()]


@router.get("/personas/{persona_id}", response_model=PersonaDetail)
def persona(persona_id: str):
    p = load_personas().get(persona_id)
    if p is None:
        raise HTTPException(404, "Нет такой демо-персоны")
    return PersonaDetail(id=persona_id, who=p["who"], situation=p["situation"])


@router.post("/validate", response_model=ValidateResponse)
def validate_situation(req: ValidateRequest):
    errors = validate(req.situation)
    return ValidateResponse(ok=not errors, errors=errors)


@router.post("/dashboard", response_model=Dashboard)
def dashboard(req: DashboardRequest):
    _ensure_valid(req.situation, req.purchase)
    return build_dashboard(req.situation, req.purchase)


@router.post("/purchase/check", response_model=PurchaseCheck)
def purchase_check(req: PurchaseCheckRequest):
    _ensure_valid(req.situation, req.purchase)
    return check_purchase(req.situation, req.purchase)


@router.get("/checks", response_model=ChecksResult)
def checks():
    return run_checks()
