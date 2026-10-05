# app/main.py

# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from sqlalchemy import text


from app.auth.router import router as auth_router
from app.core.database import engine
from app.core.redis_client import redis_client
from app.transactions.router import router as transactions_router
from app.financial.router import router as financial_router
from app.credit.router import router as credit_router
from app.schemes.router import router as schemes_router
from app.fraud.router import router as fraud_router
# pyrefly: ignore [missing-import]
from app.copilot.router import router as copilot_router
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from app.consent.router import router as consent_router
from app.core.logging_config import configure_logging
from app.core.middleware import request_logging_middleware


app = FastAPI(
    title="Financial Compass API",
    version="0.1.0",
)

app.middleware("http")(request_logging_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(transactions_router)
app.include_router(financial_router)
app.include_router(credit_router)
app.include_router(schemes_router)
app.include_router(fraud_router)
app.include_router(copilot_router)
app.include_router(consent_router)


@app.get("/health")
async def health_check():
    status = {"api": "ok", "database": "unknown", "redis": "unknown"}

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        status["database"] = "ok"
    except Exception as e:
        status["database"] = f"error: {e}"

    try:
        pong = await redis_client.ping()
        status["redis"] = "ok" if pong else "error: no pong"
    except Exception as e:
        status["redis"] = f"error: {e}"

    return status


@app.on_event("startup")
async def on_startup():
    configure_logging()