from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import connect_to_mongo, close_mongo_connection
from app.api.v1.endpoints import auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Before application startup
    connect_to_mongo()
    yield
    # After application shutdown
    close_mongo_connection()

app = FastAPI(
    title="Auth Service",
    description="Handles user authentication and authorization",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Auth Service"}