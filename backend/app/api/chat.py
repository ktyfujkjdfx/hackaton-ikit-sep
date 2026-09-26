"""POST /api/chat — единственный эндпоинт роли B (контракт, раздел 6)."""
from __future__ import annotations

from fastapi import APIRouter

from app.ai.orchestrator import handle
from app.ai.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api")


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return handle(request)
