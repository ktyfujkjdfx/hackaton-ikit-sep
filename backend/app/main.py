import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.chat import router as chat_router
from app.api.routes import router as routes_router

load_dotenv()

app = FastAPI(title="Дотяну API")

cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

SECTIONS = {"balance", "daily", "incomes", "obligations", "spends", "goal", "purchase"}


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    """Ошибки валидации движка отдаём ровно как { "errors": [...] }, без обёртки detail."""
    if isinstance(exc.detail, dict) and "errors" in exc.detail:
        return JSONResponse(exc.detail, status_code=exc.status_code)
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


def _request_error(err: dict) -> dict:
    """Ошибку формы запроса (не число, нет поля) переводим в ValidationError раздела 6."""
    loc = [p for p in err.get("loc", []) if p not in ("body", "situation")]
    field = next((p for p in loc if p in SECTIONS), str(loc[0]) if loc else "body")
    index = next((p for p in loc if isinstance(p, int)), None)
    subfield = next((p for p in loc if p in ("amount", "date")), None)
    if err.get("type") == "missing":
        message = "Заполни это поле."
    elif err.get("type") == "int_from_float":
        message = "Укажи сумму в целых рублях, без копеек."
    elif subfield == "date" or "date" in err.get("type", ""):
        message = "Укажи дату в формате ГГГГ-ММ-ДД."
    else:
        message = "Укажи число без букв и пробелов."
    return {"field": field, "index": index, "subfield": subfield, "message": message}


@app.exception_handler(RequestValidationError)
async def request_error(request: Request, exc: RequestValidationError):
    return JSONResponse({"errors": [_request_error(e) for e in exc.errors()]}, status_code=422)


app.include_router(routes_router)
app.include_router(chat_router)
