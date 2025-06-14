import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGO_DB_URL: str = os.getenv("MONGO_DB_URL", "mongodb://localhost:27017/auth_db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-jwt-key-replace-this")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

settings = Settings()