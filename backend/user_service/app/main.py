from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import connect_to_mongo, close_mongo_connection
from app.api.v1.endpoints import users

@asynccontextmanager
async def lifespan(app: FastAPI):
    # connect_to_mongo is not an awaitable function in your database.py, so remove await
    connect_to_mongo() 
    yield
    # close_mongo_connection is not an awaitable function
    close_mongo_connection() 

app = FastAPI(
    title="User Service",
    description="Manages user profiles and friend relationships",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(users.router, prefix="/users", tags=["Users"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "User Service"}