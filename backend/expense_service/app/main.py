from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import connect_to_mongo, close_mongo_connection
from app.core.rabbitmq import connect_to_rabbitmq, close_rabbitmq_connection
from app.api.v1.endpoints import expenses

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_rabbitmq() # Connect RabbitMQ before app startup
    connect_to_mongo()
    yield
    close_mongo_connection()
    await close_rabbitmq_connection() # Close RabbitMQ after app shutdown

app = FastAPI(
    title="Expense Service",
    description="Manages group expenses and publishes events for AI splitting",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(expenses.router, prefix="/expenses", tags=["Expenses"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Expense Service"}