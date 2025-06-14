import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGO_DB_URL: str = os.getenv("MONGO_DB_URL", "mongodb://localhost:27017/expense_db")
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")

settings = Settings()