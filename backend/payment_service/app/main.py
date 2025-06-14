from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import connect_to_mongo, close_mongo_connection
from app.api.v1.endpoints import payments

@asynccontextmanager
async def lifespan(app: FastAPI):
    connect_to_mongo()
    yield
    close_mongo_connection()

app = FastAPI(
    title="Payment Service",
    description="Processes dummy payments via Stripe and tracks balances",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(payments.router, prefix="/payments", tags=["Payments"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Payment Service"}