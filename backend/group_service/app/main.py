from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import connect_to_mongo, close_mongo_connection
from app.api.v1.endpoints import groups

@asynccontextmanager
async def lifespan(app: FastAPI):
    connect_to_mongo()
    yield
    close_mongo_connection()

app = FastAPI(
    title="Group Service",
    description="Manages shared expense groups",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(groups.router, prefix="/groups", tags=["Groups"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Group Service"}