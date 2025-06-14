# backend/group_service/app/core/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGO_DB_URL: str = os.getenv("MONGO_DB_URL", "mongodb://localhost:27017/group_db")
    # Add other config variables specific to group_service here

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY") # This MUST match auth_service's key
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

settings = Settings()

if not settings.JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable not set in group_service.")