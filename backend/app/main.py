import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as routes_router
from app.api.chat import router as chat_router

load_dotenv()

app = FastAPI(title="Дотяну API")

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "nlu": os.getenv("NLU_MODE", "sklearn"),
        "explain": os.getenv("EXPLAIN_MODE", "templates"),
    }


app.include_router(routes_router)
app.include_router(chat_router)
